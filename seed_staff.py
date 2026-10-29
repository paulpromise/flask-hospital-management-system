
from app import app, db, Staff, Department, generate_public_id

first_names = [
    "Kwame", "Ama", "Kofi", "Akosua", "Yaw", "Abena",
    "Kojo", "Esi", "Kweku", "Adwoa", "Daniel", "Grace",
    "Michael", "Esther", "Samuel", "Linda", "Joseph", "Ruth",
    "Emmanuel", "Patricia"
]

last_names = [
    "Mensah", "Boateng", "Asante", "Owusu", "Appiah",
    "Osei", "Adjei", "Agyeman", "Darko", "Frimpong",
    "Badu", "Addo", "Amoah", "Antwi", "Kusi"
]

job_titles = [
    "Receptionist",
    "Nurse",
    "Laboratory Technician",
    "Pharmacy Assistant",
    "Administrative Officer",
    "Medical Records Officer",
    "Accounts Officer",
    "Health Assistant",
    "Customer Service Officer",
    "Ward Assistant",
    "Billing Officer",
    "Records Clerk"
]

with app.app_context():
    departments = Department.query.order_by(Department.id).all()

    if not departments:
        raise RuntimeError("Insert departments before inserting staff.")

    staff_to_insert = []

    for i in range(120):
        first = first_names[i % len(first_names)]
        last = last_names[(i * 3) % len(last_names)]
        code = generate_public_id(Staff, "staff_code", "STF-", 6)

        staff_to_insert.append(
            Staff(
                staff_code=code,
                first_name=first,
                last_name=last,
                job_title=job_titles[i % len(job_titles)],
                phone=f"050{7000000 + i:07d}",
                email=f"{first.lower()}.{last.lower()}{i + 1}@mcleansdata.com",
                department_id=departments[i % len(departments)].id,
                is_active=True,
            )
        )

    try:
        db.session.add_all(staff_to_insert)
        db.session.commit()
        print("Successfully inserted 120 staff members.")
    except Exception:
        db.session.rollback()
        raise
