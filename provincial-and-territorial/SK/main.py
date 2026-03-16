import asyncio
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup
from model import Party
from pydoll.browser.chromium import Chrome

URL = "https://www.elections.sk.ca/candidates-political-parties/political-parties/"
HERE = Path(__file__).resolve().parent


async def scrape() -> list[Party]:
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to(URL)
        html = await tab.page_source

    soup = BeautifulSoup(html, "html.parser")
    parties: list[Party] = []

    marker = soup.find(string=re.compile(r"registered political parties in Saskatchewan", re.I))
    if not marker:
        return parties

    container = marker.find_parent(["div", "section", "main"]) or marker.find_parent()
    if not container:
        return parties

    for a in container.find_all("a", href=True):
        href = (a.get("href") or "").strip()
        if not href.startswith(("http://", "https://")):
            continue
        if "elections.sk.ca" in href:
            continue

        full_name = a.get_text(strip=True)
        if not full_name:
            continue

        parent = a.find_parent("p") or a.parent
        short_name = full_name
        if parent:
            text = parent.get_text(" ", strip=True)
            after_name = text.find(full_name)
            if after_name != -1:
                start = text.find("(", after_name + len(full_name))
                if start != -1 and text.rfind(")") > start:
                    short_name = text[start + 1 : text.rfind(")")].strip()

        parties.append(
            Party(
                full_name=full_name,
                short_name=short_name,
                website=href,
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
