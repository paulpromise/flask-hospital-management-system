from sqlalchemy import text

from app import app, db


with app.app_context():
    constraint = db.session.execute(
        text(
            """
            SELECT CHECK_CLAUSE
            FROM information_schema.CHECK_CONSTRAINTS
            WHERE CONSTRAINT_SCHEMA = DATABASE()
              AND CONSTRAINT_NAME = 'ck_users_role'
            """
        )
    ).scalar()

    if constraint and "'staff'" in constraint:
        print("User role constraint already includes staff.")
    else:
        db.session.execute(text("ALTER TABLE users DROP CHECK ck_users_role"))
        db.session.execute(
            text(
                """
                ALTER TABLE users
                ADD CONSTRAINT ck_users_role
                CHECK (role IN ('admin', 'doctor', 'nurse', 'receptionist', 'staff'))
                """
            )
        )
        db.session.commit()
        print("Updated user role constraint to include staff.")
