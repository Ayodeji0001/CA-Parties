import asyncio
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup
from model import Party
from pydoll.browser.chromium import Chrome

URL = "https://www.electionsnb.ca/content/enb/en/parties_assoc/rpp.html"
HERE = Path(__file__).parent


def extract_after_label(text: str, label: str) -> str | None:
    """Return the value after a label (e.g. 'Telephone: (506) 453-3950') or None."""
    if label not in text:
        return None
    after = text.split(label, 1)[1].strip()
    # Take first line or up to next label-like part
    line = after.split("\n")[0].strip()
    return line or None


async def scrape():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to(URL)
        html = await tab.page_source

    soup = BeautifulSoup(html, "html.parser")
    parties = []

    table = soup.select_one("div.table-responsive table.table")
    if not table:
        return parties

    for row in table.select("tbody tr"):
        cells = row.find_all("td")
        if len(cells) < 2:
            continue

        name_cell = cells[0]
        details_cell = cells[1]

        full_name = name_cell.get_text(strip=True) or ""
        if not full_name:
            continue

        text = details_cell.get_text("\n", strip=True)

        # Address: lines before Email/Telephone/Toll free/Fax/URL
        address_lines = []
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue
            if (
                line.startswith("Email:")
                or line.startswith("Telephone:")
                or line.startswith("Toll free:")
                or line.startswith("Fax:")
            ):
                break
            if re.match(r"^https?://", line, re.I):
                break
            address_lines.append(line)
        address = " ".join(address_lines) if address_lines else None

        phone = extract_after_label(text, "Telephone:")
        toll_free = extract_after_label(text, "Toll free:")
        fax = extract_after_label(text, "Fax:")

        email = None
        website = None
        for a in details_cell.find_all("a", href=True):
            href = a.get("href", "")
            if href.startswith("mailto:"):
                email = href
            elif href.startswith("http://") or href.startswith("https://"):
                website = href

        parties.append(
            Party(
                full_name=full_name,
                address=address,
                email=email,
                phone=phone,
                toll_free=toll_free,
                fax=fax,
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
