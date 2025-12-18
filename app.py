# app.py — CAYF Data Monitoring (Single-file Pro)
# Streamlit app: Agriculture (Banane/Taro/PIF) + Apiculture + Cunicululture + Vivoplants
# DB: SQLite local file created automatically.

from __future__ import annotations

import sqlite3
from pathlib import Path
from datetime import datetime, date, timedelta
import pandas as pd
import streamlit as st

# -----------------------------
# Config
# -----------------------------
APP_VERSION = "V4 (Single-file Pro)"
ASSETS_DIR = Path("assets")
LOGO_CAYF = ASSETS_DIR / "cayf.jpg"
LOGO_DURABILIS = ASSETS_DIR / "durabilis.png"
DB_PATH = Path("cafy_monitoring.db")

BRAND_TITLE = "CAYF – Data Monitoring Data • développé par DURABILIS & CO"
BRAND_SUBTITLE_1 = "CENTRE AGROÉCOLOGIQUE INNOVANT DE N'ZAMALIGUÉ"
BRAND_SUBTITLE_2 = "porté par la Coopérative Agricole Young Foundation"
BRAND_LOCATION = "Localisation : N'zamaligué, Komo-Mondah, Gabon"

# 7-en-1 fields (you can rename labels here)
SENSOR_FIELDS = [
    ("soil_moisture", "Humidité du sol (%)", 0.0, 100.0),
    ("soil_temp", "Température du sol (°C)", -5.0, 60.0),
    ("soil_ph", "pH du sol", 0.0, 14.0),
    ("soil_ec", "Fertilité / EC (µS/cm)", 0.0, 20000.0),
    ("light", "Lumière (lux)", 0.0, 200000.0),
    ("air_temp", "Température de l’air (°C)", -5.0, 60.0),
    ("air_humidity", "Humidité de l’air (%)", 0.0, 100.0),
]

# Simple rule thresholds (tune for your site)
RULES = {
    "soil_moisture_low": 25.0,
    "soil_moisture_high": 85.0,
    "soil_ph_low": 5.5,
    "soil_ph_high": 7.5,
    "soil_temp_low": 18.0,
    "soil_temp_high": 35.0,
    "air_humidity_low": 40.0,
    "air_humidity_high": 90.0,
}

# -----------------------------
# DB helpers
# -----------------------------
def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def exec_sql(sql: str, params: tuple = ()) -> None:
    with get_conn() as conn:
        conn.execute(sql, params)
        conn.commit()


def read_df(sql: str, params: tuple = ()) -> pd.DataFrame:
    with get_conn() as conn:
        return pd.read_sql_query(sql, conn, params=params)


def init_db() -> None:
    # Agriculture blocks
    exec_sql(
        """
        CREATE TABLE IF NOT EXISTS agri_blocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            crop_type TEXT NOT NULL,              -- banane / taro / pif
            variety TEXT,
            area_ha REAL,
            location TEXT,
            planting_date TEXT,
            notes TEXT,
            created_at TEXT NOT NULL
        );
        """
    )

    # Sensor readings (7-en-1)
    exec_sql(
        """
        CREATE TABLE IF NOT EXISTS sensor_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            block_id INTEGER NOT NULL,
            reading_at TEXT NOT NULL,
            sensor_id TEXT,
            battery_level REAL,

            soil_moisture REAL,
            soil_temp REAL,
            soil_ph REAL,
            soil_ec REAL,
            light REAL,
            air_temp REAL,
            air_humidity REAL,

            note TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(block_id) REFERENCES agri_blocks(id) ON DELETE CASCADE
        );
        """
    )

    # Field observations (agriculture qualitative/quantitative)
    exec_sql(
        """
        CREATE TABLE IF NOT EXISTS agri_observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            block_id INTEGER NOT NULL,
            obs_at TEXT NOT NULL,
            plant_stage TEXT,     -- ex: plantule / croissance / floraison / fructification
            pests TEXT,           -- ravageurs/maladies
            irrigation TEXT,      -- ok / à faire / incident
            growth_cm REAL,
            leaves_state TEXT,    -- ex: vert / jaunissant / nécrose
            general_note TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(block_id) REFERENCES agri_blocks(id) ON DELETE CASCADE
        );
        """
    )

    # Apiculture: hives + inspections
    exec_sql(
        """
        CREATE TABLE IF NOT EXISTS hives (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location TEXT,
            install_date TEXT,
            hive_type TEXT,
            notes TEXT,
            created_at TEXT NOT NULL
        );
        """
    )
    exec_sql(
        """
        CREATE TABLE IF NOT EXISTS hive_inspections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hive_id INTEGER NOT NULL,
            inspect_at TEXT NOT NULL,
            queen_seen INTEGER,          -- 0/1
            brood_level INTEGER,         -- 0-5
            honey_frames INTEGER,        -- frames
            pests TEXT,
            actions TEXT,
            honey_harvest_kg REAL,
            note TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(hive_id) REFERENCES hives(id) ON DELETE CASCADE
        );
        """
    )

    # Cunicululture: cycles + events
    exec_sql(
        """
        CREATE TABLE IF NOT EXISTS rabbit_cycles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cycle_name TEXT NOT NULL,
            start_date TEXT,
            females INTEGER,
            males INTEGER,
            notes TEXT,
            created_at TEXT NOT NULL
        );
        """
    )
    exec_sql(
        """
        CREATE TABLE IF NOT EXISTS rabbit_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cycle_id INTEGER NOT NULL,
            event_at TEXT NOT NULL,
            births INTEGER,
            deaths INTEGER,
            vaccinations TEXT,
            feed_note TEXT,
            note TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(cycle_id) REFERENCES rabbit_cycles(id) ON DELETE CASCADE
        );
        """
    )

    # Vivoplants: lots + production events
    exec_sql(
        """
        CREATE TABLE IF NOT EXISTS vivoplants_lots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lot_name TEXT NOT NULL,
            species TEXT,                 -- ex: bananier / taro / autre
            start_date TEXT,
            target_qty INTEGER,
            notes TEXT,
            created_at TEXT NOT NULL
        );
        """
    )
    exec_sql(
        """
        CREATE TABLE IF NOT EXISTS vivoplants_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lot_id INTEGER NOT NULL,
            event_at TEXT NOT NULL,
            produced_qty INTEGER,
            losses_qty INTEGER,
            reprise_rate REAL,            -- %
            note TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(lot_id) REFERENCES vivoplants_lots(id) ON DELETE CASCADE
        );
        """
    )

    # Targets / KPI
    exec_sql(
        """
        CREATE TABLE IF NOT EXISTS targets (
            id INTEGER PRIMARY KEY CHECK (id=1),
            banana_ca_target REAL,
            taro_ca_target REAL,
            rabbits_target_per_cycle INTEGER,
            hives_target INTEGER,
            vivoplants_target_per_cycle INTEGER,
            loss_tolerance_pct REAL,
            updated_at TEXT NOT NULL
        );
        """
    )
    # Ensure singleton row exists
    if read_df("SELECT COUNT(*) as n FROM targets").iloc[0]["n"] == 0:
        exec_sql(
            """
            INSERT INTO targets (id, banana_ca_target, taro_ca_target, rabbits_target_per_cycle, hives_target, vivoplants_target_per_cycle, loss_tolerance_pct, updated_at)
            VALUES (1, 33320000, 5000000, 540, 2, 1000, 10.0, ?)
            """,
            (now_iso(),),
        )


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def to_dt(d: date, t: datetime.time) -> datetime:
    return datetime.combine(d, t).replace(microsecond=0)


# -----------------------------
# UI helpers
# -----------------------------
def safe_image(path: Path, width: int | None = None) -> None:
    if path.exists():
        st.image(str(path), width=width)
    else:
        st.warning(f"Logo introuvable: {path}. Mets le fichier dans /assets avec le bon nom.")


def brand_header() -> None:
    # Top banner with logos and text
    st.markdown(
        """
        <style>
        .cafy-banner {
            display:flex; gap:16px; align-items:stretch;
            padding: 10px 10px 2px 10px;
        }
        .cafy-left, .cafy-right {
            width: 160px; min-width:160px;
            background: transparent;
            border-radius: 14px;
        }
        .cafy-center {
            flex:1;
            background: linear-gradient(90deg, rgba(45,51,129,0.9), rgba(44,110,161,0.9), rgba(68,160,201,0.9));
            border-radius: 14px;
            padding: 14px 18px;
        }
        .cafy-title { color:#fff; font-weight:700; font-size: 16px; margin:0; }
        .cafy-sub { color:#eaf3ff; margin: 6px 0 0 0; font-size: 13px; }
        .cafy-sub2 { color:#eaf3ff; margin: 2px 0 0 0; font-size: 13px; }
        .cafy-loc { color:#eaf3ff; margin: 10px 0 0 0; font-size: 13px; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns([1.3, 6.2, 1.3], vertical_alignment="center")
    with c1:
        safe_image(LOGO_CAYF, width=150)
    with c2:
        st.markdown(
            f"""
            <div class="cafy-center">
              <p class="cafy-title">{BRAND_TITLE}</p>
              <p class="cafy-sub">{BRAND_SUBTITLE_1}</p>
              <p class="cafy-sub2">{BRAND_SUBTITLE_2}</p>
              <p class="cafy-loc">{BRAND_LOCATION}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        safe_image(LOGO_DURABILIS, width=150)

    st.caption(f"🌿 CAFY Monitoring • Développé par DURABILIS & CO • Version {APP_VERSION}")


def df_empty_info(msg: str) -> None:
    st.info(msg)


def sidebar_nav() -> tuple[str, int]:
    st.sidebar.title("🧭 Navigation")
    page = st.sidebar.radio(
        "Choisir une page",
        [
            "Tableau de bord (Récap & Recos)",
            "Agriculture (Blocs & Capteurs)",
            "Observations terrain (Agriculture)",
            "Apiculture (Ruches)",
            "Cuniculuture (Lapins)",
            "Vivoplants",
            "Objectifs & KPI",
            "Export (CSV)",
        ],
        index=0,
    )

    # Global filter
    st.sidebar.divider()
    st.sidebar.subheader("Filtres")
    days = st.sidebar.slider("Période d’analyse (jours)", 7, 365, 180, step=1)

    return page, days


def metric_card(label: str, value, suffix: str = "") -> None:
    st.metric(label, f"{value}{suffix}")


# -----------------------------
# Recommendation engine (simple rules)
# -----------------------------
def get_latest_sensor_per_block(start_dt: datetime) -> pd.DataFrame:
    # Latest reading per block within period
    df = read_df(
        """
        SELECT sr.*
        FROM sensor_readings sr
        JOIN (
            SELECT block_id, MAX(reading_at) AS max_reading_at
            FROM sensor_readings
            WHERE reading_at >= ?
            GROUP BY block_id
        ) x ON x.block_id = sr.block_id AND x.max_reading_at = sr.reading_at
        """,
        (start_dt.isoformat(),),
    )
    return df


def compute_recommendations(start_dt: datetime) -> list[str]:
    recos: list[str] = []

    blocks = read_df("SELECT * FROM agri_blocks ORDER BY id DESC", ())
    if blocks.empty:
        return ["Commence par créer tes blocs agricoles (banane / taro / PIF)."]

    latest = get_latest_sensor_per_block(start_dt)
    if latest.empty:
        return ["Ajoute au moins une mesure capteur (7-en-1) pour activer des recommandations automatiques."]

    # Map block names
    bmap = {int(r["id"]): str(r["name"]) for _, r in blocks.iterrows()}

    for _, r in latest.iterrows():
        block_id = int(r["block_id"])
        name = bmap.get(block_id, f"Bloc #{block_id}")

        sm = r.get("soil_moisture")
        ph = r.get("soil_ph")
        stemp = r.get("soil_temp")
        ah = r.get("air_humidity")

        # Soil moisture
        if sm is not None:
            if sm < RULES["soil_moisture_low"]:
                recos.append(f"💧 **{name}** : humidité du sol basse ({sm:.1f}%). Prévoir arrosage / paillage.")
            elif sm > RULES["soil_moisture_high"]:
                recos.append(f"⚠️ **{name}** : humidité du sol très élevée ({sm:.1f}%). Risque asphyxie/racines → vérifier drainage.")

        # pH
        if ph is not None:
            if ph < RULES["soil_ph_low"]:
                recos.append(f"🧪 **{name}** : pH bas ({ph:.2f}). Envisager amendement (selon protocole local).")
            elif ph > RULES["soil_ph_high"]:
                recos.append(f"🧪 **{name}** : pH élevé ({ph:.2f}). Surveiller disponibilité nutriments (selon protocole local).")

        # Soil temp
        if stemp is not None:
            if stemp < RULES["soil_temp_low"]:
                recos.append(f"🌡️ **{name}** : sol frais ({stemp:.1f}°C). Croissance potentiellement ralentie.")
            elif stemp > RULES["soil_temp_high"]:
                recos.append(f"🌡️ **{name}** : sol chaud ({stemp:.1f}°C). Surveiller stress hydrique.")

        # Air humidity
        if ah is not None:
            if ah > RULES["air_humidity_high"]:
                recos.append(f"🍃 **{name}** : humidité air élevée ({ah:.1f}%). Risque fongique → surveillance maladies.")
            elif ah < RULES["air_humidity_low"]:
                recos.append(f"🍃 **{name}** : humidité air basse ({ah:.1f}%). Surveiller stress & irrigation.")

    if not recos:
        recos.append("✅ Aucun signal critique détecté sur la dernière mesure de chaque bloc (période sélectionnée).")

    return recos


# -----------------------------
# Pages
# -----------------------------
def page_dashboard(start_dt: datetime) -> None:
    st.header("📊 Tableau de bord – Vue d’ensemble")

    blocks = read_df("SELECT * FROM agri_blocks", ())
    hives = read_df("SELECT * FROM hives", ())
    cycles = read_df("SELECT * FROM rabbit_cycles", ())
    lots = read_df("SELECT * FROM vivoplants_lots", ())

    # --- NEW: split agriculture by crop_type
    banana_blocks = int((blocks["crop_type"] == "banane").sum()) if not blocks.empty else 0
    taro_blocks   = int((blocks["crop_type"] == "taro").sum()) if not blocks.empty else 0
    pif_blocks    = int((blocks["crop_type"] == "pif").sum()) if not blocks.empty else 0

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        metric_card("Banane (blocs)", banana_blocks)
        st.caption("Agriculture")
    with c2:
        metric_card("Taro (blocs)", taro_blocks)
        st.caption("Agriculture")
    with c3:
        metric_card("PIF (blocs)", pif_blocks)
        st.caption("Agriculture")
    with c4:
        metric_card("Ruches", len(hives))
        st.caption("Apiculture")
    with c5:
        metric_card("Cuniculuture", len(cycles))
        st.caption("Lapins")
    with c6:
        metric_card("Vivoplants (lots)", len(lots))
        st.caption("Vivoplants")


    st.divider()
    st.subheader("🧠 Recommandations automatisées (règles)")
    recos = compute_recommendations(start_dt)
    for r in recos:
        st.markdown(f"- {r}")

    st.divider()
    st.subheader("📈 Tendances (capteurs) – sur la période sélectionnée")
    sensors = read_df(
        """
        SELECT sr.reading_at, b.name as block_name, sr.soil_moisture, sr.soil_temp, sr.soil_ph, sr.soil_ec, sr.light, sr.air_temp, sr.air_humidity
        FROM sensor_readings sr
        JOIN agri_blocks b ON b.id = sr.block_id
        WHERE sr.reading_at >= ?
        ORDER BY sr.reading_at ASC
        """,
        (start_dt.isoformat(),),
    )

    if sensors.empty:
        df_empty_info("Aucune donnée capteur. Va dans « Agriculture (Blocs & Capteurs) » pour ajouter une mesure.")
        return

    # Simple line charts: user can choose metric
    metric = st.selectbox(
        "Choisir un indicateur à visualiser",
        ["soil_moisture", "soil_temp", "soil_ph", "soil_ec", "light", "air_temp", "air_humidity"],
        index=0,
    )
    plot_df = sensors[["reading_at", "block_name", metric]].copy()
    plot_df["reading_at"] = pd.to_datetime(plot_df["reading_at"])

    st.line_chart(plot_df, x="reading_at", y=metric, color="block_name")


def page_agriculture_blocks_and_sensors(start_dt: datetime) -> None:
    st.header("🌿 Agriculture – Blocs & Capteurs (7-en-1)")

    st.subheader("1) Créer un bloc agricole (banane / taro / PIF)")
    with st.form("create_block", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns([2.2, 1.6, 1.8, 1.4])
        with c1:
            name = st.text_input("Nom du bloc", value="Bloc A")
        with c2:
            crop_type = st.selectbox("Culture", ["banane", "taro", "pif"])
        with c3:
            variety = st.text_input("Variété", value="Big Ebanga / locale…")
        with c4:
            area_ha = st.number_input("Superficie (ha)", min_value=0.0, max_value=1000.0, value=1.0, step=0.1)

        location = st.text_input("Localisation interne", value="Zone humide / parcelle nord…")
        planting_date = st.date_input("Date de mise en place", value=date.today())
        notes = st.text_area("Notes", placeholder="Irrigation, sol, contraintes, etc.")

        submitted = st.form_submit_button("✅ Créer le bloc")
        if submitted:
            if not name.strip():
                st.error("Donne un nom au bloc.")
            else:
                exec_sql(
                    """
                    INSERT INTO agri_blocks (name, crop_type, variety, area_ha, location, planting_date, notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        name.strip(),
                        crop_type,
                        variety.strip() if variety else None,
                        float(area_ha) if area_ha else None,
                        location.strip() if location else None,
                        planting_date.isoformat() if planting_date else None,
                        notes.strip() if notes else None,
                        now_iso(),
                    ),
                )
                st.success("Bloc créé ✅")

    st.divider()
    st.subheader("2) Liste des blocs")
    blocks = read_df("SELECT * FROM agri_blocks ORDER BY id DESC", ())
    if blocks.empty:
        df_empty_info("Aucun bloc créé pour le moment. Crée un bloc pour activer la saisie capteur.")
        return

    st.dataframe(blocks, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("3) Ajouter une mesure capteur (7-en-1)")

    # Build label mapping
    block_labels = [f"{int(r['id'])} — {r['name']} ({r['crop_type']})" for _, r in blocks.iterrows()]
    label_to_id = {label: int(label.split("—")[0].strip()) for label in block_labels}

    chosen_label = st.selectbox("Choisir un bloc", block_labels)
    chosen_block_id = label_to_id[chosen_label]

    with st.form("add_sensor", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            reading_date = st.date_input("Date", value=date.today(), key="sr_date")
        with c2:
            reading_time = st.time_input("Heure", value=datetime.now().time().replace(second=0, microsecond=0), key="sr_time")
        with c3:
            sensor_id = st.text_input("ID capteur (optionnel)", value="sensor-01")
        with c4:
            battery_level = st.number_input("Batterie % (optionnel)", min_value=0.0, max_value=100.0, value=0.0, step=1.0)

        st.markdown("**Paramètres 7-en-1**")
        cols = st.columns(3)
        values: dict[str, float] = {}

        for idx, (key, label, mn, mx) in enumerate(SENSOR_FIELDS):
            with cols[idx % 3]:
                values[key] = st.number_input(label, min_value=float(mn), max_value=float(mx), value=0.0, step=0.1)

        note = st.text_area("Note (optionnel)", placeholder="Contexte : pluie, arrosage récent, etc.")

        submitted = st.form_submit_button("💾 Enregistrer la mesure")
        if submitted:
            reading_at = to_dt(reading_date, reading_time).isoformat()
            exec_sql(
                """
                INSERT INTO sensor_readings (
                    block_id, reading_at, sensor_id, battery_level,
                    soil_moisture, soil_temp, soil_ph, soil_ec, light, air_temp, air_humidity,
                    note, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chosen_block_id,
                    reading_at,
                    sensor_id.strip() if sensor_id else None,
                    float(battery_level) if battery_level else None,
                    float(values["soil_moisture"]),
                    float(values["soil_temp"]),
                    float(values["soil_ph"]),
                    float(values["soil_ec"]),
                    float(values["light"]),
                    float(values["air_temp"]),
                    float(values["air_humidity"]),
                    note.strip() if note else None,
                    now_iso(),
                ),
            )
            st.success("Mesure capteur enregistrée ✅")

    st.divider()
    st.subheader("4) Dernières mesures (période)")
    sensors = read_df(
        """
        SELECT sr.reading_at, b.name as bloc, b.crop_type as culture,
               sr.soil_moisture, sr.soil_temp, sr.soil_ph, sr.soil_ec, sr.light, sr.air_temp, sr.air_humidity
        FROM sensor_readings sr
        JOIN agri_blocks b ON b.id = sr.block_id
        WHERE sr.reading_at >= ?
        ORDER BY sr.reading_at DESC
        """,
        (start_dt.isoformat(),),
    )
    if sensors.empty:
        df_empty_info("Aucune mesure capteur sur la période.")
    else:
        st.dataframe(sensors, use_container_width=True, hide_index=True)


def page_observations_agri(start_dt: datetime) -> None:
    st.header("📝 Observations terrain (Agriculture)")

    blocks = read_df("SELECT * FROM agri_blocks ORDER BY id DESC", ())
    if blocks.empty:
        df_empty_info("Crée d’abord un bloc dans « Agriculture (Blocs & Capteurs) ».")
        return

    block_labels = [f"{int(r['id'])} — {r['name']} ({r['crop_type']})" for _, r in blocks.iterrows()]
    label_to_id = {label: int(label.split("—")[0].strip()) for label in block_labels}
    chosen_label = st.selectbox("Choisir un bloc", block_labels)
    chosen_block_id = label_to_id[chosen_label]

    st.subheader("1) Ajouter une observation")
    with st.form("add_obs", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            obs_date = st.date_input("Date", value=date.today())
        with c2:
            obs_time = st.time_input("Heure", value=datetime.now().time().replace(second=0, microsecond=0))
        with c3:
            stage = st.selectbox("Stade", ["plantule", "croissance", "floraison", "fructification", "récolte", "autre"])

        pests = st.text_input("Ravageurs / maladies (si présent)", placeholder="ex: charançon, cercosporiose…")
        irrigation = st.selectbox("Irrigation", ["ok", "à faire", "incident", "non renseigné"])
        c4, c5 = st.columns(2)
        with c4:
            growth_cm = st.number_input("Croissance (cm) (optionnel)", min_value=0.0, max_value=1000.0, value=0.0, step=0.5)
        with c5:
            leaves_state = st.selectbox("État des feuilles", ["vert", "jaunissant", "taches", "nécrose", "non renseigné"])

        note = st.text_area("Note générale", placeholder="Qualitatif : stress hydrique, fertilisation, désherbage, etc.")

        submitted = st.form_submit_button("✅ Enregistrer l’observation")
        if submitted:
            obs_at = to_dt(obs_date, obs_time).isoformat()
            exec_sql(
                """
                INSERT INTO agri_observations (block_id, obs_at, plant_stage, pests, irrigation, growth_cm, leaves_state, general_note, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chosen_block_id,
                    obs_at,
                    stage,
                    pests.strip() if pests else None,
                    irrigation,
                    float(growth_cm) if growth_cm else None,
                    leaves_state,
                    note.strip() if note else None,
                    now_iso(),
                ),
            )
            st.success("Observation enregistrée ✅")

    st.divider()
    st.subheader("2) Historique (période)")
    hist = read_df(
        """
        SELECT o.obs_at, b.name as bloc, b.crop_type as culture,
               o.plant_stage, o.pests, o.irrigation, o.growth_cm, o.leaves_state, o.general_note
        FROM agri_observations o
        JOIN agri_blocks b ON b.id = o.block_id
        WHERE o.obs_at >= ?
        ORDER BY o.obs_at DESC
        """,
        (start_dt.isoformat(),),
    )
    if hist.empty:
        df_empty_info("Aucune observation sur la période.")
    else:
        st.dataframe(hist, use_container_width=True, hide_index=True)


def page_apiculture(start_dt: datetime) -> None:
    st.header("🐝 Apiculture (Ruches)")

    st.subheader("1) Créer une ruche")
    with st.form("create_hive", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            name = st.text_input("Nom ruche", value="Ruche 1")
        with c2:
            location = st.text_input("Emplacement", value="Zone A")
        with c3:
            install_date = st.date_input("Date d’installation", value=date.today())
        hive_type = st.selectbox("Type", ["Langstroth", "Dadant", "KTBH", "Autre"])
        notes = st.text_area("Notes", placeholder="Matériel, particularités, etc.")
        submitted = st.form_submit_button("✅ Créer la ruche")
        if submitted:
            if not name.strip():
                st.error("Nom requis.")
            else:
                exec_sql(
                    """
                    INSERT INTO hives (name, location, install_date, hive_type, notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (name.strip(), location.strip() if location else None, install_date.isoformat(), hive_type, notes.strip() if notes else None, now_iso()),
                )
                st.success("Ruche créée ✅")

    st.divider()
    hives = read_df("SELECT * FROM hives ORDER BY id DESC", ())
    st.subheader("2) Liste des ruches")
    if hives.empty:
        df_empty_info("Aucune ruche. Crée une ruche pour activer les inspections.")
        return

    st.dataframe(hives, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("3) Ajouter une inspection")
    hive_labels = [f"{int(r['id'])} — {r['name']}" for _, r in hives.iterrows()]
    label_to_id = {label: int(label.split("—")[0].strip()) for label in hive_labels}
    chosen = st.selectbox("Choisir une ruche", hive_labels)
    hive_id = label_to_id[chosen]

    with st.form("add_hive_inspection", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            d = st.date_input("Date", value=date.today())
        with c2:
            t = st.time_input("Heure", value=datetime.now().time().replace(second=0, microsecond=0))
        with c3:
            queen_seen = st.selectbox("Reine vue ?", ["Non", "Oui"])
        with c4:
            brood_level = st.slider("Couvain (0-5)", 0, 5, 2)

        honey_frames = st.number_input("Cadres miel (nb)", min_value=0, max_value=50, value=0, step=1)
        honey_kg = st.number_input("Miel récolté (kg)", min_value=0.0, max_value=500.0, value=0.0, step=0.5)
        pests = st.text_input("Parasites / problèmes", placeholder="Varroa, fourmis, etc.")
        actions = st.text_input("Actions", placeholder="Traitement, nourrissage, nettoyage…")
        note = st.text_area("Note")

        submitted = st.form_submit_button("💾 Enregistrer inspection")
        if submitted:
            inspect_at = to_dt(d, t).isoformat()
            exec_sql(
                """
                INSERT INTO hive_inspections (hive_id, inspect_at, queen_seen, brood_level, honey_frames, pests, actions, honey_harvest_kg, note, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    hive_id,
                    inspect_at,
                    1 if queen_seen == "Oui" else 0,
                    int(brood_level),
                    int(honey_frames),
                    pests.strip() if pests else None,
                    actions.strip() if actions else None,
                    float(honey_kg),
                    note.strip() if note else None,
                    now_iso(),
                ),
            )
            st.success("Inspection enregistrée ✅")

    st.divider()
    st.subheader("4) Historique inspections (période)")
    hist = read_df(
        """
        SELECT i.inspect_at, h.name as ruche, i.queen_seen, i.brood_level, i.honey_frames, i.honey_harvest_kg, i.pests, i.actions, i.note
        FROM hive_inspections i
        JOIN hives h ON h.id = i.hive_id
        WHERE i.inspect_at >= ?
        ORDER BY i.inspect_at DESC
        """,
        (start_dt.isoformat(),),
    )
    if hist.empty:
        df_empty_info("Aucune inspection sur la période.")
    else:
        st.dataframe(hist, use_container_width=True, hide_index=True)


def page_cuniculture(start_dt: datetime) -> None:
    st.header("🐇 Cuniculuture (Lapins)")

    st.subheader("1) Créer un cycle")
    with st.form("create_cycle", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            cycle_name = st.text_input("Nom cycle", value="Cycle 2026-01")
        with c2:
            start_date = st.date_input("Date début", value=date.today())
        with c3:
            females = st.number_input("Femelles", min_value=0, max_value=10000, value=90, step=1)
        with c4:
            males = st.number_input("Mâles", min_value=0, max_value=10000, value=15, step=1)

        notes = st.text_area("Notes", placeholder="Alimentation, génétique, protocoles…")
        submitted = st.form_submit_button("✅ Créer cycle")
        if submitted:
            if not cycle_name.strip():
                st.error("Nom requis.")
            else:
                exec_sql(
                    """
                    INSERT INTO rabbit_cycles (cycle_name, start_date, females, males, notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (cycle_name.strip(), start_date.isoformat(), int(females), int(males), notes.strip() if notes else None, now_iso()),
                )
                st.success("Cycle créé ✅")

    cycles = read_df("SELECT * FROM rabbit_cycles ORDER BY id DESC", ())
    st.divider()
    st.subheader("2) Liste des cycles")
    if cycles.empty:
        df_empty_info("Aucun cycle lapins.")
        return

    st.dataframe(cycles, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("3) Ajouter un événement (naissances, décès, vaccins)")
    labels = [f"{int(r['id'])} — {r['cycle_name']}" for _, r in cycles.iterrows()]
    label_to_id = {label: int(label.split("—")[0].strip()) for label in labels}
    chosen = st.selectbox("Choisir un cycle", labels)
    cycle_id = label_to_id[chosen]

    with st.form("add_rabbit_event", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            d = st.date_input("Date", value=date.today())
        with c2:
            t = st.time_input("Heure", value=datetime.now().time().replace(second=0, microsecond=0))
        with c3:
            births = st.number_input("Naissances", min_value=0, max_value=10000, value=0, step=1)
        with c4:
            deaths = st.number_input("Décès", min_value=0, max_value=10000, value=0, step=1)

        vaccinations = st.text_input("Vaccinations / traitements", placeholder="ex: vermifuge…")
        feed_note = st.text_input("Alimentation", placeholder="ration, qualité, rupture…")
        note = st.text_area("Note")

        submitted = st.form_submit_button("💾 Enregistrer événement")
        if submitted:
            event_at = to_dt(d, t).isoformat()
            exec_sql(
                """
                INSERT INTO rabbit_events (cycle_id, event_at, births, deaths, vaccinations, feed_note, note, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cycle_id,
                    event_at,
                    int(births),
                    int(deaths),
                    vaccinations.strip() if vaccinations else None,
                    feed_note.strip() if feed_note else None,
                    note.strip() if note else None,
                    now_iso(),
                ),
            )
            st.success("Événement enregistré ✅")

    st.divider()
    st.subheader("4) Historique événements (période)")
    hist = read_df(
        """
        SELECT e.event_at, c.cycle_name, e.births, e.deaths, e.vaccinations, e.feed_note, e.note
        FROM rabbit_events e
        JOIN rabbit_cycles c ON c.id = e.cycle_id
        WHERE e.event_at >= ?
        ORDER BY e.event_at DESC
        """,
        (start_dt.isoformat(),),
    )
    if hist.empty:
        df_empty_info("Aucun événement sur la période.")
    else:
        st.dataframe(hist, use_container_width=True, hide_index=True)


def page_vivoplants(start_dt: datetime) -> None:
    st.header("🌱 Vivoplants")

    st.subheader("1) Créer un lot")
    with st.form("create_lot", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            lot_name = st.text_input("Nom lot", value="Lot VP-01")
        with c2:
            species = st.selectbox("Espèce", ["bananier", "taro", "autre"])
        with c3:
            start_date = st.date_input("Date début", value=date.today())
        target_qty = st.number_input("Objectif quantité (nb)", min_value=0, max_value=1000000, value=1000, step=10)
        notes = st.text_area("Notes", placeholder="milieu, protocole, variété…")
        submitted = st.form_submit_button("✅ Créer lot")
        if submitted:
            if not lot_name.strip():
                st.error("Nom requis.")
            else:
                exec_sql(
                    """
                    INSERT INTO vivoplants_lots (lot_name, species, start_date, target_qty, notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (lot_name.strip(), species, start_date.isoformat(), int(target_qty), notes.strip() if notes else None, now_iso()),
                )
                st.success("Lot créé ✅")

    lots = read_df("SELECT * FROM vivoplants_lots ORDER BY id DESC", ())
    st.divider()
    st.subheader("2) Lots")
    if lots.empty:
        df_empty_info("Aucun lot vivoplants.")
        return
    st.dataframe(lots, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("3) Ajouter une production (événement)")
    labels = [f"{int(r['id'])} — {r['lot_name']} ({r['species']})" for _, r in lots.iterrows()]
    label_to_id = {label: int(label.split("—")[0].strip()) for label in labels}
    chosen = st.selectbox("Choisir un lot", labels)
    lot_id = label_to_id[chosen]

    with st.form("add_vp_event", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            d = st.date_input("Date", value=date.today())
        with c2:
            t = st.time_input("Heure", value=datetime.now().time().replace(second=0, microsecond=0))
        with c3:
            produced = st.number_input("Produits (nb)", min_value=0, max_value=1000000, value=0, step=10)
        with c4:
            losses = st.number_input("Pertes (nb)", min_value=0, max_value=1000000, value=0, step=10)

        reprise = st.number_input("Taux de reprise (%)", min_value=0.0, max_value=100.0, value=0.0, step=1.0)
        note = st.text_area("Note")
        submitted = st.form_submit_button("💾 Enregistrer")
        if submitted:
            event_at = to_dt(d, t).isoformat()
            exec_sql(
                """
                INSERT INTO vivoplants_events (lot_id, event_at, produced_qty, losses_qty, reprise_rate, note, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (lot_id, event_at, int(produced), int(losses), float(reprise), note.strip() if note else None, now_iso()),
            )
            st.success("Événement vivoplants enregistré ✅")

    st.divider()
    st.subheader("4) Historique (période)")
    hist = read_df(
        """
        SELECT e.event_at, l.lot_name, l.species, e.produced_qty, e.losses_qty, e.reprise_rate, e.note
        FROM vivoplants_events e
        JOIN vivoplants_lots l ON l.id = e.lot_id
        WHERE e.event_at >= ?
        ORDER BY e.event_at DESC
        """,
        (start_dt.isoformat(),),
    )
    if hist.empty:
        df_empty_info("Aucun événement sur la période.")
    else:
        st.dataframe(hist, use_container_width=True, hide_index=True)


def page_objectifs_kpi(start_dt: datetime) -> None:
    st.header("🎯 Objectifs chiffrés & suivi")

    targets = read_df("SELECT * FROM targets WHERE id=1", ())
    t = targets.iloc[0].to_dict()

    st.subheader("Définir des objectifs annuels (exemples)")
    with st.form("targets_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            banana_target = st.number_input("Banane – CA théorique (FCFA/an)", value=float(t["banana_ca_target"]), step=100000.0)
            taro_target = st.number_input("Taro – CA théorique (FCFA/an)", value=float(t["taro_ca_target"]), step=100000.0)
        with c2:
            rabbits_target = st.number_input("Lapins – production (nb/cycle)", value=int(t["rabbits_target_per_cycle"]), step=10)
            hives_target = st.number_input("Ruches – nombre cible", value=int(t["hives_target"]), step=1)
        with c3:
            vivoplants_target = st.number_input("Vivoplants – volume (nb/cycle)", value=int(t["vivoplants_target_per_cycle"]), step=50)
            loss_tol = st.number_input("Pertes tolérées (%)", value=float(t["loss_tolerance_pct"]), step=1.0)

        saved = st.form_submit_button("💾 Enregistrer les objectifs")
        if saved:
            exec_sql(
                """
                UPDATE targets
                SET banana_ca_target=?, taro_ca_target=?, rabbits_target_per_cycle=?, hives_target=?, vivoplants_target_per_cycle=?, loss_tolerance_pct=?, updated_at=?
                WHERE id=1
                """,
                (float(banana_target), float(taro_target), int(rabbits_target), int(hives_target), int(vivoplants_target), float(loss_tol), now_iso()),
            )
            st.success("Objectifs mis à jour ✅")

    st.divider()
    st.subheader("📌 Progression (MVP)")

    # Rabbits: sum births/deaths in period
    rabbit_stats = read_df(
        "SELECT COALESCE(SUM(births),0) as births, COALESCE(SUM(deaths),0) as deaths FROM rabbit_events WHERE event_at >= ?",
        (start_dt.isoformat(),),
    ).iloc[0]
    honey_stats = read_df(
        "SELECT COALESCE(SUM(honey_harvest_kg),0) as honey_kg FROM hive_inspections WHERE inspect_at >= ?",
        (start_dt.isoformat(),),
    ).iloc[0]
    vp_stats = read_df(
        "SELECT COALESCE(SUM(produced_qty),0) as prod, COALESCE(SUM(losses_qty),0) as loss FROM vivoplants_events WHERE event_at >= ?",
        (start_dt.isoformat(),),
    ).iloc[0]

    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card("Naissances (période)", int(rabbit_stats["births"]))
        st.caption(f"Décès: {int(rabbit_stats['deaths'])}")
    with c2:
        metric_card("Miel récolté (kg)", float(honey_stats["honey_kg"]))
        st.caption("Somme des inspections")
    with c3:
        metric_card("Vivoplants produits", int(vp_stats["prod"]))
        st.caption(f"Pertes: {int(vp_stats['loss'])}")

    st.divider()
    st.subheader("🧠 Recommandations (pilotage)")
    recos = compute_recommendations(start_dt)
    for r in recos:
        st.markdown(f"- {r}")


def page_export(start_dt: datetime) -> None:
    st.header("⬇️ Export des données (CSV)")
    st.info("Les exports seront disponibles dès la saisie des données terrain.")

    tables = [
        ("Capteurs (7-en-1)", "sensor_readings", "reading_at"),
        ("Blocs agricoles", "agri_blocks", "created_at"),
        ("Observations terrain (agri)", "agri_observations", "obs_at"),
        ("Ruches", "hives", "created_at"),
        ("Inspections ruches", "hive_inspections", "inspect_at"),
        ("Cycles lapins", "rabbit_cycles", "created_at"),
        ("Événements lapins", "rabbit_events", "event_at"),
        ("Lots vivoplants", "vivoplants_lots", "created_at"),
        ("Événements vivoplants", "vivoplants_events", "event_at"),
        ("Objectifs (targets)", "targets", "updated_at"),
    ]

    tab_objs = st.tabs([t[0] for t in tables])

    for tab, (label, table, dtcol) in zip(tab_objs, tables):
        with tab:
            try:
                if table == "targets":
                    df = read_df("SELECT * FROM targets", ())
                else:
                    df = read_df(f"SELECT * FROM {table} WHERE {dtcol} >= ? ORDER BY {dtcol} DESC", (start_dt.isoformat(),))
            except Exception as e:
                st.error(f"Erreur export table {table}: {e}")
                continue

            if df.empty:
                df_empty_info("Aucune donnée sur la période.")
                continue

            st.dataframe(df, use_container_width=True, hide_index=True)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                f"📥 Télécharger {label} (CSV)",
                data=csv,
                file_name=f"cafy_{table}.csv",
                mime="text/csv",
            )


# -----------------------------
# Main
# -----------------------------
def main() -> None:
    st.set_page_config(page_title="CAFY Monitoring", layout="wide")

    # Dark-friendly tweaks
    st.markdown(
        """
        <style>
        .stApp { background: #0b0f14; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    init_db()
    brand_header()

    page, days = sidebar_nav()
    start_dt = datetime.now().replace(microsecond=0) - timedelta(days=int(days))

    if page == "Tableau de bord (Récap & Recos)":
        page_dashboard(start_dt)
    elif page == "Agriculture (Blocs & Capteurs)":
        page_agriculture_blocks_and_sensors(start_dt)
    elif page == "Observations terrain (Agriculture)":
        page_observations_agri(start_dt)
    elif page == "Apiculture (Ruches)":
        page_apiculture(start_dt)
    elif page == "Cuniculuture (Lapins)":
        page_cuniculture(start_dt)
    elif page == "Vivoplants":
        page_vivoplants(start_dt)
    elif page == "Objectifs & KPI":
        page_objectifs_kpi(start_dt)
    elif page == "Export (CSV)":
        page_export(start_dt)
    else:
        st.error("Page inconnue.")


if __name__ == "__main__":
    main()
