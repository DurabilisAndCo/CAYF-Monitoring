# app.py
# CAFY - Data Monitoring (Pro, single-file)
# Streamlit app: Agriculture (Banane/Taro/PIF) + Capteurs 7-en-1 + Apiculture + Cuniculture + Vivoplants
# + Objectifs & KPI + Recommandations (règles) + Export CSV

import os
import sqlite3
from datetime import datetime, timedelta, date
from typing import Dict, Any, Optional, List, Tuple

import pandas as pd
import numpy as np
import streamlit as st

# -----------------------------
# CONFIG UI
# -----------------------------
st.set_page_config(
    page_title="CAFY - Data Monitoring",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# BRANDING / TEXTS
# -----------------------------
BRAND_TITLE = "CAFY – Data Monitoring Data · développé par DURABILIS & CO"
BRAND_SUBTITLE_1 = "CENTRE AGROÉCOLOGIQUE INNOVANT DE N'ZAMALIGUÉ"
BRAND_SUBTITLE_2 = "porté par la Coopérative Agricole Young Foundation"
BRAND_LOCATION = "Localisation : N'zamaligué, Komo-Mondah, Gabon"

ASSETS_DIR = "assets"
LOGO_CAYF = os.path.join(ASSETS_DIR, "cayf.jpg")       # <- vérifie le nom exact
LOGO_DURABILIS = os.path.join(ASSETS_DIR, "durabilis.png")  # <- vérifie le nom exact

APP_VERSION = "V4 (Single-file Pro)"

DB_PATH = "cafymonitoring.db"

# -----------------------------
# THRESHOLDS / RULES (simple & safe)
# Ajuste selon tes pratiques terrain
# -----------------------------
RULES = {
    "soil_moisture_low": 25,     # %
    "soil_moisture_high": 80,    # %
    "soil_temp_low": 18,         # °C
    "soil_temp_high": 32,        # °C
    "ph_low": 5.5,
    "ph_high": 7.5,
    "ec_low": 200,               # µS/cm (fertilité faible)
    "light_low": 2000,           # lux (très indicatif)
    "air_humidity_low": 40,      # %
    "air_humidity_high": 85,     # %
    "inspection_max_days": 14,   # apiculture: inspection au moins toutes les 2 semaines
    "rabbit_mortality_alert": 0.05,  # 5%
    "vivoplant_success_low": 0.80,   # 80%
}

# -----------------------------
# DB UTILITIES
# -----------------------------
def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    conn = get_conn()
    cur = conn.cursor()

    # Agriculture blocks (parcelles / blocs)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS agri_blocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        crop_type TEXT NOT NULL,            -- banane / taro / pif
        variety TEXT,
        area_ha REAL,
        location TEXT,
        planting_date TEXT,                 -- ISO date
        notes TEXT,
        created_at TEXT NOT NULL
    );
    """)

    # Sensor readings (7-en-1)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sensor_readings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        block_id INTEGER NOT NULL,
        reading_time TEXT NOT NULL,         -- ISO datetime
        soil_moisture REAL,                 -- %
        soil_temp REAL,                     -- °C
        soil_ph REAL,                       -- pH
        soil_ec REAL,                       -- µS/cm
        light_lux REAL,                     -- lux
        air_temp REAL,                      -- °C
        air_humidity REAL,                  -- %
        battery_level REAL,                 -- % (optionnel)
        sensor_id TEXT,                     -- (optionnel)
        created_at TEXT NOT NULL,
        FOREIGN KEY(block_id) REFERENCES agri_blocks(id) ON DELETE CASCADE
    );
    """)

    # Field observations (qualitatives + quanti)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS field_observations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        block_id INTEGER NOT NULL,
        obs_date TEXT NOT NULL,             -- ISO date
        phenology_stage TEXT,               -- ex: végétatif / floraison / fructification
        height_cm REAL,
        leaf_color TEXT,                    -- vert / jaune / etc
        pest_pressure TEXT,                 -- faible / moyen / fort
        disease_symptoms TEXT,
        weed_pressure TEXT,
        irrigation_done INTEGER,            -- 0/1
        fertilization_done INTEGER,         -- 0/1
        notes TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(block_id) REFERENCES agri_blocks(id) ON DELETE CASCADE
    );
    """)

    # Apiculture
    cur.execute("""
    CREATE TABLE IF NOT EXISTS hives (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        location TEXT,
        install_date TEXT,                  -- ISO date
        queen_status TEXT,                  -- ok / unknown / issue
        notes TEXT,
        created_at TEXT NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS hive_inspections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hive_id INTEGER NOT NULL,
        inspection_date TEXT NOT NULL,      -- ISO date
        brood_present INTEGER,              -- 0/1
        honey_present INTEGER,              -- 0/1
        pests TEXT,                         -- varroa, etc
        aggressiveness TEXT,                -- low/med/high
        feeding_done INTEGER,               -- 0/1
        actions TEXT,
        notes TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(hive_id) REFERENCES hives(id) ON DELETE CASCADE
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS honey_harvests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hive_id INTEGER NOT NULL,
        harvest_date TEXT NOT NULL,         -- ISO date
        honey_kg REAL,
        notes TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(hive_id) REFERENCES hives(id) ON DELETE CASCADE
    );
    """)

    # Cuniculture (lapins)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS rabbit_batches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,                 -- ex: Cycle Jan 2026
        start_date TEXT,
        females_count INTEGER,
        males_count INTEGER,
        notes TEXT,
        created_at TEXT NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS rabbit_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_id INTEGER NOT NULL,
        event_date TEXT NOT NULL,           -- ISO date
        event_type TEXT NOT NULL,           -- birth/death/weighing/treatment/sale
        count INTEGER,                      -- nb (naissances, décès, ventes)
        avg_weight_kg REAL,                 -- pesée (optionnel)
        notes TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(batch_id) REFERENCES rabbit_batches(id) ON DELETE CASCADE
    );
    """)

    # Vivoplants
    cur.execute("""
    CREATE TABLE IF NOT EXISTS vivoplant_lots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        species TEXT,
        start_date TEXT,
        target_qty INTEGER,
        notes TEXT,
        created_at TEXT NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS vivoplant_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lot_id INTEGER NOT NULL,
        event_date TEXT NOT NULL,
        produced_qty INTEGER,
        losses_qty INTEGER,
        success_rate REAL,                  -- optionnel (0-1)
        notes TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(lot_id) REFERENCES vivoplant_lots(id) ON DELETE CASCADE
    );
    """)

    # Targets / KPIs (one row)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS targets (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        banane_ca_fcfa REAL,
        taro_ca_fcfa REAL,
        lapins_production_cycle INTEGER,
        ruche_count INTEGER,
        vivoplants_volume_cycle INTEGER,
        pertes_tolerees_pct REAL,
        updated_at TEXT NOT NULL
    );
    """)

    cur.execute("INSERT OR IGNORE INTO targets (id, updated_at) VALUES (1, ?);", (now_iso(),))

    conn.commit()
    conn.close()


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def today_iso() -> str:
    return date.today().isoformat()


def qdf(df: pd.DataFrame) -> pd.DataFrame:
    """Quick clean display."""
    return df.copy()


def read_df(query: str, params: Tuple = ()) -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def exec_sql(query: str, params: Tuple = ()) -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    conn.close()


def exec_sql_return_id(query: str, params: Tuple = ()) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    rid = cur.lastrowid
    conn.close()
    return rid


# -----------------------------
# UI HELPERS
# -----------------------------
def safe_image(path: str, width: Optional[int] = None, use_container_width: bool = False):
    try:
        if os.path.exists(path):
            st.image(path, width=width, use_container_width=use_container_width)
        else:
            st.caption(f"⚠️ Logo manquant: {path}")
    except Exception as e:
        st.caption(f"⚠️ Impossible d'afficher l'image ({path}). {e}")


def brand_header():
    # Header layout: logo left + center banner text + logo right
    col1, col2, col3 = st.columns([1.2, 5.6, 1.2], vertical_alignment="center")
    with col1:
        safe_image(LOGO_CAYF, use_container_width=True)
    with col2:
        st.markdown(
            f"""
            <div style="
                padding:16px 18px;
                border-radius:14px;
                background: linear-gradient(90deg, rgba(45,51,129,0.85), rgba(44,110,161,0.85), rgba(68,160,201,0.85));
                color:white;
                ">
                <div style="font-size:18px; font-weight:700; margin-bottom:6px;">{BRAND_TITLE}</div>
                <div style="font-size:14px; font-weight:600; opacity:0.95;">{BRAND_SUBTITLE_1}</div>
                <div style="font-size:13px; opacity:0.95;">{BRAND_SUBTITLE_2}</div>
                <div style="font-size:13px; opacity:0.95; margin-top:8px;">{BRAND_LOCATION}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        safe_image(LOGO_DURABILIS, use_container_width=True)

    st.caption(f"🌿 CAFY Monitoring · Développé par DURABILIS & CO · Version {APP_VERSION}")


def sidebar_nav() -> Dict[str, Any]:
    st.sidebar.title("🧭 Navigation")
    page = st.sidebar.radio(
        "Choisir une page",
        [
            "📊 Tableau de bord (Récap & Recos)",
            "🌿 Agriculture (Blocs & Capteurs)",
            "📝 Observations terrain (Agriculture)",
            "🐝 Apiculture (Ruches)",
            "🐇 Cuniculture (Lapins)",
            "🌱 Vivoplants",
            "🎯 Objectifs & KPI",
            "⬇️ Export (CSV)",
        ],
        index=0,
    )

    st.sidebar.divider()
    st.sidebar.subheader("Filtres")
    days = st.sidebar.slider("Période d'analyse (jours)", min_value=7, max_value=365, value=180, step=1)
    start_dt = datetime.now() - timedelta(days=days)
    return {"page": page, "days": days, "start_dt": start_dt}


def to_dt(s: str) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


def to_date(s: str) -> Optional[date]:
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except Exception:
        return None


def metric_card(label: str, value: Any, help_text: Optional[str] = None):
    st.metric(label, value, help=help_text)


def df_empty_info(msg: str):
    st.info(msg)


# -----------------------------
# DASHBOARD LOGIC
# -----------------------------
def get_latest_sensor_per_block(start_dt: datetime) -> pd.DataFrame:
    # Get last reading per block (not perfect SQL but safe & simple)
    df = read_df(
        """
        SELECT sr.*, ab.name AS block_name, ab.crop_type
        FROM sensor_readings sr
        JOIN agri_blocks ab ON ab.id = sr.block_id
        WHERE sr.reading_time >= ?
        """,
        (start_dt.isoformat(),),
    )
    if df.empty:
        return df
    df["reading_time"] = pd.to_datetime(df["reading_time"], errors="coerce")
    df = df.sort_values("reading_time").groupby("block_id").tail(1)
    return df


def compute_recommendations(start_dt: datetime) -> List[str]:
    recos = []

    # --- Agriculture / sensors
    latest = get_latest_sensor_per_block(start_dt)
    if not latest.empty:
        for _, r in latest.iterrows():
            bn = r.get("block_name", "Bloc")
            sm = r.get("soil_moisture")
            stp = r.get("soil_temp")
            ph = r.get("soil_ph")
            ec = r.get("soil_ec")
            lux = r.get("light_lux")
            aht = r.get("air_humidity")
            atp = r.get("air_temp")

            if pd.notna(sm) and sm < RULES["soil_moisture_low"]:
                recos.append(f"💧 {bn} : humidité du sol basse ({sm:.0f}%). Programmer un arrosage et vérifier le paillage.")
            if pd.notna(sm) and sm > RULES["soil_moisture_high"]:
                recos.append(f"⚠️ {bn} : humidité du sol très élevée ({sm:.0f}%). Risque d’asphyxie racinaire → réduire l’arrosage / drainage.")

            if pd.notna(stp) and stp < RULES["soil_temp_low"]:
                recos.append(f"🌡️ {bn} : température du sol basse ({stp:.1f}°C). Surveiller la croissance, limiter stress hydrique.")
            if pd.notna(stp) and stp > RULES["soil_temp_high"]:
                recos.append(f"🔥 {bn} : température du sol élevée ({stp:.1f}°C). Renforcer ombrage / paillage / irrigation raisonnée.")

            if pd.notna(ph) and (ph < RULES["ph_low"] or ph > RULES["ph_high"]):
                recos.append(f"🧪 {bn} : pH hors plage ({ph:.1f}). Prévoir correction (amendement) après validation agronomique.")

            if pd.notna(ec) and ec < RULES["ec_low"]:
                recos.append(f"🧬 {bn} : fertilité/EC faible ({ec:.0f} µS/cm). Planifier une fertilisation organique/compost + analyse sol si possible.")

            if pd.notna(lux) and lux < RULES["light_low"]:
                recos.append(f"☀️ {bn} : faible luminosité ({lux:.0f} lux). Vérifier ombrage excessif (arbres, filets, etc.).")

            if pd.notna(aht) and aht < RULES["air_humidity_low"]:
                recos.append(f"💨 {bn} : humidité de l’air basse ({aht:.0f}%). Risque de stress → irrigation tôt le matin, paillage, brumisation si pertinent.")
            if pd.notna(aht) and aht > RULES["air_humidity_high"]:
                recos.append(f"🦠 {bn} : humidité de l’air élevée ({aht:.0f}%). Surveiller maladies cryptogamiques, aérer, éviter arrosage sur feuillage.")

            # Small generic note
            if pd.notna(atp):
                recos.append(f"📌 {bn} : dernière mesure air {atp:.1f}°C / RH {aht if pd.notna(aht) else '—'}% (vérifier cohérence capteur).")

    # --- Apiculture: last inspection per hive
    hives = read_df("SELECT * FROM hives", ())
    if not hives.empty:
        insp = read_df("SELECT * FROM hive_inspections", ())
        if insp.empty:
            recos.append("🐝 Apiculture : aucune inspection enregistrée. Faire une inspection initiale (présence couvain, réserves, parasites).")
        else:
            insp["inspection_date"] = pd.to_datetime(insp["inspection_date"], errors="coerce")
            last_insp = insp.sort_values("inspection_date").groupby("hive_id").tail(1)
            for _, r in last_insp.iterrows():
                hid = r["hive_id"]
                hive_name = hives.loc[hives["id"] == hid, "name"].values
                hive_name = hive_name[0] if len(hive_name) else "Ruche"
                d = r["inspection_date"]
                if pd.notna(d):
                    days_since = (datetime.now() - d.to_pydatetime()).days
                    if days_since > RULES["inspection_max_days"]:
                        recos.append(f"🐝 {hive_name} : dernière inspection il y a {days_since} jours. Planifier une inspection (objectif ≤ {RULES['inspection_max_days']} jours).")

    # --- Lapins: mortality alert
    batches = read_df("SELECT * FROM rabbit_batches", ())
    events = read_df("SELECT * FROM rabbit_events", ())
    if not batches.empty and not events.empty:
        ev = events.copy()
        ev["event_date"] = pd.to_datetime(ev["event_date"], errors="coerce")
        ev = ev[ev["event_date"] >= pd.Timestamp(start_dt)]
        for _, b in batches.iterrows():
            bid = b["id"]
            bname = b["name"]
            b_ev = ev[ev["batch_id"] == bid]
            births = b_ev.loc[b_ev["event_type"] == "birth", "count"].sum()
            deaths = b_ev.loc[b_ev["event_type"] == "death", "count"].sum()
            if births and births > 0:
                mort = deaths / births
                if mort >= RULES["rabbit_mortality_alert"]:
                    recos.append(f"🐇 {bname} : mortalité élevée ({mort:.1%}). Vérifier hygiène, alimentation, traitements et causes (diarrhées, chaleur, etc.).")

    # --- Vivoplants: success rate
    lots = read_df("SELECT * FROM vivoplant_lots", ())
    v_ev = read_df("SELECT * FROM vivoplant_events", ())
    if not lots.empty and not v_ev.empty:
        v_ev["event_date"] = pd.to_datetime(v_ev["event_date"], errors="coerce")
        v_ev = v_ev[v_ev["event_date"] >= pd.Timestamp(start_dt)]
        for _, lot in lots.iterrows():
            lid = lot["id"]
            lname = lot["name"]
            d = v_ev[v_ev["lot_id"] == lid]
            if not d.empty:
                prod = d["produced_qty"].fillna(0).sum()
                loss = d["losses_qty"].fillna(0).sum()
                total = prod + loss
                if total > 0:
                    success = prod / total
                    if success < RULES["vivoplant_success_low"]:
                        recos.append(f"🌱 {lname} : taux de reprise faible ({success:.0%}). Revoir substrat, ombrage, arrosage, protocole de repiquage.")

    # de-duplicate & keep readable
    recos = list(dict.fromkeys([r for r in recos if r and isinstance(r, str)]))
    return recos


# -----------------------------
# PAGES
# -----------------------------
def page_dashboard(start_dt: datetime):
    st.header("📊 Tableau de bord – Vue d’ensemble")

    # Summary cards
    colA, colB, colC, colD = st.columns(4)

    agri_blocks = read_df("SELECT * FROM agri_blocks", ())
    hives = read_df("SELECT * FROM hives", ())
    batches = read_df("SELECT * FROM rabbit_batches", ())
    lots = read_df("SELECT * FROM vivoplant_lots", ())

    with colA:
        metric_card("🌿 Blocs agricoles", int(len(agri_blocks)), "Banane / Taro / PIF")
    with colB:
        metric_card("🐝 Ruches", int(len(hives)), "Suivi inspections & production")
    with colC:
        metric_card("🐇 Cuniculture", int(len(batches)), "Suivi cheptel & cycles")
    with colD:
        metric_card("🌱 Vivoplants", int(len(lots)), "Lots / taux de reprise")

    st.divider()

    st.subheader("🧠 Recommandations automatisées (règles)")
    recos = compute_recommendations(start_dt)
    if not recos:
        st.info("Commence par créer tes blocs/ruches/lots et saisir quelques mesures/observations pour générer des recommandations.")
    else:
        for r in recos[:30]:
            st.write("• " + r)
        if len(recos) > 30:
            st.caption(f"+ {len(recos)-30} recommandations supplémentaires (ajuste les seuils si nécessaire).")

    st.divider()
    st.subheader("📈 Tendances capteurs (sur la période sélectionnée)")

    df = read_df(
        """
        SELECT sr.reading_time, sr.soil_moisture, sr.soil_temp, sr.soil_ph, sr.soil_ec,
               sr.light_lux, sr.air_temp, sr.air_humidity,
               ab.name AS block_name, ab.crop_type
        FROM sensor_readings sr
        JOIN agri_blocks ab ON ab.id = sr.block_id
        WHERE sr.reading_time >= ?
        ORDER BY sr.reading_time ASC
        """,
        (start_dt.isoformat(),),
    )

    if df.empty:
        df_empty_info("Aucune donnée capteur. Va dans « Agriculture (Blocs & Capteurs) » pour ajouter une mesure.")
        return

    df["reading_time"] = pd.to_datetime(df["reading_time"], errors="coerce")
    df = df.dropna(subset=["reading_time"])

    # Simple charts without extra libs: line charts
    tabs = st.tabs(["Humidité sol", "Température sol", "pH", "EC (fertilité)", "Lumière", "Air (T° / RH)"])
    with tabs[0]:
        st.line_chart(df, x="reading_time", y="soil_moisture", color="block_name")
    with tabs[1]:
        st.line_chart(df, x="reading_time", y="soil_temp", color="block_name")
    with tabs[2]:
        st.line_chart(df, x="reading_time", y="soil_ph", color="block_name")
    with tabs[3]:
        st.line_chart(df, x="reading_time", y="soil_ec", color="block_name")
    with tabs[4]:
        st.line_chart(df, x="reading_time", y="light_lux", color="block_name")
    with tabs[5]:
        st.line_chart(df, x="reading_time", y="air_temp", color="block_name")
        st.line_chart(df, x="reading_time", y="air_humidity", color="block_name")


def page_agriculture_blocks_and_sensors(start_dt: datetime):
    st.header("🌿 Agriculture – Blocs & Capteurs (7-en-1)")

    # ---- Create block
    st.subheader("1) Créer un bloc agricole (banane / taro / PIF)")
    with st.form("create_block", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            name = st.text_input("Nom du bloc", placeholder="Bloc A")
        with c2:
            crop_type = st.selectbox("Culture", ["banane", "taro", "pif"], index=0)
        with c3:
            variety = st.text_input("Variété", placeholder="Big Ebanga / locale…")
        with c4:
            area_ha = st.number_input("Superficie (ha)", min_value=0.0, value=1.0, step=0.1)

        c5, c6 = st.columns(2)
        with c5:
            location = st.text_input("Localisation interne", placeholder="Zone humide / parcelle nord…")
        with c6:
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

    # ---- List blocks
    blocks = read_df("SELECT * FROM agri_blocks ORDER BY id DESC", ())
    st.subheader("2) Liste des blocs")
    if blocks.empty:
        df_empty_info("Aucun bloc créé pour le moment.")
        return

    st.dataframe(blocks, use_container_width=True, hide_index=True)

    st.divider()

    # ---- Add sensor reading
    st.subheader("3) Ajouter une mesure capteur (7-en-1)")
    block_map = {f"[{r['id']}] {r['name']} ({r['crop_type']})": int(r["id"]) for _, r in blocks.iterrows()}
    chosen_label = st.selectbox("Choisir un bloc", list(block_map.keys()))
    chosen_block_id = block_map[chosen_label]

    with st.form("add_sensor", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            reading_date = st.date_input("Date", value=date.today(), key="sr_date")
        with c2:
            reading_time = st.time_input("Heure", value=datetime.now().time().replace(second=0, microsecond=0), key="sr_time")
        with c3:
            sensor_id = st.text_input("ID capteur (optionnel)", placeholder="sensor-01")
        with c4:
            battery_level = st.number_input("Batterie % (optionnel)", min_value=0.0, max_value=100.0, value=0.0, step=1.0)

        st.markdown("**Paramètres 7-en-1**")
        a, b, c, d = st.columns(4)
        with a:
            soil_moisture = st.number_input("Humidité sol (%)", min_value=0.0, max_value=100.0, value=0.0, step=1.0)
            soil_temp = st.number_input("Température sol (°C)", min_value=-5.0, max_value=60.0, value=0.0, step=0.5)
        with b:
            soil_ph = st.number_input("pH sol", min_value=0.0, max_value=14.0, value=0.0, step=0.1)
            soil_ec = st.number_input("EC / Fertilité (µS/cm)", min_value=0.0, max_value=50000.0, value=0.0, step=10.0)
        with c:
            light_lux = st.number_input("Lumière (lux)", min_value=0.0, max_value=200000.0, value=0.0, step=50.0)
            air_temp = st.number_input("Température air (°C)", min_value=-5.0, max_value=60.0, value=0.0, step=0.5)
        with d:
            air_humidity = st.number_input("Humidité air (%)", min_value=0.0, max_value=100.0, value=0.0, step=1.0)

        notes = st.text_area("Notes (optionnel)", placeholder="Ex: après pluie, à l’ombre, etc.")
        ok = st.form_submit_button("✅ Enregistrer la mesure")

    if ok:
        dt = datetime.combine(reading_date, reading_time).replace(microsecond=0)
        exec_sql(
            """
            INSERT INTO sensor_readings
            (block_id, reading_time, soil_moisture, soil_temp, soil_ph, soil_ec, light_lux, air_temp, air_humidity, battery_level, sensor_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                chosen_block_id,
                dt.isoformat(),
                float(soil_moisture) if soil_moisture else None,
                float(soil_temp) if soil_temp else None,
                float(soil_ph) if soil_ph else None,
                float(soil_ec) if soil_ec else None,
                float(light_lux) if light_lux else None,
                float(air_temp) if air_temp else None,
                float(air_humidity) if air_humidity else None,
                float(battery_level) if battery_level else None,
                sensor_id.strip() if sensor_id else None,
                now_iso(),
            ),
        )
        st.success("Mesure capteur enregistrée ✅")

    st.divider()

    st.subheader("4) Dernières mesures (période filtrée)")
    df = read_df(
        """
        SELECT sr.reading_time, ab.name AS block_name, ab.crop_type,
               sr.soil_moisture, sr.soil_temp, sr.soil_ph, sr.soil_ec, sr.light_lux, sr.air_temp, sr.air_humidity,
               sr.battery_level, sr.sensor_id
        FROM sensor_readings sr
        JOIN agri_blocks ab ON ab.id = sr.block_id
        WHERE sr.reading_time >= ?
        ORDER BY sr.reading_time DESC
        LIMIT 250
        """,
        (start_dt.isoformat(),),
    )
    if df.empty:
        df_empty_info("Aucune mesure sur la période sélectionnée.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)


def page_observations_agri(start_dt: datetime):
    st.header("📝 Observations terrain (Agriculture)")

    blocks = read_df("SELECT * FROM agri_blocks ORDER BY id DESC", ())
    if blocks.empty:
        df_empty_info("Crée d'abord un bloc agricole dans « Agriculture (Blocs & Capteurs) ».")
        return

    block_map = {f"[{r['id']}] {r['name']} ({r['crop_type']})": int(r["id"]) for _, r in blocks.iterrows()}
    chosen_label = st.selectbox("Choisir un bloc", list(block_map.keys()))
    block_id = block_map[chosen_label]

    st.subheader("1) Ajouter une observation")
    with st.form("add_obs", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            obs_date = st.date_input("Date d’observation", value=date.today())
        with c2:
            phenology = st.selectbox("Stade", ["", "végétatif", "floraison", "fructification", "récolte"], index=0)
        with c3:
            height_cm = st.number_input("Hauteur moyenne (cm)", min_value=0.0, max_value=1000.0, value=0.0, step=1.0)
        with c4:
            leaf_color = st.selectbox("Couleur feuilles", ["", "vert", "vert pâle", "jaune", "brun", "taches"], index=0)

        c5, c6, c7 = st.columns(3)
        with c5:
            pest_pressure = st.selectbox("Pression ravageurs", ["", "faible", "moyen", "fort"], index=0)
        with c6:
            disease = st.text_input("Symptômes maladies (optionnel)", placeholder="taches, moisissures…")
        with c7:
            weed_pressure = st.selectbox("Adventices", ["", "faible", "moyen", "fort"], index=0)

        c8, c9 = st.columns(2)
        with c8:
            irrigation_done = st.checkbox("Arrosage effectué")
        with c9:
            fertilization_done = st.checkbox("Fertilisation effectuée")

        notes = st.text_area("Notes", placeholder="Actions, anomalies, photos (référence), etc.")
        ok = st.form_submit_button("✅ Enregistrer")

    if ok:
        exec_sql(
            """
            INSERT INTO field_observations
            (block_id, obs_date, phenology_stage, height_cm, leaf_color, pest_pressure, disease_symptoms, weed_pressure,
             irrigation_done, fertilization_done, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                block_id,
                obs_date.isoformat(),
                phenology if phenology else None,
                float(height_cm) if height_cm else None,
                leaf_color if leaf_color else None,
                pest_pressure if pest_pressure else None,
                disease.strip() if disease else None,
                weed_pressure if weed_pressure else None,
                1 if irrigation_done else 0,
                1 if fertilization_done else 0,
                notes.strip() if notes else None,
                now_iso(),
            ),
        )
        st.success("Observation enregistrée ✅")

    st.divider()
    st.subheader("2) Historique observations (période filtrée)")
    df = read_df(
        """
        SELECT fo.obs_date, ab.name AS block_name, ab.crop_type,
               fo.phenology_stage, fo.height_cm, fo.leaf_color,
               fo.pest_pressure, fo.disease_symptoms, fo.weed_pressure,
               fo.irrigation_done, fo.fertilization_done, fo.notes
        FROM field_observations fo
        JOIN agri_blocks ab ON ab.id = fo.block_id
        WHERE fo.obs_date >= ?
        ORDER BY fo.obs_date DESC
        LIMIT 250
        """,
        ((start_dt.date().isoformat()),),
    )
    if df.empty:
        df_empty_info("Aucune observation sur la période sélectionnée.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)


def page_apiculture(start_dt: datetime):
    st.header("🐝 Apiculture – Ruches, inspections & récoltes")

    st.subheader("1) Créer une ruche")
    with st.form("create_hive", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            name = st.text_input("Nom ruche", placeholder="Ruche 1")
        with c2:
            location = st.text_input("Localisation", placeholder="Zone A / ombrage…")
        with c3:
            install_date = st.date_input("Date installation", value=date.today())
        queen_status = st.selectbox("Statut reine", ["unknown", "ok", "issue"], index=0)
        notes = st.text_area("Notes")
        ok = st.form_submit_button("✅ Créer ruche")

    if ok:
        if not name.strip():
            st.error("Nom ruche obligatoire.")
        else:
            exec_sql(
                """
                INSERT INTO hives (name, location, install_date, queen_status, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (name.strip(), location.strip() if location else None, install_date.isoformat(), queen_status, notes.strip() if notes else None, now_iso()),
            )
            st.success("Ruche créée ✅")

    st.divider()
    hives = read_df("SELECT * FROM hives ORDER BY id DESC", ())
    if hives.empty:
        df_empty_info("Aucune ruche. Crée une ruche pour saisir des inspections.")
        return

    st.subheader("2) Ajouter une inspection")
    hive_map = {f"[{r['id']}] {r['name']}": int(r["id"]) for _, r in hives.iterrows()}
    chosen = st.selectbox("Choisir ruche", list(hive_map.keys()))
    hive_id = hive_map[chosen]

    with st.form("add_inspection", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            insp_date = st.date_input("Date inspection", value=date.today())
        with c2:
            brood = st.checkbox("Couvain présent")
        with c3:
            honey = st.checkbox("Miel présent")
        with c4:
            feeding = st.checkbox("Nourrissement effectué")

        c5, c6 = st.columns(2)
        with c5:
            pests = st.text_input("Parasites / nuisibles", placeholder="Varroa, fourmis…")
        with c6:
            aggress = st.selectbox("Agressivité", ["low", "med", "high"], index=0)

        actions = st.text_area("Actions", placeholder="Nettoyage, changement cadre, traitement…")
        notes = st.text_area("Notes", placeholder="Observations complémentaires")
        ok2 = st.form_submit_button("✅ Enregistrer inspection")

    if ok2:
        exec_sql(
            """
            INSERT INTO hive_inspections
            (hive_id, inspection_date, brood_present, honey_present, pests, aggressiveness, feeding_done, actions, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                hive_id,
                insp_date.isoformat(),
                1 if brood else 0,
                1 if honey else 0,
                pests.strip() if pests else None,
                aggress,
                1 if feeding else 0,
                actions.strip() if actions else None,
                notes.strip() if notes else None,
                now_iso(),
            ),
        )
        st.success("Inspection enregistrée ✅")

    st.divider()
    st.subheader("3) Ajouter une récolte de miel")
    with st.form("add_harvest", clear_on_submit=True):
        h_date = st.date_input("Date récolte", value=date.today(), key="harvest_date")
        honey_kg = st.number_input("Miel récolté (kg)", min_value=0.0, value=0.0, step=0.1)
        notes = st.text_area("Notes récolte")
        ok3 = st.form_submit_button("✅ Enregistrer récolte")
    if ok3:
        exec_sql(
            """
            INSERT INTO honey_harvests (hive_id, harvest_date, honey_kg, notes, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (hive_id, h_date.isoformat(), float(honey_kg), notes.strip() if notes else None, now_iso()),
        )
        st.success("Récolte enregistrée ✅")

    st.divider()
    st.subheader("4) Historique (période filtrée)")
    insp = read_df(
        """
        SELECT hi.inspection_date, h.name AS hive_name, hi.brood_present, hi.honey_present, hi.pests, hi.aggressiveness, hi.feeding_done, hi.actions, hi.notes
        FROM hive_inspections hi
        JOIN hives h ON h.id = hi.hive_id
        WHERE hi.inspection_date >= ?
        ORDER BY hi.inspection_date DESC
        LIMIT 250
        """,
        ((start_dt.date().isoformat()),),
    )
    harv = read_df(
        """
        SELECT hh.harvest_date, h.name AS hive_name, hh.honey_kg, hh.notes
        FROM honey_harvests hh
        JOIN hives h ON h.id = hh.hive_id
        WHERE hh.harvest_date >= ?
        ORDER BY hh.harvest_date DESC
        LIMIT 250
        """,
        ((start_dt.date().isoformat()),),
    )

    t1, t2 = st.tabs(["Inspections", "Récoltes"])
    with t1:
        if insp.empty:
            df_empty_info("Aucune inspection sur la période.")
        else:
            st.dataframe(insp, use_container_width=True, hide_index=True)
    with t2:
        if harv.empty:
            df_empty_info("Aucune récolte sur la période.")
        else:
            st.dataframe(harv, use_container_width=True, hide_index=True)


def page_cuniculture(start_dt: datetime):
    st.header("🐇 Cuniculture – Cycles, naissances, décès, ventes, pesées")

    st.subheader("1) Créer un cycle / lot lapins")
    with st.form("create_batch", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            name = st.text_input("Nom cycle", placeholder="Cycle 2026-01")
        with c2:
            start_date = st.date_input("Date début", value=date.today())
        with c3:
            females = st.number_input("Femelles", min_value=0, value=90, step=1)
        with c4:
            males = st.number_input("Mâles", min_value=0, value=15, step=1)
        notes = st.text_area("Notes")
        ok = st.form_submit_button("✅ Créer cycle")

    if ok:
        if not name.strip():
            st.error("Nom du cycle obligatoire.")
        else:
            exec_sql(
                """
                INSERT INTO rabbit_batches (name, start_date, females_count, males_count, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (name.strip(), start_date.isoformat(), int(females), int(males), notes.strip() if notes else None, now_iso()),
            )
            st.success("Cycle créé ✅")

    st.divider()
    batches = read_df("SELECT * FROM rabbit_batches ORDER BY id DESC", ())
    if batches.empty:
        df_empty_info("Crée un cycle pour enregistrer des événements.")
        return

    batch_map = {f"[{r['id']}] {r['name']}": int(r["id"]) for _, r in batches.iterrows()}
    chosen = st.selectbox("Choisir un cycle", list(batch_map.keys()))
    batch_id = batch_map[chosen]

    st.subheader("2) Ajouter un événement")
    with st.form("add_rabbit_event", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            ev_date = st.date_input("Date", value=date.today(), key="rb_date")
        with c2:
            ev_type = st.selectbox("Type", ["birth", "death", "sale", "weighing", "treatment"], index=0)
        with c3:
            count = st.number_input("Quantité (nb)", min_value=0, value=0, step=1)
        with c4:
            avg_w = st.number_input("Poids moyen (kg) (optionnel)", min_value=0.0, value=0.0, step=0.1)
        notes = st.text_area("Notes", placeholder="Cause décès, traitement, acheteur, etc.")
        ok2 = st.form_submit_button("✅ Enregistrer")

    if ok2:
        exec_sql(
            """
            INSERT INTO rabbit_events (batch_id, event_date, event_type, count, avg_weight_kg, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                batch_id,
                ev_date.isoformat(),
                ev_type,
                int(count) if count else 0,
                float(avg_w) if avg_w else None,
                notes.strip() if notes else None,
                now_iso(),
            ),
        )
        st.success("Événement enregistré ✅")

    st.divider()
    st.subheader("3) Historique (période filtrée)")
    df = read_df(
        """
        SELECT re.event_date, rb.name AS cycle, re.event_type, re.count, re.avg_weight_kg, re.notes
        FROM rabbit_events re
        JOIN rabbit_batches rb ON rb.id = re.batch_id
        WHERE re.event_date >= ?
        ORDER BY re.event_date DESC
        LIMIT 250
        """,
        ((start_dt.date().isoformat()),),
    )
    if df.empty:
        df_empty_info("Aucun événement lapins sur la période.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)


def page_vivoplants(start_dt: datetime):
    st.header("🌱 Vivoplants – Lots, production, pertes, taux de reprise")

    st.subheader("1) Créer un lot")
    with st.form("create_lot", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            name = st.text_input("Nom lot", placeholder="Lot PIF-01")
        with c2:
            species = st.text_input("Espèce", placeholder="Banane / autre…")
        with c3:
            start_date = st.date_input("Date début", value=date.today())
        with c4:
            target = st.number_input("Objectif quantité", min_value=0, value=1000, step=10)
        notes = st.text_area("Notes")
        ok = st.form_submit_button("✅ Créer lot")

    if ok:
        if not name.strip():
            st.error("Nom lot obligatoire.")
        else:
            exec_sql(
                """
                INSERT INTO vivoplant_lots (name, species, start_date, target_qty, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (name.strip(), species.strip() if species else None, start_date.isoformat(), int(target), notes.strip() if notes else None, now_iso()),
            )
            st.success("Lot créé ✅")

    st.divider()
    lots = read_df("SELECT * FROM vivoplant_lots ORDER BY id DESC", ())
    if lots.empty:
        df_empty_info("Crée un lot pour ajouter des événements.")
        return

    lot_map = {f"[{r['id']}] {r['name']}": int(r["id"]) for _, r in lots.iterrows()}
    chosen = st.selectbox("Choisir un lot", list(lot_map.keys()))
    lot_id = lot_map[chosen]

    st.subheader("2) Ajouter un événement (production / pertes)")
    with st.form("add_vivo_event", clear_on_submit=True):
        ev_date = st.date_input("Date", value=date.today(), key="vivo_date")
        c1, c2, c3 = st.columns(3)
        with c1:
            produced = st.number_input("Produits (nb)", min_value=0, value=0, step=1)
        with c2:
            losses = st.number_input("Pertes (nb)", min_value=0, value=0, step=1)
        with c3:
            success_rate = st.number_input("Taux de reprise (0-1) optionnel", min_value=0.0, max_value=1.0, value=0.0, step=0.01)
        notes = st.text_area("Notes", placeholder="Substrat, arrosage, protocole…")
        ok2 = st.form_submit_button("✅ Enregistrer")

    if ok2:
        exec_sql(
            """
            INSERT INTO vivoplant_events (lot_id, event_date, produced_qty, losses_qty, success_rate, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                lot_id,
                ev_date.isoformat(),
                int(produced) if produced else 0,
                int(losses) if losses else 0,
                float(success_rate) if success_rate else None,
                notes.strip() if notes else None,
                now_iso(),
            ),
        )
        st.success("Événement vivoplants enregistré ✅")

    st.divider()
    st.subheader("3) Historique (période filtrée)")
    df = read_df(
        """
        SELECT ve.event_date, vl.name AS lot, vl.species, ve.produced_qty, ve.losses_qty, ve.success_rate, ve.notes
        FROM vivoplant_events ve
        JOIN vivoplant_lots vl ON vl.id = ve.lot_id
        WHERE ve.event_date >= ?
        ORDER BY ve.event_date DESC
        LIMIT 250
        """,
        ((start_dt.date().isoformat()),),
    )
    if df.empty:
        df_empty_info("Aucun événement vivoplants sur la période.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)


def page_targets_kpi(start_dt: datetime):
    st.header("🎯 Objectifs chiffrés & suivi (bailleurs / pilotage)")

    targets = read_df("SELECT * FROM targets WHERE id = 1", ())
    row = targets.iloc[0].to_dict() if not targets.empty else {}

    st.subheader("1) Définir des objectifs annuels (exemples)")
    with st.form("save_targets"):
        c1, c2, c3 = st.columns(3)
        with c1:
            banane_ca = st.number_input("Banane – CA théorique (FCFA/an)", min_value=0.0, value=float(row.get("banane_ca_fcfa") or 33320000), step=10000.0)
            taro_ca = st.number_input("Taro – CA théorique (FCFA/an)", min_value=0.0, value=float(row.get("taro_ca_fcfa") or 5000000), step=10000.0)
        with c2:
            lapins_prod = st.number_input("Lapins – production (nb/cycle)", min_value=0, value=int(row.get("lapins_production_cycle") or 540), step=10)
            ruche_count = st.number_input("Ruches – nombre cible", min_value=0, value=int(row.get("ruche_count") or 2), step=1)
        with c3:
            vivo_vol = st.number_input("Vivoplants – volume (nb/cycle)", min_value=0, value=int(row.get("vivoplants_volume_cycle") or 1000), step=10)
            pertes_pct = st.number_input("Pertes tolérées (%)", min_value=0.0, max_value=100.0, value=float(row.get("pertes_tolerees_pct") or 10.0), step=0.5)

        ok = st.form_submit_button("✅ Enregistrer les objectifs")

    if ok:
        exec_sql(
            """
            UPDATE targets
            SET banane_ca_fcfa=?, taro_ca_fcfa=?, lapins_production_cycle=?, ruche_count=?, vivoplants_volume_cycle=?, pertes_tolerees_pct=?, updated_at=?
            WHERE id=1
            """,
            (float(banane_ca), float(taro_ca), int(lapins_prod), int(ruche_count), int(vivo_vol), float(pertes_pct), now_iso()),
        )
        st.success("Objectifs enregistrés ✅")

    st.divider()
    st.subheader("2) Progression (MVP)")

    # Simple KPIs from DB
    # Honey total
    honey = read_df(
        "SELECT SUM(honey_kg) AS honey_kg FROM honey_harvests WHERE harvest_date >= ?",
        ((start_dt.date().isoformat()),),
    )
    honey_kg = float(honey.iloc[0]["honey_kg"]) if not honey.empty and honey.iloc[0]["honey_kg"] is not None else 0.0

    # Rabbits births/deaths
    rabbits = read_df(
        """
        SELECT
            SUM(CASE WHEN event_type='birth' THEN count ELSE 0 END) AS births,
            SUM(CASE WHEN event_type='death' THEN count ELSE 0 END) AS deaths
        FROM rabbit_events
        WHERE event_date >= ?
        """,
        ((start_dt.date().isoformat()),),
    )
    births = int(rabbits.iloc[0]["births"]) if not rabbits.empty and rabbits.iloc[0]["births"] is not None else 0
    deaths = int(rabbits.iloc[0]["deaths"]) if not rabbits.empty and rabbits.iloc[0]["deaths"] is not None else 0

    # Vivoplants produced/losses
    vivo = read_df(
        """
        SELECT
            SUM(produced_qty) AS produced,
            SUM(losses_qty) AS losses
        FROM vivoplant_events
        WHERE event_date >= ?
        """,
        ((start_dt.date().isoformat()),),
    )
    produced = int(vivo.iloc[0]["produced"]) if not vivo.empty and vivo.iloc[0]["produced"] is not None else 0
    losses = int(vivo.iloc[0]["losses"]) if not vivo.empty and vivo.iloc[0]["losses"] is not None else 0

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("🐇 Naissances (période)", births)
        st.caption(f"Décès: {deaths}")
    with c2:
        st.metric("🍯 Miel récolté (kg)", round(honey_kg, 1))
        st.caption("Somme des récoltes sur la période")
    with c3:
        st.metric("🌱 Vivoplants produits", produced)
        st.caption(f"Pertes: {losses}")

    st.divider()
    st.subheader("3) Recommandations (pilotage)")
    recos = compute_recommendations(start_dt)
    if not recos:
        st.info("Les recommandations apparaîtront quand tu auras des données (capteurs / inspections / événements).")
    else:
        for r in recos[:40]:
            st.write("• " + r)


def page_export(start_dt: datetime):
    st.header("⬇️ Export des données (CSV)")
    st.info("Les exports seront disponibles dès la saisie des données terrain.")

    tabs = st.tabs(["Capteurs (7-en-1)", "Observations Agriculture", "Apiculture", "Lapins", "Vivoplants"])

    with tabs[0]:
        df = read_df(
            """
            SELECT sr.*, ab.name AS block_name, ab.crop_type, ab.variety, ab.location
            FROM sensor_readings sr
            JOIN agri_blocks ab ON ab.id = sr.block_id
            WHERE sr.reading_time >= ?
            ORDER BY sr.reading_time DESC
            """,
            (start_dt.isoformat(),),
        )
        if df.empty:
            df_empty_info("Aucune donnée capteur.")
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Télécharger capteurs.csv", data=csv, file_name="capteurs.csv", mime="text/csv")

    with tabs[1]:
        df = read_df(
            """
            SELECT fo.*, ab.name AS block_name, ab.crop_type, ab.variety, ab.location
            FROM field_observations fo
            JOIN agri_blocks ab ON ab.id = fo.block_id
            WHERE fo.obs_date >= ?
            ORDER BY fo.obs_date DESC
            """,
            ((start_dt.date().isoformat()),),
        )
        if df.empty:
            df_empty_info("Aucune observation.")
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.download_button("Télécharger observations_agri.csv", df.to_csv(index=False).encode("utf-8"), "observations_agri.csv", "text/csv")

    with tabs[2]:
        insp = read_df(
            """
            SELECT hi.*, h.name AS hive_name, h.location
            FROM hive_inspections hi
            JOIN hives h ON h.id = hi.hive_id
            WHERE hi.inspection_date >= ?
            ORDER BY hi.inspection_date DESC
            """,
            ((start_dt.date().isoformat()),),
        )
        harv = read_df(
            """
            SELECT hh.*, h.name AS hive_name, h.location
            FROM honey_harvests hh
            JOIN hives h ON h.id = hh.hive_id
            WHERE hh.harvest_date >= ?
            ORDER BY hh.harvest_date DESC
            """,
            ((start_dt.date().isoformat()),),
        )
        st.write("**Inspections**")
        if insp.empty:
            df_empty_info("Aucune inspection.")
        else:
            st.dataframe(insp, use_container_width=True, hide_index=True)
            st.download_button("Télécharger apiculture_inspections.csv", insp.to_csv(index=False).encode("utf-8"), "apiculture_inspections.csv", "text/csv")

        st.write("**Récoltes**")
        if harv.empty:
            df_empty_info("Aucune récolte.")
        else:
            st.dataframe(harv, use_container_width=True, hide_index=True)
            st.download_button("Télécharger apiculture_recoltes.csv", harv.to_csv(index=False).encode("utf-8"), "apiculture_recoltes.csv", "text/csv")

    with tabs[3]:
        df = read_df(
            """
            SELECT re.*, rb.name AS cycle
            FROM rabbit_events re
            JOIN rabbit_batches rb ON rb.id = re.batch_id
            WHERE re.event_date >= ?
            ORDER BY re.event_date DESC
            """,
            ((start_dt.date().isoformat()),),
        )
        if df.empty:
            df_empty_info("Aucun événement lapins.")
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.download_button("Télécharger lapins.csv", df.to_csv(index=False).encode("utf-8"), "lapins.csv", "text/csv")

    with tabs[4]:
        df = read_df(
            """
            SELECT ve.*, vl.name AS lot, vl.species
            FROM vivoplant_events ve
            JOIN vivoplant_lots vl ON vl.id = ve.lot_id
            WHERE ve.event_date >= ?
            ORDER BY ve.event_date DESC
            """,
            ((start_dt.date().isoformat()),),
        )
        if df.empty:
            df_empty_info("Aucun événement vivoplants.")
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.download_button("Télécharger vivoplants.csv", df.to_csv(index=False).encode("utf-8"), "vivoplants.csv", "text/csv")

    st.divider()
    st.subheader("📄 Télécharger un exemple CSV (template)")
    example = pd.DataFrame(
        {
            "block_name": ["Bloc A"],
            "reading_time": [datetime.now().replace(microsecond=0).isoformat()],
            "soil_moisture": [45],
            "soil_temp": [26.2],
            "soil_ph": [6.3],
            "soil_ec": [365],
            "light_lux": [8000],
            "air_temp": [28.1],
            "air_humidity": [70],
        }
    )
    st.download_button("Télécharger un exemple CSV", example.to_csv(index=False).encode("utf-8"), "template_capteurs.csv", "text/csv")


# -----------------------------
# MAIN
# -----------------------------
def main():
    init_db()
    brand_header()
    nav = sidebar_nav()
    page = nav["page"]
    start_dt = nav["start_dt"]

    if page.startswith("📊"):
        page_dashboard(start_dt)
    elif page.startswith("🌿 Agriculture"):
        page_agriculture_blocks_and_sensors(start_dt)
    elif page.startswith("📝"):
        page_observations_agri(start_dt)
    elif page.startswith("🐝"):
        page_apiculture(start_dt)
    elif page.startswith("🐇"):
        page_cuniculture(start_dt)
    elif page.startswith("🌱"):
        page_vivoplants(start_dt)
    elif page.startswith("🎯"):
        page_targets_kpi(start_dt)
    elif page.startswith("⬇️"):
        page_export(start_dt)
    else:
        st.error("Page inconnue.")


if __name__ == "__main__":
    main()
