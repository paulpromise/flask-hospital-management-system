
from app import app, db, Patient, generate_public_id
from datetime import date
import random

sample_patients = [
    ("John", "Mensah", "1990-05-12", "Male", "0241234501", "Accra, Ghana"),
    ("Ama", "Boateng", "1985-08-23", "Female", "0201234502", "Kumasi, Ghana"),
    ("Kwame", "Asante", "1992-11-04", "Male", "0551234503", "Tema, Ghana"),
    ("Akosua", "Owusu", "1988-02-15", "Female", "0271234504", "Cape Coast, Ghana"),
    ("Kofi", "Appiah", "1995-07-19", "Male", "0261234505", "Tamale, Ghana"),
    ("Abena", "Osei", "1993-04-27", "Female", "0241234506", "Madina, Ghana"),
    ("Yaw", "Darko", "1987-09-08", "Male", "0201234507", "Dansoman, Ghana"),
    ("Adwoa", "Frimpong", "1998-12-30", "Female", "0551234508", "Legon, Ghana"),
    ("Kojo", "Arthur", "1991-06-11", "Male", "0271234509", "Kasoa, Ghana"),
    ("Efua", "Sarpong", "1989-03-22", "Female", "0261234510", "Ho, Ghana"),
]

# Extend the sample data to exactly 99 records.
first_names = [
    "Daniel", "Grace", "Michael", "Esi", "Samuel",
    "Linda", "Emmanuel", "Mabel", "Joseph", "Patricia",
    "Peter", "Esther", "Isaac", "Ruth", "Francis",
    "Janet", "Richard", "Beatrice", "Patrick", "Mercy",
    "Benjamin", "Florence", "Stephen", "Dorcas", "George",
    "Comfort", "Alex", "Hannah", "Anthony", "Victoria",
    "Charles", "Priscilla", "Eric", "Paulina", "Martin",
    "Diana", "Felix", "Gloria", "Solomon", "Irene",
    "David", "Elizabeth", "Christopher", "Rebecca", "Augustine",
    "Rosemond", "Nicholas", "Abigail", "Dennis", "Matilda",
    "Robert", "Sandra", "Bernard", "Juliet", "Kenneth",
    "Martha", "Andrew", "Selina", "Franklin", "Eunice",
    "Godfred", "Veronica", "Sylvester", "Cynthia", "Matthew",
    "Bernice", "Edward", "Simon", "Deborah", "Philip",
    "Adelaide", "Joyce", "Kwabena", "Akua", "Nana Ama",
    "Lawrence", "Miriam", "Christiana", "Josephine", "Kofi",
    "Adwoa", "Yaw", "Ama", "Kojo", "Esi",
    "Abena", "Daniel", "Grace", "Michael"
]

last_names = [
    "Addo", "Nyarko", "Agyeman", "Quartey", "Tetteh",
    "Acheampong", "Baah", "Kusi", "Nkrumah", "Amoah",
    "Boadu", "Ansah", "Mensimah", "Gyasi", "Owusu",
    "Opoku", "Kwarteng", "Lamptey", "Ofori", "Aidoo",
    "Antwi", "Yeboah", "Poku", "Achebe", "Ababio",
    "Biney", "Okyere", "Koomson", "Danquah", "Agyapong",
    "Amankwah", "Badu", "Asiedu", "Tandoh", "Sefa",
    "Appiah", "Boakye", "Adu", "Kyei", "Asante",
    "Osei", "Tetteh", "Aidoo", "Nyame", "Kofi",
    "Baah", "Baffour", "Frempong", "Amponsah", "Kwarteng",
    "Ofori", "Mensah", "Asare", "Addai", "Antwi",
    "Osei", "Darko", "Asiedu", "Appau", "Baidoo",
    "Agyekum", "Ofori", "Amoako", "Adjei", "Owusu",
    "Tutu", "Adom", "Asante", "Frimpong", "Asiedu",
    "Mensah", "Kusi", "Appiah", "Mensima", "Boateng",
    "Kofi", "Addo", "Agyeman", "Osei"
]

towns = [
    "Accra, Ghana", "Kumasi, Ghana", "Tema, Ghana",
    "Cape Coast, Ghana", "Tamale, Ghana", "Madina, Ghana",
    "Dansoman, Ghana", "Legon, Ghana", "Kasoa, Ghana",
    "Ho, Ghana", "Takoradi, Ghana", "Sunyani, Ghana"
]

with app.app_context():
    existing_count = Patient.query.count()

    if existing_count:
        print(f"Warning: {existing_count} patients already exist.")

    patients_to_insert = []

    for i in range(99):
        if i < len(sample_patients):
            first, last, dob, gender, phone, address = sample_patients[i]
            birth_date = date.fromisoformat(dob)
        else:
            first = first_names[(i - len(sample_patients)) % len(first_names)]
            last = last_names[(i - len(sample_patients)) % len(last_names)]
            birth_year = random.randint(1960, 2005)
            birth_month = random.randint(1, 12)
            birth_day = random.randint(1, 28)
            birth_date = date(birth_year, birth_month, birth_day)
            gender = random.choice(["Male", "Female"])
            phone = f"050{7000000 + i:07d}"
            address = random.choice(towns)

        patient_code = generate_public_id(
            Patient, "patient_code", "MCN-", 8
        )

        patients_to_insert.append(
            Patient(
                patient_code=patient_code,
                first_name=first,
                last_name=last,
                date_of_birth=birth_date,
                gender=gender,
                phone=phone,
                address=address,
            )
        )

    try:
        db.session.add_all(patients_to_insert)
        db.session.commit()
        print("Successfully inserted 99 patients.")
    except Exception:
        db.session.rollback()
        raise
