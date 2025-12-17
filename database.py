
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
        updated_at TEXT
    );
    """)

    # Ensure row id=1 exists
    cur.execute("INSERT OR IGNORE INTO targets (id, updated_at) VALUES (1, ?)", (datetime.now().isoformat(),))

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
