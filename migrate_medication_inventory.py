import re

from sqlalchemy import inspect, text

from app import app, db


with app.app_context():
    inspector = inspect(db.engine)
    columns = {column["name"] for column in inspector.get_columns("medications")}

    try:
        if "inventory_code" not in columns:
            db.session.execute(
                text(
                    "ALTER TABLE medications "
                    "ADD COLUMN inventory_code VARCHAR(30) NULL"
                )
            )
            db.session.commit()

        rows = db.session.execute(
            text("SELECT id, name, inventory_code FROM medications ORDER BY id")
        ).mappings().all()
        used_codes = {
            row["inventory_code"] for row in rows if row["inventory_code"]
        }

        for row in rows:
            if row["inventory_code"]:
                continue

            match = re.search(r"- Inventory (\d+)$", row["name"])
            if match:
                inventory_number = int(match.group(1))
                inventory_code = f"INV-{inventory_number:03d}"
                clean_name = row["name"][:match.start()].strip()
            else:
                inventory_code = f"INV-{row['id']:03d}"
                clean_name = row["name"]

            while inventory_code in used_codes:
                inventory_code = f"INV-{row['id']:06d}"
            used_codes.add(inventory_code)

            db.session.execute(
                text(
                    "UPDATE medications "
                    "SET inventory_code = :inventory_code, name = :name "
                    "WHERE id = :id"
                ),
                {
                    "inventory_code": inventory_code,
                    "name": clean_name,
                    "id": row["id"],
                },
            )

        db.session.commit()

        inspector = inspect(db.engine)
        indexes = {
            index["name"] for index in inspector.get_indexes("medications")
        }
        if "uq_medications_inventory_code" not in indexes:
            db.session.execute(
                text(
                    "ALTER TABLE medications "
                    "ADD UNIQUE KEY uq_medications_inventory_code "
                    "(inventory_code)"
                )
            )
            db.session.commit()

        db.session.execute(
            text(
                "ALTER TABLE medications "
                "MODIFY inventory_code VARCHAR(30) NOT NULL"
            )
        )
        db.session.commit()
        print("Medication inventory migration completed.")
    except Exception:
        db.session.rollback()
        raise
