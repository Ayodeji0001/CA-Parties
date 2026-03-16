import asyncio
import json
from collections.abc import Iterable
from pathlib import Path

import httpx
from model import Party

HERE = Path(__file__).resolve().parent
DONNEES_BASE = "https://donnees.electionsquebec.qc.ca/production"
PP_AUTORISES_PATH = (
    f"{DONNEES_BASE}/provincial/repaq/partis-politiques/pp_autorises.json"
)
MNAs_PATH = (
    f"{DONNEES_BASE}/provincial/repaq/partis-politiques/listeDeputes.json"
)


def _build_address(parts: Iterable[str | None]) -> str | None:
    chunks = [p for p in parts if p]
    if not chunks:
        return None
    return ", ".join(chunks)


async def scrape() -> list[Party]:
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        parties_resp = await client.get(PP_AUTORISES_PATH)
        parties_resp.raise_for_status()
        parties_json = parties_resp.json()

        mnas_resp = await client.get(MNAs_PATH)
        mnas_resp.raise_for_status()
        mnas_json = mnas_resp.json()

    mnas_by_party: dict[str, int] = {}
    for entry in mnas_json:
        party_id = entry.get("numero_parti")
        if not party_id:
            continue
        mnas_by_party[party_id] = mnas_by_party.get(party_id, 0) + 1

    parties: list[Party] = []
    for parti in parties_json:
        party_id = (parti.get("id") or "").strip()
        if not party_id:
            continue

        old_party_id = (parti.get("id_ancien") or "").strip() or None

        leader_nom = None
        official_representative = None
        official_agent = None
        executive_officials: list[str] = []
        auditor = None

        for itv in parti.get("intervenants") or []:
            itv_type = itv.get("type")
            if itv_type == "CHEF" and leader_nom is None:
                leader_nom = itv.get("nom")
            elif itv_type == "REPOFF" and official_representative is None:
                official_representative = itv.get("nom")
            elif itv_type == "AO" and official_agent is None:
                official_agent = itv.get("nom")
            elif itv_type == "DIRI":
                for d in itv.get("dirigeants") or []:
                    name = d.get("nom")
                    if name:
                        executive_officials.append(name)
            elif itv_type == "VERIF" and auditor is None:
                auditor = itv.get("nom")

        base_data = {
            "party_name": parti.get("nom"),
            "party_id": party_id,
            "old_party_id": old_party_id,
            "previous_name": parti.get("ancienNom"),
            # If a party has no MNAs in the list, treat that as 0 rather than
            # omitting the field entirely so the JSON consistently shows a count.
            "number_of_mnas": mnas_by_party.get(party_id, 0),
            "leader": leader_nom,
            "authorization_date": parti.get("dateAutorisation"),
            "address": _build_address(
                (
                    parti.get("adresseRueCom"),
                    parti.get("adresseMunCom"),
                    parti.get("adresseCodePostalCom"),
                )
            ),
            "official_representative": official_representative,
            "official_agent": official_agent,
            "executive_officials": " | ".join(executive_officials) if executive_officials else None,
            "auditor": auditor,
        }

        data = {k: v for k, v in base_data.items() if v is not None}
        parties.append(Party(**data))

    return parties


async def main() -> None:
    parties = await scrape()
    data = [p.model_dump(mode="json", exclude_none=True) for p in parties]
    out = HERE / "parties.json"
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Extracted {len(parties)} parties → {out}")


if __name__ == "__main__":
    asyncio.run(main())