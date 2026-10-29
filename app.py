import os
import uuid
import secrets
import string
from datetime import datetime , date
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, UniqueConstraint, text, or_
from sqlalchemy.engine import URL
from decimal import Decimal, InvalidOperation
from datetime import date


load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]

app.config["SQLALCHEMY_DATABASE_URI"] = URL.create(
    drivername="mysql+pymysql",
    username=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    host=os.environ["DB_HOST"],
    database=os.environ["DB_NAME"],
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# Public IDs are separate from numeric primary keys so database relationships
# remain stable. IDs use uppercase letters and digits and are checked for uniqueness.
ID_CHARACTERS = string.ascii_uppercase + string.digits


def generate_public_id(model, field_name, prefix, random_length):
    """Generate a unique human-readable ID for a record."""
    while True:
        suffix = "".join(secrets.choice(ID_CHARACTERS) for _ in range(random_length))
        public_id = f"{prefix}{suffix}"
        if not model.query.filter(getattr(model, field_name) == public_id).first():
            return public_id


# ==========================================================
# 1. PATIENTS
# Existing table: preserve the current database structure.
# ==========================================================

class Patient(db.Model):
    __tablename__ = "patients"

    id = db.Column(db.Integer, primary_key=True)
    patient_code = db.Column(db.String(12), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(255))

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.current_timestamp(),
    )


# ==========================================================
# 2. DEPARTMENTS
# ==========================================================

class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.current_timestamp(),
    )


# ==========================================================
# 3. DOCTORS
# ==========================================================

class Doctor(db.Model):
    __tablename__ = "doctors"

    id = db.Column(db.Integer, primary_key=True)
    doctor_code = db.Column(db.String(8), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(150), unique=True)

    department_id = db.Column(
        db.Integer,
        db.ForeignKey("departments.id", ondelete="RESTRICT"),
        nullable=False,
    )

    is_active = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.current_timestamp(),
    )

    department = db.relationship("Department", backref="doctors")


# ==========================================================
# 4. STAFF
# ==========================================================

class Staff(db.Model):
    __tablename__ = "staff"

    id = db.Column(db.Integer, primary_key=True)
    staff_code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    job_title = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(150), unique=True)

    department_id = db.Column(
        db.Integer,
        db.ForeignKey("departments.id", ondelete="RESTRICT"),
    )

    is_active = db.Column(db.Boolean, nullable=False, default=True)

    department = db.relationship("Department", backref="staff_members")


# ==========================================================
# 5. USERS
# Login accounts and roles.
# Store password hashes, never plain-text passwords.
# ==========================================================

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    role = db.Column(
        db.String(30),
        nullable=False,
        default="receptionist",
    )

    is_active = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.current_timestamp(),
    )

    __table_args__ = (
        CheckConstraint(
            "role IN ('admin', 'doctor', 'nurse', 'receptionist')",
            name="ck_users_role",
        ),
    )


# ==========================================================
# 6. APPOINTMENTS
# ==========================================================

class Appointment(db.Model):
    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)

    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey("doctors.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    appointment_at = db.Column(db.DateTime, nullable=False)
    reason = db.Column(db.String(255))

    status = db.Column(
        db.String(30),
        nullable=False,
        default="scheduled",
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.current_timestamp(),
    )

    patient = db.relationship("Patient", backref="appointments")
    doctor = db.relationship("Doctor", backref="appointments")

    __table_args__ = (
        CheckConstraint(
            "status IN ('scheduled', 'completed', 'cancelled', 'no_show')",
            name="ck_appointments_status",
        ),
    )


# ==========================================================
# 7. MEDICAL RECORDS
# ==========================================================

class MedicalRecord(db.Model):
    __tablename__ = "medical_records"

    id = db.Column(db.Integer, primary_key=True)

    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey("doctors.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    appointment_id = db.Column(
        db.Integer,
        db.ForeignKey("appointments.id", ondelete="RESTRICT"),
        unique=True,
    )

    consultation_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.current_timestamp(),
    )

    symptoms = db.Column(db.Text)
    diagnosis = db.Column(db.Text)
    treatment_notes = db.Column(db.Text)

    patient = db.relationship("Patient", backref="medical_records")
    doctor = db.relationship("Doctor", backref="medical_records")
    appointment = db.relationship("Appointment", backref="medical_record")


# ==========================================================
# 8. MEDICATIONS / INVENTORY
# ==========================================================

class Medication(db.Model):
    __tablename__ = "medications"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    strength = db.Column(db.String(50))
    dosage_form = db.Column(db.String(50))

    stock_quantity = db.Column(
        db.Integer,
        nullable=False,
        default=0,
    )

    reorder_level = db.Column(
        db.Integer,
        nullable=False,
        default=10,
    )

    unit_price = db.Column(
        db.Numeric(10, 2),
        nullable=False,
        default=0,
    )

    expiry_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    __table_args__ = (
        CheckConstraint(
            "stock_quantity >= 0",
            name="ck_medications_stock",
        ),
        CheckConstraint(
            "reorder_level >= 0",
            name="ck_medications_reorder",
        ),
        CheckConstraint(
            "unit_price >= 0",
            name="ck_medications_price",
        ),
    )



# ==========================================================
# 8. BILLABLE SERVICES
# Consultation fees, laboratory tests, and other services.
# ==========================================================

class Service(db.Model):
    __tablename__ = "services"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    __table_args__ = (
        CheckConstraint(
            "category IN ('consultation', 'laboratory', 'other')",
            name="ck_services_category",
        ),
        CheckConstraint(
            "unit_price >= 0",
            name="ck_services_price",
        ),
    )


# ==========================================================
# 9. PRESCRIPTIONS
# ==========================================================

class Prescription(db.Model):
    __tablename__ = "prescriptions"

    id = db.Column(db.Integer, primary_key=True)

    medical_record_id = db.Column(
        db.Integer,
        db.ForeignKey("medical_records.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    prescribed_by = db.Column(
        db.Integer,
        db.ForeignKey("doctors.id", ondelete="RESTRICT"),
        nullable=False,
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="active",
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.current_timestamp(),
    )

    medical_record = db.relationship(
        "MedicalRecord",
        backref="prescriptions",
    )

    doctor = db.relationship("Doctor", backref="prescriptions")

    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'completed', 'cancelled')",
            name="ck_prescriptions_status",
        ),
    )


# ==========================================================
# 10. PRESCRIPTION ITEMS
# One prescription can contain multiple medications.
# ==========================================================

class PrescriptionItem(db.Model):
    __tablename__ = "prescription_items"

    id = db.Column(db.Integer, primary_key=True)

    prescription_id = db.Column(
        db.Integer,
        db.ForeignKey("prescriptions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    medication_id = db.Column(
        db.Integer,
        db.ForeignKey("medications.id", ondelete="RESTRICT"),
    )

    # Snapshot of the prescribed medicine name.
    medication_name = db.Column(db.String(150), nullable=False)
    dosage = db.Column(db.String(100), nullable=False)
    frequency = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    instructions = db.Column(db.Text)

    prescription = db.relationship(
        "Prescription",
        backref="items",
    )

    medication = db.relationship(
        "Medication",
        backref="prescription_items",
    )

    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name="ck_prescription_items_quantity",
        ),
    )


# ==========================================================
# 11. BILLS
# ==========================================================

class Bill(db.Model):
    __tablename__ = "bills"

    id = db.Column(db.Integer, primary_key=True)

    invoice_number = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
    )

    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    appointment_id = db.Column(
        db.Integer,
        db.ForeignKey("appointments.id", ondelete="RESTRICT"),
    )

    total_amount = db.Column(db.Numeric(10, 2), nullable=False)

    status = db.Column(
        db.String(30),
        nullable=False,
        default="unpaid",
    )

    issued_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.current_timestamp(),
    )

    due_date = db.Column(db.Date)

    patient = db.relationship("Patient", backref="bills")
    appointment = db.relationship("Appointment", backref="bills")

    __table_args__ = (
        CheckConstraint(
            "total_amount >= 0",
            name="ck_bills_total",
        ),
        CheckConstraint(
            "status IN ('unpaid', 'partially_paid', 'paid', 'cancelled')",
            name="ck_bills_status",
        ),
    )


# ==========================================================
# BILL ITEMS
# Individual services included on each bill.
# ==========================================================


class BillItem(db.Model):
    __tablename__ = "bill_items"

    id = db.Column(db.Integer, primary_key=True)

    bill_id = db.Column(
        db.Integer,
        db.ForeignKey("bills.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # A bill item can represent either a service or a medication.
    service_id = db.Column(
        db.Integer,
        db.ForeignKey("services.id", ondelete="RESTRICT"),
        nullable=True,
    )

    medication_id = db.Column(
        db.Integer,
        db.ForeignKey("medications.id", ondelete="RESTRICT"),
        nullable=True,
    )

    item_name = db.Column(db.String(150), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)

    bill = db.relationship("Bill", backref="items")
    service = db.relationship("Service")
    medication = db.relationship("Medication")

    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name="ck_bill_items_quantity",
        ),
        CheckConstraint(
            "unit_price >= 0",
            name="ck_bill_items_price",
        ),
        CheckConstraint(
            "(service_id IS NOT NULL AND medication_id IS NULL) OR "
            "(service_id IS NULL AND medication_id IS NOT NULL)",
            name="ck_bill_items_one_item_type",
        ),
    )

    @property
    def subtotal(self):
        return self.quantity * self.unit_price


# ==========================================================
# 12. PAYMENTS
# A bill can have multiple payments.
# ==========================================================

class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)

    bill_id = db.Column(
        db.Integer,
        db.ForeignKey("bills.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(30), nullable=False)

    transaction_reference = db.Column(
        db.String(100),
        unique=True,
    )

    paid_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.current_timestamp(),
    )

    bill = db.relationship("Bill", backref="payments")

    __table_args__ = (
        CheckConstraint(
            "amount > 0",
            name="ck_payments_amount",
        ),
        CheckConstraint(
            "payment_method IN ('cash', 'card', 'mobile_money', 'bank_transfer', 'other')",
            name="ck_payments_method",
        ),
    )


# ==========================================================
# ROUTES
# ==========================================================

@app.route("/")
def home():
    total_patients = db.session.query(Patient).count()
    total_doctors = db.session.query(Doctor).count()

    scheduled_appointments = (
        db.session.query(Appointment)
        .filter_by(status="scheduled")
        .count()
    )

    total_departments = db.session.query(Department).count()

    return render_template(
        "dashboard.html",
        total_patients=total_patients,
        total_doctors=total_doctors,
        scheduled_appointments=scheduled_appointments,
        total_departments=total_departments,
    )

@app.route("/patients")
def patients():
    search = request.args.get("q", "").strip()
    query = Patient.query
    if search:
        query = query.filter(or_(
            Patient.patient_code.ilike(f"%{search}%"),
            Patient.first_name.ilike(f"%{search}%"),
            Patient.last_name.ilike(f"%{search}%"),
            Patient.phone.ilike(f"%{search}%"),
        ))
    all_patients = query.order_by(Patient.id.desc()).all()
    return render_template("patients.html", patients=all_patients, search=search)


@app.route("/patients/add", methods=["GET", "POST"])
def add_patient():
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        date_of_birth = request.form.get("date_of_birth", "").strip()
        gender = request.form.get("gender", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()

        if not all([first_name, last_name, date_of_birth, gender, phone]):
            flash("Please complete all required fields.", "error")
            return render_template("patient_form.html")

        from datetime import date

        try:
            birth_date = date.fromisoformat(date_of_birth)
            if birth_date > date.today():
                flash("Date of birth cannot be in the future.", "error")
                return render_template("patient_form.html")
        except ValueError:
            flash("Please enter a valid date of birth.", "error")
            return render_template("patient_form.html")

        patient = Patient(
            patient_code=generate_public_id(Patient, "patient_code", "MCN-", 8),
            first_name=first_name,
            last_name=last_name,
            date_of_birth=birth_date,
            gender=gender,
            phone=phone,
            address=address or None,
        )

        try:
            db.session.add(patient)
            db.session.commit()
            flash("Patient registered successfully.", "success")
            return redirect(url_for("patients"))
        except Exception:
            db.session.rollback()
            app.logger.exception("Failed to register patient")
            flash("Unable to register the patient. Please try again.", "error")

    return render_template("patient_form.html")


@app.route("/departments")
def departments():
    all_departments = Department.query.order_by(
        Department.name.asc()
    ).all()

    return render_template(
        "departments.html",
        departments=all_departments,
    )


@app.route("/departments/add", methods=["GET", "POST"])
def add_department():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Department name is required.", "error")
            return render_template("department_form.html")

        existing = Department.query.filter(
            db.func.lower(Department.name) == name.lower()
        ).first()

        if existing:
            flash("This department already exists.", "error")
            return render_template("department_form.html")

        department = Department(
            name=name,
            description=description or None,
        )

        try:
            db.session.add(department)
            db.session.commit()
            flash("Department added successfully.", "success")
            return redirect(url_for("departments"))
        except Exception:
            db.session.rollback()
            app.logger.exception("Failed to add department")
            flash("Unable to add the department.", "error")

    return render_template("department_form.html")


@app.route("/doctors")
def doctors():
    search = request.args.get("q", "").strip()
    query = Doctor.query

    if search:
        query = query.filter(
            or_(
                Doctor.doctor_code.ilike(f"%{search}%"),
                Doctor.first_name.ilike(f"%{search}%"),
                Doctor.last_name.ilike(f"%{search}%"),
                Doctor.specialization.ilike(f"%{search}%"),
                Doctor.phone.ilike(f"%{search}%"),
                Doctor.email.ilike(f"%{search}%"),
                Doctor.department.has(
                    Department.name.ilike(f"%{search}%")
                ),
            )
        )

    all_doctors = query.order_by(Doctor.id.desc()).all()

    return render_template(
        "doctors.html",
        doctors=all_doctors,
        search=search,
    )


@app.route("/doctors/add", methods=["GET", "POST"])
def add_doctor():
    departments = Department.query.order_by(
        Department.name.asc()
    ).all()

    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        specialization = request.form.get("specialization", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip().lower()
        department_id = request.form.get("department_id", "").strip()

        if not all([
            first_name, last_name, specialization,
            phone, department_id
        ]):
            flash("Please complete all required fields.", "error")
            return render_template(
                "doctor_form.html",
                departments=departments,
            )

        try:
            department_id = int(department_id)
        except ValueError:
            flash("Please select a valid department.", "error")
            return render_template(
                "doctor_form.html",
                departments=departments,
            )

        department = db.session.get(Department, department_id)
        if department is None:
            flash("The selected department does not exist.", "error")
            return render_template(
                "doctor_form.html",
                departments=departments,
            )

        if email:
            existing_doctor = Doctor.query.filter(
                db.func.lower(Doctor.email) == email
            ).first()

            if existing_doctor:
                flash("A doctor with this email already exists.", "error")
                return render_template(
                    "doctor_form.html",
                    departments=departments,
                )
        else:
            email = None

        doctor = Doctor(
            doctor_code=generate_public_id(Doctor, "doctor_code", "DOC-", 4),
            first_name=first_name,
            last_name=last_name,
            specialization=specialization,
            phone=phone,
            email=email,
            department_id=department_id,
        )

        try:
            db.session.add(doctor)
            db.session.commit()
            flash("Doctor registered successfully.", "success")
            return redirect(url_for("doctors"))
        except Exception:
            db.session.rollback()
            app.logger.exception("Failed to register doctor")
            flash("Unable to register the doctor.", "error")

    return render_template(
        "doctor_form.html",
        departments=departments,
    )



@app.route("/medical-records")
def medical_records():
    records = MedicalRecord.query.order_by(
        MedicalRecord.consultation_at.desc()
    ).all()

    return render_template(
        "medical_records.html",
        records=records,
    )


@app.route("/medical-records/add", methods=["GET", "POST"])
def add_medical_record():
    patients = Patient.query.order_by(Patient.first_name).all()
    doctors = Doctor.query.filter_by(is_active=True).order_by(
        Doctor.first_name
    ).all()
    appointments = Appointment.query.filter_by(
        status="completed"
    ).order_by(Appointment.appointment_at.desc()).all()

    if request.method == "POST":
        patient_id = request.form.get("patient_id", "").strip()
        doctor_id = request.form.get("doctor_id", "").strip()
        appointment_id = request.form.get("appointment_id", "").strip()
        symptoms = request.form.get("symptoms", "").strip()
        diagnosis = request.form.get("diagnosis", "").strip()
        treatment_notes = request.form.get("treatment_notes", "").strip()

        if not all([patient_id, doctor_id, diagnosis]):
            flash(
                "Patient, doctor, and diagnosis are required.",
                "error",
            )
        else:
            try:
                patient_id = int(patient_id)
                doctor_id = int(doctor_id)
                appointment_id = (
                    int(appointment_id) if appointment_id else None
                )

                patient = db.session.get(Patient, patient_id)
                doctor = db.session.get(Doctor, doctor_id)

                if patient is None or doctor is None or not doctor.is_active:
                    flash("Please select a valid patient and active doctor.", "error")

                elif appointment_id is not None and not any(
                    a.id == appointment_id
                    and a.patient_id == patient_id
                    and a.doctor_id == doctor_id
                    and a.status == "completed"
                    for a in appointments
                ):
                    flash(
                        "Select a completed appointment matching this patient and doctor.",
                        "error",
                    )

                elif appointment_id is not None and MedicalRecord.query.filter_by(
                    appointment_id=appointment_id
                ).first():
                    flash(
                        "A medical record already exists for this appointment.",
                        "error",
                    )

                else:
                    record = MedicalRecord(
                        patient_id=patient_id,
                        doctor_id=doctor_id,
                        appointment_id=appointment_id,
                        symptoms=symptoms or None,
                        diagnosis=diagnosis,
                        treatment_notes=treatment_notes or None,
                    )

                    db.session.add(record)
                    db.session.commit()

                    flash("Medical record saved successfully.", "success")
                    return redirect(url_for("medical_records"))

            except ValueError:
                flash("Please enter valid record details.", "error")
            except Exception:
                db.session.rollback()
                app.logger.exception("Failed to save medical record")
                flash("Unable to save the medical record.", "error")

    return render_template(
        "medical_record_form.html",
        patients=patients,
        doctors=doctors,
        appointments=appointments,
    )


@app.route("/prescriptions")
def prescriptions():
    prescriptions_list = (
        Prescription.query
        .order_by(Prescription.created_at.desc())
        .all()
    )

    return render_template(
        "prescriptions.html",
        prescriptions=prescriptions_list,
    )


@app.route("/prescriptions/add", methods=["GET", "POST"])
def add_prescription():
    medical_records = (
        MedicalRecord.query
        .order_by(MedicalRecord.consultation_at.desc())
        .all()
    )

    if request.method == "POST":
        medical_record_id = request.form.get(
            "medical_record_id", ""
        ).strip()

        status = request.form.get("status", "active").strip()

        if not medical_record_id:
            flash("Please select a medical record.", "error")

        elif status not in {"active", "completed", "cancelled"}:
            flash("Please select a valid prescription status.", "error")

        else:
            try:
                medical_record_id = int(medical_record_id)
                medical_record = db.session.get(
                    MedicalRecord, medical_record_id
                )

                if medical_record is None:
                    flash("The selected medical record does not exist.", "error")

                else:
                    prescription = Prescription(medical_record_id=medical_record.id, prescribed_by=medical_record.doctor.id, status=status,
)



                    db.session.add(prescription)
                    db.session.commit()

                    flash(
                        "Prescription created successfully. You can add medication items next.",
                        "success",
                    )
                    return redirect(url_for("prescriptions"))

            except ValueError:
                flash("Please select a valid medical record.", "error")

            except Exception:
                db.session.rollback()
                app.logger.exception("Failed to create prescription")
                flash("Unable to create the prescription.", "error")

    return render_template(
        "prescription_form.html",
        medical_records=medical_records,
    )



@app.route(
    "/prescriptions/<int:prescription_id>",
    methods=["GET", "POST"],
)
def prescription_detail(prescription_id):
    prescription = db.get_or_404(Prescription, prescription_id)

    medications_list = Medication.query.filter_by(
        is_active=True
    ).order_by(Medication.name.asc()).all()

    if request.method == "POST":
        medication_id = request.form.get("medication_id", "").strip()
        medication_name = request.form.get("medication_name", "").strip()
        dosage = request.form.get("dosage", "").strip()
        frequency = request.form.get("frequency", "").strip()
        duration = request.form.get("duration", "").strip()
        quantity = request.form.get("quantity", "").strip()
        instructions = request.form.get("instructions", "").strip()

        if not all([dosage, frequency, duration, quantity]):
            flash(
                "Dosage, frequency, duration, and quantity are required.",
                "error",
            )
        elif prescription.status != "active":
            flash(
                "Medication items can only be added to active prescriptions.",
                "error",
            )
        else:
            try:
                quantity = int(quantity)

                if quantity <= 0:
                    raise ValueError

                medication = None

                if medication_id:
                    medication = db.session.get(
                        Medication, int(medication_id)
                    )

                    if medication is None or not medication.is_active:
                        flash("Please select a valid active medication.", "error")
                        return redirect(
                            url_for(
                                "prescription_detail",
                                prescription_id=prescription.id,
                            )
                        )

                    medication_name = medication.name
                elif not medication_name:
                    flash(
                        "Select a medication or enter a medication name.",
                        "error",
                    )
                    return redirect(
                        url_for(
                            "prescription_detail",
                            prescription_id=prescription.id,
                        )
                    )

                item = PrescriptionItem(
                    prescription_id=prescription.id,
                    medication_id=medication.id if medication else None,
                    medication_name=medication_name,
                    dosage=dosage,
                    frequency=frequency,
                    duration=duration,
                    quantity=quantity,
                    instructions=instructions or None,
                )

                db.session.add(item)
                db.session.commit()

                flash("Prescription item added successfully.", "success")
                return redirect(
                    url_for(
                        "prescription_detail",
                        prescription_id=prescription.id,
                    )
                )

            except (ValueError, TypeError):
                db.session.rollback()
                flash("Please enter a valid positive quantity.", "error")

            except Exception:
                db.session.rollback()
                app.logger.exception("Failed to add prescription item")
                flash("Unable to add the prescription item.", "error")

    return render_template(
        "prescription_detail.html",
        prescription=prescription,
        medications=medications_list,
    )


@app.route("/medications")
def medications():
    medication_list = Medication.query.order_by(
        Medication.name.asc()
    ).all()

    return render_template(
    "medications.html",
    medications=medication_list,
    today=date.today(),
)


@app.route("/medications/add", methods=["GET", "POST"])
def add_medication():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        strength = request.form.get("strength", "").strip()
        dosage_form = request.form.get("dosage_form", "").strip()
        stock_quantity = request.form.get("stock_quantity", "").strip()
        reorder_level = request.form.get("reorder_level", "").strip()
        unit_price = request.form.get("unit_price", "").strip()
        expiry_date = request.form.get("expiry_date", "").strip()

        if not all([name, stock_quantity, reorder_level, unit_price]):
            flash(
                "Name, stock quantity, reorder level, and unit price are required.",
                "error",
            )
        else:
            try:
                from datetime import date
                from decimal import Decimal, InvalidOperation

                stock_quantity = int(stock_quantity)
                reorder_level = int(reorder_level)
                unit_price = Decimal(unit_price)

                if stock_quantity < 0 or reorder_level < 0:
                    raise ValueError

                if not unit_price.is_finite() or unit_price < 0:
                    raise ValueError

                parsed_expiry_date = (
                    date.fromisoformat(expiry_date)
                    if expiry_date
                    else None
                )

                medication = Medication(
                    name=name,
                    strength=strength or None,
                    dosage_form=dosage_form or None,
                    stock_quantity=stock_quantity,
                    reorder_level=reorder_level,
                    unit_price=unit_price,
                    expiry_date=parsed_expiry_date,
                )

                db.session.add(medication)
                db.session.commit()

                flash("Medication added successfully.", "success")
                return redirect(url_for("medications"))

            except (ValueError, InvalidOperation):
                db.session.rollback()
                flash(
                    "Enter valid quantities, price, and expiry date.",
                    "error",
                )

            except Exception:
                db.session.rollback()
                app.logger.exception("Failed to add medication")
                flash("Unable to add the medication.", "error")

    return render_template("medication_form.html")


@app.route("/appointments")
def appointments():
    all_appointments = Appointment.query.order_by(
        Appointment.appointment_at.desc()
    ).all()

    return render_template(
        "appointments.html",
        appointments=all_appointments,
    )


@app.route("/appointments/add", methods=["GET", "POST"])
def add_appointment():
    patients = Patient.query.order_by(Patient.first_name).all()
    doctors = Doctor.query.filter_by(is_active=True).order_by(
        Doctor.first_name
    ).all()

    if request.method == "POST":
        patient_id = request.form.get("patient_id", "").strip()
        doctor_id = request.form.get("doctor_id", "").strip()
        appointment_at = request.form.get("appointment_at", "").strip()
        reason = request.form.get("reason", "").strip()

        if not all([patient_id, doctor_id, appointment_at]):
            flash("Please complete all required fields.", "error")
        else:
            try:
                patient_id = int(patient_id)
                doctor_id = int(doctor_id)
                appointment_datetime = datetime.fromisoformat(
                    appointment_at
                )

                patient = db.session.get(Patient, patient_id)
                doctor = db.session.get(Doctor, doctor_id)

                if patient is None:
                    flash("Please select a valid patient.", "error")
                elif doctor is None or not doctor.is_active:
                    flash("Please select an active doctor.", "error")
                else:
                    appointment = Appointment(
                        patient_id=patient_id,
                        doctor_id=doctor_id,
                        appointment_at=appointment_datetime,
                        reason=reason or None,
                        status="scheduled",
                    )

                    db.session.add(appointment)
                    db.session.commit()

                    flash("Appointment scheduled successfully.", "success")
                    return redirect(url_for("appointments"))

            except ValueError:
                flash("Please enter valid appointment details.", "error")
            except Exception:
                db.session.rollback()
                app.logger.exception("Failed to schedule appointment")
                flash("Unable to schedule appointment.", "error")

    return render_template(
        "appointment_form.html",
        patients=patients,
        doctors=doctors,
    )


@app.route("/appointments/<int:appointment_id>/status", methods=["POST"])
def update_appointment_status(appointment_id):
    appointment = db.session.get(Appointment, appointment_id)

    if appointment is None:
        flash("Appointment not found.", "error")
        return redirect(url_for("appointments"))

    new_status = request.form.get("status", "").strip()
    allowed_statuses = {
        "scheduled", "completed", "cancelled", "no_show"
    }

    if new_status not in allowed_statuses:
        flash("Invalid appointment status.", "error")
        return redirect(url_for("appointments"))

    appointment.status = new_status

    try:
        db.session.commit()
        flash("Appointment status updated.", "success")
    except Exception:
        db.session.rollback()
        app.logger.exception("Failed to update appointment status")
        flash("Unable to update appointment status.", "error")

    return redirect(url_for("appointments"))


@app.route("/health")
def health():
    try:
        with db.engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "database": "connected",
        }, 200

    except Exception:
        app.logger.exception("Database connection failed")

        return {
            "status": "error",
            "database": "unavailable",
        }, 503



@app.route("/billing")
def billing():
    bills = Bill.query.order_by(Bill.issued_at.desc()).all()

    return render_template(
        "billing.html",
        bills=bills,
        today=date.today(),
    )



@app.route("/billing/add", methods=["GET", "POST"])
def add_bill():
    patients = Patient.query.order_by(Patient.first_name).all()

    appointments = (
        Appointment.query
        .order_by(Appointment.appointment_at.desc())
        .all()
    )

    services = (
        Service.query
        .filter_by(is_active=True)
        .order_by(Service.name.asc())
        .all()
    )

    medications_list = (
        Medication.query
        .filter_by(is_active=True)
        .order_by(Medication.name.asc())
        .all()
    )

    if request.method == "POST":
        patient_id = request.form.get("patient_id", "").strip()
        appointment_id = request.form.get("appointment_id", "").strip()
        due_date = request.form.get("due_date", "").strip()

        service_ids = request.form.getlist("service_id")
        service_quantities = request.form.getlist("service_quantity")
        medication_ids = request.form.getlist("medication_id")
        medication_quantities = request.form.getlist("medication_quantity")

        try:
            if not patient_id:
                raise ValueError("Please select a patient.")

            patient_id = int(patient_id)
            appointment_id = int(appointment_id) if appointment_id else None

            patient = db.session.get(Patient, patient_id)

            if patient is None:
                raise ValueError("Please select a valid patient.")

            if appointment_id is not None:
                appointment = db.session.get(Appointment, appointment_id)

                if (
                    appointment is None
                    or appointment.patient_id != patient_id
                ):
                    raise ValueError(
                        "Select an appointment belonging to this patient."
                    )

            parsed_due_date = (
                date.fromisoformat(due_date) if due_date else None
            )

            items_to_bill = []
            total_amount = Decimal("0.00")

            # Validate and price selected services using database prices.
            if len(service_ids) != len(service_quantities):
                raise ValueError("Invalid service selections.")

            for raw_id, raw_quantity in zip(
                service_ids, service_quantities
            ):
                if not raw_id and not raw_quantity:
                    continue

                if not raw_id or not raw_quantity:
                    raise ValueError(
                        "Select a service and enter its quantity."
                    )

                service_id = int(raw_id)
                quantity = int(raw_quantity)

                service = db.session.get(Service, service_id)

                if service is None or not service.is_active:
                    raise ValueError("Select a valid active service.")

                if quantity <= 0:
                    raise ValueError("Quantities must be greater than zero.")

                unit_price = Decimal(service.unit_price)
                subtotal = unit_price * quantity
                total_amount += subtotal

                items_to_bill.append({
                    "service_id": service.id,
                    "medication_id": None,
                    "item_name": service.name,
                    "quantity": quantity,
                    "unit_price": unit_price,
                })

            # Validate and price selected medications using database prices.
            if len(medication_ids) != len(medication_quantities):
                raise ValueError("Invalid medication selections.")

            for raw_id, raw_quantity in zip(
                medication_ids, medication_quantities
            ):
                if not raw_id and not raw_quantity:
                    continue

                if not raw_id or not raw_quantity:
                    raise ValueError(
                        "Select a medication and enter its quantity."
                    )

                medication_id = int(raw_id)
                quantity = int(raw_quantity)

                medication = db.session.get(Medication, medication_id)

                if medication is None or not medication.is_active:
                    raise ValueError("Select a valid active medication.")

                if quantity <= 0:
                    raise ValueError("Quantities must be greater than zero.")

                unit_price = Decimal(medication.unit_price)
                subtotal = unit_price * quantity
                total_amount += subtotal

                items_to_bill.append({
                    "service_id": None,
                    "medication_id": medication.id,
                    "item_name": medication.name,
                    "quantity": quantity,
                    "unit_price": unit_price,
                })

            if not items_to_bill:
                raise ValueError(
                    "Add at least one service or medication to the bill."
                )

            if total_amount <= 0:
                raise ValueError(
                    "The bill total must be greater than zero."
                )

            bill = Bill(
                invoice_number=f"INV-{uuid.uuid4().hex[:12].upper()}",
                patient_id=patient_id,
                appointment_id=appointment_id,
                total_amount=total_amount,
                status="unpaid",
                due_date=parsed_due_date,
            )

            db.session.add(bill)
            db.session.flush()

            for item_data in items_to_bill:
                db.session.add(
                    BillItem(
                        bill_id=bill.id,
                        **item_data,
                    )
                )

            db.session.commit()

            flash("Bill created successfully.", "success")
            return redirect(url_for("billing"))

        except (ValueError, TypeError, InvalidOperation):
            db.session.rollback()
            flash(
                "Please check the patient, appointment, quantities, and due date.",
                "error",
            )

        except Exception:
            db.session.rollback()
            app.logger.exception("Failed to create bill")
            flash("Unable to create the bill.", "error")

    return render_template(
        "bill_form.html",
        patients=patients,
        appointments=appointments,
        services=services,
        medications=medications_list,
    )



@app.route("/staff")
def staff():
    search = request.args.get("q", "").strip()
    query = Staff.query
    if search:
        query = query.filter(or_(
            Staff.staff_code.ilike(f"%{search}%"),
            Staff.first_name.ilike(f"%{search}%"),
            Staff.last_name.ilike(f"%{search}%"),
            Staff.phone.ilike(f"%{search}%"),
            Staff.email.ilike(f"%{search}%"),
        ))
    staff_members = query.order_by(Staff.id.desc()).all()
    return render_template("staff.html", staff_members=staff_members, search=search)


@app.route("/staff/add", methods=["GET", "POST"])
def add_staff():
    departments = Department.query.order_by(
        Department.name.asc()
    ).all()

    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        job_title = request.form.get("job_title", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip().lower()
        department_id = request.form.get("department_id", "").strip()

        if not all([first_name, last_name, job_title, phone]):
            flash("Please complete all required fields.", "error")
        else:
            try:
                department_id = int(department_id) if department_id else None

                if department_id is not None and db.session.get(
                    Department, department_id
                ) is None:
                    raise ValueError

                if email:
                    existing_staff = Staff.query.filter(
                        db.func.lower(Staff.email) == email
                    ).first()

                    if existing_staff:
                        flash("A staff member with this email already exists.", "error")
                        return render_template(
                            "staff_form.html",
                            departments=departments,
                        )
                else:
                    email = None

                member = Staff(
                    staff_code=generate_public_id(Staff, "staff_code", "STF-", 6),
                    first_name=first_name,
                    last_name=last_name,
                    job_title=job_title,
                    phone=phone,
                    email=email,
                    department_id=department_id,
                )

                db.session.add(member)
                db.session.commit()

                flash("Staff member added successfully.", "success")
                return redirect(url_for("staff"))

            except ValueError:
                flash("Please select a valid department.", "error")
            except Exception:
                db.session.rollback()
                app.logger.exception("Failed to add staff member")
                flash("Unable to add the staff member.", "error")

    return render_template(
        "staff_form.html",
        departments=departments,
    )



@app.route("/payments")
def payments():
    payment_records = (
        Payment.query
        .order_by(Payment.paid_at.desc(), Payment.id.desc())
        .all()
    )

    return render_template(
        "payments.html",
        payments=payment_records,
    )


@app.route("/payments/add", methods=["GET", "POST"])
def add_payment():
    payment_methods = [
        ("cash", "Cash"),
        ("card", "Card"),
        ("mobile_money", "Mobile Money"),
        ("bank_transfer", "Bank Transfer"),
        ("other", "Other"),
    ]

    # Only bills that can still receive payments.
    bills = (
        Bill.query
        .filter(Bill.status.in_(["unpaid", "partially_paid"]))
        .order_by(Bill.issued_at.desc())
        .all()
    )

    if request.method == "POST":
        try:
            bill_id = int(request.form.get("bill_id", ""))
            amount_text = request.form.get("amount", "").strip()
            payment_method = request.form.get(
                "payment_method", ""
            ).strip()
            transaction_reference = (
                request.form.get("transaction_reference", "").strip()
                or None
            )

            if not amount_text:
                raise ValueError("Enter the payment amount.")

            amount = Decimal(amount_text)

            if not amount.is_finite() or amount <= Decimal("0"):
                raise ValueError("The payment amount must be greater than zero.")

            amount = amount.quantize(Decimal("0.01"))

            if payment_method not in {
                "cash", "card", "mobile_money",
                "bank_transfer", "other"
            }:
                raise ValueError("Select a valid payment method.")

            if transaction_reference and len(transaction_reference) > 100:
                raise ValueError("The transaction reference is too long.")

            bill = db.session.get(Bill, bill_id)

            if bill is None:
                raise ValueError("Select a valid bill.")

            if bill.status not in ("unpaid", "partially_paid"):
                raise ValueError("This bill cannot receive payments.")

            paid_so_far = (
                db.session.query(
                    db.func.coalesce(db.func.sum(Payment.amount), 0)
                )
                .filter(Payment.bill_id == bill.id)
                .scalar()
            )

            paid_so_far = Decimal(str(paid_so_far))
            outstanding = bill.total_amount - paid_so_far

            if outstanding <= Decimal("0"):
                raise ValueError("This bill has no outstanding balance.")

            if amount > outstanding:
                raise ValueError(
                    f"Payment exceeds the outstanding balance "
                    f"of {outstanding:.2f}."
                )

            if transaction_reference:
                duplicate = Payment.query.filter_by(
                    transaction_reference=transaction_reference
                ).first()

                if duplicate:
                    raise ValueError(
                        "That transaction reference has already been used."
                    )

            payment = Payment(
                bill_id=bill.id,
                amount=amount,
                payment_method=payment_method,
                transaction_reference=transaction_reference,
            )

            db.session.add(payment)

            new_total_paid = paid_so_far + amount

            if new_total_paid >= bill.total_amount:
                bill.status = "paid"
            elif new_total_paid > Decimal("0"):
                bill.status = "partially_paid"
            else:
                bill.status = "unpaid"

            db.session.commit()

            flash("Payment recorded successfully.", "success")
            return redirect(url_for("payments"))

        except (ValueError, InvalidOperation) as error:
            db.session.rollback()
            flash(str(error), "error")

        except Exception:
            db.session.rollback()
            app.logger.exception("Failed to record payment.")
            flash(
                "Unable to record the payment. Please try again.",
                "error",
            )

    # Calculate the outstanding balance for each bill for the form.
    bill_balances = {}

    for bill in bills:
        paid = (
            db.session.query(
                db.func.coalesce(db.func.sum(Payment.amount), 0)
            )
            .filter(Payment.bill_id == bill.id)
            .scalar()
        )

        bill_balances[bill.id] = (
            bill.total_amount - Decimal(str(paid))
        )

    return render_template(
        "payment_form.html",
        bills=bills,
        bill_balances=bill_balances,
        payment_methods=payment_methods,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
