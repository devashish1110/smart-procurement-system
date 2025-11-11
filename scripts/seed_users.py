#!/usr/bin/env python3
"""
Seed default users (doctor, pharmacist, receptionist, therapist)
with bcrypt-hashed passwords.

✅ Hardcoded DB URL (no .env needed)
✅ Always updates password_hash + role
✅ Matches your exact DB schema
"""

import sys
from sqlalchemy import create_engine, text
from passlib.context import CryptContext

# ✅ bcrypt hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ✅ Hardcoded DB credentials (your password included)
DB_URL = "postgresql+psycopg2://postgres:qK4Asnk0&8@localhost:5432/procurement"

# ✅ Your actual table + columns
USERS_TABLE = "users"
USERNAME_FIELD = "username"
PASSWORD_FIELD = "password_hash"
ROLE_FIELD = "role"
IS_ACTIVE_FIELD = "is_active"

# ✅ Users to create/update
DEFAULT_USERS = [
    ("doctor_1",       "doctor",       "doctor123"),
    ("pharmacist_1",   "pharmacist",   "pharma123"),
    ("receptionist_1", "receptionist", "reception123"),
    ("therapist_1",    "therapist",    "therapy123"),
]


# ✅ check if table has needed column
def table_has_column(engine, table, column):
    q = text("""
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = :t AND column_name = :c
        LIMIT 1
    """)
    with engine.begin() as conn:
        return conn.execute(q, {"t": table, "c": column}).first() is not None


# ✅ insert OR update (always updates password + role)
def upsert_user(engine, username, role, password_hash):
    with engine.begin() as conn:
        # check if exists
        exists = conn.execute(
            text(f"SELECT 1 FROM {USERS_TABLE} WHERE {USERNAME_FIELD} = :u"),
            {"u": username}
        ).first()

        if exists:
            # ✅ update password & role
            conn.execute(
                text(f"""
                    UPDATE {USERS_TABLE}
                    SET {ROLE_FIELD} = :r,
                        {PASSWORD_FIELD} = :p
                    WHERE {USERNAME_FIELD} = :u
                """),
                {"u": username, "r": role, "p": password_hash}
            )
            return "updated (password + role)"

        else:
            # ✅ insert new
            conn.execute(
                text(f"""
                    INSERT INTO {USERS_TABLE}
                    ({USERNAME_FIELD}, {ROLE_FIELD}, {PASSWORD_FIELD}, {IS_ACTIVE_FIELD})
                    VALUES (:u, :r, :p, TRUE)
                """),
                {"u": username, "r": role, "p": password_hash}
            )
            return "inserted"


def main():
    engine = create_engine(DB_URL, future=True)

    # ✅ validate schema
    if not table_has_column(engine, USERS_TABLE, PASSWORD_FIELD):
        print(f"[ERROR] Column '{PASSWORD_FIELD}' not found in table '{USERS_TABLE}'.")
        sys.exit(1)

    results = []
    for username, role, plain_pw in DEFAULT_USERS:
        hashed = pwd_context.hash(plain_pw)
        result = upsert_user(engine, username, role, hashed)
        results.append((username, role, result))

    # ✅ summary
    print("\n✅ Seeding complete:")
    for u, r, res in results:
        print(f" - {u:<15} ({r:<12}) → {res}")

    print("\n✅ Login credentials ready:")
    for u, r, pw in DEFAULT_USERS:
        print(f"   {u} / {pw}")


if __name__ == "__main__":
    main()
