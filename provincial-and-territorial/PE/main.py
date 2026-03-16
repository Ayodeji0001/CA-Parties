import asyncio
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup
from model import Party
from pydoll.browser.chromium import Chrome

URL = "https://www.electionspei.ca/index.php/provincial-election-by-elections/registered-political-parties"
HERE = Path(__file__).resolve().parent


async def scrape() -> list[Party]:
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to(URL)
        html = await tab.page_source

    soup = BeautifulSoup(html, "html.parser")
    parties: list[Party] = []

    header = soup.find(string=re.compile(r"Currently there are", re.IGNORECASE))
    container = (
        header.find_parent("div", class_="Left-Side-Menu_Body-Text")
        if header
        else soup
    )

    for link in container.find_all("a", href=True):
        name = (link.get_text(strip=True) or "").strip()
        if not name:
            continue

        paragraph = link.find_parent("p") or link.parent
        if not paragraph:
            continue

        full_text = paragraph.get_text(" ", strip=True)
        if "Leader:" not in full_text and "Interim Leader:" not in full_text:
            continue

        website = str(link["href"]).strip() or None

        after_name = full_text.split(name, 1)[1].strip() if name in full_text else full_text

        phone_match = re.search(r"Phone:\s*([^\n]+)", after_name)
        phone = phone_match.group(1).strip() if phone_match else None

        leader_match = re.search(r"(?:Interim Leader|Leader):\s*([^\n]+)", after_name)
        leader = leader_match.group(1).strip() if leader_match else "Not provided"

        cut_points = []
        for label in ["Phone:", "Leader:", "Interim Leader:"]:
            idx = after_name.find(label)
            if idx != -1:
                cut_points.append(idx)
        addr_end = min(cut_points) if cut_points else len(after_name)
        address = after_name[:addr_end].strip(" ,")

        email = None
        links_in_p = paragraph.find_all("a", href=True)
        for a in links_in_p:
            if a is link:
                continue
            text = a.get_text(strip=True)
            if "@" in text:
                email = text
                break

        logo_url = None
        img = paragraph.find("img")
        if img and img.get("src"):
            src = img["src"].strip()
            if src.startswith("http://") or src.startswith("https://"):
                logo_url = src
            else:
                logo_url = "https://www.electionspei.ca" + src

        parties.append(
            Party(
                party_name=name,
                leader=leader,
                address=address,
                phone=phone,
                email=email,
                website=website,
                logo_url=logo_url,
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
