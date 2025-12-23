import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
from datetime import datetime, date
import database as db

# ------------------ Page config ------------------
st.set_page_config(
    page_title="Ganvié Durable 2030 – Dashboard",
    page_icon="🌊",
    layout="wide",
)

# ------------------ Enhanced Styling ------------------
CSS = """
<style>
/* Import premium font */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* CSS Variables for theming */
:root {
    --bg-primary: #f1f5f9;
    --bg-card: rgba(255,255,255,0.75);
    --text-primary: #1e293b;
    --text-secondary: #64748b;
    --accent-blue: #3b82f6;
    --accent-blue-dark: #2563eb;
    --accent-green: #10b981;
    --accent-orange: #f59e0b;
    --accent-red: #ef4444;
    --accent-purple: #8b5cf6;
    --shadow-soft: 0 4px 20px rgba(0,0,0,0.06);
    --shadow-medium: 0 8px 30px rgba(0,0,0,0.12);
    --glass-blur: blur(12px);
    --border-glass: 1px solid rgba(255,255,255,0.3);
    --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --gradient-ocean: linear-gradient(135deg, #2c3e7d 0%, #2c6ea1 50%, #44a0c9 100%);
}

/* Global typography */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* Main container adjustments */
.block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
}

/* Enhanced Banner */
.banner {
    border-radius: 20px;
    padding: 24px 28px;
    background: var(--gradient-ocean);
    color: white;
    box-shadow: var(--shadow-medium);
    margin-bottom: 20px;
    position: relative;
    overflow: hidden;
}

.banner::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -20%;
    width: 60%;
    height: 200%;
    background: radial-gradient(ellipse, rgba(255,255,255,0.15) 0%, transparent 70%);
    pointer-events: none;
}

.banner-title {
    font-size: 1.6rem;
    font-weight: 800;
    margin: 0;
    letter-spacing: -0.02em;
}

.banner-sub {
    opacity: 0.9;
    margin-top: 8px;
    font-size: 0.95rem;
    font-weight: 500;
}

.badge {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 999px;
    background: rgba(255,255,255,0.2);
    backdrop-filter: blur(4px);
    margin-left: 12px;
    font-size: 0.8rem;
    font-weight: 600;
}

/* Glassmorphism KPI Cards */
.kpi {
    border-radius: 18px;
    padding: 20px;
    background: var(--bg-card);
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
    border: var(--border-glass);
    box-shadow: var(--shadow-soft);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}

.kpi:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-medium);
}

.kpi::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: var(--gradient-primary);
    opacity: 0;
    transition: opacity 0.3s ease;
}

.kpi:hover::before {
    opacity: 1;
}

.kpi-icon {
    font-size: 1.8rem;
    margin-bottom: 8px;
}

.kpi-label {
    color: var(--text-secondary);
    font-size: 0.85rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 4px;
}

.kpi-value {
    font-weight: 800;
    font-size: 1.8rem;
    color: var(--text-primary);
    margin-top: 4px;
    letter-spacing: -0.02em;
}

.kpi-hint {
    color: var(--text-secondary);
    font-size: 0.8rem;
    margin-top: 8px;
    font-weight: 500;
}

.kpi-trend {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
}

.kpi-trend-up {
    background: rgba(16, 185, 129, 0.15);
    color: #059669;
}

.kpi-trend-down {
    background: rgba(239, 68, 68, 0.15);
    color: #dc2626;
}

/* Recommendation Cards */
.rec {
    border-radius: 16px;
    padding: 16px 18px;
    background: var(--bg-card);
    backdrop-filter: var(--glass-blur);
    border: var(--border-glass);
    box-shadow: var(--shadow-soft);
    margin-bottom: 12px;
    transition: all 0.2s ease;
}

.rec:hover {
    transform: translateX(4px);
}

.rec-title {
    font-weight: 650;
    margin-bottom: 4px;
    line-height: 1.5;
}

/* Status Tags */
.tag {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    margin-right: 8px;
}

.tag-ok {
    background: linear-gradient(135deg, rgba(16,185,129,0.15), rgba(16,185,129,0.25));
    color: #059669;
    border: 1px solid rgba(16,185,129,0.3);
}

.tag-warn {
    background: linear-gradient(135deg, rgba(245,158,11,0.15), rgba(245,158,11,0.25));
    color: #d97706;
    border: 1px solid rgba(245,158,11,0.3);
}

.tag-bad {
    background: linear-gradient(135deg, rgba(239,68,68,0.15), rgba(239,68,68,0.25));
    color: #dc2626;
    border: 1px solid rgba(239,68,68,0.3);
}

.small-muted {
    color: var(--text-secondary);
    font-size: 0.82rem;
    margin-top: 6px;
}

/* Section Headers */
.section-header {
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 24px 0 16px 0;
    display: flex;
    align-items: center;
    gap: 10px;
}

.section-header::after {
    content: '';
    flex: 1;
    height: 2px;
    background: linear-gradient(90deg, rgba(59,130,246,0.3), transparent);
    margin-left: 12px;
}

/* Data Info Badge */
.data-info {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    background: rgba(59,130,246,0.1);
    border-radius: 8px;
    font-size: 0.82rem;
    color: var(--accent-blue-dark);
    font-weight: 500;
    margin-bottom: 16px;
}

/* Tab styling enhancements */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: rgba(255,255,255,0.5);
    padding: 6px;
    border-radius: 14px;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    padding: 10px 20px;
    font-weight: 600;
}

.stTabs [aria-selected="true"] {
    background: white;
    box-shadow: var(--shadow-soft);
}

/* Sidebar enhancements */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
}

section[data-testid="stSidebar"] .block-container {
    padding-top: 2rem;
}

/* Filter section styling */
.filter-section {
    background: white;
    border-radius: 12px;
    padding: 14px;
    margin-bottom: 16px;
    box-shadow: var(--shadow-soft);
}

.filter-title {
    font-weight: 700;
    font-size: 0.9rem;
    color: var(--text-primary);
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 6px;
}

/* Reset button styling */
.reset-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 16px;
    background: linear-gradient(135deg, #ef4444, #dc2626);
    color: white;
    border-radius: 8px;
    font-size: 0.82rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
}

.reset-btn:hover {
    transform: scale(1.02);
    box-shadow: 0 4px 12px rgba(239,68,68,0.3);
}

/* Chart containers */
.chart-container {
    background: white;
    border-radius: 16px;
    padding: 16px;
    box-shadow: var(--shadow-soft);
    margin-bottom: 20px;
}

/* Loading states */
.loading-pulse {
    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

/* Map legend */
.map-legend {
    display: flex;
    gap: 16px;
    padding: 12px 16px;
    background: white;
    border-radius: 10px;
    box-shadow: var(--shadow-soft);
    margin-top: 12px;
    flex-wrap: wrap;
}

.legend-item {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.82rem;
    font-weight: 500;
}

.legend-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
}

/* Empty states */
.empty-state {
    text-align: center;
    padding: 48px 24px;
    background: var(--bg-card);
    border-radius: 16px;
    border: 2px dashed rgba(0,0,0,0.1);
}

.empty-state-icon {
    font-size: 3rem;
    margin-bottom: 12px;
}

.empty-state-text {
    color: var(--text-secondary);
    font-size: 0.95rem;
}

/* Hide Streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ------------------ DB init ------------------
conn = db.get_connection()
db.init_db(conn)

# ------------------ Caching for performance ------------------
@st.cache_data(ttl=60)
def load_households():
    """Load households data with caching (60s TTL)"""
    return db.households_df(db.get_connection())

@st.cache_data(ttl=60)
def load_water_samples():
    """Load water samples data with caching (60s TTL)"""
    return db.water_df(db.get_connection())

# ------------------ Chart Theme ------------------
CHART_TEMPLATE = {
    'layout': {
        'font': {'family': 'Inter, sans-serif'},
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'colorway': ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#06b6d4'],
        'margin': {'l': 40, 'r': 20, 't': 40, 'b': 40},
    }
}

def apply_chart_style(fig):
    """Apply consistent styling to Plotly charts"""
    fig.update_layout(
        font_family="Inter, sans-serif",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=20, t=40, b=40),
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Inter"
        )
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.05)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.05)')
    return fig

# ------------------ Helpers ------------------
NEED_COLS = {
    "Eau": "needs_water",
    "Assainissement": "needs_sanitation",
    "Habitat": "needs_housing",
    "Éducation": "needs_education",
    "Santé": "needs_health",
    "Activités économiques": "needs_economic",
}

NEED_ICONS = {
    "Eau": "💧",
    "Assainissement": "🚽",
    "Habitat": "🏠",
    "Éducation": "📚",
    "Santé": "🏥",
    "Activités économiques": "💼",
}

def banner():
    st.markdown(
        """
        <div class="banner">
          <div class="banner-title">🌊 Dashboard Ganvié Durable 2030 – Phase 1 : Diagnostic participatif
            <span class="badge">Powered by Durabilis & Co. Bénin</span>
          </div>
          <div class="banner-sub">📊 Données en temps réel • 🏘️ Ménages • 💧 Eau & Environnement • 🗺️ Cartes • 💡 Insights & priorités</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def kpi(col, label, value, hint="", icon="📊", trend=None):
    trend_html = ""
    if trend is not None:
        if trend > 0:
            trend_html = f'<span class="kpi-trend kpi-trend-up">↑ +{trend:.1f}%</span>'
        elif trend < 0:
            trend_html = f'<span class="kpi-trend kpi-trend-down">↓ {trend:.1f}%</span>'
    
    with col:
        st.markdown(f"""
        <div class="kpi">
          <div class="kpi-icon">{icon}</div>
          <div class="kpi-label">{label}</div>
          <div class="kpi-value">{value} {trend_html}</div>
          <div class="kpi-hint">{hint}</div>
        </div>
        """, unsafe_allow_html=True)

def tag(level):
    if level == "OK":
        return '<span class="tag tag-ok">✓ OK</span>'
    if level == "ATTENTION":
        return '<span class="tag tag-warn">⚠ ATTENTION</span>'
    return '<span class="tag tag-bad">⚠ CRITIQUE</span>'

def parse_dt(s):
    try:
        return pd.to_datetime(s)
    except Exception:
        return pd.NaT

def needs_count(df):
    cols = list(NEED_COLS.values())
    for c in cols:
        if c not in df.columns:
            df[c] = 0
    return df[cols].fillna(0).sum(axis=1)

def format_number(n):
    """Format numbers with thousand separators"""
    if isinstance(n, float):
        return f"{n:,.1f}".replace(",", " ")
    return f"{n:,}".replace(",", " ")

def filtered_data():
    h = load_households()
    w = load_water_samples()

    if len(h):
        h["collected_at"] = pd.to_datetime(h["collected_at"])
    if len(w):
        w["collected_at"] = pd.to_datetime(w["collected_at"])

    # Sidebar filters with enhanced styling
    st.sidebar.markdown('<div class="filter-title">🔍 Filtres de données</div>', unsafe_allow_html=True)
    
    zones = sorted(list(set(h["zone"].dropna().unique().tolist() + w["zone"].dropna().unique().tolist())))
    zone_sel = st.sidebar.multiselect("📍 Quartier / zone", zones, default=zones)

    if len(h):
        dmin, dmax = h["collected_at"].min().date(), h["collected_at"].max().date()
    elif len(w):
        dmin, dmax = w["collected_at"].min().date(), w["collected_at"].max().date()
    else:
        dmin, dmax = date.today(), date.today()

    dr = st.sidebar.date_input("📅 Période d'analyse", value=(dmin, dmax))
    if isinstance(dr, tuple) and len(dr) == 2:
        start, end = dr[0], dr[1]
    else:
        start, end = dmin, dmax

    vuln_sel = st.sidebar.multiselect("⚡ Niveau de vulnérabilité", ["Faible", "Moyen", "Élevé"], default=["Faible", "Moyen", "Élevé"])
    need_sel = st.sidebar.multiselect("🎯 Type de besoin", list(NEED_COLS.keys()), default=list(NEED_COLS.keys()))

    # Filter reset and refresh buttons
    st.sidebar.markdown("---")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🔄 Actualiser", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with col2:
        if st.button("↩️ Réinitialiser", use_container_width=True):
            st.rerun()

    # Show active filter count
    active_filters = 0
    if len(zone_sel) != len(zones): active_filters += 1
    if start != dmin or end != dmax: active_filters += 1
    if len(vuln_sel) != 3: active_filters += 1
    if len(need_sel) != len(NEED_COLS): active_filters += 1
    
    if active_filters > 0:
        st.sidebar.info(f"🎯 {active_filters} filtre(s) actif(s)")

    # Apply filters
    if len(h):
        h = h[h["zone"].isin(zone_sel)]
        h = h[(h["collected_at"].dt.date >= start) & (h["collected_at"].dt.date <= end)]
        h = h[h["vulnerability"].isin(vuln_sel)]
        # keep households that have at least one selected need
        sel_cols = [NEED_COLS[n] for n in need_sel]
        if sel_cols:
            h = h[h[sel_cols].fillna(0).sum(axis=1) >= 1]

    if len(w):
        w = w[w["zone"].isin(zone_sel)]
        w = w[(w["collected_at"].dt.date >= start) & (w["collected_at"].dt.date <= end)]

    return h, w, {"zones": zone_sel, "start": start, "end": end, "vuln": vuln_sel, "needs": need_sel}

def compute_kpis(h, target_total):
    if len(h) == 0:
        return dict(
            pct_water=0, pct_san=0, pct_school=0, pct_3needs=0,
            surveyed=0, target=target_total
        )
    pct_water = 100 * h["water_improved"].fillna(0).mean()
    pct_san = 100 * h["sanitation"].fillna(0).mean()
    pct_school = 100 * h["children_schooling"].fillna(0).mean()
    needc = needs_count(h)
    pct_3needs = 100 * (needc >= 3).mean()
    return dict(
        pct_water=pct_water,
        pct_san=pct_san,
        pct_school=pct_school,
        pct_3needs=pct_3needs,
        surveyed=len(h),
        target=target_total
    )

def top_zones(h):
    if len(h) == 0:
        return pd.DataFrame(columns=["zone", "vuln_elevee_pct", "sans_san_pct", "besoins_moy"])
    tmp = h.copy()
    tmp["need_count"] = needs_count(tmp)
    g = tmp.groupby("zone").agg(
        vuln_elevee_pct=("vulnerability", lambda s: 100*(s=="Élevé").mean()),
        sans_san_pct=("sanitation", lambda s: 100*(s.fillna(0)==0).mean()),
        besoins_moy=("need_count", "mean"),
        menages=("household_id","count")
    ).reset_index()
    g["score"] = g["vuln_elevee_pct"]*0.45 + g["sans_san_pct"]*0.35 + g["besoins_moy"]*10*0.20
    return g.sort_values("score", ascending=False)

def water_map(w):
    if len(w) == 0 or w[["lat","lon"]].dropna().empty:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">🗺️</div>
            <div class="empty-state-text">Aucun point d'eau géolocalisé sur la période / filtres sélectionnés.</div>
        </div>
        """, unsafe_allow_html=True)
        return
    df = w.dropna(subset=["lat","lon"]).copy()
    color = {
        "Conforme": [16, 185, 129, 200],
        "A_surveiller": [245, 158, 11, 200],
        "A_risque": [239, 68, 68, 200],
    }
    df["color"] = df["risk_level"].apply(lambda x: color.get(x, [120,120,120,180]))
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position='[lon, lat]',
        get_fill_color="color",
        get_radius=65,
        pickable=True,
    )
    view_state = pdk.ViewState(latitude=float(df["lat"].mean()), longitude=float(df["lon"].mean()), zoom=11.5, pitch=0)
    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={"html": "<b>Zone:</b> {zone}<br/><b>Risque:</b> {risk_level}<br/><b>pH:</b> {ph}<br/><b>Turbidité:</b> {turbidity}<br/><b>E. coli:</b> {e_coli}"},
    )
    st.pydeck_chart(deck, use_container_width=True)
    
    # Map legend
    st.markdown("""
    <div class="map-legend">
        <div class="legend-item"><div class="legend-dot" style="background:#10b981"></div> Conforme</div>
        <div class="legend-item"><div class="legend-dot" style="background:#f59e0b"></div> À surveiller</div>
        <div class="legend-item"><div class="legend-dot" style="background:#ef4444"></div> À risque</div>
    </div>
    """, unsafe_allow_html=True)

def households_map(h):
    if len(h) == 0 or h[["lat","lon"]].dropna().empty:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">🏘️</div>
            <div class="empty-state-text">Aucun ménage géolocalisé sur la période / filtres sélectionnés.</div>
        </div>
        """, unsafe_allow_html=True)
        return
    df = h.dropna(subset=["lat","lon"]).copy()
    df["need_count"] = needs_count(df)
    # scale to colors (blue gradients)
    def col(n):
        if n >= 4: return [45,51,129,200]
        if n == 3: return [59,130,246,200]
        if n == 2: return [96,165,250,180]
        return [191, 219, 254, 160]
    df["color"] = df["need_count"].apply(col)
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position='[lon, lat]',
        get_fill_color="color",
        get_radius=30,
        pickable=True,
    )
    view_state = pdk.ViewState(latitude=float(df["lat"].mean()), longitude=float(df["lon"].mean()), zoom=11.5, pitch=0)
    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={"html": "<b>Zone:</b> {zone}<br/><b>Vulnérabilité:</b> {vulnerability}<br/><b>Besoins:</b> {need_count}"},
    )
    st.pydeck_chart(deck, use_container_width=True)
    
    # Map legend
    st.markdown("""
    <div class="map-legend">
        <div class="legend-item"><div class="legend-dot" style="background:#bfdbfe"></div> 0-1 besoins</div>
        <div class="legend-item"><div class="legend-dot" style="background:#60a5fa"></div> 2 besoins</div>
        <div class="legend-item"><div class="legend-dot" style="background:#3b82f6"></div> 3 besoins</div>
        <div class="legend-item"><div class="legend-dot" style="background:#2d3381"></div> 4+ besoins</div>
    </div>
    """, unsafe_allow_html=True)

def insights(h, w):
    recs = []
    if len(h):
        k = compute_kpis(h, db.get_target(conn))
        if k["pct_water"] < 50:
            recs.append(("CRITIQUE", "💧 Accès à l'eau améliorée < 50% : prioriser interventions WASH sur zones à score élevé."))
        elif k["pct_water"] < 70:
            recs.append(("ATTENTION", "💧 Accès à l'eau à surveiller : cibler les zones où la vulnérabilité est élevée."))
        if k["pct_san"] < 40:
            recs.append(("CRITIQUE", "🚽 Assainissement faible : lancer actions rapides (latrines, sensibilisation, gestion déchets)."))
        if k["pct_3needs"] > 35:
            recs.append(("ATTENTION", "📊 Beaucoup de ménages expriment ≥3 besoins : planifier un paquet d'investissements multi-secteurs par zone."))

        tz = top_zones(h).head(5)
        if len(tz):
            recs.append(("OK", f"🎯 Top zones prioritaires (score composite): {', '.join(tz['zone'].tolist())}."))

    if len(w):
        risk_share = w["risk_level"].value_counts(normalize=True) * 100
        if risk_share.get("A_risque", 0) > 25:
            recs.append(("CRITIQUE", "⚠️ Qualité de l'eau : forte proportion de points à risque. Activer plan de prévention (traitement, points alternatifs, alertes)."))
        elif risk_share.get("A_surveiller", 0) > 40:
            recs.append(("ATTENTION", "👀 Qualité de l'eau : plusieurs points à surveiller. Renforcer la fréquence des prélèvements en zones sensibles."))

    if not recs:
        recs.append(("OK", "✅ Aucun signal critique sur les filtres actuels. Continuer la collecte et consolider la couverture des zones."))

    for lvl, txt in recs[:6]:
        st.markdown(f'<div class="rec"><div class="rec-title">{tag(lvl)} {txt}</div><div class="small-muted">Recommandation automatique (règles simples) – à valider par les parties prenantes.</div></div>', unsafe_allow_html=True)

def report_pdf_bytes(meta, kpis, tz_df):
    # PDF minimal (sans images) pour rester léger sur Streamlit Cloud
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buff = BytesIO()
    c = canvas.Canvas(buff, pagesize=A4)
    width, height = A4

    y = height - 50
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "Ganvié Durable 2030 – Note de synthèse (extrait)")
    y -= 18
    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Période: {meta['start']} → {meta['end']} | Zones: {', '.join(meta['zones']) if meta['zones'] else '—'}")
    y -= 26

    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Indicateurs clés")
    y -= 16
    c.setFont("Helvetica", 10)
    lines = [
        f"• Accès à une source d'eau améliorée: {kpis['pct_water']:.1f}%",
        f"• Ménages avec dispositif d'assainissement: {kpis['pct_san']:.1f}%",
        f"• Scolarisation (proxy): {kpis['pct_school']:.1f}%",
        f"• Ménages déclarant ≥3 besoins: {kpis['pct_3needs']:.1f}%",
        f"• Ménages enquêtés (filtres): {kpis['surveyed']} / cible: {kpis['target']}",
    ]
    for ln in lines:
        c.drawString(50, y, ln); y -= 14

    y -= 8
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Top zones prioritaires (score composite)")
    y -= 16
    c.setFont("Helvetica", 9)

    if tz_df is None or tz_df.empty:
        c.drawString(50, y, "—"); y -= 14
    else:
        for _, r in tz_df.head(10).iterrows():
            c.drawString(50, y, f"- {r['zone']} | vuln. élevée: {r['vuln_elevee_pct']:.0f}% | sans assain.: {r['sans_san_pct']:.0f}% | besoins moy.: {r['besoins_moy']:.2f}")
            y -= 12
            if y < 80:
                c.showPage()
                y = height - 60

    c.setFont("Helvetica-Oblique", 8)
    c.drawString(40, 40, "Document généré automatiquement depuis le dashboard (démo). À compléter avec cartes/graphes sur version finale.")
    c.save()
    buff.seek(0)
    return buff.getvalue()

# ------------------ UI ------------------
banner()

h, w, meta = filtered_data()
target_total = db.get_target(conn)
k = compute_kpis(h, target_total)

# Data info badge
st.markdown(f'<div class="data-info">📊 <strong>{len(h)}</strong> ménages • <strong>{len(w)}</strong> échantillons d\'eau • Dernière mise à jour: {datetime.now().strftime("%H:%M")}</div>', unsafe_allow_html=True)

tabs = st.tabs(["🏠 Vue d'ensemble", "👥 Diagnostic ménages", "💧 Eau & Environnement", "🗺️ Cartes & Zones", "💡 Insights & Priorités", "📄 Rapport"])

# 1) Accueil
with tabs[0]:
    c1, c2, c3, c4, c5 = st.columns(5)
    kpi(c1, "Accès eau améliorée", f"{k['pct_water']:.1f}%", "Moyenne sur ménages filtrés", "💧")
    kpi(c2, "Assainissement", f"{k['pct_san']:.1f}%", "Moyenne sur ménages filtrés", "🚽")
    kpi(c3, "Scolarisation (proxy)", f"{k['pct_school']:.1f}%", "Au moins 1 enfant scolarisé", "📚")
    kpi(c4, "Ménages ≥ 3 besoins", f"{k['pct_3needs']:.1f}%", "Indicateur de multi‑vulnérabilité", "⚠️")
    kpi(c5, "Ménages enquêtés", f"{k['surveyed']}/{k['target']}", "Cible paramétrable", "📋")

    st.markdown('<div class="section-header">📈 Évolution de la collecte</div>', unsafe_allow_html=True)
    if len(h):
        hh_daily = h.set_index("collected_at").resample("D")["household_id"].count().reset_index()
        hh_daily["cumul"] = hh_daily["household_id"].cumsum()
        fig = px.area(hh_daily, x="collected_at", y="cumul", 
                     labels={"collected_at":"Date", "cumul":"Ménages (cumul)"},
                     color_discrete_sequence=['#3b82f6'])
        fig = apply_chart_style(fig)
        fig.update_traces(fillcolor='rgba(59, 130, 246, 0.2)', line=dict(width=3))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">📈</div>
            <div class="empty-state-text">Aucune donnée ménage sur la période / filtres.</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="section-header">🎯 Répartition des besoins</div>', unsafe_allow_html=True)
    if len(h):
        need_sum = {k: int(h[v].fillna(0).sum()) for k, v in NEED_COLS.items()}
        df_need = pd.DataFrame({"Besoin": list(need_sum.keys()), "Nombre": list(need_sum.values())}).sort_values("Nombre", ascending=True)
        fig2 = px.bar(df_need, x="Nombre", y="Besoin", orientation='h',
                     labels={"Nombre":"Nombre de ménages"},
                     color_discrete_sequence=['#8b5cf6'])
        fig2 = apply_chart_style(fig2)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">🎯</div>
            <div class="empty-state-text">Aucune donnée ménage pour calculer la répartition des besoins.</div>
        </div>
        """, unsafe_allow_html=True)

# 2) Diagnostic ménages
with tabs[1]:
    st.markdown('<div class="section-header">📊 Comparaisons par zone</div>', unsafe_allow_html=True)
    if len(h):
        tmp = h.copy()
        tmp["need_count"] = needs_count(tmp)
        g = tmp.groupby("zone").agg(
            pct_eau=("water_improved", "mean"),
            pct_san=("sanitation", "mean"),
            vuln_elevee=("vulnerability", lambda s: (s=="Élevé").mean()),
            besoins_moy=("need_count", "mean"),
            menages=("household_id","count")
        ).reset_index()
        g["pct_eau"] *= 100; g["pct_san"] *= 100; g["vuln_elevee"] *= 100
        
        fig = px.bar(g.sort_values("pct_eau"), x="zone", y="pct_eau", 
                    labels={"pct_eau":"% accès eau améliorée", "zone":"Zone"},
                    color_discrete_sequence=['#3b82f6'])
        fig = apply_chart_style(fig)
        st.plotly_chart(fig, use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            figb = px.bar(g.sort_values("vuln_elevee"), x="zone", y="vuln_elevee", 
                         labels={"vuln_elevee":"% vulnérabilité élevée", "zone":"Zone"},
                         color_discrete_sequence=['#ef4444'])
            figb = apply_chart_style(figb)
            st.plotly_chart(figb, use_container_width=True)
        with c2:
            figc = px.bar(g.sort_values("besoins_moy"), x="zone", y="besoins_moy", 
                         labels={"besoins_moy":"Besoins moyens (0–6)", "zone":"Zone"},
                         color_discrete_sequence=['#f59e0b'])
            figc = apply_chart_style(figc)
            st.plotly_chart(figc, use_container_width=True)

        st.markdown('<div class="section-header">🔗 Lien activité ↔ besoins</div>', unsafe_allow_html=True)
        figd = px.scatter(tmp, x="hh_size", y="need_count", color="main_activity", 
                         hover_data=["zone","vulnerability"], 
                         labels={"hh_size":"Taille ménage", "need_count":"Nombre de besoins"},
                         color_discrete_sequence=['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#06b6d4'])
        figd = apply_chart_style(figd)
        st.plotly_chart(figd, use_container_width=True)

        st.markdown('<div class="section-header">🏆 Top zones prioritaires</div>', unsafe_allow_html=True)
        tz = top_zones(h).head(5)[["zone","menages","vuln_elevee_pct","sans_san_pct","besoins_moy","score"]]
        st.dataframe(tz, use_container_width=True, hide_index=True)
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">👥</div>
            <div class="empty-state-text">Aucune donnée ménage sur la période / filtres.</div>
        </div>
        """, unsafe_allow_html=True)

# 3) Eau & Environnement
with tabs[2]:
    st.markdown('<div class="section-header">🗺️ Carte des points de prélèvement</div>', unsafe_allow_html=True)
    water_map(w)

    st.markdown('<div class="section-header">📊 Évolution saisonnière</div>', unsafe_allow_html=True)
    if len(w):
        c1, c2 = st.columns(2)
        with c1:
            fig = px.box(w, x="season", y="turbidity", points="all", 
                        labels={"season":"Saison", "turbidity":"Turbidité"},
                        color_discrete_sequence=['#3b82f6'])
            fig = apply_chart_style(fig)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig2 = px.box(w, x="season", y="e_coli", points="all", 
                         labels={"season":"Saison", "e_coli":"E. coli (CFU/100ml)"},
                         color_discrete_sequence=['#ef4444'])
            fig2 = apply_chart_style(fig2)
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown('<div class="section-header">📋 Derniers prélèvements</div>', unsafe_allow_html=True)
        latest = w.sort_values("collected_at").groupby(["zone"]).tail(1).sort_values("risk_level")
        st.dataframe(latest[["zone","collected_at","season","ph","turbidity","conductivity","e_coli","risk_level"]], 
                    use_container_width=True, hide_index=True)
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">💧</div>
            <div class="empty-state-text">Aucune donnée d'eau sur la période / filtres.</div>
        </div>
        """, unsafe_allow_html=True)

# 4) Cartes & Zones
with tabs[3]:
    st.markdown('<div class="section-header">🏘️ Carte des ménages</div>', unsafe_allow_html=True)
    st.caption("Couleur = intensité des besoins (plus foncé = plus de besoins)")
    households_map(h)

    st.markdown('<div class="section-header">📊 Synthèse par zone</div>', unsafe_allow_html=True)
    if len(h):
        tz = top_zones(h)[["zone","menages","vuln_elevee_pct","sans_san_pct","besoins_moy","score"]]
        st.dataframe(tz, use_container_width=True, hide_index=True)
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">🗺️</div>
            <div class="empty-state-text">Aucune donnée ménage sur la période / filtres.</div>
        </div>
        """, unsafe_allow_html=True)

# 5) Insights
with tabs[4]:
    st.markdown('<div class="section-header">💡 Tendances & recommandations</div>', unsafe_allow_html=True)
    insights(h, w)

    st.markdown('<div class="section-header">🎮 Simulation d\'impact</div>', unsafe_allow_html=True)
    if len(h):
        tz = top_zones(h).head(6)
        zones = tz["zone"].tolist()
        pick = st.multiselect("🎯 Zones ciblées (simulation)", zones, default=zones[:2])
        delta = st.slider("📈 Gain d'accès eau améliorée (points de %)", min_value=0, max_value=40, value=15, step=5)
        cur = compute_kpis(h, target_total)["pct_water"]
        sim = min(100.0, cur + (delta * (len(pick)/max(1,len(zones)))))
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Accès eau actuel", f"{cur:.1f}%")
        with col2:
            st.metric("Accès eau simulé", f"{sim:.1f}%", f"+{sim-cur:.1f}%")
        with col3:
            st.metric("Zones ciblées", f"{len(pick)}")
        
        st.caption("⚠️ Simulation indicative (démo) : la version finale doit utiliser un modèle d'impact par zone/ménage.")
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">🎮</div>
            <div class="empty-state-text">Aucune donnée ménage pour la simulation.</div>
        </div>
        """, unsafe_allow_html=True)

# 6) Rapport
with tabs[5]:
    st.markdown('<div class="section-header">📄 Générer un rapport PDF</div>', unsafe_allow_html=True)
    st.caption("Export PDF avec KPIs et top zones prioritaires")
    tz = top_zones(h)
    
    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("📄 Générer le PDF", use_container_width=True, type="primary"):
            with st.spinner("Génération en cours..."):
                pdf_bytes = report_pdf_bytes(meta, k, tz)
                st.download_button(
                    label="⬇️ Télécharger la note PDF",
                    data=pdf_bytes,
                    file_name="ganvie_durable_note_synthese.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

    st.markdown('<div class="section-header">💾 Exports données</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("⬇️ Export ménages (CSV)", data=h.to_csv(index=False).encode("utf-8"), file_name="households_filtered.csv", mime="text/csv", use_container_width=True)
    with c2:
        st.download_button("⬇️ Export eau (CSV)", data=w.to_csv(index=False).encode("utf-8"), file_name="water_samples_filtered.csv", mime="text/csv", use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.subheader("🛠️ Administration")
if st.sidebar.button("🌱 Générer des données fictives", use_container_width=True):
    import seed_data
    seed_data.seed()
    st.cache_data.clear()
    st.sidebar.success("✅ Données générées. Rechargez la page.")
    st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: var(--text-secondary); font-size: 0.85rem; padding: 16px 0;">
    🌊 Ganvié Durable 2030 • Powered by <strong>Durabilis & Co. Bénin</strong> • Dashboard v2.0
</div>
""", unsafe_allow_html=True)
