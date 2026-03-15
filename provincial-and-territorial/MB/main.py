import asyncio
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup
from model import Party
from pydoll.browser.chromium import Chrome

URL = "https://www.electionsmanitoba.ca/en/Political_Participation/Registered_Political_Parties"
HERE = Path(__file__).parent


async def scrape():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to(URL)
        html = await tab.page_source

    soup = BeautifulSoup(html, "html.parser")
    parties = []

    for wrap in soup.select("div.extra-wrap"):
        strong = wrap.select_one("p.p0 strong")
        if not strong:
            continue

        full_name = strong.get_text(strip=True)
        short_match = re.search(r"\(([^)]+)\)\s*$", full_name)
        short_name = short_match.group(1) if short_match else full_name

        address_lines = []
        phone = None
        email = None
        website = None

        for p in wrap.select("p.p0"):
            text = p.get_text(strip=True)
            if not text or text == full_name:
                continue
            if text.startswith("Phone:"):
                phone = text.replace("Phone:", "").strip()
            elif "Email:" in text:
                a = p.find("a", href=re.compile(r"^mailto:", re.I))
                if a and a.get("href"):
                    email = a["href"].replace("mailto:", "").strip()
            elif "Website:" in text:
                a = p.find("a", href=re.compile(r"^https?://", re.I))
                if a and a.get("href"):
                    website = a["href"].strip()
            elif "Note:" in text or text.startswith("(Note:"):
                continue
            else:
                address_lines.append(text)

        address = "\n".join(address_lines).strip() if address_lines else "Not provided"

        full_text = wrap.get_text()
        leader_match = re.search(r"Leader:\s*([^\n(p]+)", full_text)
        leader = leader_match.group(1).strip() if leader_match else "Not provided"

        parties.append(
            Party(
                full_name=full_name,
                short_name=short_name,
                leader=leader,
                address=address,
                phone=phone,
                email=email,
                website=website,
            )
        )

    return parties


async def main():
    parties = await scrape()
    data = [p.model_dump(mode="json") for p in parties]
    out = HERE / "parties.json"
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Extracted {len(parties)} parties -> {out}")


if __name__ == "__main__":
    asyncio.run(main())
