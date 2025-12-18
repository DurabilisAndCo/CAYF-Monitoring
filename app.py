# app.py — CAFY Monitoring (Single-file Pro)
# Streamlit app: Agriculture (Banane/Taro) + Vivoplants + Apiculture + Cuniculture
# + Dashboard + Objectifs & KPI + Export CSV + Admin reset (safe by crop)

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, date, timedelta
from typing import Optional, Tuple, List

import pandas as pd
import streamlit as st


# =========================
# Config
# =========================
APP_VERSION = "V5 (Single-file Pro)"
ASSETS_DIR = "assets"
LOGO_CAYF = os.path.join(ASSETS_DIR, "cayf.jpg")
LOGO_DURABILIS = os.path.join(ASSETS_DIR, "durabilis.png")

DB_PATH = "monitoring_agri.db"  # SQLite local file in repo root


# =========================
# Helpers: DB
# =========================
def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def exec_sql(query: str, params: Tuple = ()) -> None:
    conn = get_conn()
    try:
        conn.execute(query, params)
        conn.commit()
    finally:
        conn.close()


def exec_sql_many(query: str, params_list: List[Tuple]) -> None:
    conn = get_conn()
    try:
        conn.executemany(query, params_list)
        conn.commit()
    finally:
        conn.close()


def read_df(query: str, params: Tuple = ()) -> pd.DataFrame:
    conn = get_conn()
    try:
        return pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()


def init_db() -> None:
    # Tables Agriculture
    exec_sql(
        """
        CREATE TABLE IF NOT EXISTS agri_blocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            crop_type TEXT NOT NULL,          -- 'banane' | 'taro'
            variety TEXT,
            area_ha REAL,
            location TEXT,
            planting_date TEXT,              -- ISO date
            notes TEXT,
            created_at TEXT NOT NULL
        )
        """
    )

    exec_sql(
        """
        CREATE TABLE IF NOT EXISTS sensor_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            block_id INTEGER NOT NULL,
            crop_type TEXT NOT NULL,          -- redundancy for faster filters
            reading_dt TEXT NOT NULL,         -- ISO datetime
            sensor_id TEXT,

            battery_pct REAL,                 -- optionnel
            soil_moisture_pct REAL,           -- 1
            soil_temp_c REAL,                 -- 2
            air_temp_c REAL,                  -- 3
            air_humidity_pct REAL,            -- 4
            light_lux REAL,                   -- 5
            rainfall_mm REAL,                 -- 6
            ph REAL,                          -- 7 (optionnel mais dans le 7-en-1, utile)

            created_at TEXT NOT NULL,
            FOREIGN KEY (block_id) REFERENCES agri_blocks(id) ON DELETE CASCADE
        )
        """
    )

    exec_sql(
        """
        CREATE TABLE IF NOT EXISTS agri_observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            block_id INTEGER NOT NULL,
            crop_type TEXT NOT NULL,
            obs_dt TEXT NOT NULL,            -- ISO datetime
            stage TEXT,
            pests TEXT,
            irrigation TEXT,
            note TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (block_id) REFERENCES agri_blocks(id) ON DELETE CASCADE
        )
        """
    )

    # Vivoplants
    exec_sql(
        """
        CREATE TABLE IF NOT EXISTS vivoplants_lots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lot_name TEXT NOT NULL,
            species TEXT,
            qty_planted INTEGER,
            start_date TEXT,
            expected_qty INTEGER,
            notes TEXT,
            created_at TEXT NOT NULL
        )
        """
    )

    exec_sql(
        """
        CREATE TABLE IF NOT EXISTS vivoplants_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lot_id INTEGER NOT NULL,
            event_dt TEXT NOT NULL,
            event_type TEXT NOT NULL,     -- 'entree'|'sortie'|'perte'|'inspection'
            qty INTEGER,
            note TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (lot_id) REFERENCES vivoplants_lots(id) ON DELETE CASCADE
        )
        """
    )

    # Apiculture
    exec_sql(
        """
        CREATE TABLE IF NOT EXISTS hives (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hive_code TEXT NOT NULL,
            status TEXT,
            install_date TEXT,
            location TEXT,
            notes TEXT,
            created_at TEXT NOT NULL
        )
        """
    )

    exec_sql(
        """
        CREATE TABLE IF NOT EXISTS hive_inspections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hive_id INTEGER NOT NULL,
            insp_dt TEXT NOT NULL,
            honey_kg REAL,
            queen_seen INTEGER,           -- 0/1
            disease_signs TEXT,
            actions TEXT,
            note TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (hive_id) REFERENCES hives(id) ON DELETE CASCADE
        )
        """
    )

    # Cuniculture
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
        )
        """
    )

    exec_sql(
        """
        CREATE TABLE IF NOT EXISTS rabbit_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cycle_id INTEGER NOT NULL,
            event_dt TEXT NOT NULL,
            event_type TEXT NOT NULL,      -- 'naissance'|'deces'|'vente'|'soin'|'autre'
            qty INTEGER,
            note TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (cycle_id) REFERENCES rabbit_cycles(id) ON DELETE CASCADE
        )
        """
    )

    # Objectifs / KPI
    exec_sql(
        """
        CREATE TABLE IF NOT EXISTS targets (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            banana_ca_target REAL,
            taro_ca_target REAL,
            vivoplants_volume_target INTEGER,
            hives_target INTEGER,
            rabbits_per_cycle_target INTEGER,
            loss_tolerance_pct REAL,
            updated_at TEXT
        )
        """
    )

    # Ensure one row exists
    df = read_df("SELECT id FROM targets WHERE id = 1")
    if df.empty:
        exec_sql(
            """
            INSERT INTO targets (id, banana_ca_target, taro_ca_target, vivoplants_volume_target,
                                 hives_target, rabbits_per_cycle_target, loss_tolerance_pct, updated_at)
            VALUES (1, 33320000, 5000000, 1000, 2, 540, 10.0, ?)
            """,
            (now_iso(),),
        )


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def to_dt(d: date, t) -> datetime:
    return datetime(d.year, d.month, d.day, t.hour, t.minute, t.second)


def safe_image(path: str):
    if os.path.exists(path):
        st.image(path, use_container_width=True)
        return True
    return False


# =========================
# Admin reset (SAFE)
# =========================
def delete_agri_by_crop(crop: str) -> None:
    # Delete only rows linked to blocks of a crop_type
    df_ids = read_df("SELECT id FROM agri_blocks WHERE crop_type = ?", (crop,))
    if df_ids.empty:
        st.info(f"Aucun bloc '{crop}' à supprimer.")
        return

    ids = df_ids["id"].tolist()
    placeholders = ",".join(["?"] * len(ids))

    exec_sql(
        f"DELETE FROM sensor_readings WHERE block_id IN ({placeholders})",
        tuple(ids),
    )
    exec_sql(
        f"DELETE FROM agri_observations WHERE block_id IN ({placeholders})",
        tuple(ids),
    )
    exec_sql(
        f"DELETE FROM agri_blocks WHERE id IN ({placeholders})",
        tuple(ids),
    )


# =========================
# UI: Branding
# =========================
BRAND_TITLE = "CAFY – Data Monitoring Data • développé par DURABILIS & CO"
BRAND_SUBTITLE_1 = "CENTRE AGROÉCOLOGIQUE INNOVANT DE N'ZAMALIGUÉ"
BRAND_SUBTITLE_2 = "porté par la Coopérative Agricole Young Foundation"
BRAND_LOCATION = "Localisation : N'zamaligué, Komo-Mondah, Gabon"


def brand_header():
    c1, c2, c3 = st.columns([1.2, 5.6, 1.2], vertical_alignment="center")
    with c1:
        if not safe_image(LOGO_CAYF):
            st.caption("Logo CAYF manquant (assets/cayf.jpg)")
    with c2:
        st.markdown(
            f"""
            <div style="padding:14px 18px; border-radius:14px; background: linear-gradient(90deg, #2d3381 0%, #2c6ea1 55%, #44a0c9 100%);">
              <div style="font-weight:700; font-size:16px; color:white;">{BRAND_TITLE}</div>
              <div style="margin-top:6px; color:white; opacity:0.95; font-weight:700;">{BRAND_SUBTITLE_1}</div>
              <div style="color:white; opacity:0.92;">{BRAND_SUBTITLE_2}</div>
              <div style="margin-top:8px; color:white; opacity:0.92;">{BRAND_LOCATION}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        if not safe_image(LOGO_DURABILIS):
            st.caption("Logo Durabilis manquant (assets/durabilis.png)")

    st.caption(f"🌿 CAFY Monitoring • Développé par DURABILIS & CO • Version {APP_VERSION}")
    st.divider()


def sidebar_nav() -> Tuple[str, int]:
    st.sidebar.title("🧭 Navigation")
    page = st.sidebar.radio(
        "Choisir une page",
        [
            "Tableau de bord (Récap & Recos)",
            "Agriculture – Banane (Blocs & Capteurs)",
            "Agriculture – Taro (Blocs & Capteurs)",
            "Observations terrain (Agriculture)",
            "Vivoplants",
            "Apiculture (Ruches)",
            "Cuniculture (Lapins)",
            "Objectifs & KPI",
            "Export (CSV)",
        ],
    )

    st.sidebar.divider()
    st.sidebar.subheader("Filtres")
    days = st.sidebar.slider("Période d'analyse (jours)", 7, 365, 180, step=1)
    return page, days


# =========================
# Recos (rules) by activity
# =========================
def compute_recommendations(start_dt: datetime) -> List[str]:
    recos: List[str] = []

    # Agriculture (Banane + Taro separately)
    for crop in ["banane", "taro"]:
        blocks = read_df("SELECT id FROM agri_blocks WHERE crop_type = ?", (crop,))
        if blocks.empty:
            recos.append(f"🌱 {crop.capitalize()} : crée au moins 1 bloc pour activer le suivi capteur + observations.")
        else:
            # any sensor readings last X days?
            df_read = read_df(
                """
                SELECT COUNT(*) AS n
                FROM sensor_readings
                WHERE crop_type = ? AND reading_dt >= ?
                """,
                (crop, start_dt.isoformat()),
            )
            n = int(df_read["n"].iloc[0]) if not df_read.empty else 0
            if n == 0:
                recos.append(f"📡 {crop.capitalize()} : aucune mesure capteur sur la période. Ajoute au moins 1 relevé 7-en-1.")
            else:
                # simple agronomic signals (example)
                df_last = read_df(
                    """
                    SELECT soil_moisture_pct, soil_temp_c, ph, air_temp_c, rainfall_mm
                    FROM sensor_readings
                    WHERE crop_type = ?
                    ORDER BY reading_dt DESC
                    LIMIT 1
                    """,
                    (crop,),
                )
                if not df_last.empty:
                    sm = df_last["soil_moisture_pct"].iloc[0]
                    stc = df_last["soil_temp_c"].iloc[0]
                    ph = df_last["ph"].iloc[0]
                    if pd.notna(sm) and sm < 25:
                        recos.append(f"💧 {crop.capitalize()} : humidité sol faible (<25%). Vérifie irrigation / paillage.")
                    if pd.notna(stc) and stc > 32:
                        recos.append(f"🌡️ {crop.capitalize()} : température sol élevée (>32°C). Ajouter ombrage/paillage si possible.")
                    if pd.notna(ph) and (ph < 5.5 or ph > 7.5):
                        recos.append(f"🧪 {crop.capitalize()} : pH hors zone (5.5–7.5). Prévoir correction/diagnostic sol.")

    # Vivoplants
    lots = read_df("SELECT id FROM vivoplants_lots")
    if lots.empty:
        recos.append("🌿 Vivoplants : crée un lot (variété + quantités) pour démarrer le suivi.")
    else:
        ev = read_df(
            "SELECT COUNT(*) AS n FROM vivoplants_events WHERE event_dt >= ?",
            (start_dt.isoformat(),),
        )
        n = int(ev["n"].iloc[0]) if not ev.empty else 0
        if n == 0:
            recos.append("🧾 Vivoplants : aucune opération sur la période. Ajoute entrées/sorties/pertes pour piloter la reprise.")

    # Apiculture
    hives = read_df("SELECT id FROM hives")
    if hives.empty:
        recos.append("🍯 Apiculture : enregistre tes ruches (codes) pour activer inspections & production.")
    else:
        insp = read_df(
            "SELECT COUNT(*) AS n FROM hive_inspections WHERE insp_dt >= ?",
            (start_dt.isoformat(),),
        )
        n = int(insp["n"].iloc[0]) if not insp.empty else 0
        if n == 0:
            recos.append("🔎 Apiculture : aucune inspection sur la période. Planifie au moins 1 inspection par ruche.")

    # Cuniculture
    cycles = read_df("SELECT id FROM rabbit_cycles")
    if cycles.empty:
        recos.append("🐇 Cuniculture : crée un cycle (date + effectifs) pour suivre naissances/décès/ventes.")
    else:
        ev = read_df(
            "SELECT COUNT(*) AS n FROM rabbit_events WHERE event_dt >= ?",
            (start_dt.isoformat(),),
        )
        n = int(ev["n"].iloc[0]) if not ev.empty else 0
        if n == 0:
            recos.append("📋 Cuniculture : aucun événement sur la période. Ajoute naissances/décès/ventes/soins.")

    return recos


# =========================
# Pages
# =========================
def page_dashboard(start_dt: datetime):
    st.header("📊 Tableau de bord – Vue d’ensemble")

    col1, col2, col3, col4 = st.columns(4)

    agri_blocks = read_df("SELECT COUNT(*) AS n FROM agri_blocks")
    nb_blocks = int(agri_blocks["n"].iloc[0]) if not agri_blocks.empty else 0

    hives = read_df("SELECT COUNT(*) AS n FROM hives")
    nb_hives = int(hives["n"].iloc[0]) if not hives.empty else 0

    cycles = read_df("SELECT COUNT(*) AS n FROM rabbit_cycles")
    nb_cycles = int(cycles["n"].iloc[0]) if not cycles.empty else 0

    lots = read_df("SELECT COUNT(*) AS n FROM vivoplants_lots")
    nb_lots = int(lots["n"].iloc[0]) if not lots.empty else 0

    with col1:
        st.metric("Blocs agricoles", nb_blocks, help="Banane + Taro")
        st.caption("Banane / Taro")
    with col2:
        st.metric("Ruches", nb_hives)
        st.caption("Suivi inspections & production")
    with col3:
        st.metric("Cuniculture", nb_cycles)
        st.caption("Suivi cheptel & cycles")
    with col4:
        st.metric("Vivoplants", nb_lots)
        st.caption("Lots / taux de reprise")

    st.divider()
    st.subheader("🧠 Recommandations automatisées (par activité)")
    recos = compute_recommendations(start_dt)
    if not recos:
        st.success("Tout est à jour ✅")
    else:
        for r in recos:
            st.write("• " + r)

    st.divider()
    st.subheader("📈 Tendances capteurs – sur la période sélectionnée")
    df = read_df(
        """
        SELECT reading_dt, crop_type, soil_moisture_pct, soil_temp_c, air_temp_c, air_humidity_pct, light_lux, rainfall_mm, ph
        FROM sensor_readings
        WHERE reading_dt >= ?
        ORDER BY reading_dt ASC
        """,
        (start_dt.isoformat(),),
    )
    if df.empty:
        st.info("Aucune donnée capteur. Va dans « Agriculture – Banane/Taro » pour ajouter une mesure.")
        return

    df["reading_dt"] = pd.to_datetime(df["reading_dt"])
    st.dataframe(df, use_container_width=True, hide_index=True)


def page_agri_blocks_and_sensors(start_dt: datetime, crop: str):
    crop_label = "Banane" if crop == "banane" else "Taro"
    st.header(f"🌿 Agriculture – {crop_label} (Blocs & Capteurs 7-en-1)")

    # 1) Create block
    st.subheader("1) Créer un bloc agricole")
    with st.form(f"create_block_{crop}", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            name = st.text_input("Nom du bloc", value=f"Bloc {crop_label}")
        with c2:
            variety = st.text_input("Variété", placeholder="Ex: Big Ebanga / locale…")
        with c3:
            area_ha = st.number_input("Superficie (ha)", min_value=0.0, value=1.0, step=0.1)
        with c4:
            planting_date = st.date_input("Date de mise en place", value=date.today())

        location = st.text_input("Localisation interne", placeholder="Zone humide / parcelle nord…")
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
                        crop,
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

    # 2) List blocks
    st.subheader("2) Liste des blocs")
    blocks = read_df("SELECT * FROM agri_blocks WHERE crop_type = ? ORDER BY id DESC", (crop,))
    if blocks.empty:
        st.info("Aucun bloc créé pour le moment. Crée un bloc pour activer la saisie capteur.")
        return

    st.dataframe(blocks, use_container_width=True, hide_index=True)

    st.divider()

    # 3) Add sensor reading 7-en-1
    st.subheader("3) Ajouter une mesure capteur (7-en-1)")
    block_map = {f"#{r['id']} — {r['name']}": int(r["id"]) for _, r in blocks.iterrows()}
    chosen_label = st.selectbox("Choisir un bloc", list(block_map.keys()))
    chosen_block_id = block_map[chosen_label]

    with st.form(f"add_sensor_{crop}", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            reading_date = st.date_input("Date", value=date.today(), key=f"sr_date_{crop}")
        with c2:
            reading_time = st.time_input("Heure", value=datetime.now().time().replace(second=0, microsecond=0), key=f"sr_time_{crop}")
        with c3:
            sensor_id = st.text_input("ID capteur (optionnel)", placeholder="sensor-01", key=f"sr_id_{crop}")
        with c4:
            battery = st.number_input("Batterie % (optionnel)", min_value=0.0, max_value=100.0, value=0.0, step=1.0, key=f"sr_batt_{crop}")

        st.markdown("**📌 Les 7 valeurs (7-en-1)**")
        a, b, c, d = st.columns(4)
        with a:
            soil_moisture = st.number_input("1) Humidité sol (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.1, key=f"sr_sm_{crop}")
            soil_temp = st.number_input("2) Température sol (°C)", min_value=-10.0, max_value=80.0, value=0.0, step=0.1, key=f"sr_st_{crop}")
        with b:
            air_temp = st.number_input("3) Température air (°C)", min_value=-10.0, max_value=80.0, value=0.0, step=0.1, key=f"sr_at_{crop}")
            air_hum = st.number_input("4) Humidité air (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.1, key=f"sr_ah_{crop}")
        with c:
            light_lux = st.number_input("5) Luminosité (lux)", min_value=0.0, value=0.0, step=10.0, key=f"sr_lux_{crop}")
            rainfall = st.number_input("6) Pluie (mm)", min_value=0.0, value=0.0, step=0.1, key=f"sr_rain_{crop}")
        with d:
            ph = st.number_input("7) pH (sol/eau)", min_value=0.0, max_value=14.0, value=7.0, step=0.1, key=f"sr_ph_{crop}")

        submit_sr = st.form_submit_button("➕ Enregistrer la mesure")
        if submit_sr:
            dt_val = to_dt(reading_date, reading_time).replace(microsecond=0).isoformat()
            exec_sql(
                """
                INSERT INTO sensor_readings (
                    block_id, crop_type, reading_dt, sensor_id,
                    battery_pct, soil_moisture_pct, soil_temp_c, air_temp_c, air_humidity_pct, light_lux, rainfall_mm, ph,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chosen_block_id,
                    crop,
                    dt_val,
                    sensor_id.strip() if sensor_id else None,
                    float(battery) if battery else None,
                    float(soil_moisture),
                    float(soil_temp),
                    float(air_temp),
                    float(air_hum),
                    float(light_lux),
                    float(rainfall),
                    float(ph),
                    now_iso(),
                ),
            )
            st.success("Mesure enregistrée ✅")

    st.divider()
    st.subheader("4) Dernières mesures capteur (période)")
    df = read_df(
        """
        SELECT reading_dt, sensor_id, battery_pct,
               soil_moisture_pct, soil_temp_c, air_temp_c, air_humidity_pct, light_lux, rainfall_mm, ph
        FROM sensor_readings
        WHERE crop_type = ? AND reading_dt >= ?
        ORDER BY reading_dt DESC
        """,
        (crop, start_dt.isoformat()),
    )
    if df.empty:
        st.info("Aucune mesure sur la période sélectionnée.")
    else:
        df["reading_dt"] = pd.to_datetime(df["reading_dt"])
        st.dataframe(df, use_container_width=True, hide_index=True)


def page_observations_agri(start_dt: datetime):
    st.header("📝 Observations terrain (Agriculture)")

    blocks = read_df("SELECT id, name, crop_type FROM agri_blocks ORDER BY crop_type, id DESC")
    if blocks.empty:
        st.info("Crée d’abord au moins 1 bloc (banane ou taro).")
        return

    block_map = {f"{r['crop_type'].capitalize()} — #{r['id']} — {r['name']}": int(r["id"]) for _, r in blocks.iterrows()}
    chosen = st.selectbox("Choisir un bloc", list(block_map.keys()))
    block_id = block_map[chosen]

    # Fetch crop_type for this block
    row = read_df("SELECT crop_type FROM agri_blocks WHERE id = ?", (block_id,))
    crop_type = row["crop_type"].iloc[0] if not row.empty else "banane"

    with st.form("add_obs", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            obs_date = st.date_input("Date", value=date.today())
        with c2:
            obs_time = st.time_input("Heure", value=datetime.now().time().replace(second=0, microsecond=0))

        stage = st.text_input("Stade (optionnel)", placeholder="Croissance / floraison / récolte…")
        pests = st.text_input("Ravageurs / maladies (optionnel)", placeholder="Ex: charançon, nématodes…")
        irrigation = st.text_input("Irrigation (optionnel)", placeholder="Ex: goutte-à-goutte / arrosage manuel…")
        note = st.text_area("Note")

        submit = st.form_submit_button("➕ Enregistrer l’observation")
        if submit:
            dt_val = to_dt(obs_date, obs_time).replace(microsecond=0).isoformat()
            exec_sql(
                """
                INSERT INTO agri_observations (block_id, crop_type, obs_dt, stage, pests, irrigation, note, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    block_id,
                    crop_type,
                    dt_val,
                    stage.strip() if stage else None,
                    pests.strip() if pests else None,
                    irrigation.strip() if irrigation else None,
                    note.strip() if note else None,
                    now_iso(),
                ),
            )
            st.success("Observation enregistrée ✅")

    st.divider()
    st.subheader("Historique (période)")
    df = read_df(
        """
        SELECT obs_dt, crop_type, stage, pests, irrigation, note
        FROM agri_observations
        WHERE obs_dt >= ?
        ORDER BY obs_dt DESC
        """,
        (start_dt.isoformat(),),
    )
    if df.empty:
        st.info("Aucune observation sur la période.")
    else:
        df["obs_dt"] = pd.to_datetime(df["obs_dt"])
        st.dataframe(df, use_container_width=True, hide_index=True)


def page_vivoplants(start_dt: datetime):
    st.header("🌱 Vivoplants")

    st.subheader("1) Créer un lot")
    with st.form("create_vivo_lot", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            lot_name = st.text_input("Nom du lot", value="Lot A")
        with c2:
            species = st.text_input("Espèce/variété", placeholder="Ex: plantain / bananier…")
        with c3:
            qty_planted = st.number_input("Quantité plantée", min_value=0, value=0, step=10)
        with c4:
            start_date = st.date_input("Date de démarrage", value=date.today())

        expected_qty = st.number_input("Objectif (quantité attendue)", min_value=0, value=0, step=10)
        notes = st.text_area("Notes")
        submit = st.form_submit_button("✅ Créer le lot")
        if submit:
            if not lot_name.strip():
                st.error("Nom du lot requis.")
            else:
                exec_sql(
                    """
                    INSERT INTO vivoplants_lots (lot_name, species, qty_planted, start_date, expected_qty, notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        lot_name.strip(),
                        species.strip() if species else None,
                        int(qty_planted),
                        start_date.isoformat(),
                        int(expected_qty),
                        notes.strip() if notes else None,
                        now_iso(),
                    ),
                )
                st.success("Lot créé ✅")

    st.divider()

    lots = read_df("SELECT * FROM vivoplants_lots ORDER BY id DESC")
    st.subheader("2) Lots")
    if lots.empty:
        st.info("Aucun lot pour le moment.")
        return
    st.dataframe(lots, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("3) Ajouter un événement")
    lot_map = {f"#{r['id']} — {r['lot_name']}": int(r["id"]) for _, r in lots.iterrows()}
    lot_label = st.selectbox("Choisir un lot", list(lot_map.keys()))
    lot_id = lot_map[lot_label]

    with st.form("add_vivo_event", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            ev_date = st.date_input("Date", value=date.today(), key="vivo_date")
        with c2:
            ev_time = st.time_input("Heure", value=datetime.now().time().replace(second=0, microsecond=0), key="vivo_time")
        with c3:
            ev_type = st.selectbox("Type", ["entree", "sortie", "perte", "inspection"], index=3)

        qty = st.number_input("Quantité (si applicable)", min_value=0, value=0, step=10)
        note = st.text_area("Note")
        submit = st.form_submit_button("➕ Ajouter")
        if submit:
            dt_val = to_dt(ev_date, ev_time).replace(microsecond=0).isoformat()
            exec_sql(
                """
                INSERT INTO vivoplants_events (lot_id, event_dt, event_type, qty, note, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    lot_id,
                    dt_val,
                    ev_type,
                    int(qty) if qty else None,
                    note.strip() if note else None,
                    now_iso(),
                ),
            )
            st.success("Événement ajouté ✅")

    st.divider()
    st.subheader("Historique (période)")
    df = read_df(
        """
        SELECT event_dt, event_type, qty, note
        FROM vivoplants_events
        WHERE event_dt >= ?
        ORDER BY event_dt DESC
        """,
        (start_dt.isoformat(),),
    )
    if df.empty:
        st.info("Aucun événement sur la période.")
    else:
        df["event_dt"] = pd.to_datetime(df["event_dt"])
        st.dataframe(df, use_container_width=True, hide_index=True)


def page_apiculture(start_dt: datetime):
    st.header("🍯 Apiculture (Ruches)")

    st.subheader("1) Enregistrer une ruche")
    with st.form("create_hive", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            hive_code = st.text_input("Code ruche", value="RUCHE-01")
        with c2:
            status = st.selectbox("Statut", ["active", "faible", "à surveiller", "inactive"])
        with c3:
            install_date = st.date_input("Date d’installation", value=date.today())
        location = st.text_input("Localisation", placeholder="Zone / repère…")
        notes = st.text_area("Notes")
        submit = st.form_submit_button("✅ Ajouter la ruche")
        if submit:
            if not hive_code.strip():
                st.error("Code requis.")
            else:
                exec_sql(
                    """
                    INSERT INTO hives (hive_code, status, install_date, location, notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        hive_code.strip(),
                        status,
                        install_date.isoformat(),
                        location.strip() if location else None,
                        notes.strip() if notes else None,
                        now_iso(),
                    ),
                )
                st.success("Ruche ajoutée ✅")

    st.divider()
    hives = read_df("SELECT * FROM hives ORDER BY id DESC")
    st.subheader("2) Ruches")
    if hives.empty:
        st.info("Aucune ruche.")
        return
    st.dataframe(hives, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("3) Inspection")
    hive_map = {f"#{r['id']} — {r['hive_code']}": int(r["id"]) for _, r in hives.iterrows()}
    hive_label = st.selectbox("Choisir une ruche", list(hive_map.keys()))
    hive_id = hive_map[hive_label]

    with st.form("add_insp", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            insp_date = st.date_input("Date", value=date.today(), key="insp_date")
        with c2:
            insp_time = st.time_input("Heure", value=datetime.now().time().replace(second=0, microsecond=0), key="insp_time")
        with c3:
            honey_kg = st.number_input("Miel récolté (kg)", min_value=0.0, value=0.0, step=0.5)

        queen_seen = st.checkbox("Reine observée ?", value=False)
        disease_signs = st.text_input("Signes maladie (optionnel)")
        actions = st.text_input("Actions (optionnel)")
        note = st.text_area("Note")

        submit = st.form_submit_button("➕ Enregistrer")
        if submit:
            dt_val = to_dt(insp_date, insp_time).replace(microsecond=0).isoformat()
            exec_sql(
                """
                INSERT INTO hive_inspections (hive_id, insp_dt, honey_kg, queen_seen, disease_signs, actions, note, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    hive_id,
                    dt_val,
                    float(honey_kg),
                    1 if queen_seen else 0,
                    disease_signs.strip() if disease_signs else None,
                    actions.strip() if actions else None,
                    note.strip() if note else None,
                    now_iso(),
                ),
            )
            st.success("Inspection enregistrée ✅")

    st.divider()
    st.subheader("Historique (période)")
    df = read_df(
        """
        SELECT insp_dt, honey_kg, queen_seen, disease_signs, actions, note
        FROM hive_inspections
        WHERE insp_dt >= ?
        ORDER BY insp_dt DESC
        """,
        (start_dt.isoformat(),),
    )
    if df.empty:
        st.info("Aucune inspection sur la période.")
    else:
        df["insp_dt"] = pd.to_datetime(df["insp_dt"])
        st.dataframe(df, use_container_width=True, hide_index=True)


def page_cuniculture(start_dt: datetime):
    st.header("🐇 Cuniculture (Lapins)")

    st.subheader("1) Créer un cycle")
    with st.form("create_cycle", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            cycle_name = st.text_input("Nom du cycle", value="Cycle 1")
        with c2:
            start_date = st.date_input("Date de démarrage", value=date.today())
        with c3:
            females = st.number_input("Femelles", min_value=0, value=0, step=1)
        with c4:
            males = st.number_input("Mâles", min_value=0, value=0, step=1)

        notes = st.text_area("Notes")
        submit = st.form_submit_button("✅ Créer")
        if submit:
            if not cycle_name.strip():
                st.error("Nom requis.")
            else:
                exec_sql(
                    """
                    INSERT INTO rabbit_cycles (cycle_name, start_date, females, males, notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        cycle_name.strip(),
                        start_date.isoformat(),
                        int(females),
                        int(males),
                        notes.strip() if notes else None,
                        now_iso(),
                    ),
                )
                st.success("Cycle créé ✅")

    st.divider()
    cycles = read_df("SELECT * FROM rabbit_cycles ORDER BY id DESC")
    st.subheader("2) Cycles")
    if cycles.empty:
        st.info("Aucun cycle.")
        return
    st.dataframe(cycles, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("3) Événement")
    cyc_map = {f"#{r['id']} — {r['cycle_name']}": int(r["id"]) for _, r in cycles.iterrows()}
    cyc_label = st.selectbox("Choisir un cycle", list(cyc_map.keys()))
    cycle_id = cyc_map[cyc_label]

    with st.form("add_rabbit_event", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            ev_date = st.date_input("Date", value=date.today(), key="rb_date")
        with c2:
            ev_time = st.time_input("Heure", value=datetime.now().time().replace(second=0, microsecond=0), key="rb_time")
        with c3:
            ev_type = st.selectbox("Type", ["naissance", "deces", "vente", "soin", "autre"])

        qty = st.number_input("Quantité", min_value=0, value=0, step=1)
        note = st.text_area("Note")
        submit = st.form_submit_button("➕ Enregistrer")
        if submit:
            dt_val = to_dt(ev_date, ev_time).replace(microsecond=0).isoformat()
            exec_sql(
                """
                INSERT INTO rabbit_events (cycle_id, event_dt, event_type, qty, note, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    cycle_id,
                    dt_val,
                    ev_type,
                    int(qty) if qty else None,
                    note.strip() if note else None,
                    now_iso(),
                ),
            )
            st.success("Événement enregistré ✅")

    st.divider()
    st.subheader("Historique (période)")
    df = read_df(
        """
        SELECT event_dt, event_type, qty, note
        FROM rabbit_events
        WHERE event_dt >= ?
        ORDER BY event_dt DESC
        """,
        (start_dt.isoformat(),),
    )
    if df.empty:
        st.info("Aucun événement sur la période.")
    else:
        df["event_dt"] = pd.to_datetime(df["event_dt"])
        st.dataframe(df, use_container_width=True, hide_index=True)


def page_objectifs_kpi():
    st.header("🎯 Objectifs chiffrés & suivi")

    t = read_df("SELECT * FROM targets WHERE id = 1")
    row = t.iloc[0].to_dict() if not t.empty else {}

    st.subheader("Définir des objectifs annuels (exemples)")
    c1, c2, c3 = st.columns(3)
    with c1:
        banana = st.number_input("Banane – CA théorique (FCFA/an)", value=float(row.get("banana_ca_target", 33320000) or 0))
        taro = st.number_input("Taro – CA théorique (FCFA/an)", value=float(row.get("taro_ca_target", 5000000) or 0))
    with c2:
        rabbits = st.number_input("Lapins – production (nb/cycle)", value=int(row.get("rabbits_per_cycle_target", 540) or 0))
        hives = st.number_input("Ruches – nombre cible", value=int(row.get("hives_target", 2) or 0))
    with c3:
        vivo = st.number_input("Vivoplants – volume (nb/cycle)", value=int(row.get("vivoplants_volume_target", 1000) or 0))
        loss = st.number_input("Pertes tolérées (%)", value=float(row.get("loss_tolerance_pct", 10.0) or 0.0))

    if st.button("💾 Enregistrer les objectifs"):
        exec_sql(
            """
            UPDATE targets
            SET banana_ca_target = ?, taro_ca_target = ?, vivoplants_volume_target = ?,
                hives_target = ?, rabbits_per_cycle_target = ?, loss_tolerance_pct = ?, updated_at = ?
            WHERE id = 1
            """,
            (banana, taro, int(vivo), int(hives), int(rabbits), float(loss), now_iso()),
        )
        st.success("Objectifs enregistrés ✅")

    st.divider()
    st.subheader("📌 Progression (MVP)")

    # Simple rollups
    births = read_df("SELECT COALESCE(SUM(qty),0) AS n FROM rabbit_events WHERE event_type = 'naissance'")
    deaths = read_df("SELECT COALESCE(SUM(qty),0) AS n FROM rabbit_events WHERE event_type = 'deces'")
    honey = read_df("SELECT COALESCE(SUM(honey_kg),0) AS kg FROM hive_inspections")
    vivo_out = read_df("SELECT COALESCE(SUM(qty),0) AS n FROM vivoplants_events WHERE event_type = 'sortie'")
    vivo_loss = read_df("SELECT COALESCE(SUM(qty),0) AS n FROM vivoplants_events WHERE event_type = 'perte'")

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("🐇 Naissances (année)", int(births["n"].iloc[0]) if not births.empty else 0)
        st.caption(f"Décès : {int(deaths['n'].iloc[0]) if not deaths.empty else 0}")
    with m2:
        st.metric("🍯 Miel récolté (kg)", float(honey["kg"].iloc[0]) if not honey.empty else 0.0)
        st.caption("Somme des inspections")
    with m3:
        st.metric("🌱 Vivoplants sortis", int(vivo_out["n"].iloc[0]) if not vivo_out.empty else 0)
        st.caption(f"Pertes : {int(vivo_loss['n'].iloc[0]) if not vivo_loss.empty else 0}")

    st.divider()
    st.subheader("🧠 Recommandations (pilotage)")
    start_dt = datetime.now().replace(microsecond=0) - timedelta(days=180)
    for r in compute_recommendations(start_dt):
        st.write("• " + r)


def page_export():
    st.header("⬇️ Export des données (CSV)")
    st.info("Les exports seront disponibles dès la saisie des données terrain.")

    tables = {
        "Agriculture – Blocs": "agri_blocks",
        "Agriculture – Capteurs": "sensor_readings",
        "Agriculture – Observations": "agri_observations",
        "Vivoplants – Lots": "vivoplants_lots",
        "Vivoplants – Événements": "vivoplants_events",
        "Apiculture – Ruches": "hives",
        "Apiculture – Inspections": "hive_inspections",
        "Cuniculture – Cycles": "rabbit_cycles",
        "Cuniculture – Événements": "rabbit_events",
        "Objectifs – targets": "targets",
    }

    label = st.selectbox("Choisir une table", list(tables.keys()))
    tbl = tables[label]

    df = read_df(f"SELECT * FROM {tbl} ORDER BY 1 DESC")
    if df.empty:
        st.warning("Aucune donnée à exporter pour cette table.")
        return

    st.dataframe(df, use_container_width=True, hide_index=True)
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        f"⬇️ Télécharger {label} (CSV)",
        data=csv_bytes,
        file_name=f"cafy_{tbl}.csv",
        mime="text/csv",
    )


# =========================
# Admin block (sidebar)
# =========================
def admin_reset_block():
    with st.sidebar.expander("🛠️ Admin – Reset données (TEST)", expanded=False):
        st.warning("Action irréversible. À utiliser uniquement pour des données de test.")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Effacer Banane"):
                delete_agri_by_crop("banane")
                st.success("Banane supprimée ✅")
                st.rerun()

            if st.button("🗑️ Effacer Taro"):
                delete_agri_by_crop("taro")
                st.success("Taro supprimé ✅")
                st.rerun()

            if st.button("🗑️ Effacer Vivoplants"):
                for tbl in ["vivoplants_events", "vivoplants_lots"]:
                    exec_sql(f"DELETE FROM {tbl}")
                st.success("Vivoplants supprimés ✅")
                st.rerun()

        with col2:
            if st.button("🗑️ Effacer Apiculture"):
                for tbl in ["hive_inspections", "hives"]:
                    exec_sql(f"DELETE FROM {tbl}")
                st.success("Apiculture supprimée ✅")
                st.rerun()

            if st.button("🗑️ Effacer Cuniculture"):
                for tbl in ["rabbit_events", "rabbit_cycles"]:
                    exec_sql(f"DELETE FROM {tbl}")
                st.success("Cuniculture supprimée ✅")
                st.rerun()

        st.divider()
        if st.button("⚠️ Tout effacer (reset total)"):
            for tbl in [
                "sensor_readings", "agri_observations", "agri_blocks",
                "vivoplants_events", "vivoplants_lots",
                "hive_inspections", "hives",
                "rabbit_events", "rabbit_cycles",
            ]:
                exec_sql(f"DELETE FROM {tbl}")
            st.success("Reset total effectué ✅")
            st.rerun()


# =========================
# Main
# =========================
def main() -> None:
    st.set_page_config(page_title="CAFY Monitoring", layout="wide")

    # UI skin (dark + slight polish)
    st.markdown(
        """
        <style>
          .stApp { background: #0b0f14; }
          [data-testid="stSidebar"] { background: #0a0d12; }
          .stDataFrame { border-radius: 12px; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    init_db()
    admin_reset_block()
    brand_header()

    page, days = sidebar_nav()
    start_dt = datetime.now().replace(microsecond=0) - timedelta(days=int(days))

    if page == "Tableau de bord (Récap & Recos)":
        page_dashboard(start_dt)
    elif page == "Agriculture – Banane (Blocs & Capteurs)":
        page_agri_blocks_and_sensors(start_dt, "banane")
    elif page == "Agriculture – Taro (Blocs & Capteurs)":
        page_agri_blocks_and_sensors(start_dt, "taro")
    elif page == "Observations terrain (Agriculture)":
        page_observations_agri(start_dt)
    elif page == "Vivoplants":
        page_vivoplants(start_dt)
    elif page == "Apiculture (Ruches)":
        page_apiculture(start_dt)
    elif page == "Cuniculture (Lapins)":
        page_cuniculture(start_dt)
    elif page == "Objectifs & KPI":
        page_objectifs_kpi()
    elif page == "Export (CSV)":
        page_export()
    else:
        st.error("Page inconnue.")

    st.caption("© CAFY Monitoring • DURABILIS & CO")


if __name__ == "__main__":
    main()
