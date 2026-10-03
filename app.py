"""
app.py
Backend API for the Childhood Cancer Genetic Risk Surveillance System.

Endpoints:
  GET  /syndromes                -> list all known syndromes
  GET  /syndromes/<id>           -> details of one syndrome (risks + protocols)
  POST /children                 -> add a child (name, dob, syndrome_id)
  GET  /children/<id>/schedule   -> get auto-generated screening schedule
  GET  /children/<id>/schedule/upcoming -> only pending/upcoming tests

Run with: python app.py
Then visit http://localhost:5000/syndromes
"""

from flask import Flask, request, jsonify
import sqlite3
from datetime import date, timedelta

DB_NAME = "cancer_risk.db"
app = Flask(__name__)


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def add_months(start_date: date, months: int) -> date:
    """Add a number of months to a date, handling year rollover and month-length safely."""
    month = start_date.month - 1 + months
    year = start_date.year + month // 12
    month = month % 12 + 1
    day = min(start_date.day, 28)  # keep it simple/safe across all months
    return date(year, month, day)


@app.route("/syndromes", methods=["GET"])
def list_syndromes():
    conn = get_db()
    rows = conn.execute("SELECT id, name, gene, description FROM syndromes").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/syndromes/<int:syndrome_id>", methods=["GET"])
def syndrome_detail(syndrome_id):
    conn = get_db()
    syndrome = conn.execute(
        "SELECT id, name, gene, description FROM syndromes WHERE id = ?", (syndrome_id,)
    ).fetchone()
    if not syndrome:
        conn.close()
        return jsonify({"error": "Syndrome not found"}), 404

    risks = conn.execute(
        "SELECT cancer_type FROM cancer_risks WHERE syndrome_id = ?", (syndrome_id,)
    ).fetchall()
    protocols = conn.execute(
        """SELECT test_name, start_age_months, frequency_months, end_age_months
           FROM screening_protocols WHERE syndrome_id = ?""", (syndrome_id,)
    ).fetchall()
    conn.close()

    result = dict(syndrome)
    result["cancer_risks"] = [r["cancer_type"] for r in risks]
    result["screening_protocols"] = [dict(p) for p in protocols]
    return jsonify(result)


@app.route("/children", methods=["POST"])
def add_child():
    data = request.get_json(force=True)
    name = data.get("name")
    dob = data.get("dob")            # expected format: YYYY-MM-DD
    syndrome_id = data.get("syndrome_id")

    if not all([name, dob, syndrome_id]):
        return jsonify({"error": "name, dob, and syndrome_id are all required"}), 400

    conn = get_db()
    syndrome = conn.execute(
        "SELECT id FROM syndromes WHERE id = ?", (syndrome_id,)
    ).fetchone()
    if not syndrome:
        conn.close()
        return jsonify({"error": "Invalid syndrome_id"}), 400

    cur = conn.execute(
        "INSERT INTO children (name, dob, syndrome_id) VALUES (?, ?, ?)",
        (name, dob, syndrome_id)
    )
    child_id = cur.lastrowid
    conn.commit()

    _generate_schedule(conn, child_id, dob, syndrome_id)
    conn.commit()
    conn.close()

    return jsonify({"message": "Child added and schedule generated", "child_id": child_id}), 201


def _generate_schedule(conn, child_id, dob_str, syndrome_id):
    """Core logic: reads screening protocols for the syndrome and generates
    concrete scheduled dates for this specific child, based on their date of birth."""
    dob = date.fromisoformat(dob_str)
    today = date.today()

    protocols = conn.execute(
        """SELECT test_name, start_age_months, frequency_months, end_age_months
           FROM screening_protocols WHERE syndrome_id = ?""", (syndrome_id,)
    ).fetchall()

    for p in protocols:
        test_name = p["test_name"]
        start_months = p["start_age_months"]
        freq_months = p["frequency_months"]
        end_months = p["end_age_months"] if p["end_age_months"] is not None else 216  # default cap: 18 years

        current_offset = start_months
        # Generate occurrences from birth up to the end age.
        # (In production you'd cap how many rows you generate at once; kept simple here.)
        while current_offset <= end_months:
            scheduled_date = add_months(dob, current_offset)
            status = "done" if scheduled_date < today else "pending"
            conn.execute(
                """INSERT INTO screening_schedule (child_id, test_name, scheduled_date, status)
                   VALUES (?, ?, ?, ?)""",
                (child_id, test_name, scheduled_date.isoformat(), status)
            )
            current_offset += freq_months


@app.route("/children/<int:child_id>/schedule", methods=["GET"])
def get_schedule(child_id):
    conn = get_db()
    child = conn.execute("SELECT * FROM children WHERE id = ?", (child_id,)).fetchone()
    if not child:
        conn.close()
        return jsonify({"error": "Child not found"}), 404

    rows = conn.execute(
        """SELECT test_name, scheduled_date, status FROM screening_schedule
           WHERE child_id = ? ORDER BY scheduled_date ASC""", (child_id,)
    ).fetchall()
    conn.close()
    return jsonify({
        "child": dict(child),
        "schedule": [dict(r) for r in rows]
    })


@app.route("/children/<int:child_id>/schedule/upcoming", methods=["GET"])
def get_upcoming_schedule(child_id):
    conn = get_db()
    rows = conn.execute(
        """SELECT test_name, scheduled_date, status FROM screening_schedule
           WHERE child_id = ? AND status = 'pending' ORDER BY scheduled_date ASC LIMIT 10""",
        (child_id,)
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


if __name__ == "__main__":
    app.run(debug=True, port=5000)
