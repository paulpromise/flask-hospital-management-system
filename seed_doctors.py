
from app import app, db, Doctor, Department, generate_public_id

doctors_data = [
    ("Kofi", "Asante", "Pediatrics", "0241000003",
     "kofi.asante@mcleansdata.com"),
    ("Akosua", "Owusu", "Obstetrics and Gynecology", "0241000004",
     "akosua.owusu@mcleansdata.com"),
    ("Yaw", "Appiah", "Orthopedics", "0241000005",
     "yaw.appiah@mcleansdata.com"),
    ("Abena", "Osei", "Dermatology", "0241000006",
     "abena.osei@mcleansdata.com"),
    ("Kojo", "Adjei", "Neurology", "0241000007",
     "kojo.adjei@mcleansdata.com"),
    ("Esi", "Agyeman", "Ophthalmology", "0241000008",
     "esi.agyeman@mcleansdata.com"),
    ("Daniel", "Darko", "ENT", "0241000009",
     "daniel.darko@mcleansdata.com"),
]

with app.app_context():
    added = 0

    try:
        for first, last, specialization, phone, email in doctors_data:
            if Doctor.query.filter_by(email=email).first():
                print(f"SKIPPED: Email already exists: {email}")
                continue

            department = Department.query.filter_by(
                name=specialization
            ).first()

            if department is None:
                print(f"SKIPPED: Department not found: {specialization}")
                continue

            doctor = Doctor(
                doctor_code=generate_public_id(
                    Doctor, "doctor_code", "DOC-", 4
                ),
                first_name=first,
                last_name=last,
                specialization=specialization,
                phone=phone,
                email=email,
                department_id=department.id,
                is_active=True,
            )

            db.session.add(doctor)
            db.session.flush()
            print(f"ADDED: {first} {last} - {doctor.doctor_code}")
            added += 1

        db.session.commit()
        print(f"\nCompleted. {added} doctors added.")
        print(f"Total doctors in database: {Doctor.query.count()}")

    except Exception as error:
        db.session.rollback()
        print(f"ERROR: {error}")
        raise
