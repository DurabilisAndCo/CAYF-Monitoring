
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
import database as db

# ------------------ Page config ------------------
st.set_page_config(
    page_title="Monitoring Agri – Tableau de bord",
    page_icon="🌿",
    layout="wide",
)

# ------------------ Styling ------------------
CSS = """
<style>
/* Global */
.block-container {padding-top: 1.2rem;}
h1,h2,h3 {letter-spacing: .2px;}
/* Header banner */
.banner {
  border-radius: 18px;
  padding: 18px 18px;
  background: linear-gradient(90deg, rgba(45,51,129,.9), rgba(44,110,161,.85), rgba(68,160,201,.85));
  color: white;
  box-shadow: 0 10px 26px rgba(0,0,0,.22);
  margin-bottom: 14px;
}
.banner-title {font-size: 1.45rem; font-weight: 750; margin: 0;}
.banner-sub {opacity:.92; margin-top: 6px; font-size: .92rem;}
.badge {display:inline-block; padding: 2px 10px; border-radius: 999px; background: rgba(255,255,255,.18); margin-left: 8px; font-size:.78rem;}
.kpi {
  border-radius: 16px; padding: 14px 14px;
  border: 1px solid rgba(255,255,255,.08);
  background: rgba(255,255,255,.03);
}
.kpi-label {opacity: .8; font-size:.86rem;}
.kpi-value {font-weight: 800; font-size: 1.45rem; margin-top: 2px;}
.kpi-hint {opacity: .75; font-size:.82rem; margin-top: 6px;}
.rec {
  border-radius: 14px; padding: 12px 12px;
  border: 1px solid rgba(255,255,255,.08);
  background: rgba(255,255,255,.03);
}
.rec-title {font-weight: 750; margin-bottom: 6px;}
.tag {display:inline-block; padding: 2px 10px; border-radius: 999px; font-size:.78rem; margin-right: 6px;}
.tag-ok {background: rgba(0,255,127,.12); border: 1px solid rgba(0,255,127,.25);}
.tag-warn {background: rgba(255,165,0,.12); border: 1px solid rgba(255,165,0,.25);}
.tag-bad {background: rgba(255,0,0,.12); border: 1px solid rgba(255,0,0,.25);}
.small-muted {opacity:.75; font-size:.85rem;}
.hr {height:1px; background: rgba(255,255,255,.08); margin: 10px 0;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ------------------ Init DB ------------------
conn = db.get_connection()
db.init_db(conn)

# ------------------ Constants ------------------
CROP_TYPES = ["Banane", "Taro", "PIF (plants issues de fragments)", "Autre"]
SENSOR_FIELDS = [
    ("light", "Lumière (lux)"),
    ("air_temp", "Température air (°C)"),
    ("air_humidity", "Humidité air (%)"),
    ("soil_temp", "Température sol (°C)"),
    ("soil_moisture", "Humidité sol (%)"),
    ("soil_ph", "pH du sol"),
    ("fertility", "EC / Fertilité (µS/cm)"),
    ("battery", "Batterie capteur (%)"),
]

# Culture thresholds (simple, ajustables)
THRESHOLDS = {
    "Banane": {
        "soil_ph": (5.5, 7.0),
        "soil_moisture": (60, 85),
        "soil_temp": (22, 32),
        "air_temp": (20, 35),
        "air_humidity": (55, 95),
        "fertility": (800, 2000),  # µS/cm
        "light": (8000, 120000),   # lux (approx; depends sensor placement)
    },
    "Taro": {
        "soil_ph": (5.5, 6.8),
        "soil_moisture": (70, 95),
        "soil_temp": (20, 32),
        "air_temp": (18, 35),
        "air_humidity": (60, 98),
        "fertility": (500, 1800),
        "light": (5000, 100000),
    },
    "PIF (plants issues de fragments)": {
        "soil_ph": (5.5, 7.0),
        "soil_moisture": (55, 80),
        "soil_temp": (20, 32),
        "air_temp": (20, 35),
        "air_humidity": (60, 95),
        "fertility": (600, 1800),
        "light": (3000, 80000),
    }
}

# ------------------ Helpers ------------------
def banner():
    st.markdown(
        """
        <div class="banner">
          <div class="banner-title">🌿 Monitoring Multi-Activités – Agriculture • Apiculture • Cunicul﻿ture • Vivoplants
            <span class="badge">Durabilis&Co</span>
          </div>
          <div class="banner-sub">Tableau de bord récap + recommandations automatisées (règles) • Saisie terrain qualitative & quantitative • Export CSV</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def kpi(col, label, value, hint=""):
    with col:
        st.markdown(f"""
        <div class="kpi">
          <div class="kpi-label">{label}</div>
          <div class="kpi-value">{value}</div>
          <div class="kpi-hint">{hint}</div>
        </div>
        """, unsafe_allow_html=True)

def tag(level):
    if level == "OK":
        return '<span class="tag tag-ok">OK</span>'
    if level == "ATTENTION":
        return '<span class="tag tag-warn">ATTENTION</span>'
    return '<span class="tag tag-bad">CRITIQUE</span>'

def assess_value(metric, v, crop):
    if v is None:
        return None
    th = THRESHOLDS.get(crop, {}).get(metric)
    if not th:
        return ("OK", "Seuil non défini")
    lo, hi = th
    if v < lo:
        return ("ATTENTION", f"Trop bas (min {lo})")
    if v > hi:
        return ("ATTENTION", f"Trop élevé (max {hi})")
    return ("OK", f"Dans la plage ({lo}–{hi})")

def recommendations_for_crop(latest_row, crop):
    # Rule-based suggestions
    if latest_row is None:
        return [("ATTENTION", "Aucune donnée capteur récente. Ajouter une mesure (7‑en‑1) pour activer les recommandations.")]
    recs = []
    m = latest_row.to_dict()
    # Soil moisture
    a = assess_value("soil_moisture", m.get("soil_moisture"), crop)
    if a:
        lvl, note = a
        if lvl != "OK":
            if m.get("soil_moisture") is not None and m["soil_moisture"] < THRESHOLDS[crop]["soil_moisture"][0]:
                recs.append(("ATTENTION", f"Humidité du sol basse ({m['soil_moisture']}%). Prioriser arrosage / paillage."))
            else:
                recs.append(("ATTENTION", f"Humidité du sol élevée ({m['soil_moisture']}%). Vérifier drainage / risques de pourriture."))
    # pH
    a = assess_value("soil_ph", m.get("soil_ph"), crop)
    if a and a[0] != "OK":
        recs.append(("ATTENTION", f"pH hors plage ({m.get('soil_ph')}). Ajuster amendements (selon analyse)."))
    # Fertility / EC
    a = assess_value("fertility", m.get("fertility"), crop)
    if a and a[0] != "OK":
        if m.get("fertility") is not None and m["fertility"] < THRESHOLDS[crop]["fertility"][0]:
            recs.append(("ATTENTION", f"EC faible ({m['fertility']} µS/cm). Envisager fertilisation progressive."))
        else:
            recs.append(("ATTENTION", f"EC élevée ({m['fertility']} µS/cm). Risque de salinité: ajuster dosage/lessivage."))
    # Air humidity/temp
    if m.get("air_humidity") is not None and m["air_humidity"] < THRESHOLDS[crop]["air_humidity"][0]:
        recs.append(("ATTENTION", f"Humidité de l’air basse ({m['air_humidity']}%). Surveiller stress hydrique."))
    if m.get("air_temp") is not None and m["air_temp"] > THRESHOLDS[crop]["air_temp"][1]:
        recs.append(("ATTENTION", f"Température air élevée ({m['air_temp']}°C). Prévoir ombrage/irrigation."))
    # Battery
    if m.get("battery") is not None and m["battery"] < 20:
        recs.append(("ATTENTION", f"Batterie capteur faible ({m['battery']}%). Recharger / remplacer pour éviter perte de données."))
    if not recs:
        recs.append(("OK", "Paramètres globalement stables. Continuer le suivi et consigner les observations terrain."))
    return recs[:6]

def swot_from_signals(recs, qual_flags):
    # Very lightweight SWOT
    strengths = []
    weaknesses = []
    threats = []
    opportunities = []
    if all(lvl=="OK" for lvl,_ in recs):
        strengths.append("Stabilité des paramètres agro‑environnementaux (capteur 7‑en‑1).")
    else:
        weaknesses.append("Au moins un indicateur hors seuil – besoin d’ajustement opérationnel.")
    if qual_flags.get("disease") or qual_flags.get("pests"):
        threats.append("Signaux terrain: maladies/ravageurs déclarés. Renforcer surveillance & traitement adapté.")
    else:
        strengths.append("Aucun signal terrain majeur (maladies/ravageurs) sur la dernière observation.")
    opportunities.append("Standardiser la collecte (capteurs + fiches terrain) pour produire des rapports et attirer des bailleurs.")
    opportunities.append("Comparer blocs/cultures (Banane vs Taro) pour optimiser eau & fertilisation.")
    return strengths[:4], weaknesses[:4], opportunities[:4], threats[:4]

def load_filters():
    with st.sidebar:
        st.markdown("### 🔎 Filtres")
        days = st.slider("Période d'analyse (jours)", 7, 180, 30, step=1)
        since = datetime.now() - timedelta(days=days)
        return since

def empty_state(msg):
    st.info(msg)

# ------------------ Sidebar navigation ------------------
with st.sidebar:
    st.markdown("## 🧭 Navigation")
    page = st.selectbox("Choisir une page", [
        "Accueil – Récap & Recos",
        "Agriculture – Blocs & Capteurs",
        "Agriculture – Observations terrain",
        "Apiculture – Ruches",
        "Cunicul﻿ture – Lapins",
        "Vivoplants – Pépinière",
        "Objectifs & KPI",
        "Export",
    ])

since = load_filters()
banner()

# ------------------ Data loaders ------------------
plots = db.get_plots(conn)
latest_by_plot = db.get_latest_sensor_by_plot(conn)
latest_qual_by_plot = db.get_latest_qual_by_plot(conn)

# ------------------ Pages ------------------
if page == "Accueil – Récap & Recos":
    st.markdown("## 📊 Tableau de bord – Vue d’ensemble")

    # KPIs
    crops_count = len(plots[plots["asset_type"].isin(["plot"])]) if not plots.empty else 0
    hives_count = len(plots[plots["asset_type"].isin(["hive"])]) if not plots.empty else 0
    rabbits_count = len(plots[plots["asset_type"].isin(["rabbitry"])]) if not plots.empty else 0
    viv_batches = len(plots[plots["asset_type"].isin(["vivoplant"])]) if not plots.empty else 0

    # Latest sensor date
    last_sensor_date = latest_by_plot["date"].max() if not latest_by_plot.empty else None
    last_sensor_str = pd.to_datetime(last_sensor_date).strftime("%Y-%m-%d %H:%M") if last_sensor_date else "—"

    c1,c2,c3,c4 = st.columns(4)
    kpi(c1, "🌱 Blocs agricoles", crops_count, "Banane / Taro / PIF")
    kpi(c2, "🐝 Ruches", hives_count, "Suivi inspections & production")
    kpi(c3, "🐇 Cunicul﻿ture", rabbits_count, "Suivi cheptel & cycles")
    kpi(c4, "🌿 Vivoplants", viv_batches, "Lots / taux de reprise")

    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)

    # Récap recommandations (top 1 bloc de chaque culture si dispo)
    st.markdown("### 🤖 Recommandations automatisées (règles)")
    if plots.empty:
        empty_state("Commence par créer tes blocs/ruches/lots dans les pages dédiées.")
    else:
        cols = st.columns(2)
        # Pick up to 4 assets to summarize
        summary_assets = plots.head(4)
        for i, (_, asset) in enumerate(summary_assets.iterrows()):
            with cols[i % 2]:
                name = asset["name"]
                atype = asset["asset_type"]
                crop = asset.get("crop_type", None)
                st.markdown(f"#### {name}")
                if atype == "plot":
                    latest = latest_by_plot[latest_by_plot["asset_id"]==asset["asset_id"]]
                    latest_row = latest.sort_values("date").tail(1).iloc[0] if not latest.empty else None
                    recs = recommendations_for_crop(latest_row, crop or "Banane")
                    # Qual flags
                    qual = latest_qual_by_plot[latest_qual_by_plot["asset_id"]==asset["asset_id"]]
                    qual_row = qual.sort_values("date").tail(1).iloc[0] if not qual.empty else None
                    qual_flags = {"disease": bool(qual_row["disease"]) if qual_row is not None else False,
                                  "pests": bool(qual_row["pests"]) if qual_row is not None else False}
                    strengths, weaknesses, opportunities, threats = swot_from_signals(recs, qual_flags)

                    st.markdown("<div class='rec'><div class='rec-title'>📌 Actions recommandées</div>", unsafe_allow_html=True)
                    for lvl, txt in recs:
                        st.markdown(f"{tag(lvl)} {txt}", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

                    with st.expander("🧠 Mini SWOT (auto)"):
                        st.markdown("**Forces**")
                        for x in strengths: st.write("✅ " + x)
                        st.markdown("**Faiblesses**")
                        for x in weaknesses: st.write("⚠️ " + x)
                        st.markdown("**Opportunités**")
                        for x in opportunities: st.write("💡 " + x)
                        st.markdown("**Menaces**")
                        for x in threats: st.write("🛑 " + x)
                else:
                    st.markdown("<div class='rec'><div class='rec-title'>📌 Récap</div>", unsafe_allow_html=True)
                    st.write("Cet actif est suivi via sa page dédiée (inspections / cheptel / lots).")
                    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
    st.markdown("### 📈 Tendances (capteurs) – sur la période sélectionnée")
    if latest_by_plot.empty:
        empty_state("Aucune donnée capteur. Va dans « Agriculture – Blocs & Capteurs » pour ajouter une mesure.")
    else:
        readings = db.get_sensor_readings(conn, since=since)
        if readings.empty:
            empty_state("Aucune donnée capteur sur la période.")
        else:
            # Filter to plots only
            readings = readings.merge(plots[["asset_id","name","crop_type","asset_type"]], on="asset_id", how="left")
            readings = readings[readings["asset_type"]=="plot"]
            metric = st.selectbox("Choisir l'indicateur", [f[0] for f in SENSOR_FIELDS if f[0]!="battery"], index=4)
            fig = px.line(readings, x="date", y=metric, color="name", markers=True)
            st.plotly_chart(fig, use_container_width=True)

    st.caption(f"Dernière mesure capteur: **{last_sensor_str}**")

elif page == "Agriculture – Blocs & Capteurs":
    st.markdown("## 🌱 Agriculture – Blocs (Banane/Taro/PIF) & mesures capteur 7‑en‑1")

    tab1, tab2 = st.tabs(["➕ Créer / gérer des blocs", "📡 Ajouter une mesure capteur"])
    with tab1:
        st.markdown("### Créer un bloc")
        with st.form("create_plot"):
            name = st.text_input("Nom du bloc", placeholder="Ex: Bloc A – Banane")
            crop = st.selectbox("Culture", CROP_TYPES, index=0)
            area = st.number_input("Surface (m²) – optionnel", min_value=0.0, value=0.0, step=10.0)
            location = st.text_input("Localisation – optionnel", placeholder="Ex: Ntoum – Zone humide")
            notes = st.text_area("Notes – optionnel", placeholder="Accès, irrigation, observations générales…")
            submitted = st.form_submit_button("Créer le bloc")
            if submitted:
                if not name.strip():
                    st.error("Le nom du bloc est obligatoire.")
                else:
                    db.create_asset(conn, asset_type="plot", name=name.strip(), crop_type=crop, area_m2=area or None, location=location.strip() or None, notes=notes.strip() or None)
                    st.success("Bloc créé ✅")
                    st.rerun()

        st.markdown("### Blocs existants")
        plots_only = plots[plots["asset_type"]=="plot"] if not plots.empty else pd.DataFrame()
        if plots_only.empty:
            empty_state("Aucun bloc. Crée ton premier bloc ci-dessus.")
        else:
            st.dataframe(plots_only[["asset_id","name","crop_type","area_m2","location"]], use_container_width=True)

    with tab2:
        plots_only = plots[plots["asset_type"]=="plot"] if not plots.empty else pd.DataFrame()
        if plots_only.empty:
            empty_state("Crée d’abord un bloc dans l’onglet « Créer / gérer des blocs ».")
        else:
            st.markdown("### Saisir une mesure capteur (7‑en‑1)")
            with st.form("add_sensor"):
                asset_id = st.selectbox("Bloc", plots_only["asset_id"], format_func=lambda x: plots_only.set_index("asset_id").loc[x,"name"])
                dt = st.datetime_input("Date/heure", value=datetime.now())
                cols = st.columns(4)
                values = {}
                for i,(key,label) in enumerate(SENSOR_FIELDS):
                    with cols[i % 4]:
                        if key in ["soil_ph"]:
                            values[key] = st.number_input(label, min_value=0.0, max_value=14.0, value=6.5, step=0.1)
                        elif key in ["air_humidity","soil_moisture","battery"]:
                            values[key] = st.number_input(label, min_value=0.0, max_value=100.0, value=0.0, step=1.0)
                        elif key in ["air_temp","soil_temp"]:
                            values[key] = st.number_input(label, min_value=-10.0, max_value=60.0, value=0.0, step=0.1)
                        else:
                            values[key] = st.number_input(label, min_value=0.0, value=0.0, step=1.0)
                submitted = st.form_submit_button("Enregistrer la mesure")
                if submitted:
                    db.add_sensor_reading(conn, asset_id=asset_id, dt=dt, **values)
                    st.success("Mesure enregistrée ✅")
                    st.rerun()

            st.markdown("### Dernières mesures")
            recent = db.get_sensor_readings(conn, since=datetime.now()-timedelta(days=7))
            if recent.empty:
                empty_state("Aucune mesure sur 7 jours.")
            else:
                recent = recent.merge(plots_only[["asset_id","name","crop_type"]], on="asset_id", how="left")
                st.dataframe(recent.sort_values("date", ascending=False).head(30), use_container_width=True)

elif page == "Agriculture – Observations terrain":
    st.markdown("## 📝 Agriculture – Observations terrain (qualitatives)")
    plots_only = plots[plots["asset_type"]=="plot"] if not plots.empty else pd.DataFrame()
    if plots_only.empty:
        empty_state("Crée d’abord un bloc dans « Agriculture – Blocs & Capteurs ».")
    else:
        left, right = st.columns([1,1])
        with left:
            st.markdown("### Ajouter une observation")
            with st.form("add_qual"):
                asset_id = st.selectbox("Bloc", plots_only["asset_id"], format_func=lambda x: plots_only.set_index("asset_id").loc[x,"name"])
                dt = st.datetime_input("Date/heure", value=datetime.now(), key="qual_dt")
                stage = st.selectbox("Stade", ["Plantation", "Croissance", "Développement", "Floraison", "Fructification", "Récolte", "Autre"], index=1)
                vigor = st.selectbox("Vigueur", ["Faible", "Moyenne", "Bonne"], index=2)
                leaf_status = st.selectbox("État des feuilles", ["Normal", "Jaunissement", "Taches", "Nécrose", "Autre"], index=0)
                disease = st.checkbox("Maladies observées ?")
                disease_notes = st.text_input("Détails maladies (si oui)", placeholder="Ex: cercosporiose, mildiou…")
                pests = st.checkbox("Ravageurs observés ?")
                pests_notes = st.text_input("Détails ravageurs (si oui)", placeholder="Ex: charançon, pucerons…")
                notes = st.text_area("Notes libres", placeholder="Photo, action prise, irrigation, fertilisation…")
                submitted = st.form_submit_button("Enregistrer l’observation")
                if submitted:
                    db.add_field_observation(conn, asset_id=asset_id, dt=dt, stage=stage, vigor=vigor, leaf_status=leaf_status,
                                             disease=int(disease), disease_notes=disease_notes, pests=int(pests), pests_notes=pests_notes, notes=notes)
                    st.success("Observation enregistrée ✅")
                    st.rerun()
        with right:
            st.markdown("### Dernières observations")
            obs = db.get_field_observations(conn, since=datetime.now()-timedelta(days=60))
            if obs.empty:
                empty_state("Aucune observation.")
            else:
                obs = obs.merge(plots_only[["asset_id","name","crop_type"]], on="asset_id", how="left")
                st.dataframe(obs.sort_values("date", ascending=False).head(50), use_container_width=True)

elif page == "Apiculture – Ruches":
    st.markdown("## 🐝 Apiculture – Suivi des ruches")
    tab1, tab2 = st.tabs(["➕ Créer / gérer des ruches", "🧾 Inspections & production"])
    with tab1:
        with st.form("create_hive"):
            name = st.text_input("Nom de la ruche", placeholder="Ex: Ruche 1")
            location = st.text_input("Localisation – optionnel", placeholder="Ex: Bordure parcelle")
            notes = st.text_area("Notes – optionnel", placeholder="Type de ruche, emplacement, ombrage…")
            submitted = st.form_submit_button("Créer la ruche")
            if submitted:
                if not name.strip():
                    st.error("Nom obligatoire.")
                else:
                    db.create_asset(conn, asset_type="hive", name=name.strip(), crop_type=None, area_m2=None, location=location.strip() or None, notes=notes.strip() or None)
                    st.success("Ruche créée ✅")
                    st.rerun()
        h = plots[plots["asset_type"]=="hive"] if not plots.empty else pd.DataFrame()
        if h.empty:
            empty_state("Aucune ruche.")
        else:
            st.dataframe(h[["asset_id","name","location","notes"]], use_container_width=True)
    with tab2:
        h = plots[plots["asset_type"]=="hive"] if not plots.empty else pd.DataFrame()
        if h.empty:
            empty_state("Crée d’abord une ruche.")
        else:
            with st.form("add_hive"):
                asset_id = st.selectbox("Ruche", h["asset_id"], format_func=lambda x: h.set_index("asset_id").loc[x,"name"])
                dt = st.datetime_input("Date/heure", value=datetime.now(), key="hive_dt")
                colony_strength = st.selectbox("Force colonie", ["Faible","Moyenne","Forte"], index=1)
                queen_seen = st.checkbox("Reine vue ?")
                pests = st.checkbox("Parasites / nuisibles ?")
                honey_kg = st.number_input("Miel récolté (kg) – optionnel", min_value=0.0, value=0.0, step=0.1)
                notes = st.text_area("Notes", placeholder="Cadres, couvain, nourrissement, traitement…")
                submitted = st.form_submit_button("Enregistrer inspection")
                if submitted:
                    db.add_hive_inspection(conn, asset_id=asset_id, dt=dt, colony_strength=colony_strength, queen_seen=int(queen_seen),
                                          pests=int(pests), honey_kg=honey_kg, notes=notes)
                    st.success("Inspection enregistrée ✅")
                    st.rerun()

            insp = db.get_hive_inspections(conn, since=datetime.now()-timedelta(days=180))
            if insp.empty:
                empty_state("Aucune inspection.")
            else:
                insp = insp.merge(h[["asset_id","name"]], on="asset_id", how="left")
                st.dataframe(insp.sort_values("date", ascending=False).head(80), use_container_width=True)

elif page == "Cunicul﻿ture – Lapins":
    st.markdown("## 🐇 Cunicul﻿ture – Suivi lapins (cheptel & cycles)")
    tab1, tab2 = st.tabs(["➕ Créer / gérer l’unité", "🧾 Journal (naissances, mortalité, alimentation)"])
    with tab1:
        with st.form("create_rabbitry"):
            name = st.text_input("Nom unité / bâtiment", placeholder="Ex: Clapier principal")
            notes = st.text_area("Notes", placeholder="Capacité, cages, hygiène…")
            submitted = st.form_submit_button("Créer l’unité")
            if submitted:
                if not name.strip():
                    st.error("Nom obligatoire.")
                else:
                    db.create_asset(conn, asset_type="rabbitry", name=name.strip(), crop_type=None, area_m2=None, location=None, notes=notes.strip() or None)
                    st.success("Unité créée ✅")
                    st.rerun()
        r = plots[plots["asset_type"]=="rabbitry"] if not plots.empty else pd.DataFrame()
        if r.empty:
            empty_state("Aucune unité lapins.")
        else:
            st.dataframe(r[["asset_id","name","notes"]], use_container_width=True)

    with tab2:
        r = plots[plots["asset_type"]=="rabbitry"] if not plots.empty else pd.DataFrame()
        if r.empty:
            empty_state("Crée d’abord une unité lapins.")
        else:
            with st.form("add_rabbit_log"):
                asset_id = st.selectbox("Unité", r["asset_id"], format_func=lambda x: r.set_index("asset_id").loc[x,"name"])
                dt = st.datetime_input("Date/heure", value=datetime.now(), key="rab_dt")
                females = st.number_input("Femelles (effectif)", min_value=0, value=0, step=1)
                males = st.number_input("Mâles (effectif)", min_value=0, value=0, step=1)
                births = st.number_input("Naissances (nb)", min_value=0, value=0, step=1)
                deaths = st.number_input("Mortalité (nb)", min_value=0, value=0, step=1)
                feed_kg = st.number_input("Aliment distribué (kg)", min_value=0.0, value=0.0, step=0.1)
                notes = st.text_area("Notes", placeholder="Santé, vaccinations, hygiène, ventes…")
                submitted = st.form_submit_button("Enregistrer")
                if submitted:
                    db.add_rabbit_log(conn, asset_id=asset_id, dt=dt, females=females, males=males, births=births, deaths=deaths, feed_kg=feed_kg, notes=notes)
                    st.success("Journal mis à jour ✅")
                    st.rerun()
            logs = db.get_rabbit_logs(conn, since=datetime.now()-timedelta(days=365))
            if logs.empty:
                empty_state("Aucune entrée.")
            else:
                logs = logs.merge(r[["asset_id","name"]], on="asset_id", how="left")
                st.dataframe(logs.sort_values("date", ascending=False).head(120), use_container_width=True)

elif page == "Vivoplants – Pépinière":
    st.markdown("## 🌿 Vivoplants – Suivi pépinière (lots)")
    tab1, tab2 = st.tabs(["➕ Créer / gérer des lots", "🧾 Suivi des lots"])
    with tab1:
        with st.form("create_vivo"):
            name = st.text_input("Nom du lot", placeholder="Ex: Lot PIF – Déc 2025")
            species = st.text_input("Espèce/variété", placeholder="Ex: Banane plantain Big Ebanga")
            planned = st.number_input("Quantité prévue", min_value=0, value=0, step=10)
            notes = st.text_area("Notes")
            submitted = st.form_submit_button("Créer le lot")
            if submitted:
                if not name.strip():
                    st.error("Nom obligatoire.")
                else:
                    db.create_asset(conn, asset_type="vivoplant", name=name.strip(), crop_type=species.strip() or None, area_m2=None, location=None, notes=notes.strip() or None)
                    # store initial in vivoplant log
                    db.add_vivoplant_log(conn, asset_id=db.get_asset_id_by_name(conn, "vivoplant", name.strip()), dt=datetime.now(),
                                         produced=planned, transplanted=0, losses=0, notes="Création du lot")
                    st.success("Lot créé ✅")
                    st.rerun()
        v = plots[plots["asset_type"]=="vivoplant"] if not plots.empty else pd.DataFrame()
        if v.empty:
            empty_state("Aucun lot.")
        else:
            st.dataframe(v[["asset_id","name","crop_type","notes"]], use_container_width=True)

    with tab2:
        v = plots[plots["asset_type"]=="vivoplant"] if not plots.empty else pd.DataFrame()
        if v.empty:
            empty_state("Crée d’abord un lot.")
        else:
            with st.form("add_vivo_log"):
                asset_id = st.selectbox("Lot", v["asset_id"], format_func=lambda x: v.set_index("asset_id").loc[x,"name"])
                dt = st.datetime_input("Date/heure", value=datetime.now(), key="vivo_dt")
                produced = st.number_input("Produits (nb)", min_value=0, value=0, step=10)
                transplanted = st.number_input("Transplantés (nb)", min_value=0, value=0, step=10)
                losses = st.number_input("Pertes (nb)", min_value=0, value=0, step=10)
                notes = st.text_area("Notes", placeholder="Taux de reprise, serre, arrosage…")
                submitted = st.form_submit_button("Enregistrer")
                if submitted:
                    db.add_vivoplant_log(conn, asset_id=asset_id, dt=dt, produced=produced, transplanted=transplanted, losses=losses, notes=notes)
                    st.success("Suivi lot enregistré ✅")
                    st.rerun()
            logs = db.get_vivoplant_logs(conn, since=datetime.now()-timedelta(days=365))
            if logs.empty:
                empty_state("Aucune entrée.")
            else:
                logs = logs.merge(v[["asset_id","name"]], on="asset_id", how="left")
                st.dataframe(logs.sort_values("date", ascending=False).head(120), use_container_width=True)

elif page == "Objectifs & KPI":
    st.markdown("## 🎯 Objectifs chiffrés & suivi")
    st.markdown("Définis tes objectifs (bailleurs / pilotage interne) et suis la progression.")

    # Create/edit targets
    with st.form("set_targets"):
        st.markdown("### Définir des objectifs annuels (exemples)")
        col1,col2,col3 = st.columns(3)
        with col1:
            target_banane = st.number_input("Banane – CA théorique (FCFA/an)", min_value=0, value=33320000, step=100000)
            target_taro = st.number_input("Taro – CA théorique (FCFA/an)", min_value=0, value=5000000, step=100000)
        with col2:
            target_rabbits = st.number_input("Lapins – production (nb/cycle)", min_value=0, value=540, step=10)
            target_hives = st.number_input("Ruches – nombre cible", min_value=0, value=2, step=1)
        with col3:
            target_vivo = st.number_input("Vivoplants – volume (nb/cycle)", min_value=0, value=1000, step=50)
            loss_rate = st.number_input("Pertes tolérées (%)", min_value=0.0, max_value=100.0, value=10.0, step=0.5)
        submitted = st.form_submit_button("Enregistrer les objectifs")
        if submitted:
            db.upsert_targets(conn, {
                "banane_ca": int(target_banane),
                "taro_ca": int(target_taro),
                "rabbits_cycle": int(target_rabbits),
                "hives_count": int(target_hives),
                "vivoplants_cycle": int(target_vivo),
                "loss_rate": float(loss_rate),
            })
            st.success("Objectifs enregistrés ✅")
            st.rerun()

    targets = db.get_targets(conn)
    def tnum(key, default=0.0):
        """Convert target values (SQLite may return strings) to float for safe comparisons."""
        try:
            val = targets.get(key, default)
            if val is None or val == "":
                return float(default)
            return float(val)
        except Exception:
            return float(default)

    st.markdown("### 📌 Progression (MVP)")
    # We compute a few proxy KPIs from logs
    # Rabbits: last known births - deaths
    rabbit_logs = db.get_rabbit_logs(conn, since=datetime.now()-timedelta(days=365))
    honey = db.get_hive_inspections(conn, since=datetime.now()-timedelta(days=365))
    vivo = db.get_vivoplant_logs(conn, since=datetime.now()-timedelta(days=365))

    c1,c2,c3 = st.columns(3)
    if not rabbit_logs.empty:
        rabbits_out = int(rabbit_logs["births"].sum())
        rabbits_deaths = int(rabbit_logs["deaths"].sum())
    else:
        rabbits_out, rabbits_deaths = 0, 0
    if not honey.empty:
        honey_kg = float(honey["honey_kg"].sum())
    else:
        honey_kg = 0.0
    if not vivo.empty:
        vivo_prod = int(vivo["produced"].sum())
        vivo_losses = int(vivo["losses"].sum())
    else:
        vivo_prod, vivo_losses = 0, 0

    kpi(c1, "🐇 Naissances (année)", rabbits_out, f"Décès: {rabbits_deaths}")
    kpi(c2, "🐝 Miel récolté (kg/an)", f"{honey_kg:.1f}", "Somme des inspections")
    kpi(c3, "🌿 Vivoplants produits (an)", vivo_prod, f"Pertes: {vivo_losses}")

    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
    st.markdown("### 🤖 Recommandations (pilotage)")
    recs = []
    if rabbits_deaths > 0 and rabbits_out > 0:
        mort_rate = rabbits_deaths / max(rabbits_out,1) * 100
        if mort_rate > tnum("loss_rate", 10):
            recs.append(("ATTENTION", f"Mortalité lapins élevée (~{mort_rate:.1f}%). Renforcer hygiène, alimentation, suivi vétérinaire."))
    if vivo_prod > 0:
        loss_rate_v = vivo_losses / max(vivo_prod,1) * 100
        if loss_rate_v > tnum("loss_rate", 10):
            recs.append(("ATTENTION", f"Pertes vivoplants élevées (~{loss_rate_v:.1f}%). Ajuster ombrage/arrosage/substrat."))
    if tnum("hives_count", 0) > 0:
        current_hives = len(plots[plots["asset_type"]=="hive"]) if not plots.empty else 0
        if current_hives < int(tnum("hives_count", 0)):
            recs.append(("ATTENTION", f"Ruches: {current_hives}/{int(tnum('hives_count', 0))} installées. Planifier installation/extension."))
    if not recs:
        recs.append(("OK", "Objectifs sous contrôle à ce stade. Continuer la collecte structurée (preuves pour bailleurs)."))

    st.markdown("<div class='rec'><div class='rec-title'>📌 Synthèse</div>", unsafe_allow_html=True)
    for lvl, txt in recs:
        st.markdown(f"{tag(lvl)} {txt}", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

elif page == "Export":
    st.markdown("## ⬇️ Export des données (CSV)")
    st.markdown("Télécharge les données pour analyse avancée, reporting bailleurs, ou archivage.")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Capteurs (7‑en‑1)")
        df = db.get_sensor_readings(conn, since=None)
        if df.empty:
            empty_state("Aucune donnée capteur.")
        else:
            st.download_button("Télécharger CSV – capteurs", data=df.to_csv(index=False).encode("utf-8"),
                               file_name="sensor_readings.csv", mime="text/csv")
            st.dataframe(df.tail(20), use_container_width=True)

    with col2:
        st.markdown("### Observations terrain (agriculture)")
        obs = db.get_field_observations(conn, since=None)
        if obs.empty:
            empty_state("Aucune observation terrain.")
        else:
            st.download_button("Télécharger CSV – observations", data=obs.to_csv(index=False).encode("utf-8"),
                               file_name="field_observations.csv", mime="text/csv")
            st.dataframe(obs.tail(20), use_container_width=True)

    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
    st.markdown("### Apiculture / Lapins / Vivoplants")
    c1,c2,c3 = st.columns(3)
    with c1:
        insp = db.get_hive_inspections(conn, since=None)
        if not insp.empty:
            st.download_button("CSV – inspections ruches", data=insp.to_csv(index=False).encode("utf-8"),
                               file_name="hive_inspections.csv", mime="text/csv")
    with c2:
        logs = db.get_rabbit_logs(conn, since=None)
        if not logs.empty:
            st.download_button("CSV – lapins", data=logs.to_csv(index=False).encode("utf-8"),
                               file_name="rabbit_logs.csv", mime="text/csv")
    with c3:
        v = db.get_vivoplant_logs(conn, since=None)
        if not v.empty:
            st.download_button("CSV – vivoplants", data=v.to_csv(index=False).encode("utf-8"),
                               file_name="vivoplant_logs.csv", mime="text/csv")

else:
    st.error("Page inconnue.")
