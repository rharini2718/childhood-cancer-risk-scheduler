"""
database.py
Creates the SQLite database and seeds it with syndrome/screening guideline data.
Run this once before starting the API: python database.py
"""

import sqlite3

DB_NAME = "cancer_risk.db"


def create_tables(cursor):
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS syndromes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        gene TEXT NOT NULL,
        description TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cancer_risks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        syndrome_id INTEGER NOT NULL,
        cancer_type TEXT NOT NULL,
        FOREIGN KEY (syndrome_id) REFERENCES syndromes(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS screening_protocols (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        syndrome_id INTEGER NOT NULL,
        test_name TEXT NOT NULL,
        start_age_months INTEGER NOT NULL,
        frequency_months INTEGER NOT NULL,
        end_age_months INTEGER,
        FOREIGN KEY (syndrome_id) REFERENCES syndromes(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS children (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        dob TEXT NOT NULL,
        syndrome_id INTEGER NOT NULL,
        FOREIGN KEY (syndrome_id) REFERENCES syndromes(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS screening_schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        child_id INTEGER NOT NULL,
        test_name TEXT NOT NULL,
        scheduled_date TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        FOREIGN KEY (child_id) REFERENCES children(id)
    )
    """)


def seed_data(cursor):
    # Clear existing seed data (safe re-run)
    cursor.execute("DELETE FROM cancer_risks")
    cursor.execute("DELETE FROM screening_protocols")
    cursor.execute("DELETE FROM syndromes")

    syndromes = [
        ("Li-Fraumeni Syndrome", "TP53",
         "Predisposes to sarcoma, brain tumors, adrenal cortical carcinoma, breast cancer."),
        ("Retinoblastoma Predisposition", "RB1",
         "Predisposes to retinoblastoma, an eye cancer in early childhood."),
        ("DICER1 Syndrome", "DICER1",
         "Predisposes to pleuropulmonary blastoma, thyroid nodules, ovarian tumors."),
        ("MEN2 (Multiple Endocrine Neoplasia type 2)", "RET",
         "Predisposes to medullary thyroid cancer; often managed with prophylactic surgery."),
        ("Beckwith-Wiedemann Syndrome", "11p15 (imprinting region)",
         "Predisposes to Wilms tumor and hepatoblastoma in early childhood."),
    ]

    cursor.executemany(
        "INSERT INTO syndromes (name, gene, description) VALUES (?, ?, ?)",
        syndromes
    )

    # Map syndrome name -> id for seeding related tables
    cursor.execute("SELECT id, name FROM syndromes")
    ids = {name: sid for sid, name in cursor.fetchall()}

    cancer_risks = [
        (ids["Li-Fraumeni Syndrome"], "Sarcoma"),
        (ids["Li-Fraumeni Syndrome"], "Brain tumor"),
        (ids["Li-Fraumeni Syndrome"], "Adrenal cortical carcinoma"),
        (ids["Retinoblastoma Predisposition"], "Retinoblastoma (eye cancer)"),
        (ids["DICER1 Syndrome"], "Pleuropulmonary blastoma"),
        (ids["DICER1 Syndrome"], "Thyroid nodules/cancer"),
        (ids["MEN2 (Multiple Endocrine Neoplasia type 2)"], "Medullary thyroid cancer"),
        (ids["Beckwith-Wiedemann Syndrome"], "Wilms tumor"),
        (ids["Beckwith-Wiedemann Syndrome"], "Hepatoblastoma"),
    ]
    cursor.executemany(
        "INSERT INTO cancer_risks (syndrome_id, cancer_type) VALUES (?, ?)",
        cancer_risks
    )

    # start_age_months, frequency_months, end_age_months (None = ongoing/lifelong)
    screening_protocols = [
        (ids["Li-Fraumeni Syndrome"], "Whole-body MRI", 0, 12, None),
        (ids["Li-Fraumeni Syndrome"], "Abdominal Ultrasound", 0, 3, 216),  # every 3mo till age 18
        (ids["Li-Fraumeni Syndrome"], "Blood test (CBC)", 0, 4, None),

        (ids["Retinoblastoma Predisposition"], "Dilated Eye Exam", 0, 2, 48),  # every 2mo till age 4

        (ids["DICER1 Syndrome"], "Chest X-ray", 0, 6, 96),
        (ids["DICER1 Syndrome"], "Thyroid Ultrasound", 96, 12, None),  # start at age 8

        (ids["MEN2 (Multiple Endocrine Neoplasia type 2)"], "Calcitonin Blood Test", 6, 6, None),

        (ids["Beckwith-Wiedemann Syndrome"], "Abdominal Ultrasound", 0, 3, 48),
        (ids["Beckwith-Wiedemann Syndrome"], "AFP Blood Test", 0, 3, 48),
    ]
    cursor.executemany(
        """INSERT INTO screening_protocols
           (syndrome_id, test_name, start_age_months, frequency_months, end_age_months)
           VALUES (?, ?, ?, ?, ?)""",
        screening_protocols
    )


def main():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    create_tables(cur)
    seed_data(cur)
    conn.commit()
    conn.close()
    print(f"Database '{DB_NAME}' created and seeded successfully.")


if __name__ == "__main__":
    main()
