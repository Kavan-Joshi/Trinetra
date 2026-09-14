"""Government records integration layer (Workstream 1).

Mirrors the camera-gateway federation pattern: each government database
(VAHAN, SARTHI, eGujCop/CCTNS, AFIS, NAFIS) is fronted by a connector behind a
small interface. A :class:`RecordsEnricher` facade combines them so callers
(correlator, core API) deal with one object. Mock connectors stand in for the
demo using :mod:`sim.records`; real connectors drop in behind the same ABCs.
"""

from __future__ import annotations

import abc
from typing import Optional

from .models import FingerprintMatch, PersonRecord, VehicleRecord
from .plates import format_plate, normalize_plate


class VahanConnector(abc.ABC):
    @abc.abstractmethod
    async def lookup_plate(self, plate_norm: str) -> Optional[VehicleRecord]:
        ...


class SarathiConnector(abc.ABC):
    @abc.abstractmethod
    async def lookup_owner(self, owner_name: str) -> Optional[dict]:
        ...


class CctnsConnector(abc.ABC):
    @abc.abstractmethod
    async def watchlist_updates(self) -> list[dict]:
        ...

    @abc.abstractmethod
    async def lookup_person(self, name: str | None) -> Optional[PersonRecord]:
        ...

    @abc.abstractmethod
    async def lookup_plate_history(self, plate_norm: str) -> Optional[dict]:
        ...


class NafisConnector(abc.ABC):
    @abc.abstractmethod
    async def search_fingerprint(self, name: str | None) -> FingerprintMatch:
        ...


class RecordsEnricher:
    """Federated records facade combining all government database connectors."""

    def __init__(self, vahan: VahanConnector, sarathi: SarathiConnector,
                 cctns: CctnsConnector, nafis: NafisConnector):
        self.vahan = vahan
        self.sarathi = sarathi
        self.cctns = cctns
        self.nafis = nafis

    async def enrich_plate(self, plate_norm: str) -> dict:
        """VAHAN vehicle details + SARTHI DL of the registered owner (best-effort)."""
        out: dict = {"vahan": None, "sarathi": None}
        try:
            vehicle = await self.vahan.lookup_plate(plate_norm)
            if vehicle:
                out["vahan"] = vehicle.model_dump()
                if vehicle.owner_name:
                    out["sarathi"] = await self.sarathi.lookup_owner(vehicle.owner_name)
        except Exception:
            pass
        return out

    async def enrich_person(self, name: str | None) -> dict:
        """CCTNS person record + NAFIS fingerprint match (best-effort)."""
        out: dict = {"cctns": None, "nafis": None}
        try:
            person = await self.cctns.lookup_person(name)
            if person:
                out["cctns"] = person.model_dump()
            out["nafis"] = (await self.nafis.search_fingerprint(name)).model_dump()
        except Exception:
            pass
        return out

    async def lookup_plate(self, plate_norm: str) -> dict:
        """Full plate dossier for the UI: VAHAN + CCTNS watchlist hit + SARTHI."""
        norm = normalize_plate(plate_norm)
        dossier = {"plate_norm": norm, "plate_display": format_plate(norm),
                   "vahan": None, "cctns": None, "sarathi": None}
        vehicle = await self.vahan.lookup_plate(norm)
        if vehicle:
            dossier["vahan"] = vehicle.model_dump()
            if vehicle.owner_name:
                dossier["sarathi"] = await self.sarathi.lookup_owner(vehicle.owner_name)
        dossier["cctns"] = await self.cctns.lookup_plate_history(norm)
        return dossier

    async def cctns_feed(self) -> list[dict]:
        return await self.cctns.watchlist_updates()


# --------------------------------------------------------------------------- #
# Mock implementations (backed by sim.records) — demo / no real DB access.
# --------------------------------------------------------------------------- #


class MockVahanConnector(VahanConnector):
    def __init__(self, records: dict):
        self._records = records

    async def lookup_plate(self, plate_norm: str) -> Optional[VehicleRecord]:
        row = self._records.get(normalize_plate(plate_norm))
        if not row:
            return None
        return VehicleRecord(
            plate_norm=plate_norm, plate_display=format_plate(plate_norm),
            owner_name=row.get("owner_name"), make=row.get("make"), model=row.get("model"),
            color=row.get("color"), vehicle_class=row.get("vehicle_class"),
            fitness_expiry=row.get("fitness_expiry"), insurance_valid=row.get("insurance_valid"),
            source_system="vahan", source_ref=row.get("source_ref"),
        )


class MockSarathiConnector(SarathiConnector):
    def __init__(self, records: dict):
        self._records = records

    async def lookup_owner(self, owner_name: str) -> Optional[dict]:
        row = self._records.get(owner_name)
        if not row:
            return None
        return {"source_system": "sarathi", **row}


class MockCctnsConnector(CctnsConnector):
    def __init__(self, feed: list[dict]):
        self._feed = feed

    async def watchlist_updates(self) -> list[dict]:
        return list(self._feed)

    async def lookup_person(self, name: str | None) -> Optional[PersonRecord]:
        if not name:
            return None
        for entry in self._feed:
            if entry.get("person_name", "").lower() == name.lower():
                return PersonRecord(
                    person_name=entry["person_name"], category=entry["category"],
                    fir_ref=entry.get("source_ref"), description=entry.get("description", ""),
                    source_system=entry.get("source_system", "cctns"), source_ref=entry.get("source_ref"),
                )
        return None

    async def lookup_plate_history(self, plate_norm: str) -> Optional[dict]:
        norm = normalize_plate(plate_norm)
        for entry in self._feed:
            if entry.get("plate") and normalize_plate(entry["plate"]) == norm:
                return {"source_system": entry.get("source_system", "cctns"),
                        "source_ref": entry.get("source_ref"),
                        "category": entry["category"], "description": entry.get("description", "")}
        return None


class MockNafisConnector(NafisConnector):
    def __init__(self, matches: list[dict]):
        self._matches = matches

    async def search_fingerprint(self, name: str | None) -> FingerprintMatch:
        if name:
            for m in self._matches:
                if m.get("person_name", "").lower() == name.lower():
                    return FingerprintMatch(**m)
        return FingerprintMatch(matched=False)


def mock_enricher() -> RecordsEnricher:
    """Build a RecordsEnricher wired to the simulated government databases."""
    from sim.records import CCTNS_FEED, NAFIS_MATCHES, SARTHI_RECORDS, VAHAN_RECORDS

    return RecordsEnricher(
        vahan=MockVahanConnector(VAHAN_RECORDS),
        sarathi=MockSarathiConnector(SARTHI_RECORDS),
        cctns=MockCctnsConnector(CCTNS_FEED),
        nafis=MockNafisConnector(NAFIS_MATCHES),
    )
