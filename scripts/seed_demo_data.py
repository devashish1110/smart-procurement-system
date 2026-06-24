"""
Single-command seed script: populates a fresh database with realistic demo
data so the app never opens to empty tables, and tops up date-sensitive data
(patients/appointments/bills/low-stock flags) on every re-run.

Run once after initial setup (tables created, e.g. via init_db() or alembic):
    python scripts/seed_demo_data.py

Safe to re-run any time - catalog data (users/medicines/vendors/treatments) is
only created if those tables are empty; patients/appointments/bills are always
topped up so "today"/"this month" dashboard stats stay non-zero going forward.

What it creates on a fresh database:
  - Default users (admin/doctor/pharmacist/receptionist/therapist) if missing
  - ~8 vendors, ~40 medicines, 5 treatments if those tables are empty
  - Inventory stock per medicine if missing: a realistic mix of healthy,
    low-stock (for inventory alerts), and near-expiry batches
  - ~12 purchase orders with items, across draft/approved/ordered/received,
    if the purchase_orders table is empty
  - New patients (last ~20 days) and appointments+bills spanning 30 days ago
    to 60 days ahead, every run (re-run periodically to keep "today" fresh)

Data-integrity note: every bill/appointment created here always gets a real,
non-None patient_id (see the assert in seed_appointments_and_bills). A prior,
unrelated legacy-data corruption (584 bills with NULL patient_id, from what
looked like an old "Test update" script) was found and cleaned up directly in
the database - this script was not its cause and cannot reproduce it.

Schema-drift note: a couple of tables in the live/legacy database don't match
the SQLAlchemy models exactly (treatments missing `is_active`; appointments/
inventory_stock check constraints narrower than the model enums). The
purchase_order_items `item_id`/`po_item_id` mismatch that used to be here too
has been fixed (model aligned to the real column name). This script still
uses raw SQL for the handful of reads/inserts affected by the remaining
mismatches, so it works whether the target database was created from the
(drifted) live schema or a clean `Base.metadata.create_all()` run.
"""
import os
import sys
import random
import uuid
from datetime import date, datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from faker import Faker
from sqlalchemy import text
from passlib.context import CryptContext

from backend.config.database import get_db_context
from backend.models.database import (
    Patient, Appointment, Bill, InventoryStock, Medicine, Vendor, PurchaseOrder, PurchaseOrderItem,
    AppointmentStatus, StockStatus, OrderStatus, UserRole,
)

fake = Faker("en_IN")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ADMIN_ID = 1
DOCTOR_ID = 2       # doctor_1
PHARMACIST_ID = 3   # pharmacist_1
RECEPTIONIST_ID = 4  # receptionist_1
THERAPIST_ID = 5    # therapist_1

today = date.today()

MEDICINE_CATEGORIES = ['tablet', 'oil', 'kashaya', 'ghrutam', 'choorna', 'other']
CATEGORY_FORM_LABEL = {
    'tablet': 'Tablet', 'oil': 'Oil', 'kashaya': 'Kashayam',
    'ghrutam': 'Ghrutam', 'choorna': 'Choornam', 'other': 'Capsule',
}
MEDICINE_BASES = [
    'Ashwagandha', 'Brahmi', 'Triphala', 'Punarnava', 'Gokshura', 'Guduchi',
    'Shatavari', 'Haritaki', 'Bibhitaki', 'Amalaki', 'Neem', 'Tulsi',
    'Yashtimadhu', 'Pippali', 'Shankhpushpi', 'Bala', 'Musta', 'Chitrak',
    'Kutki', 'Arjuna',
]
MEDICINE_COMPANIES = [
    'Baidyanath', 'Himalaya', 'Dabur', 'Patanjali', 'Zandu', 'Vicco',
    'Sri Sri Tattva', 'Kerala Ayurveda',
]


class TreatmentInfo:
    """Lightweight stand-in for the Treatment model.

    The real `treatments` table is missing the `is_active` column the ORM
    model declares, so `db.query(Treatment)` raises UndefinedColumn. Fetch
    only the columns that actually exist via raw SQL instead.
    """
    def __init__(self, row):
        self.treatment_id = row.treatment_id
        self.base_price = row.base_price
        self.requires_therapist = row.requires_therapist
        self.requires_doctor = row.requires_doctor


def fetch_treatments(db):
    rows = db.execute(text(
        "SELECT treatment_id, base_price, requires_therapist, requires_doctor FROM treatments"
    )).fetchall()
    return [TreatmentInfo(r) for r in rows]


def ensure_users(db):
    count = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
    if count > 0:
        print(f"= users already present ({count}) - skipping")
        return

    default_users = [
        ("admin", "Admin User", UserRole.admin, "admin123", "admin@clinic.com"),
        ("doctor_1", "Dr. Rajesh Sharma", UserRole.doctor, "doctor123", "doctor@clinic.com"),
        ("pharmacist_1", "Pharmacist", UserRole.pharmacist, "pharma123", "pharmacist@clinic.com"),
        ("receptionist_1", "Receptionist", UserRole.receptionist, "reception123", "receptionist@clinic.com"),
        ("therapist_1", "Therapist", UserRole.therapist, "therapy123", "therapist@clinic.com"),
    ]
    for username, full_name, role, password, email in default_users:
        # created_at has no server-side DEFAULT (it's a Python/ORM-level
        # default only), so it must be set explicitly here - otherwise every
        # raw-SQL-inserted user gets created_at=NULL, which breaks login
        # (UserResponse requires a valid datetime).
        db.execute(text(
            "INSERT INTO users (username, password_hash, full_name, role, email, is_active, created_at) "
            "VALUES (:u, :p, :f, :r, :e, TRUE, NOW())"
        ), {"u": username, "p": pwd_context.hash(password), "f": full_name, "r": role.value, "e": email})
    db.flush()
    print(f"+ {len(default_users)} default users (e.g. doctor_1/doctor123)")


def ensure_catalog(db):
    medicine_count = db.query(Medicine).count()
    if medicine_count > 0:
        print(f"= medicines already present ({medicine_count}) - skipping catalog creation")
        return [], []

    vendors = []
    for _ in range(8):
        vendor = Vendor(
            vendor_name=fake.company(),
            contact_person=fake.name(),
            phone=fake.msisdn()[:10],
            email=fake.company_email(),
            address=fake.address(),
            gstin=f"GST{random.randint(10**9, 10**10 - 1)}",
            payment_terms=random.choice(["Net 15", "Net 30", "Net 45", "COD"]),
            lead_time_days=random.randint(3, 21),
            rating=round(random.uniform(3.0, 5.0), 1),
            total_orders=0,
        )
        db.add(vendor)
        vendors.append(vendor)
    db.flush()

    medicines = []
    seen_names = set()
    for base in MEDICINE_BASES:
        for category in random.sample(MEDICINE_CATEGORIES, 2):
            name = f"{base} {CATEGORY_FORM_LABEL[category]}"
            if name in seen_names:
                continue
            seen_names.add(name)
            mrp = round(random.uniform(50, 1200), 2)
            medicine = Medicine(
                medicine_name=name,
                category=category,
                company=random.choice(MEDICINE_COMPANIES),
                unit_type=random.choice(["bottle", "strip", "jar", "box"]),
                unit_quantity=random.choice([10, 15, 30, 50, 100]),
                mrp_per_unit=mrp,
                cost_per_unit=round(mrp * random.uniform(0.5, 0.75), 2),
                reorder_level=random.randint(10, 25),
                storage_location=random.choice(["Shelf-A1", "Shelf-A2", "Shelf-B1", "Cold Storage"]),
            )
            db.add(medicine)
            medicines.append(medicine)
    db.flush()
    print(f"+ {len(vendors)} vendors, {len(medicines)} medicines")
    return vendors, medicines


def ensure_treatments(db):
    count = db.execute(text("SELECT COUNT(*) FROM treatments")).scalar()
    if count > 0:
        print(f"= treatments already present ({count}) - skipping")
        return

    treatments = [
        ("GC", "General Consultation", "consultation", 300.0, 20, False, True),
        ("PK", "Panchakarma", "therapy", 1700.0, 90, True, False),
        ("SSS", "Sarwang Snehan Swedan", "therapy", 1500.0, 60, True, False),
        ("WVT", "Waman (Vomiting Therapy)", "therapy", 9000.0, 120, True, True),
        ("MB", "Matra Basti", "therapy", 400.0, 30, True, False),
    ]
    for code, name, category, price, duration, req_therapist, req_doctor in treatments:
        db.execute(text(
            "INSERT INTO treatments (treatment_code, treatment_name, category, base_price, "
            "duration_minutes, requires_therapist, requires_doctor) "
            "VALUES (:c, :n, :cat, :p, :d, :rt, :rd)"
        ), {"c": code, "n": name, "cat": category, "p": price, "d": duration, "rt": req_therapist, "rd": req_doctor})
    db.flush()
    print(f"+ {len(treatments)} treatments")


def ensure_inventory(db, vendors):
    medicines_without_stock = db.execute(text(
        "SELECT m.medicine_id, m.reorder_level, m.cost_per_unit FROM medicines m "
        "LEFT JOIN inventory_stock i ON m.medicine_id = i.medicine_id "
        "WHERE i.stock_id IS NULL"
    )).fetchall()

    if not medicines_without_stock:
        print("= all medicines already have inventory stock - skipping")
        return

    vendor_ids = [v.vendor_id for v in vendors] or [
        v.vendor_id for v in db.query(Vendor.vendor_id).limit(20).all()
    ]

    created = 0
    for med_id, reorder_level, cost_per_unit in medicines_without_stock:
        reorder_level = reorder_level or 10
        roll = random.random()
        if roll < 0.15:
            quantity = random.randint(1, max(1, reorder_level))
            expiry = today + timedelta(days=200)
            status = StockStatus.low_stock
        elif roll < 0.30:
            quantity = random.randint(reorder_level, reorder_level * 3)
            expiry = today + timedelta(days=random.randint(5, 29))
            status = StockStatus.near_expiry
        else:
            quantity = random.randint(reorder_level * 2, reorder_level * 6)
            expiry = today + timedelta(days=random.randint(120, 720))
            status = StockStatus.available

        db.add(InventoryStock(
            medicine_id=med_id,
            batch_number=f"BATCH-{med_id}-{uuid.uuid4().hex[:6].upper()}",
            quantity_available=quantity,
            expiry_date=expiry,
            purchase_date=today - timedelta(days=random.randint(10, 300)),
            purchase_price=cost_per_unit or 0,
            vendor_id=random.choice(vendor_ids) if vendor_ids else None,
            status=status,
        ))
        # Flush one row at a time - batching many new InventoryStock inserts
        # together makes SQLAlchemy 2.0 use a bulk-insert path that casts
        # `status` to a native Postgres enum type ("stockstatus") which
        # doesn't exist here (this DB uses a plain VARCHAR + CHECK constraint
        # instead of a real enum) - same model/DB drift as elsewhere.
        db.flush()
        created += 1

    print(f"+ {created} inventory batches (mix of healthy/low-stock/near-expiry)")


def ensure_purchase_orders(db, vendors, medicines, count=12):
    existing = db.query(PurchaseOrder).count()
    if existing > 0:
        print(f"= purchase orders already present ({existing}) - skipping")
        return

    vendor_ids = [v.vendor_id for v in vendors] or [
        v.vendor_id for v in db.query(Vendor.vendor_id).limit(20).all()
    ]
    medicine_rows = (
        [(m.medicine_id, m.cost_per_unit) for m in medicines]
        if medicines else
        db.execute(text("SELECT medicine_id, cost_per_unit FROM medicines")).fetchall()
    )
    if not vendor_ids or not medicine_rows:
        print("No vendors/medicines available - skipping purchase orders")
        return

    statuses = [OrderStatus.draft, OrderStatus.approved, OrderStatus.ordered,
                OrderStatus.partially_received, OrderStatus.received]

    created = 0
    for i in range(count):
        status = random.choice(statuses)
        days_ago = random.randint(0, 45)
        order_date = today - timedelta(days=days_ago)
        approved_by = ADMIN_ID if status != OrderStatus.draft else None

        po = PurchaseOrder(
            po_number=f"PODEMO{i + 1:04d}",
            vendor_id=random.choice(vendor_ids),
            order_date=order_date,
            expected_delivery_date=order_date + timedelta(days=random.randint(3, 14)),
            actual_delivery_date=order_date + timedelta(days=random.randint(3, 14)) if status == OrderStatus.received else None,
            total_amount=0,
            status=status,
            created_by=PHARMACIST_ID,
            approved_by=approved_by,
        )
        db.add(po)
        db.flush()

        total = 0.0
        for _ in range(random.randint(1, 3)):
            medicine_id, cost_per_unit = random.choice(medicine_rows)
            qty = random.randint(20, 200)
            unit_price = float(cost_per_unit or random.uniform(50, 500))
            line_total = round(qty * unit_price, 2)
            total += line_total
            db.add(PurchaseOrderItem(
                po_id=po.po_id,
                medicine_id=medicine_id,
                quantity_ordered=qty,
                quantity_received=qty if status == OrderStatus.received else 0,
                unit_price=unit_price,
                total_price=line_total,
            ))

        po.total_amount = round(total, 2)
        created += 1

    db.flush()
    print(f"+ {created} purchase orders with items (draft/approved/ordered/received mix)")


def seed_patients(db, count=20):
    new_patients = []
    for _ in range(count):
        days_ago = random.randint(0, 20)
        created = datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 23))
        patient = Patient(
            unique_id=f"PATD{uuid.uuid4().hex[:8].upper()}",
            name=fake.name(),
            gender=random.choice(["M", "F"]),
            phone=fake.msisdn()[:10],
            email=fake.email(),
            address=fake.address(),
            date_of_birth=fake.date_of_birth(minimum_age=5, maximum_age=85),
            created_at=created,
        )
        db.add(patient)
        new_patients.append(patient)
    db.flush()
    print(f"+ {len(new_patients)} new patients (created in the last 20 days)")
    return new_patients


def seed_appointments_and_bills(db, patient_ids, treatments, window_past=30, window_future=60):
    appt_count = 0
    bill_count = 0
    for offset in range(-window_past, window_future + 1):
        day = today + timedelta(days=offset)
        for _ in range(random.randint(1, 2)):
            treatment = random.choice(treatments)
            patient_id = random.choice(patient_ids)
            assert patient_id is not None, "patient_id must not be None - refusing to create an orphaned appointment/bill"

            if offset < 0:
                status = AppointmentStatus.completed
            elif offset == 0:
                status = random.choice([AppointmentStatus.scheduled, AppointmentStatus.completed])
            else:
                status = AppointmentStatus.scheduled

            appointment = Appointment(
                patient_id=patient_id,
                appointment_date=day,
                time_slot=random.choice(["M", "E"]),
                treatment_id=treatment.treatment_id,
                assigned_therapist=THERAPIST_ID if treatment.requires_therapist else None,
                assigned_doctor=DOCTOR_ID if treatment.requires_doctor else DOCTOR_ID,
                status=status,
            )
            db.add(appointment)
            db.flush()
            appt_count += 1

            if status == AppointmentStatus.completed:
                consultation_charge = 300.0 if treatment.requires_doctor else 0.0
                medicine_charge = round(random.uniform(150, 2500), 2)
                treatment_charge = float(treatment.base_price or 0)
                total_amount = round(consultation_charge + medicine_charge + treatment_charge, 2)
                paid_fully = random.random() < 0.8
                amount_paid = total_amount if paid_fully else round(total_amount * random.uniform(0.3, 0.9), 2)
                balance = round(total_amount - amount_paid, 2)

                bill = Bill(
                    bill_number=f"BILLD{appointment.appointment_id:06d}",
                    patient_id=patient_id,
                    appointment_id=appointment.appointment_id,
                    bill_date=day,
                    consultation_charge=consultation_charge,
                    medicine_charge=medicine_charge,
                    treatment_charge=treatment_charge,
                    total_amount=total_amount,
                    amount_paid=amount_paid,
                    balance=balance,
                    payment_mode=random.choice(["cash", "card", "upi", "online"]),
                    created_by=RECEPTIONIST_ID,
                )
                db.add(bill)
                bill_count += 1

    print(f"+ {appt_count} appointments spanning {today - timedelta(days=window_past)} to {today + timedelta(days=window_future)}")
    print(f"+ {bill_count} bills for completed appointments")


def seed_low_stock(db, target_count=12):
    candidates = (
        db.query(Medicine)
        .filter(Medicine.is_active == True)
        .order_by(Medicine.medicine_id)
        .limit(target_count)
        .all()
    )

    updated = 0
    for medicine in candidates:
        low_qty = max(1, (medicine.reorder_level or 10) // 2)
        existing_batch = (
            db.query(InventoryStock)
            .filter(InventoryStock.medicine_id == medicine.medicine_id)
            .order_by(InventoryStock.stock_id.desc())
            .first()
        )

        if existing_batch:
            existing_batch.quantity_available = low_qty
            existing_batch.expiry_date = today + timedelta(days=200)
            existing_batch.status = StockStatus.low_stock
        else:
            db.add(InventoryStock(
                medicine_id=medicine.medicine_id,
                batch_number=f"DEMO-LOW-{medicine.medicine_id}",
                quantity_available=low_qty,
                expiry_date=today + timedelta(days=200),
                purchase_date=today - timedelta(days=10),
                purchase_price=medicine.cost_per_unit or 0,
                status=StockStatus.low_stock,
            ))
        updated += 1

    print(f"+ {updated} medicines flagged as low_stock (qty below reorder level)")


def main():
    with get_db_context() as db:
        ensure_users(db)
        ensure_treatments(db)
        vendors, medicines = ensure_catalog(db)
        ensure_inventory(db, vendors)
        ensure_purchase_orders(db, vendors, medicines)

        treatments = fetch_treatments(db)
        if not treatments:
            print("No treatments found - aborting (appointments need at least one treatment).")
            return

        new_patients = seed_patients(db)
        existing_patient_ids = [p.patient_id for p in db.query(Patient.patient_id).limit(800).all()]
        new_patient_ids = [p.patient_id for p in new_patients]
        # patient_id is the primary key so this should never contain None, but
        # filter defensively anyway - a prior unrelated data corruption (legacy
        # rows with NULL patient_id on bills/appointments, now cleaned up)
        # is exactly the failure mode we don't want this script to ever cause.
        all_patient_ids = [pid for pid in existing_patient_ids + new_patient_ids if pid is not None]

        seed_appointments_and_bills(db, all_patient_ids, treatments)
        seed_low_stock(db)

    print("\nDone. Refresh the dashboard to see updated numbers.")
    print("Re-run this script periodically (e.g. monthly) to keep 'today'/'this month' stats populated.")


if __name__ == "__main__":
    main()
