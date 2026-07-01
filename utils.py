import csv
import os
from typing import List, Dict

def read_phone_numbers(file_path: str = "phone_numbers.txt") -> List[str]:
    if not os.path.exists(file_path):
        return []
    phones = []
    with open(file_path, "r", encoding="utf-8-sig") as f:
        for line in f:
            p = line.strip()
            if p:
                phones.append(p)
    return phones

def save_results(results: List[Dict], output_file: str = "results.csv") -> None:
    fieldnames = ["phone", "name", "age", "location"]
    with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({
                "phone": r.get("phone", ""),
                "name": r.get("name", ""),
                "age": r.get("age", ""),
                "location": r.get("location", "")
            })
