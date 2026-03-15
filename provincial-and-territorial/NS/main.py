import asyncio
import json
from pathlib import Path

from bs4 import BeautifulSoup
from model import Party
from pydoll.browser.chromium import Chrome

URL = "https://electionsnovascotia.ca/registered-parties"
HERE = Path(__file__).parent


async def scrape():
    html = ""
    try:
        async with Chrome() as browser:
            tab = await browser.start()
            await tab.go_to(URL)
            html = await tab.page_source
    except Exception:
        pass  # e.g. Chrome cleanup PermissionError on Windows; we may still have html

    soup = BeautifulSoup(html, "html.parser")
    parties = []

    # Page lists registered parties as <p><strong>Party Name</strong><br>Website: <a href="...">
    # Skip the "deregistered" section and any paragraph that doesn't have a website link.
    for p in soup.find_all("p"):
        if "deregistered" in p.get_text().lower():
            continue
        strong = p.find("strong")
        link = p.find("a", href=True)
        if not strong or not link or not link.get("href", "").startswith("http"):
            continue
        if "Website:" not in p.get_text():
            continue
        full_name = strong.get_text(strip=True)
        if not full_name:
            continue
        website = link["href"].strip()
        parties.append(
            Party(
                full_name=full_name,
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
