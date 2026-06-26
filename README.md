# MLOps — Data Validation & Testing

Data-quality validation for a deliberately messy customer dataset, built with
**Great Expectations 1.x** and **pytest**. No model training is involved — this
is the data-validation component of a retraining pipeline.

## Project layout

```
mlops-data-validation/
├── data/
│   └── customer_data.csv          # the provided messy dataset (5,015 rows)
├── src/
│   └── data_utils.py              # load_csv, clean_phone, validate_email
├── tests/
│   └── test_data_utils.py         # 35 pytest unit tests
├── great_expectations_setup.py    # GX project + suite + validation + Data Docs
├── profile_issues.py              # prints per-issue counts (Part 3)
├── make_report_assets.py          # renders the report screenshots
├── report_assets/                 # generated screenshots used by the report
├── gx/                            # Great Expectations project (auto-created)
├── assignment2_report.md          # the deliverable report
├── requirements.txt
└── README.md
```

## Setup

```bash
python -m venv .venv && source .venv/bin/activate     # optional
pip install -r requirements.txt
```

## Run

```bash
# Part 1–3: initialise GX, build the suite, validate, build HTML Data Docs
python great_expectations_setup.py

# Part 3: print per-issue counts
python profile_issues.py

# Part 4: run the unit tests
pytest -v

# (optional) regenerate the screenshots embedded in the report
python make_report_assets.py
```

After running the setup script, open the Great Expectations Data Docs at:

```
gx/uncommitted/data_docs/local_site/index.html
```

## The expectation suite

`customer_data_expectations` contains eight expectations:

| # | Column        | Expectation                                            |
|---|---------------|--------------------------------------------------------|
| 1 | customer_id   | values are unique                                      |
| 2 | customer_id   | values are not null                                    |
| 3 | age           | values between 0 and 120                               |
| 4 | email         | values match an email regex                            |
| 5 | salary        | not null in ≥ 95% of rows (`mostly=0.95`)              |
| 6 | country       | values in {USA, Canada, UK, Australia}                 |
| 7 | signup_date   | values are datetime type                               |
| 8 | (table)       | row count between 500 and 1000                         |

All eight fail against the raw dataset — see `assignment2_report.md`.
