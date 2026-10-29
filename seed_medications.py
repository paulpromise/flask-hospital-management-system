from datetime import date, timedelta
from decimal import Decimal

from app import Medication, app, db


ACTIVE_INGREDIENTS = [
    "Paracetamol", "Ibuprofen", "Amoxicillin", "Azithromycin", "Metformin",
    "Amlodipine", "Losartan", "Omeprazole", "Pantoprazole", "Cetirizine",
    "Loratadine", "Salbutamol", "Prednisolone", "Dexamethasone", "Diclofenac",
    "Naproxen", "Aspirin", "Atorvastatin", "Simvastatin", "Furosemide",
    "Hydrochlorothiazide", "Enalapril", "Lisinopril", "Atenolol", "Propranolol",
    "Warfarin", "Clopidogrel", "Insulin", "Gliclazide", "Glibenclamide",
    "Ciprofloxacin", "Metronidazole", "Doxycycline", "Flucloxacillin", "Cefuroxime",
    "Ceftriaxone", "Co-trimoxazole", "Fluconazole", "Acyclovir", "Miconazole",
    "Hydrocortisone", "Clotrimazole", "Benzoyl Peroxide", "Ferrous Sulfate", "Folic Acid",
    "Calcium Carbonate", "Vitamin C", "Vitamin B Complex", "Zinc Sulfate", "Oral Rehydration Salts",
]

VARIANTS = [
    ("100 mg", "Tablet"),
    ("250 mg", "Capsule"),
    ("500 mg", "Tablet"),
    ("5 mg/5 ml", "Syrup"),
    ("10 mg", "Tablet"),
    ("20 mg", "Capsule"),
    ("50 mg", "Injection"),
    ("100 mg/5 ml", "Syrup"),
    ("1%", "Cream"),
    ("0.5%", "Ointment"),
]


with app.app_context():
    existing_names = {
        medication.name for medication in Medication.query.with_entities(Medication.name)
    }
    existing_inventory_codes = {
        medication.inventory_code
        for medication in Medication.query.with_entities(Medication.inventory_code)
    }
    medications_to_insert = []
    target_count = 500

    for index in range(target_count):
        ingredient = ACTIVE_INGREDIENTS[index % len(ACTIVE_INGREDIENTS)]
        strength, dosage_form = VARIANTS[index // len(ACTIVE_INGREDIENTS)]
        name = f"{ingredient} {strength} {dosage_form}"
        inventory_code = f"INV-{index + 1:03d}"

        if name in existing_names or inventory_code in existing_inventory_codes:
            continue

        medications_to_insert.append(
            Medication(
                name=name,
                inventory_code=inventory_code,
                strength=strength,
                dosage_form=dosage_form,
                stock_quantity=50 + (index % 151),
                reorder_level=10 + (index % 21),
                unit_price=Decimal("2.50") + (Decimal(index % 40) * Decimal("0.75")),
                expiry_date=date.today() + timedelta(days=365 + (index % 730)),
                is_active=True,
            )
        )
        existing_names.add(name)
        existing_inventory_codes.add(inventory_code)

    try:
        db.session.add_all(medications_to_insert)
        db.session.commit()
        print(f"New medications added: {len(medications_to_insert)}")
        print(f"Total medications in database: {Medication.query.count()}")
    except Exception:
        db.session.rollback()
        raise
