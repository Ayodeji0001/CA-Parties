import asyncio
import json
from io import BytesIO
from pathlib import Path

import httpx
import pdfplumber
from model import Party

URL = "https://elections.bc.ca/docs/fin/Registered-Political-Parties-Information.pdf"
HERE = Path(__file__).parent


async def scrape() -> list[Party]:
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(URL)
        response.raise_for_status()
        pdf_bytes = response.content

    parties = []

    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table:
                continue

            for row in table:
                row = [cell or "" for cell in row]
                if len(row) < 4:
                    continue

                party_name, ballot_name, leader, contact_text = [
                    col.strip() for col in row[:4]
                ]

                if party_name.lower() == "party name" or not party_name:
                    continue

                contact_lines = [
                    line.strip() for line in contact_text.splitlines() if line.strip()
                ]
                contact_name = contact_lines[0] if contact_lines else None
                address, phone, fax, email = [], None, None, None

                for line in contact_lines[1:]:
                    lower = line.lower()
                    if lower.startswith("phone:"):
                        phone = line.split(":", 1)[1].strip()
                    elif lower.startswith("fax:"):
                        fax = line.split(":", 1)[1].strip()
                    elif lower.startswith("email:"):
                        email = line.split(":", 1)[1].strip()
                    else:
                        address.append(line)

                parties.append(
                    Party(
                        party_name=" ".join(party_name.split()),
                        ballot_name=" ".join(ballot_name.split()),
                        leader=" ".join(leader.split()),
                        contact_name=contact_name,
                        address="\n".join(address) or None,
                        phone=phone,
                        fax=fax,
                        email=email,
                    )
                )

    return parties


async def main():
    parties = await scrape()
    data = [p.model_dump(mode="json", exclude_none=True) for p in parties]

    out = HERE / "parties.json"
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Extracted {len(parties)} parties → {out}")


if __name__ == "__main__":
    asyncio.run(main())
