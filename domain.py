"""Builder inventory dashboard for marketing teams and broker collaboration."""
from datetime import datetime, timezone

STATUSES = ["Available", "Hold", "Reserved", "Sold"]
STATES = ["Florida", "Texas", "Arizona", "Georgia", "North Carolina"]
BROKERS = ["Unassigned", "Suncoast Realty", "Lone Star Brokers", "Metro Homes", "Capital Partners"]


def init(db):
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS projects(
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            city TEXT NOT NULL,
            state TEXT NOT NULL,
            developer TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS units(
            id INTEGER PRIMARY KEY,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            unit_code TEXT NOT NULL,
            unit_type TEXT NOT NULL,
            bedrooms INTEGER NOT NULL,
            floor TEXT NOT NULL,
            price_cents INTEGER NOT NULL,
            status TEXT NOT NULL,
            broker TEXT NOT NULL DEFAULT 'Unassigned',
            inquiries INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL,
            notes TEXT NOT NULL DEFAULT '',
            UNIQUE(project_id, unit_code)
        );
        """
    )
    if db.execute("SELECT COUNT(*) FROM projects").fetchone()[0]:
        return
    projects = [
        ("Palm Grove Residences", "Orlando", "Florida", "Northstar Builders"),
        ("Lone Star Townhomes", "Austin", "Texas", "Horizon Communities"),
        ("Desert Vista Villas", "Phoenix", "Arizona", "Civic Builders"),
    ]
    now = datetime.now(timezone.utc).isoformat()
    for project in projects:
        row = db.execute("INSERT INTO projects(name,city,state,developer) VALUES(?,?,?,?)", project)
        project_id = row.lastrowid
        db.executemany(
            """INSERT INTO units(project_id,unit_code,unit_type,bedrooms,floor,price_cents,status,broker,inquiries,updated_at,notes)
               VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            [
                (project_id, "A-101", "Condo", 2, "1", 38500000, "Available", "Suncoast Realty", 8, now, "Corner unit with pool-facing balcony."),
                (project_id, "B-204", "Townhome", 3, "2", 52500000, "Hold", "Lone Star Brokers", 11, now, "Hold expires after buyer pre-approval review."),
                (project_id, "PH-01", "Penthouse", 4, "12", 124000000, "Reserved", "Capital Partners", 5, now, "Reserved for buyer presentation meeting."),
                (project_id, "R-12", "Retail", 0, "Ground", 76000000, "Sold", "Metro Homes", 17, now, "Sold during builder launch week."),
            ],
        )


def rows(db, query, params=()):
    return [dict(row) for row in db.execute(query, params)]


def state(db):
    units = rows(
        db,
        """
        SELECT units.*, projects.name AS project_name, projects.city, projects.state, projects.developer
        FROM units
        JOIN projects ON projects.id = units.project_id
        ORDER BY projects.state, projects.name, units.unit_code
        """,
    )
    totals = {status: 0 for status in STATUSES}
    for unit in units:
        totals[unit["status"]] += 1
    return {"projects": rows(db, "SELECT * FROM projects ORDER BY state, name"), "units": units, "statuses": STATUSES, "states": STATES, "brokers": BROKERS, "totals": totals}


def cents(value):
    text = str(value or "0").strip().replace(",", "").replace("$", "")
    if not text.isdigit():
        raise ValueError("Price must be a whole number.")
    return int(text) * 100


def handle(method, path, data, db):
    if method == "GET" and path == "/api/state":
        return state(db)

    if method == "POST" and path == "/api/projects":
        name = str(data.get("name", "")).strip()
        city = str(data.get("city", "")).strip()
        region = str(data.get("state", "")).strip()
        if not 2 <= len(name) <= 120 or not 2 <= len(city) <= 80 or not region:
            raise ValueError("Enter project name, city, and state.")
        db.execute(
            "INSERT INTO projects(name,city,state,developer) VALUES(?,?,?,?)",
            (name, city, region, str(data.get("developer", "")).strip() or "Builder"),
        )
        return {"ok": True}

    if method == "POST" and path == "/api/units":
        status = str(data.get("status", "Available")).strip()
        broker = str(data.get("broker", "Unassigned")).strip()
        if status not in STATUSES:
            raise ValueError("Choose a listed inventory status.")
        if broker not in BROKERS:
            raise ValueError("Choose a listed broker.")
        unit_code = str(data.get("unit_code", "")).strip().upper()
        if not 1 <= len(unit_code) <= 30:
            raise ValueError("Enter a unit code.")
        db.execute(
            """INSERT INTO units(project_id,unit_code,unit_type,bedrooms,floor,price_cents,status,broker,inquiries,updated_at,notes)
               VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (
                data.get("project_id"),
                unit_code,
                str(data.get("unit_type", "Apartment")).strip()[:40],
                int(data.get("bedrooms") or 0),
                str(data.get("floor", "")).strip()[:30],
                cents(data.get("price")),
                status,
                broker,
                int(data.get("inquiries") or 0),
                datetime.now(timezone.utc).isoformat(),
                str(data.get("notes", "")).strip()[:1000],
            ),
        )
        return {"ok": True}

    if method == "POST" and path == "/api/update-unit":
        status = str(data.get("status", "")).strip()
        broker = str(data.get("broker", "Unassigned")).strip()
        if status not in STATUSES or broker not in BROKERS:
            raise ValueError("Choose listed status and broker values.")
        row = db.execute(
            "UPDATE units SET status=?, broker=?, inquiries=?, notes=?, updated_at=? WHERE id=?",
            (
                status,
                broker,
                int(data.get("inquiries") or 0),
                str(data.get("notes", "")).strip()[:1000],
                datetime.now(timezone.utc).isoformat(),
                data.get("id"),
            ),
        )
        if not row.rowcount:
            raise LookupError()
        return {"ok": True}

    raise LookupError()
