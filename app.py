import csv
import os
import sqlite3
from datetime import datetime
from functools import wraps

from flask import Flask, flash, g, jsonify, redirect, render_template, request, url_for

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "instance", "guardians.db")
CSV_DATA = os.path.join(BASE_DIR, "data", "accidents.csv")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "local-dev-key-change-before-deployment")
app.config["DATABASE"] = DATABASE
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024


def get_db():
    if "db" not in g:
        os.makedirs(os.path.dirname(app.config["DATABASE"]), exist_ok=True)
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            accidents INTEGER NOT NULL DEFAULT 0,
            severe INTEGER NOT NULL DEFAULT 0,
            traffic INTEGER NOT NULL DEFAULT 50,
            lighting INTEGER NOT NULL DEFAULT 50,
            road_condition TEXT NOT NULL DEFAULT 'Unknown',
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'Received',
            created_at TEXT NOT NULL
        );
    """)
    count = db.execute("SELECT COUNT(*) FROM locations").fetchone()[0]
    if count == 0:
        seed_locations(db)
    db.commit()


def seed_locations(db):
    if not os.path.exists(CSV_DATA):
        return
    with open(CSV_DATA, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            db.execute("""
                INSERT OR IGNORE INTO locations
                (name, latitude, longitude, accidents, severe, traffic, lighting, road_condition, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row["location"], float(row["latitude"]), float(row["longitude"]),
                int(row["accidents"]), int(row["severe"]), int(row["traffic"]),
                int(row["lighting"]), row.get("road_condition", "Unknown"),
                datetime.now().isoformat(timespec="seconds")
            ))


def calculate_risk(row):
    """Transparent 0-100 heuristic. Not a trained/validated prediction model."""
    accident = min(int(row["accidents"]) / 30 * 35, 35)
    severe = min(int(row["severe"]) / 10 * 25, 25)
    traffic = max(0, min(float(row["traffic"]), 100)) / 100 * 20
    lighting = (100 - max(0, min(float(row["lighting"]), 100))) / 100 * 20
    return round(accident + severe + traffic + lighting)


def classify_risk(score):
    if score >= 65:
        return "High"
    if score >= 35:
        return "Medium"
    return "Low"


def recommendation(row):
    actions = []
    if int(row["severe"]) >= 5:
        actions.append("Prioritise a junction and road-design safety audit")
    if int(row["traffic"]) >= 70:
        actions.append("Review speed management and traffic calming")
    if int(row["lighting"]) < 50:
        actions.append("Inspect street lighting and visibility")
    if not actions:
        actions.append("Review signage and continue monitoring")
    return "; ".join(actions) + "."


def decorate_location(row):
    item = dict(row)
    item["risk_score"] = calculate_risk(item)
    item["risk_level"] = classify_risk(item["risk_score"])
    item["recommendation"] = recommendation(item)
    return item


def all_locations(search="", risk="All", sort="score"):
    rows = get_db().execute("SELECT * FROM locations").fetchall()
    locations = [decorate_location(row) for row in rows]
    if search:
        locations = [x for x in locations if search.lower() in x["name"].lower()]
    if risk in ("High", "Medium", "Low"):
        locations = [x for x in locations if x["risk_level"] == risk]
    sort_keys = {
        "score": lambda x: x["risk_score"],
        "accidents": lambda x: x["accidents"],
        "name": lambda x: x["name"].lower(),
    }
    locations.sort(key=sort_keys.get(sort, sort_keys["score"]), reverse=(sort != "name"))
    return locations


@app.route("/")
def dashboard():
    search = request.args.get("q", "").strip()[:100]
    risk = request.args.get("risk", "All")
    sort = request.args.get("sort", "score")
    locations = all_locations(search, risk, sort)
    all_rows = all_locations()
    reports_count = get_db().execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    stats = {
        "locations": len(all_rows),
        "accidents": sum(x["accidents"] for x in all_rows),
        "high": sum(x["risk_level"] == "High" for x in all_rows),
        "reports": reports_count,
    }
    return render_template("index.html", locations=locations, stats=stats,
                           search=search, selected_risk=risk, selected_sort=sort,
                           generated=datetime.now().strftime("%d %b %Y, %I:%M %p"))


@app.route("/locations")
def locations_page():
    return render_template("locations.html", locations=all_locations())


@app.route("/report", methods=["GET", "POST"])
def report():
    if request.method == "POST":
        location = request.form.get("location", "").strip()
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        if not location or not category:
            flash("Location and category are required.", "error")
            return redirect(url_for("report"))
        if len(location) > 120 or len(category) > 60 or len(description) > 1000:
            flash("Please shorten the submitted fields.", "error")
            return redirect(url_for("report"))
        get_db().execute(
            "INSERT INTO reports (location, category, description, status, created_at) VALUES (?, ?, ?, ?, ?)",
            (location, category, description, "Received", datetime.now().isoformat(timespec="seconds"))
        )
        get_db().commit()
        flash("Your demo report has been saved. It has not been sent to emergency services.", "success")
        return redirect(url_for("report"))
    reports = get_db().execute("SELECT * FROM reports ORDER BY id DESC LIMIT 50").fetchall()
    return render_template("report.html", reports=reports)


@app.route("/api/locations")
def api_locations():
    return jsonify(all_locations())


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "Guardians of the Roads"})


@app.errorhandler(404)
def not_found(error):
    return render_template("error.html", code=404, message="The page you requested was not found."), 404


@app.errorhandler(413)
def too_large(error):
    return render_template("error.html", code=413, message="The submitted request is too large."), 413


with app.app_context():
    init_db()


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1")
