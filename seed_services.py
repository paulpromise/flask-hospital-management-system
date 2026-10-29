from decimal import Decimal

from app import app, db, Service


services = [
    # Consultation services (10)
    ("General Consultation", "consultation", "150.00"),
    ("Specialist Consultation", "consultation", "300.00"),
    ("Follow-up Consultation", "consultation", "100.00"),
    ("Emergency Consultation", "consultation", "250.00"),
    ("Paediatric Consultation", "consultation", "180.00"),
    ("Gynaecology Consultation", "consultation", "250.00"),
    ("Cardiology Consultation", "consultation", "350.00"),
    ("Dermatology Consultation", "consultation", "250.00"),
    ("Orthopaedic Consultation", "consultation", "300.00"),
    ("Mental Health Consultation", "consultation", "250.00"),

    # Laboratory services (15)
    ("Full Blood Count", "laboratory", "120.00"),
    ("Malaria Test", "laboratory", "50.00"),
    ("Blood Group and Rhesus Test", "laboratory", "80.00"),
    ("Fasting Blood Glucose", "laboratory", "60.00"),
    ("Random Blood Glucose", "laboratory", "40.00"),
    ("Lipid Profile", "laboratory", "180.00"),
    ("Liver Function Test", "laboratory", "200.00"),
    ("Kidney Function Test", "laboratory", "180.00"),
    ("Urinalysis", "laboratory", "50.00"),
    ("Stool Analysis", "laboratory", "60.00"),
    ("Pregnancy Test", "laboratory", "50.00"),
    ("Hepatitis B Screening", "laboratory", "100.00"),
    ("HIV Screening", "laboratory", "80.00"),
    ("Widal Test", "laboratory", "80.00"),
    ("ESR Test", "laboratory", "70.00"),

    # Imaging and diagnostic services (8)
    ("Chest X-ray", "other", "250.00"),
    ("Abdominal Ultrasound", "other", "300.00"),
    ("Pelvic Ultrasound", "other", "300.00"),
    ("Obstetric Ultrasound", "other", "350.00"),
    ("ECG", "other", "150.00"),
    ("Echocardiogram", "other", "600.00"),
    ("CT Scan", "other", "1200.00"),
    ("MRI Scan", "other", "2000.00"),

    # Nursing and treatment services (10)
    ("Injection Administration", "other", "30.00"),
    ("Intravenous Infusion Administration", "other", "100.00"),
    ("Wound Dressing", "other", "80.00"),
    ("Wound Suturing", "other", "200.00"),
    ("Suture Removal", "other", "60.00"),
    ("Blood Pressure Check", "other", "20.00"),
    ("Nebulisation", "other", "80.00"),
    ("Oxygen Therapy", "other", "150.00"),
    ("Catheterisation", "other", "150.00"),
    ("Blood Transfusion Administration", "other", "300.00"),

    # Preventive and other services (7)
    ("Medical Fitness Examination", "other", "200.00"),
    ("Pre-employment Medical Examination", "other", "300.00"),
    ("Immunisation Administration", "other", "50.00"),
    ("Family Planning Consultation", "other", "100.00"),
    ("Minor Surgical Procedure", "other", "500.00"),
    ("Ambulance Service", "other", "400.00"),
    ("Hospital Bed Charge per Day", "other", "250.00"),
]


with app.app_context():
    added = 0
    skipped = 0

    for name, category, price in services:
        existing = Service.query.filter_by(name=name).first()

        if existing:
            skipped += 1
            continue

        service = Service(
            name=name,
            category=category,
            unit_price=Decimal(price),
            is_active=True,
        )

        db.session.add(service)
        added += 1

    try:
        db.session.commit()
        print(f"Services processed: {len(services)}")
        print(f"New services added: {added}")
        print(f"Existing services skipped: {skipped}")
        print(f"Total services in database: {Service.query.count()}")

    except Exception:
        db.session.rollback()
        raise