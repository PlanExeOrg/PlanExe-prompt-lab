# Dashboard

Visualizes `identify_potential_levers` run data (success rates, durations, models).

## Setup

```bash
cd dashboard
python3 -m venv venv
source venv/bin/activate
pip install flask
```

## Extract data

Re-run this whenever new history data is available:

```bash
python extract_levers_data.py
```

## Run

```bash
python app.py
```

Open http://127.0.0.1:5001
