def build_row(phone, search, limiter):
    """Run the full pipeline for one phone and return an output row dict."""
    row = {k: "" for k in FIELDS}
    row["input_phone"] = phone
    row["occupation"] = "N/A"

    if search.get("__error__"):
        row["status"] = "error"
        row["note"] = f"search error: {search['__error__']}"
        print(f"[ERROR] {phone}: {search['__error__']}")  # 打印详细错误
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
