# Childhood Cancer Genetic Risk Surveillance System

A backend system that takes a child's known genetic predisposition syndrome
(e.g. Li-Fraumeni, RB1/Retinoblastoma, DICER1, MEN2, Beckwith-Wiedemann) and
**automatically generates a personalized cancer-screening schedule**, based on
published clinical surveillance guidelines.

> This project does not discover new medical knowledge. It operationalizes
> existing, published clinical guidelines (e.g. AACR Childhood Cancer
> Predisposition Workshop recommendations) into a usable software tool.

## Files

- `database.py` — creates `cancer_risk.db` (SQLite) and seeds it with 5
  syndromes, their associated cancer risks, and screening protocols
  (test name, start age, frequency).
- `app.py` — Flask backend exposing the API below.
- `cancer_risk.db` — generated automatically the first time you run
  `database.py` (not needed if you re-run it yourself).

## Setup

```bash
pip install flask
python database.py   # creates and seeds the database (run once)
python app.py         # starts the API on http://localhost:5000
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/syndromes` | List all known syndromes |
| GET | `/syndromes/<id>` | Details: cancer risks + screening protocols |
| POST | `/children` | Add a child (`name`, `dob`, `syndrome_id`) — auto-generates their schedule |
| GET | `/children/<id>/schedule` | Full schedule (past + upcoming) |
| GET | `/children/<id>/schedule/upcoming` | Only pending/upcoming tests |

### Example: add a child

```bash
curl -X POST http://localhost:5000/children \
  -H "Content-Type: application/json" \
  -d '{"name":"Baby Ravi","dob":"2024-01-15","syndrome_id":2}'
```

Syndrome IDs (from seed data): 1=Li-Fraumeni, 2=Retinoblastoma, 3=DICER1,
4=MEN2, 5=Beckwith-Wiedemann.

### Example: get the schedule

```bash
curl http://localhost:5000/children/1/schedule
```

The system reads the syndrome's screening protocol (e.g. "Dilated Eye Exam,
starting at birth, every 2 months, until age 4") and calculates the exact
calendar dates from the child's actual date of birth — marking past dates as
`done` and future ones as `pending`.

## How the scheduling logic works

1. Each syndrome has one or more rows in `screening_protocols`:
   `test_name`, `start_age_months`, `frequency_months`, `end_age_months`.
2. When a child is added, `_generate_schedule()` in `app.py` walks from
   `start_age_months` to `end_age_months` in steps of `frequency_months`,
   converts each offset into a real date using the child's date of birth,
   and inserts a row into `screening_schedule`.
3. Any date before today is marked `done`; anything from today onward is
   `pending` — giving a simple way to query "what's coming up next"
   (`/schedule/upcoming`).

## Possible next steps (future scope)

- Add a `status` update endpoint (mark a test as completed by a doctor).
- Add email/SMS reminders for upcoming tests.
- Add a simple frontend (calendar view) for parents/clinicians.
- Add more syndromes and cross-check protocols against updated guidelines.
- Risk-tiering logic (similar to a fraud-detection engine) to prioritize
  which children need the most urgent follow-up.

## Data sources

Screening intervals used here are simplified, illustrative examples based on
publicly published pediatric oncology surveillance literature (e.g. AACR
Childhood Cancer Predisposition Workshop). For any real clinical use, all
protocols must be reviewed and validated by a qualified geneticist or
pediatric oncologist — this project is a software scaffold, not medical advice.
