import asyncio
import json
import re
from datetime import date
from pathlib import Path

from bs4 import BeautifulSoup
from model import Party
from pydoll.browser.chromium import Chrome

URL = "https://www.elections.ca/content.aspx?section=pol&dir=par&document=index&lang=e"
HERE = Path(__file__).parent


async def scrape():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to(URL)
        html = await tab.page_source

    soup = BeautifulSoup(html, "html.parser")
    parties = []

    for div in soup.select("div.borderbox1"):
        title = div.select_one("h3.partytitle")
        full_name = title.get_text(strip=True) if title else ""

        logo = div.select_one("img")
        logo_url = str(logo["src"]) if logo and logo.get("src") else None

        col1 = div.select_one(".colun")
        col2 = div.select_one(".coldeux")
        text1 = col1.get_text(" ", strip=True) if col1 else ""
        text2 = col2.get_text(" ", strip=True) if col2 else ""

        def extract(text, label):
            if label not in text:
                return ""
            after = text.split(label, 1)[1].lstrip(" :")
            return after.split("  ")[0].strip()

        def extract_date(text, label):
            raw = extract(text, label)
            m = re.search(r"\d{4}-\d{2}-\d{2}", raw)
            return date.fromisoformat(m.group()) if m else None

        def extract_link(col, link_text):
            if not col:
                return None
            for a in col.find_all("a"):
                if link_text.lower() in a.get_text(strip=True).lower():
                    return str(a.get("href", "")) or None
            return None

        short_name = extract(text1, "Short-form Name")
        leader = extract(text1, "Party Leader")
        headquarters = extract(text1, "National Headquarters")
        email = extract_link(col1, "@") or extract_link(col1, "mail")
        website = extract_link(col1, "www")
        privacy_policy = extract_link(col1, "Privacy")

        registered_date = extract_date(text2, "Registered")
        deregistered_date = extract_date(text2, "Deregistered")
        chief_agent = extract(text2, "Chief Agent")
        auditor = extract(text2, "Auditor")

        parties.append(
            Party(
                full_name=full_name,
                short_name=short_name or full_name,
                leader=leader or "Not provided",
                headquarters=headquarters or "Not provided",
                email=email,
                website=website,
                privacy_policy=privacy_policy,
                registered_date=registered_date,
                deregistered_date=deregistered_date,
                chief_agent=chief_agent or "Not provided",
                auditor=auditor or "Not provided",
                logo_url=logo_url,
                anchor_id=str(title.get("id", "")) if title else "",
            )
        )

    return parties


async def main():
    parties = await scrape()
    data = [p.model_dump(mode="json") for p in parties]
    out = HERE / "registered_parties.json"
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"Extracted {len(parties)} parties → {out}")


if __name__ == "__main__":
    asyncio.run(main())