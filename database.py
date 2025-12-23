
import sqlite3
import pandas as pd
from datetime import datetime

DB_PATH = "monitoring_agri.db"

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db(conn):
    cur = conn.cursor()

    # Assets (generic): plots, hives, rabbitry units, vivoplant batches
    cur.execute("""
    CREATE TABLE IF NOT EXISTS assets (
        asset_id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_type TEXT NOT NULL,   -- plot | hive | rabbitry | vivoplant
        name TEXT NOT NULL,
        crop_type TEXT,             -- for plot: Banane/Taro/PIF ; for vivoplant: species/variety
        area_m2 REAL,
        location TEXT,
        notes TEXT,
        created_at TEXT NOT NULL
    );
    """)

    # Sensor readings for plots (7-en-1)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sensor_readings (
        reading_id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        light REAL,
        air_temp REAL,
        air_humidity REAL,
        soil_temp REAL,
        soil_moisture REAL,
        soil_ph REAL,
        fertility REAL,
        battery REAL,
        FOREIGN KEY(asset_id) REFERENCES assets(asset_id)
    );
    """)

    # Qualitative field observations for plots
    cur.execute("""
    CREATE TABLE IF NOT EXISTS field_observations (
        obs_id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        stage TEXT,
        vigor TEXT,
        leaf_status TEXT,
        disease INTEGER,
        disease_notes TEXT,
        pests INTEGER,
        pests_notes TEXT,
        notes TEXT,
        FOREIGN KEY(asset_id) REFERENCES assets(asset_id)
    );
    """)

    # Hive inspections
    cur.execute("""
    CREATE TABLE IF NOT EXISTS hive_inspections (
        insp_id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        colony_strength TEXT,
        queen_seen INTEGER,
        pests INTEGER,
        honey_kg REAL,
        notes TEXT,
        FOREIGN KEY(asset_id) REFERENCES assets(asset_id)
    );
    """)

    # Rabbit logs
    cur.execute("""
    CREATE TABLE IF NOT EXISTS rabbit_logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        females INTEGER,
        males INTEGER,
        births INTEGER,
        deaths INTEGER,
        feed_kg REAL,
        notes TEXT,
        FOREIGN KEY(asset_id) REFERENCES assets(asset_id)
    );
    """)

    # Vivoplant logs
    cur.execute("""
    CREATE TABLE IF NOT EXISTS vivoplant_logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        produced INTEGER,
        transplanted INTEGER,
        losses INTEGER,
        notes TEXT,
        FOREIGN KEY(asset_id) REFERENCES assets(asset_id)
    );
    """)

    # Targets (single row)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS targets (
        id INTEGER PRIMARY KEY CHECK (id=1),
        banane_ca INTEGER,
        taro_ca INTEGER,
        rabbits_cycle INTEGER,
        hives_count INTEGER,
        vivoplants_cycle INTEGER,
        loss_rate REAL,
        households_target INTEGER DEFAULT 500,
        updated_at TEXT
    );
    """)

    # Ensure row id=1 exists
    cur.execute("INSERT OR IGNORE INTO targets (id, updated_at) VALUES (1, ?)", (datetime.now().isoformat(),))

    # ==================== NEW TABLES FOR COOPERATIVE VISION ====================

    # Revenue streams configuration (Business Model)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS revenue_streams (
        stream_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT,
        target_pct REAL,
        current_pct REAL,
        notes TEXT,
        updated_at TEXT
    );
    """)

    # Financial targets by year
    cur.execute("""
    CREATE TABLE IF NOT EXISTS financial_targets (
        year INTEGER PRIMARY KEY,
        banane_ca INTEGER DEFAULT 0,
        taro_ca INTEGER DEFAULT 0,
        apiculture_ca INTEGER DEFAULT 0,
        cuniculture_ca INTEGER DEFAULT 0,
        vivoplants_ca INTEGER DEFAULT 0,
        total_target INTEGER DEFAULT 0,
        social_fund_pct REAL DEFAULT 15.0,
        updated_at TEXT
    );
    """)

    # Roadmap phases
    cur.execute("""
    CREATE TABLE IF NOT EXISTS roadmap_phases (
        phase_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        start_date TEXT,
        end_date TEXT,
        description TEXT,
        created_at TEXT
    );
    """)

    # Roadmap milestones
    cur.execute("""
    CREATE TABLE IF NOT EXISTS roadmap_milestones (
        milestone_id INTEGER PRIMARY KEY AUTOINCREMENT,
        phase_id INTEGER,
        title TEXT NOT NULL,
        target_date TEXT,
        actual_date TEXT,
        status TEXT DEFAULT 'pending',
        notes TEXT,
        FOREIGN KEY(phase_id) REFERENCES roadmap_phases(phase_id)
    );
    """)

    # Ecosystem contract - Impact indicators
    cur.execute("""
    CREATE TABLE IF NOT EXISTS impact_indicators (
        indicator_id INTEGER PRIMARY KEY AUTOINCREMENT,
        domain TEXT NOT NULL,
        name TEXT NOT NULL,
        unit TEXT,
        target_2027 REAL,
        current_value REAL DEFAULT 0,
        last_updated TEXT
    );
    """)

    # Social fund allocations
    cur.execute("""
    CREATE TABLE IF NOT EXISTS social_fund (
        allocation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        amount REAL,
        beneficiaries INTEGER DEFAULT 0,
        date TEXT,
        notes TEXT
    );
    """)

    # Committee members (Governance)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS committee_members (
        member_id INTEGER PRIMARY KEY AUTOINCREMENT,
        role TEXT NOT NULL,
        name TEXT,
        contact TEXT,
        elected_date TEXT,
        active INTEGER DEFAULT 1
    );
    """)

    # Committee meetings
    cur.execute("""
    CREATE TABLE IF NOT EXISTS committee_meetings (
        meeting_id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        attendees TEXT,
        decisions TEXT,
        next_actions TEXT
    );
    """)

    # Households table (for legacy diagnostic data)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS households (
        household_id INTEGER PRIMARY KEY AUTOINCREMENT,
        zone TEXT,
        lat REAL,
        lon REAL,
        hh_size INTEGER,
        main_activity TEXT,
        vulnerability TEXT,
        water_improved INTEGER DEFAULT 0,
        sanitation INTEGER DEFAULT 0,
        children_schooling INTEGER DEFAULT 0,
        needs_water INTEGER DEFAULT 0,
        needs_sanitation INTEGER DEFAULT 0,
        needs_housing INTEGER DEFAULT 0,
        needs_education INTEGER DEFAULT 0,
        needs_health INTEGER DEFAULT 0,
        needs_economic INTEGER DEFAULT 0,
        collected_at TEXT
    );
    """)

    # Water samples table (for legacy diagnostic data)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS water_samples (
        sample_id INTEGER PRIMARY KEY AUTOINCREMENT,
        zone TEXT,
        lat REAL,
        lon REAL,
        season TEXT,
        ph REAL,
        turbidity REAL,
        conductivity REAL,
        e_coli REAL,
        risk_level TEXT,
        collected_at TEXT
    );
    """)

    conn.commit()

# ---------------- CRUD helpers ----------------
def create_asset(conn, asset_type, name, crop_type=None, area_m2=None, location=None, notes=None):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO assets (asset_type, name, crop_type, area_m2, location, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (asset_type, name, crop_type, area_m2, location, notes, datetime.now().isoformat()))
    conn.commit()

def get_asset_id_by_name(conn, asset_type, name):
    cur = conn.cursor()
    cur.execute("SELECT asset_id FROM assets WHERE asset_type=? AND name=? ORDER BY asset_id DESC LIMIT 1", (asset_type, name))
    r = cur.fetchone()
    return r[0] if r else None

def get_plots(conn):
    return pd.read_sql_query("SELECT * FROM assets ORDER BY asset_id DESC", conn)

def add_sensor_reading(conn, asset_id, dt, light=None, air_temp=None, air_humidity=None, soil_temp=None,
                       soil_moisture=None, soil_ph=None, fertility=None, battery=None, **_):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO sensor_readings (asset_id, date, light, air_temp, air_humidity, soil_temp, soil_moisture, soil_ph, fertility, battery)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (asset_id, dt.isoformat(), light, air_temp, air_humidity, soil_temp, soil_moisture, soil_ph, fertility, battery))
    conn.commit()

def get_sensor_readings(conn, since=None):
    if since is None:
        q = "SELECT * FROM sensor_readings"
        return pd.read_sql_query(q, conn)
    q = "SELECT * FROM sensor_readings WHERE date >= ?"
    return pd.read_sql_query(q, conn, params=(since.isoformat(),))

def get_latest_sensor_by_plot(conn):
    # latest per asset_id
    q = """
    SELECT s.*
    FROM sensor_readings s
    JOIN (
        SELECT asset_id, MAX(date) AS max_date
        FROM sensor_readings
        GROUP BY asset_id
    ) x
    ON s.asset_id = x.asset_id AND s.date = x.max_date
    """
    return pd.read_sql_query(q, conn)

def add_field_observation(conn, asset_id, dt, stage, vigor, leaf_status, disease, disease_notes, pests, pests_notes, notes):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO field_observations (asset_id, date, stage, vigor, leaf_status, disease, disease_notes, pests, pests_notes, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (asset_id, dt.isoformat(), stage, vigor, leaf_status, disease, disease_notes, pests, pests_notes, notes))
    conn.commit()

def get_field_observations(conn, since=None):
    if since is None:
        return pd.read_sql_query("SELECT * FROM field_observations", conn)
    return pd.read_sql_query("SELECT * FROM field_observations WHERE date >= ?", conn, params=(since.isoformat(),))

def get_latest_qual_by_plot(conn):
    q = """
    SELECT f.*
    FROM field_observations f
    JOIN (
        SELECT asset_id, MAX(date) AS max_date
        FROM field_observations
        GROUP BY asset_id
    ) x
    ON f.asset_id = x.asset_id AND f.date = x.max_date
    """
    return pd.read_sql_query(q, conn)

# Apiculture
def add_hive_inspection(conn, asset_id, dt, colony_strength, queen_seen, pests, honey_kg, notes):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO hive_inspections (asset_id, date, colony_strength, queen_seen, pests, honey_kg, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (asset_id, dt.isoformat(), colony_strength, queen_seen, pests, honey_kg, notes))
    conn.commit()

def get_hive_inspections(conn, since=None):
    if since is None:
        return pd.read_sql_query("SELECT * FROM hive_inspections", conn)
    return pd.read_sql_query("SELECT * FROM hive_inspections WHERE date >= ?", conn, params=(since.isoformat(),))

# Rabbits
def add_rabbit_log(conn, asset_id, dt, females, males, births, deaths, feed_kg, notes):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO rabbit_logs (asset_id, date, females, males, births, deaths, feed_kg, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (asset_id, dt.isoformat(), females, males, births, deaths, feed_kg, notes))
    conn.commit()

def get_rabbit_logs(conn, since=None):
    if since is None:
        return pd.read_sql_query("SELECT * FROM rabbit_logs", conn)
    return pd.read_sql_query("SELECT * FROM rabbit_logs WHERE date >= ?", conn, params=(since.isoformat(),))

# Vivoplants
def add_vivoplant_log(conn, asset_id, dt, produced, transplanted, losses, notes):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO vivoplant_logs (asset_id, date, produced, transplanted, losses, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (asset_id, dt.isoformat(), produced, transplanted, losses, notes))
    conn.commit()

def get_vivoplant_logs(conn, since=None):
    if since is None:
        return pd.read_sql_query("SELECT * FROM vivoplant_logs", conn)
    return pd.read_sql_query("SELECT * FROM vivoplant_logs WHERE date >= ?", conn, params=(since.isoformat(),))

# Targets
def upsert_targets(conn, values: dict):
    cur = conn.cursor()
    cur.execute("""
        UPDATE targets
        SET banane_ca=?, taro_ca=?, rabbits_cycle=?, hives_count=?, vivoplants_cycle=?, loss_rate=?, updated_at=?
        WHERE id=1
    """, (
        values.get("banane_ca"),
        values.get("taro_ca"),
        values.get("rabbits_cycle"),
        values.get("hives_count"),
        values.get("vivoplants_cycle"),
        values.get("loss_rate"),
        datetime.now().isoformat()
    ))
    conn.commit()

def get_targets(conn):
    df = pd.read_sql_query("SELECT * FROM targets WHERE id=1", conn)
    if df.empty:
        return {}
    row = df.iloc[0].to_dict()
    # Remove id
    row.pop("id", None)
    return row

def get_target(conn):
    """Legacy compatibility: get households_target"""
    targets = get_targets(conn)
    return targets.get("households_target", 500)

# ==================== NEW CRUD FUNCTIONS ====================

# Revenue Streams
def add_revenue_stream(conn, name, category, target_pct, current_pct=0, notes=None):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO revenue_streams (name, category, target_pct, current_pct, notes, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, category, target_pct, current_pct, notes, datetime.now().isoformat()))
    conn.commit()

def get_revenue_streams(conn):
    return pd.read_sql_query("SELECT * FROM revenue_streams ORDER BY target_pct DESC", conn)

def update_revenue_stream(conn, stream_id, **kwargs):
    allowed = ["name", "category", "target_pct", "current_pct", "notes"]
    sets = ", ".join([f"{k}=?" for k in kwargs if k in allowed])
    if not sets:
        return
    vals = [kwargs[k] for k in kwargs if k in allowed]
    vals.append(datetime.now().isoformat())
    vals.append(stream_id)
    cur = conn.cursor()
    cur.execute(f"UPDATE revenue_streams SET {sets}, updated_at=? WHERE stream_id=?", vals)
    conn.commit()

# Financial Targets
def upsert_financial_target(conn, year, **kwargs):
    cur = conn.cursor()
    cur.execute("SELECT year FROM financial_targets WHERE year=?", (year,))
    if cur.fetchone():
        allowed = ["banane_ca", "taro_ca", "apiculture_ca", "cuniculture_ca", "vivoplants_ca", "total_target", "social_fund_pct"]
        sets = ", ".join([f"{k}=?" for k in kwargs if k in allowed])
        if sets:
            vals = [kwargs[k] for k in kwargs if k in allowed]
            vals.append(datetime.now().isoformat())
            vals.append(year)
            cur.execute(f"UPDATE financial_targets SET {sets}, updated_at=? WHERE year=?", vals)
    else:
        cur.execute("""
            INSERT INTO financial_targets (year, banane_ca, taro_ca, apiculture_ca, cuniculture_ca, vivoplants_ca, total_target, social_fund_pct, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            year,
            kwargs.get("banane_ca", 0),
            kwargs.get("taro_ca", 0),
            kwargs.get("apiculture_ca", 0),
            kwargs.get("cuniculture_ca", 0),
            kwargs.get("vivoplants_ca", 0),
            kwargs.get("total_target", 0),
            kwargs.get("social_fund_pct", 15.0),
            datetime.now().isoformat()
        ))
    conn.commit()

def get_financial_targets(conn):
    return pd.read_sql_query("SELECT * FROM financial_targets ORDER BY year", conn)

# Roadmap Phases
def add_roadmap_phase(conn, name, status="pending", start_date=None, end_date=None, description=None):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO roadmap_phases (name, status, start_date, end_date, description, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, status, start_date, end_date, description, datetime.now().isoformat()))
    conn.commit()
    return cur.lastrowid

def get_roadmap_phases(conn):
    return pd.read_sql_query("SELECT * FROM roadmap_phases ORDER BY start_date", conn)

def update_roadmap_phase(conn, phase_id, **kwargs):
    allowed = ["name", "status", "start_date", "end_date", "description"]
    sets = ", ".join([f"{k}=?" for k in kwargs if k in allowed])
    if not sets:
        return
    vals = [kwargs[k] for k in kwargs if k in allowed]
    vals.append(phase_id)
    cur = conn.cursor()
    cur.execute(f"UPDATE roadmap_phases SET {sets} WHERE phase_id=?", vals)
    conn.commit()

# Roadmap Milestones
def add_roadmap_milestone(conn, phase_id, title, target_date=None, status="pending", notes=None):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO roadmap_milestones (phase_id, title, target_date, status, notes)
        VALUES (?, ?, ?, ?, ?)
    """, (phase_id, title, target_date, status, notes))
    conn.commit()

def get_roadmap_milestones(conn, phase_id=None):
    if phase_id:
        return pd.read_sql_query("SELECT * FROM roadmap_milestones WHERE phase_id=? ORDER BY target_date", conn, params=(phase_id,))
    return pd.read_sql_query("SELECT * FROM roadmap_milestones ORDER BY target_date", conn)

def update_milestone_status(conn, milestone_id, status, actual_date=None):
    cur = conn.cursor()
    if actual_date:
        cur.execute("UPDATE roadmap_milestones SET status=?, actual_date=? WHERE milestone_id=?", (status, actual_date, milestone_id))
    else:
        cur.execute("UPDATE roadmap_milestones SET status=? WHERE milestone_id=?", (status, milestone_id))
    conn.commit()

# Impact Indicators
def add_impact_indicator(conn, domain, name, unit, target_2027, current_value=0):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO impact_indicators (domain, name, unit, target_2027, current_value, last_updated)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (domain, name, unit, target_2027, current_value, datetime.now().isoformat()))
    conn.commit()

def get_impact_indicators(conn, domain=None):
    if domain:
        return pd.read_sql_query("SELECT * FROM impact_indicators WHERE domain=?", conn, params=(domain,))
    return pd.read_sql_query("SELECT * FROM impact_indicators ORDER BY domain, name", conn)

def update_impact_indicator(conn, indicator_id, current_value):
    cur = conn.cursor()
    cur.execute("UPDATE impact_indicators SET current_value=?, last_updated=? WHERE indicator_id=?", 
                (current_value, datetime.now().isoformat(), indicator_id))
    conn.commit()

# Social Fund
def add_social_fund_allocation(conn, category, amount, beneficiaries=0, date=None, notes=None):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO social_fund (category, amount, beneficiaries, date, notes)
        VALUES (?, ?, ?, ?, ?)
    """, (category, amount, beneficiaries, date or datetime.now().isoformat()[:10], notes))
    conn.commit()

def get_social_fund(conn):
    return pd.read_sql_query("SELECT * FROM social_fund ORDER BY date DESC", conn)

def get_social_fund_summary(conn):
    return pd.read_sql_query("""
        SELECT category, SUM(amount) as total_amount, SUM(beneficiaries) as total_beneficiaries
        FROM social_fund GROUP BY category
    """, conn)

# Committee Members
def add_committee_member(conn, role, name, contact=None, elected_date=None):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO committee_members (role, name, contact, elected_date, active)
        VALUES (?, ?, ?, ?, 1)
    """, (role, name, contact, elected_date))
    conn.commit()

def get_committee_members(conn, active_only=True):
    if active_only:
        return pd.read_sql_query("SELECT * FROM committee_members WHERE active=1 ORDER BY role", conn)
    return pd.read_sql_query("SELECT * FROM committee_members ORDER BY role, active DESC", conn)

def deactivate_committee_member(conn, member_id):
    cur = conn.cursor()
    cur.execute("UPDATE committee_members SET active=0 WHERE member_id=?", (member_id,))
    conn.commit()

# Committee Meetings
def add_committee_meeting(conn, date, attendees, decisions=None, next_actions=None):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO committee_meetings (date, attendees, decisions, next_actions)
        VALUES (?, ?, ?, ?)
    """, (date, attendees, decisions, next_actions))
    conn.commit()

def get_committee_meetings(conn, limit=10):
    return pd.read_sql_query(f"SELECT * FROM committee_meetings ORDER BY date DESC LIMIT {limit}", conn)

# ==================== LEGACY COMPATIBILITY ====================

def households_df(conn):
    """Get households data for legacy dashboard"""
    return pd.read_sql_query("SELECT * FROM households", conn)

def water_df(conn):
    """Get water samples data for legacy dashboard"""
    return pd.read_sql_query("SELECT * FROM water_samples", conn)

def add_household(conn, zone, lat=None, lon=None, hh_size=None, main_activity=None, vulnerability=None,
                  water_improved=0, sanitation=0, children_schooling=0,
                  needs_water=0, needs_sanitation=0, needs_housing=0,
                  needs_education=0, needs_health=0, needs_economic=0):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO households (zone, lat, lon, hh_size, main_activity, vulnerability,
            water_improved, sanitation, children_schooling,
            needs_water, needs_sanitation, needs_housing, needs_education, needs_health, needs_economic,
            collected_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (zone, lat, lon, hh_size, main_activity, vulnerability,
          water_improved, sanitation, children_schooling,
          needs_water, needs_sanitation, needs_housing, needs_education, needs_health, needs_economic,
          datetime.now().isoformat()))
    conn.commit()

def add_water_sample(conn, zone, lat=None, lon=None, season=None, ph=None, turbidity=None,
                     conductivity=None, e_coli=None, risk_level=None):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO water_samples (zone, lat, lon, season, ph, turbidity, conductivity, e_coli, risk_level, collected_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (zone, lat, lon, season, ph, turbidity, conductivity, e_coli, risk_level, datetime.now().isoformat()))
    conn.commit()
