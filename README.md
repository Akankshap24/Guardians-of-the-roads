# Guardians of the Roads

**An accident-hotspot analysis and road-safety decision-support prototype** for HackOverflow 10.0.

The project demonstrates a web dashboard for exploring illustrative road-safety records, viewing locations on a map, comparing transparent risk scores, and reviewing suggested interventions.

## Features

- Dashboard metrics for locations, sample incidents, high-risk locations, and community reports.
- Interactive, colour-coded hotspot map.
- Search, risk-level filtering, and sorting of locations.
- Transparent 0–100 risk score and readable risk bands.
- Rule-based recommendations based on severe incidents, traffic index, and lighting index.
- Community road-concern reporting stored in SQLite.
- JSON endpoint at `/api/locations` and health endpoint at `/health`.
- Responsive layout and clear demo-data disclaimers.

## Technology

- Python 3.10+
- Flask
- SQLite
- HTML, CSS, Jinja templates
- Leaflet and OpenStreetMap tiles

## Run locally

### Windows PowerShell

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

If PowerShell blocks environment activation, use Command Prompt and run `.venv\Scripts\activate.bat`, or run `.venv\Scripts\python.exe -m pip install -r requirements.txt` and `.venv\Scripts\python.exe app.py`.

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000**. The map requires internet access for map tiles; the app's data and dashboard are local.

## Project structure

```text
guardians-of-the-roads/
├── app.py
├── data/
│   └── accidents.csv
├── instance/              # SQLite database created at runtime
├── static/
│   └── style.css
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── locations.html
│   ├── report.html
│   └── error.html
├── tests/
├── requirements.txt
├── .gitignore
└── README.md
```

## Risk-scoring approach

This prototype uses a transparent weighted heuristic, **not a trained or validated machine-learning model**:

- Accident count: up to 35 points.
- Severe incidents: up to 25 points.
- Traffic index: up to 20 points.
- Lighting concern: up to 20 points, with lower lighting values contributing more risk.

The risk bands are High (65–100), Medium (35–64), and Low (0–34). The weights and thresholds are provisional demonstration choices. They have not been calibrated against real outcomes and should not be treated as validated predictions.

## Data and limitations

The bundled location coordinates, accident counts, severe-incident counts, traffic indices, and lighting indices are **illustrative synthetic demo data**, not verified official Coimbatore accident records. The application does not ingest live traffic, IoT sensor data, weather feeds, or emergency alerts. It does not establish that accidents will be reduced.

Community reports are stored in a local SQLite database and are not sent to traffic authorities or emergency services. Do not use this prototype for operational traffic management or emergency decisions.

## Future improvements

- Replace the demo data with verified, appropriately licensed road-safety records.
- Add automated tests and stronger validation.
- Calibrate and evaluate any predictive model against historical outcomes before describing it as a prediction system.
- Add authentication, privacy controls, and secure deployment before accepting real public reports.
- Explore verified traffic and weather data integrations only when suitable APIs and permissions are available.

## Hackathon

Prepared for **HackOverflow 10.0 — NIT Durgapur**.
