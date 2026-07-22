#!/usr/bin/env python3
"""
Batch skip-trace + property-value enrichment.

Pipeline, per input phone number:

    phone
      -> /search/byphone        (skiptrace.realtyapi.io)  -> candidate people
      -> /search/detailsbyID    (skiptrace.realtyapi.io)  -> the phone owner's
                                                             name / age / current address / emails / relatives
      -> /byaddress             (zillow.realtyapi.io)     -> property value (Zestimate) for that address
      -> /detailsbyaddress      (redfin.realtyapi.io)     -> Redfin Estimate  (fallback if no Zestimate)

Reads phone numbers from input.csv, writes one row per phone to output.csv
(and, optionally, a lossless output.json).

Run:
    pip install -r requirements.txt
    echo "rt_your_key_here" > api_key.txt
    python main.py --input input.csv --output output.csv --workers 10 --rps 10

Resume a half-finished run (skips phones already in output.csv):
    python main.py --resume
"""

import os
import re
import csv
import sys
import json
import time
import argparse
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

# ------------------------------------------------------------------ config ----

REALTYAPI_KEY = ""
DEFAULT_AUTH_FILE = "api_key.txt"

SKIPTRACE_BASE = "https://skiptrace.realtyapi.io"
ZILLOW_BASE    = "https://zillow.realtyapi.io"
REDFIN_BASE    = "https://redfin.realtyapi.io"


def auth_headers():
    return {"x-realtyapi-key": REALTYAPI_KEY}

TIMEOUT = 45
RETRIES = 3
MAX_CANDIDATES = 6

FIELDS = [
    "input_phone",
    "name",
    "age",
    "property_value",
    "value_source",
    "occupation",
]


# ------------------------------------------------------------- small helpers --

def digits(s):
    return re.sub(r"\D", "", s or "")


def norm10(s):
    """Last 10 digits, for comparing phone numbers regardless of format / country code."""
    d = digits(s)
    if len(d) == 11 and d.startswith("1"):
        d = d[1:]
    return d


class RateLimiter:
    """Simple global requests-per-second cap, shared across worker threads."""
    def __init__(self, rps):
        self.min_interval = (1.0 / rps) if rps and rps > 0 else 0.0
        self.lock = threading.Lock()
        self.next_at = 0.0

    def wait(self):
        if self.min_interval <= 0:
            return
        with self.lock:
            now = time.monotonic()
            start = max(now, self.next_at)
            self.next_at = start + self.min_interval
        sleep_for = start - now
        if sleep_for > 0:
            time.sleep(sleep_for)


def http_get_json(url, headers, params, limiter):
    """GET with retry/backoff on 429/5xx. Returns parsed JSON dict, or {'__error__': ...}."""
    last = "unknown error"
    for attempt in range(RETRIES):
        limiter.wait()
        try:
            r = requests.get(url, headers=headers, params=params, timeout=TIMEOUT)
            if r.status_code == 200:
                try:
                    return r.json()
                except ValueError:
                    return {"__error__": "non-JSON 200", "__body__": r.text[:200]}
            if r.status_code in (429, 500, 502, 503, 504):
                last = f"HTTP {r.status_code}"
                time.sleep(min(2 ** attempt, 8))
                continue
            return {"__error__": f"HTTP {r.status_code}", "__body__": r.text[:200]}
        except requests.RequestException as e:
            last = str(e)
            time.sleep(min(2 ** attempt, 8))
    return {"__error__": last}


# --------------------------------------------------------------- API callers --

def search_by_phone(phone, limiter):
    url = f"{SKIPTRACE_BASE}/search/byphone"
    return http_get_json(url, auth_headers(), {"phoneno": phone, "page": "1"}, limiter)


def details_by_id(person_id, limiter):
    url = f"{SKIPTRACE_BASE}/search/detailsbyID"
    return http_get_json(url, auth_headers(), {"peo_id": person_id}, limiter)


def _find_key(obj, target):
    """Depth-first search for the first value under a dict key == target."""
    if isinstance(obj, dict):
        if target in obj:
            return obj[target]
        for v in obj.values():
            r = _find_key(v, target)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = _find_key(v, target)
            if r is not None:
                return r
    return None


def zillow_by_address(address, limiter):
    url = f"{ZILLOW_BASE}/byaddress"
    return http_get_json(url, auth_headers(), {"propertyaddress": address}, limiter)


def redfin_by_address(address, limiter):
    url = f"{REDFIN_BASE}/detailsbyaddress"
    return http_get_json(url, auth_headers(), {"property_address": address}, limiter)


def _int_or_blank(v):
    try:
        return int(round(float(v)))
    except (TypeError, ValueError):
        return ""


def enrich_value(address, limiter):
    """Home valuation for an address: try Zillow (Zestimate) first, then Redfin (Redfin Estimate)."""
    out = {"property_value": "", "value_source": "", "last_sold_price": "", "bedrooms": "",
           "bathrooms": "", "area_sqft": "", "year_built": "", "property_url": "",
           "_addr": None, "_note": ""}
    if not REALTYAPI_KEY or not address:
        return out

    # 1) Zillow
    z = zillow_by_address(address, limiter)
    if is_zillow_hit(z):
        out.update(last_sold_price=_int_or_blank(z.get("Price")),
                   bedrooms=z.get("Bedrooms", ""),
                   bathrooms=z.get("Bathrooms", ""),
                   area_sqft=z.get("Area(sqft)", ""),
                   year_built=z.get("yearBuilt", ""),
                   _addr=z.get("PropertyAddress", {}) or {})
        zval = _int_or_blank(z.get("zestimate"))
        if zval != "":
            out.update(property_value=zval, value_source="zillow",
                       property_url=z.get("PropertyZillowURL", ""))
            return out

    # 2) Redfin fallback
    rf = redfin_by_address(address, limiter)
    avm = _find_key(rf, "avmInfo") if isinstance(rf, dict) else None
    if isinstance(avm, dict):
        val = _int_or_blank(avm.get("predictedValue"))
        if val != "":
            out.update(property_value=val,
                       value_source="redfin",
                       last_sold_price=_int_or_blank(avm.get("lastSoldPrice")),
                       property_url=_find_key(rf, "url") or "")
            return out

    zmsg = "" if not z else str(z.get("message", z.get("__error__", "")))[:60]
    out["_note"] = f"no zillow/redfin value ({zmsg})".strip()
    return out


# ---------------------------------------------------------- record assembly ---

def person_phones(det):
    """Set of normalized phone numbers belonging to a details record."""
    nums = set()
    for p in det.get("All Phone Details", []) or []:
        n = norm10(p.get("phone_number", ""))
        if n:
            nums.add(n)
    for pd in det.get("Person Details", []) or []:
        n = norm10(pd.get("Telephone", ""))
        if n:
            nums.add(n)
    return nums


def pick_owner(phone, candidates, limiter):
    """Open candidate people and return the one whose phone list contains the searched number."""
    target = norm10(phone)
    first = None
    for cand in candidates[:MAX_CANDIDATES]:
        pid = cand.get("Person ID") or cand.get("PersonID") or cand.get("Person_ID")
        if not pid:
            continue
        det = details_by_id(pid, limiter)
        if det.get("__error__"):
            continue
        if first is None:
            first = (cand, det)
        if target and target in person_phones(det):
            return cand, det, True
    if first:
        return first[0], first[1], False
    return None, None, False


def current_address(det):
    """(display_string, parts_dict) for the person's current address, or (None, None)."""
    lst = det.get("Current Address Details List", []) or []
    if not lst:
        return None, None
    a = lst[0]
    street = a.get("street_address", "")
    locality = a.get("address_locality", "")
    region = a.get("address_region", "")
    postal = a.get("postal_code", "")
    tail = " ".join(x for x in [region, postal] if x).strip()
    display = ", ".join(x for x in [street, locality, tail] if x)
    return display, a


def is_zillow_hit(z):
    if not z or z.get("__error__"):
        return False
    msg = str(z.get("message", ""))
    if msg.startswith(("400", "404", "500")):
        return False
    return any(z.get(k) is not None for k in ("zestimate", "Price", "PropertyZPID"))


def build_row(phone, search, limiter):
    """Run the full pipeline for one phone and return an output row dict."""
    row = {k: "" for k in FIELDS}
    row["input_phone"] = phone
    row["occupation"] = "N/A"

    if search.get("__error__"):
        row["status"] = "error"
        row["note"] = f"search error: {search['__error__']}"
        return row, None

    candidates = search.get("PeopleDetails", []) or []
    if not candidates:
        row["status"] = "no_results"
        row["note"] = str(search.get("Message", ""))[:120]
        return row, None

    cand, det, confirmed = pick_owner(phone, candidates, limiter)
    if not det:
        row["status"] = "no_results"
        row["note"] = "candidates had no openable details"
        return row, None

    pd = (det.get("Person Details", []) or [{}])[0]
    row["name"] = pd.get("Person_name") or cand.get("Name", "")
    row["age"] = pd.get("Age") or cand.get("Age", "")
    row["born"] = pd.get("Born", "")
    row["primary_phone"] = pd.get("Telephone", "")
    row["phone_owner_confirmed"] = confirmed
    row["person_id"] = cand.get("Person ID", "")
    row["tps_link"] = cand.get("Link", "")

    phones = det.get("All Phone Details", []) or []
    row["all_phones"] = " | ".join(
        f"{p.get('phone_number','')} ({p.get('phone_type','')})".strip() for p in phones
    )
    row["emails"] = " | ".join(det.get("Email Addresses", []) or [])
    row["num_relatives"] = len(det.get("All Relatives", []) or [])
    row["num_associates"] = len(det.get("All Associates", []) or [])

    display, parts = current_address(det)
    if parts:
        row["current_address"] = display
        row["city"] = parts.get("address_locality", "")
        row["state"] = parts.get("address_region", "")
        row["zip"] = parts.get("postal_code", "")
        row["county"] = parts.get("county", "")

    row["status"] = "resolved"

    if display and REALTYAPI_KEY:
        v = enrich_value(display, limiter)
        if v.get("property_value") not in ("", None):
            row["property_value"] = v["property_value"]
            row["value_source"] = v["value_source"]

    return row, det


# ------------------------------------------------------------------- runner ---

def read_phones(path):
    phones = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for i, r in enumerate(reader):
            if not r:
                continue
            val = r[0].strip()
            if not val:
                continue
            if i == 0 and not digits(val):
                continue
            phones.append(val)
    return phones


def load_done(path):
    done = set()
    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r.get("input_phone"):
                    done.add(r["input_phone"])
    return done


def read_api_key(path):
    """Read the x-realtyapi-key from the auth file."""
    if not os.path.exists(path):
        sys.exit(f"[fatal] auth file '{path}' not found. Put your x-realtyapi-key in it "
                 f"(one line), e.g.:  echo rt_your_key > {path}")
    with open(path, encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            if "=" in s:
                s = s.split("=", 1)[1].strip()
            return s.strip().strip('"').strip("'")
    sys.exit(f"[fatal] no key found in auth file '{path}'.")


def main():
    ap = argparse.ArgumentParser(description="Batch skip-trace + property value.")
    ap.add_argument("--input", default="input.csv")
    ap.add_argument("--output", default="output.csv")
    ap.add_argument("--json", dest="json_out", default="", help="optional lossless JSON output path")
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--rps", type=float, default=10.0,
                    help="global requests/sec cap (Mega plan allows up to 50)")
    ap.add_argument("--limit", type=int, default=0, help="process only the first N phones (0 = all)")
    ap.add_argument("--resume", action="store_true", help="skip phones already present in --output")
    ap.add_argument("--auth", default=DEFAULT_AUTH_FILE,
                    help=f"file holding the x-realtyapi-key (default: {DEFAULT_AUTH_FILE})")
    args = ap.parse_args()

    global REALTYAPI_KEY
    REALTYAPI_KEY = read_api_key(args.auth)
    if not REALTYAPI_KEY:
        sys.exit("[fatal] empty x-realtyapi-key.")

    phones = read_phones(args.input)
    if args.limit:
        phones = phones[: args.limit]

    done = load_done(args.output) if args.resume else set()
    todo = [p for p in phones if p not in done]
    print(f"[info] {len(phones)} phones in input, {len(done)} already done, {len(todo)} to process.")

    limiter = RateLimiter(args.rps)
    write_lock = threading.Lock()

    file_exists = os.path.exists(args.output) and args.resume and done
    out_f = open(args.output, "a" if file_exists else "w", newline="", encoding="utf-8")
    writer = csv.DictWriter(out_f, fieldnames=FIELDS, extrasaction="ignore")
    if not file_exists:
        writer.writeheader()
        out_f.flush()

    json_records = []
    counters = {"resolved": 0, "no_results": 0, "error": 0}
    done_n = 0

    def work(phone):
        search = search_by_phone(phone, limiter)
        return build_row(phone, search, limiter)

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(work, p): p for p in todo}
        for fut in as_completed(futures):
            phone = futures[fut]
            try:
                row, det = fut.result()
            except Exception as e:
                row, det = ({k: "" for k in FIELDS}, None)
                row["input_phone"] = phone
                row["occupation"] = "N/A"
                row["status"] = "error"
                row["note"] = f"exception: {e}"
            counters[row["status"]] = counters.get(row["status"], 0) + 1
            with write_lock:
                writer.writerow(row)
                out_f.flush()
                if args.json_out:
                    json_records.append({"input_phone": phone, "row": row, "details": det})
                done_n += 1
                if done_n % 10 == 0 or done_n == len(todo):
                    print(f"[progress] {done_n}/{len(todo)}  "
                          + "  ".join(f"{k}={v}" for k, v in counters.items() if v))

    out_f.close()
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as jf:
            json.dump(json_records, jf, indent=2, ensure_ascii=False)

    print("\n[done] wrote", args.output)
    print("       " + "  ".join(f"{k}={v}" for k, v in counters.items()))
    with_value = 0
    try:
        with open(args.output, newline="", encoding="utf-8") as f:
            with_value = sum(1 for r in csv.DictReader(f) if r.get("property_value"))
        print(f"       rows with property_value: {with_value}")
    except OSError:
        pass


if __name__ == "__main__":
    main()
