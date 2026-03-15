import asyncio
import csv
import json
import re
from pathlib import Path

import httpx
from model import Party

# CSV with "Include associations" (from modal OK link)
DOWNLOAD_URL = "https://finances.elections.on.ca/api/political-parties/download?languageCode=en&includeAssociations=true"
HERE = Path(__file__).resolve().parent
CSV_NAME = "registered-parties.csv"


def _header_to_key(name: str) -> str:
    s = (name or "").strip().lower()
    s = re.sub(r"[^\w\s]", "", s)
    s = re.sub(r"\s+", "_", s)
    return s


# Map CSV keys (after _header_to_key) to Party model fields
# CSV columns: "Registered Political Party - English", "Abbreviation - English", "Registration Date", "President", "Leader", "Address", "Phone", "Fax", "Email", "Web Address", "Association Electoral District"
CSV_KEY_TO_FIELD = {
    "party_name": "party_name",
    "registered_political_party": "party_name",
    "registered_political_party_english": "party_name",
    "name_in_election_documents": "name_in_election_documents",
    "name_in_elections_documents": "name_in_election_documents",
    "abbreviation_english": "name_in_election_documents",
    "president": "president",
    "leader": "leader",
    "registered": "registered_date",
    "registered_date": "registered_date",
    "registration_date": "registered_date",
    "address": "address",
    "telephone": "telephone",
    "phone": "telephone",
    "fax": "fax",
    "email": "email",
    "website": "website",
    "web_site": "website",
    "web_address": "website",
    "url": "website",
    "constituency_associations": "constituency_associations",
    "associations": "constituency_associations",
    "association_electoral_district": "constituency_associations",
}


def _row_to_party(row: dict) -> dict:
    """One CSV row → dict of Party fields (only non-empty)."""
    out = {}
    for raw_key, value in row.items():
        key = _header_to_key(raw_key)
        field = CSV_KEY_TO_FIELD.get(key, key)
        if value is not None and str(value).strip():
            out[field] = str(value).strip()
    return out


async def scrape() -> list[Party]:
    # Download CSV to current path
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(DOWNLOAD_URL)
        response.raise_for_status()

    csv_path = HERE / CSV_NAME
    csv_path.write_bytes(response.content)

    # One row per party or per association; keep one record per distinct party (prefer head-office row)
    order: list[str] = []
    by_name: dict[str, tuple[dict, bool]] = {}  # name -> (data, has_association)
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data = _row_to_party(row)
            name = data.get("party_name")
            if not name:
                continue
            has_assoc = bool(data.get("constituency_associations"))
            if name not in by_name:
                order.append(name)
                by_name[name] = (data, has_assoc)
            elif not has_assoc:
                by_name[name] = (data, False)

    parties = []
    for name in order:
        data, _ = by_name[name]
        data = {k: v for k, v in data.items() if k != "constituency_associations"}
        parties.append(Party(**{k: v for k, v in data.items() if k in Party.model_fields}))

    return parties


async def main():
    parties = await scrape()
    data = [p.model_dump(mode="json", exclude_none=True) for p in parties]

    out = HERE / "parties.json"
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Extracted {len(parties)} parties -> {out}")


if __name__ == "__main__":
    asyncio.run(main())
