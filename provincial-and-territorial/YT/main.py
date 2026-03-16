import asyncio
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup
from model import Party
from pydoll.browser.chromium import Chrome

URL = "https://electionsyukon.ca/en/territorial-elections/parties-candidates"
HERE = Path(__file__).resolve().parent


async def scrape() -> list[Party]:
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to(URL)
        html = await tab.page_source

    soup = BeautifulSoup(html, "html.parser")
    parties: list[Party] = []

    accordion = soup.select_one("div.accordion.faqs")
    if not accordion:
        return parties

    for card in accordion.select("div.card.accordion-item"):
        header = card.select_one(".card-header h4")
        if not header:
            continue
        party_name = header.get_text(strip=True)
        body = card.select_one(".card-body")
        if not body:
            parties.append(
                Party(
                    party_name=party_name,
                    leader="Not provided",
                    address="Not provided",
                )
            )
            continue

        # Inline parsing of leader, president, address, phone, email, website.
        leader = "Not provided"
        president = None
        address_lines: list[str] = []
        phone = None
        email = None
        website = None

        for p in body.select("p"):
            text = p.get_text("\n", strip=True)
            lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

            if "Leader:" in text:
                first = text.split("Leader:", 1)[1].strip()
                after = first.split("\n", 1)[0].strip() if "\n" in first else first
                name_match = re.match(r"^([^\-|]+?)(?:\s*-\s*|\s*\|\s*|$)", after)
                if name_match:
                    leader = name_match.group(1).strip()
                mailto = p.find("a", href=re.compile(r"^mailto:", re.I))
                if mailto and mailto.get("href"):
                    email = mailto["href"].replace("mailto:", "").strip()
                tel = p.find("a", href=re.compile(r"^tel:", re.I))
                if tel and tel.get("href"):
                    phone = tel["href"].replace("tel:", "").strip()
                for line in lines:
                    if "Box" in line or re.search(r"[A-Z]\d[A-Z]\s*\d[A-Z]\d", line):
                        address_lines.append(line)
                        break

            elif "Party President:" in text:
                after = text.split("Party President:", 1)[1].strip()
                name_match = re.match(r"^([^\-]+?)(?:\s*-\s*|\s*$)", after)
                if name_match:
                    president = name_match.group(1).strip()
                for line in lines:
                    if ("Box" in line or re.search(r"[A-Z]\d[A-Z]", line)) and line not in address_lines:
                        address_lines.append(line)
                        break

            elif "Website:" in text or "website" in text.lower():
                a = p.find("a", href=re.compile(r"^https?://", re.I))
                if a and a.get("href"):
                    website = a["href"].strip()

        if address_lines:
            address = " | ".join(address_lines)
        else:
            address = "Not provided"

        parties.append(
            Party(
                party_name=party_name,
                leader=leader,
                president=president,
                address=address,
                phone=phone,
                email=email,
                website=website,
            )
        )

    return parties


async def main():
    parties = await scrape()
    data = [p.model_dump(mode="json", exclude_none=True) for p in parties]
    out = HERE / "parties.json"
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Extracted {len(parties)} parties -> {out}")


if __name__ == "__main__":
    asyncio.run(main())
