import asyncio
import json
from pathlib import Path

from bs4 import BeautifulSoup
from model import Party
from pydoll.browser.chromium import Chrome

URL = "https://www.elections.gov.nl.ca/parties/official/"
HERE = Path(__file__).parent


def extract_after_label(text: str, label: str, until: str | None = None) -> str | None:
    """Return the value after a label, optionally until another label. Strips and returns None if empty."""
    if label not in text:
        return None
    after = text.split(label, 1)[1].strip()
    if until and until in after:
        after = after.split(until, 1)[0].strip()
    # Normalize whitespace/newlines to single space
    value = " ".join(after.split()).strip()
    return value or None


async def scrape():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to(URL)
        html = await tab.page_source

    soup = BeautifulSoup(html, "html.parser")
    parties = []

    for card in soup.select("div.gnl-card.gnl-card--info"):
        title_el = card.select_one("h2.gnl-card__title")
        full_name = title_el.get_text(strip=True) if title_el else ""
        if not full_name:
            continue

        body = card.select_one("div.gnl-card__body")
        body_text = body.get_text("\n", strip=True) if body else ""

        # Leader is the first line after "Leader:"; address is remaining lines until "Phone:"
        leader = None
        address = None
        if "Leader:" in body_text:
            after_leader = body_text.split("Leader:", 1)[1].strip()
            if "Phone:" in after_leader:
                block_before_phone = after_leader.split("Phone:", 1)[0].strip()
            else:
                block_before_phone = after_leader.split("Email:")[0].strip() if "Email:" in after_leader else after_leader
            lines = [ln.strip() for ln in block_before_phone.split("\n") if ln.strip()]
            if lines:
                leader = lines[0]
                if len(lines) > 1:
                    address = " ".join(lines[1:])

        phone = extract_after_label(body_text, "Phone:", until="Email:")

        email = None
        if body:
            mailto = body.select_one("a[href^='mailto:']")
            if mailto and mailto.get("href"):
                email = mailto["href"]

        website = None
        footer_link = card.select_one("a.gnl-card__footer[href]")
        if footer_link and footer_link.get("href"):
            website = footer_link["href"]

        parties.append(
            Party(
                full_name=full_name,
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
    data = [p.model_dump(mode="json", exclude_none=True) for p in parties]
    out = HERE / "parties.json"
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Extracted {len(parties)} parties -> {out}")


if __name__ == "__main__":
    asyncio.run(main())
