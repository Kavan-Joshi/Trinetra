"""Mock government-database records for the records integration layer.

These stand in for VAHAN, SARTHI, eGujCop/CCTNS, AFIS and NAFIS during the demo.
Keyed to plates **actually detected by ANPR on the live grid cameras** (cam01–cam30)
so the records lookup returns relevant data for real detections. Real connectors
drop in behind the same RecordsConnector interface in production.
"""

# --- CCTNS / eGujCop feed (auto-populates the watchlist) ---
CCTNS_FEED = [
    {
        "category": "stolen_vehicle", "plate": "GJ-18-X-3001",
        "description": "Stolen truck — FIR 4521/2026, Surat City PS",
        "color": "White", "model": "Tata LPT 1613",
        "notes": "Detected on grid camera cam06",
        "source_system": "cctns", "source_ref": "FIR/4521/2026/SURAT",
    },
    {
        "category": "blacklisted_vehicle", "plate": "GJ-11-S-4826",
        "description": "Repeat traffic offender — 23 pending e-challans",
        "color": "White", "model": "Maruti WagonR", "notes": "",
        "source_system": "cctns", "source_ref": "BLV/2026/TR-04826",
    },
    {
        "category": "wanted_person", "person_name": "Wanted Suspect A",
        "description": "Wanted in fraud case — CID Crime; last seen in Ahmedabad",
        "notes": "Face enrolled in gallery for recognition",
        "source_system": "cctns", "source_ref": "FIR/5544/2026/CIDCRIME",
    },
]

# --- VAHAN vehicle records (keyed by normalized plate) ---
VAHAN_RECORDS = {
    "GJ18X3001": {"owner_name": "Surat Transport Pvt Ltd", "make": "Tata", "model": "LPT 1613",
                  "color": "White", "vehicle_class": "Goods Truck", "fitness_expiry": "2027-06-30",
                  "insurance_valid": True, "source_ref": "VAHAN/GJ18X3001"},
    "GJ11S4826": {"owner_name": "Bharat P. Solanki", "make": "Maruti Suzuki", "model": "WagonR",
                  "color": "White", "vehicle_class": "Hatchback", "fitness_expiry": "2026-11-15",
                  "insurance_valid": False, "source_ref": "VAHAN/GJ11S4826"},
    "GJ11BHZ716": {"owner_name": "Amit R. Shah", "make": "Hyundai", "model": "Verna",
                   "color": "Grey", "vehicle_class": "Sedan", "fitness_expiry": "2027-09-30",
                   "insurance_valid": True, "source_ref": "VAHAN/GJ11BHZ716"},
    "GJ11CH0172": {"owner_name": "Deepak K. Joshi", "make": "Honda", "model": "City",
                   "color": "Blue", "vehicle_class": "Sedan", "fitness_expiry": "2028-01-31",
                   "insurance_valid": True, "source_ref": "VAHAN/GJ11CH0172"},
}

# --- SARTHI driving-licence records (keyed by owner name) ---
SARTHI_RECORDS = {
    "Surat Transport Pvt Ltd": {"dl_number": "GJ18T20180011122", "valid": True, "class": "HTV", "source_ref": "SARTHI/GJ18T20180011122"},
    "Bharat P. Solanki": {"dl_number": "GJ1120150044556", "valid": False, "class": "LMV", "source_ref": "SARTHI/GJ1120150044556"},
    "Amit R. Shah": {"dl_number": "GJ1120130078899", "valid": True, "class": "LMV", "source_ref": "SARTHI/GJ1120130078899"},
    "Deepak K. Joshi": {"dl_number": "GJ1120160033445", "valid": True, "class": "LMV", "source_ref": "SARTHI/GJ1120160033445"},
}

# --- NAFIS fingerprint / face match results ---
NAFIS_MATCHES = [
    {"matched": True, "score": 0.88, "person_name": "Wanted Suspect A",
     "fir_ref": "FIR/5544/2026/CIDCRIME", "source_system": "nafis", "source_ref": "NAFIS/2026-9001"},
]
