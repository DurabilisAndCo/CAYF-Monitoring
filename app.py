import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
from datetime import datetime, date
import database as db

# ------------------ Page config ------------------
st.set_page_config(
    page_title="CAYF Monitoring – 1er Centre Agroécologique Data-Driven du Gabon",
    page_icon="🌱",
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
    --bg-card: rgba(255,255,255,0.85);
    --text-primary: #1e293b;
    --text-secondary: #64748b;
    --accent-green: #059669;
    --accent-green-light: #10b981;
    --accent-blue: #3b82f6;
    --accent-orange: #f59e0b;
    --accent-red: #ef4444;
    --accent-purple: #8b5cf6;
    --shadow-soft: 0 4px 20px rgba(0,0,0,0.06);
    --shadow-medium: 0 8px 30px rgba(0,0,0,0.12);
    --glass-blur: blur(12px);
    --border-glass: 1px solid rgba(255,255,255,0.3);
    --gradient-primary: linear-gradient(135deg, #059669 0%, #10b981 100%);
    --gradient-earth: linear-gradient(135deg, #065f46 0%, #047857 50%, #059669 100%);
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
    background: var(--gradient-earth);
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
    background: linear-gradient(90deg, rgba(5,150,105,0.3), transparent);
    margin-left: 12px;
}

/* Filière Cards */
.filiere-card {
    border-radius: 16px;
    padding: 20px;
    background: var(--bg-card);
    box-shadow: var(--shadow-soft);
    border-left: 4px solid var(--accent-green);
    transition: all 0.2s ease;
}

.filiere-card:hover {
    box-shadow: var(--shadow-medium);
}

.filiere-title {
    font-weight: 700;
    font-size: 1.1rem;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
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

.tag-pending {
    background: linear-gradient(135deg, rgba(59,130,246,0.15), rgba(59,130,246,0.25));
    color: #2563eb;
    border: 1px solid rgba(59,130,246,0.3);
}

.tag-bad {
    background: linear-gradient(135deg, rgba(239,68,68,0.15), rgba(239,68,68,0.25));
    color: #dc2626;
    border: 1px solid rgba(239,68,68,0.3);
}

/* Timeline styling */
.timeline-item {
    position: relative;
    padding-left: 30px;
    padding-bottom: 20px;
    border-left: 3px solid #e2e8f0;
}

.timeline-item.completed {
    border-left-color: var(--accent-green);
}

.timeline-item.in-progress {
    border-left-color: var(--accent-orange);
}

.timeline-dot {
    position: absolute;
    left: -8px;
    top: 0;
    width: 14px;
    height: 14px;
    border-radius: 50%;
    background: white;
    border: 3px solid #e2e8f0;
}

.timeline-item.completed .timeline-dot {
    background: var(--accent-green);
    border-color: var(--accent-green);
}

.timeline-item.in-progress .timeline-dot {
    background: var(--accent-orange);
    border-color: var(--accent-orange);
}

/* Impact card */
.impact-card {
    border-radius: 14px;
    padding: 16px;
    background: linear-gradient(135deg, rgba(5,150,105,0.05), rgba(5,150,105,0.1));
    border: 1px solid rgba(5,150,105,0.2);
}

.progress-bar {
    height: 8px;
    background: #e2e8f0;
    border-radius: 4px;
    overflow: hidden;
    margin-top: 8px;
}

.progress-fill {
    height: 100%;
    background: var(--gradient-primary);
    border-radius: 4px;
    transition: width 0.5s ease;
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

/* Data Info Badge */
.data-info {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    background: rgba(5,150,105,0.1);
    border-radius: 8px;
    font-size: 0.82rem;
    color: var(--accent-green);
    font-weight: 500;
    margin-bottom: 16px;
}

/* Tab styling */
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

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
}

/* Hide branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ------------------ DB init ------------------
conn = db.get_connection()
db.init_db(conn)

# ------------------ Helpers ------------------
import base64
import os

# ------------------ Helpers ------------------
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

def banner():
    # Use columns for layout: Logo L | Text | Logo R
    c1, c2, c3 = st.columns([1, 4, 1])
    
    with c1:
        if os.path.exists("assets/cayf.jpg"):
            st.image("assets/cayf.jpg", width=100)
    
    with c2:
        st.markdown(
            """
            <div class="banner" style="text-align: center;">
              <div class="banner-title">🌱 CAYF Monitoring – Centre Agroécologique 2 ha
                <span class="badge">1er Centre Data-Driven du Gabon</span>
              </div>
              <div class="banner-sub">📊 Banane • Taro • Apiculture • Cuniculture • Vivoplants | Vision : devenir le 1er centre agroécologique data-driven et durable au Gabon</div>
            </div>
            """,
            unsafe_allow_html=True
        )
            
    with c3:
        if os.path.exists("assets/durabilis.png"):
            st.image("assets/durabilis.png", width=120)

def kpi(col, label, value, hint="", icon="📊", color="green"):
    with col:
        st.markdown(f"""
        <div class="kpi">
          <div class="kpi-icon">{icon}</div>
          <div class="kpi-label">{label}</div>
          <div class="kpi-value">{value}</div>
          <div class="kpi-hint">{hint}</div>
        </div>
        """, unsafe_allow_html=True)

def tag(status):
    if status == "completed":
        return '<span class="tag tag-ok">✓ Terminé</span>'
    if status == "in_progress":
        return '<span class="tag tag-warn">🔄 En cours</span>'
    if status == "pending":
        return '<span class="tag tag-pending">⏳ Prévu</span>'
    return '<span class="tag tag-bad">⚠ Attention</span>'

def format_number(n):
    if n is None:
        return "—"
    if isinstance(n, float):
        return f"{n:,.1f}".replace(",", " ")
    return f"{n:,}".replace(",", " ")

def apply_chart_style(fig):
    fig.update_layout(
        font_family="Inter, sans-serif",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=20, t=40, b=40),
        hoverlabel=dict(bgcolor="white", font_size=12, font_family="Inter")
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.05)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.05)')
    return fig

# ------------------ Load Data ------------------
@st.cache_data(ttl=60)
def load_assets():
    return db.get_plots(conn)

@st.cache_data(ttl=60)
def load_financial_targets():
    return db.get_financial_targets(conn)

@st.cache_data(ttl=60)
def load_roadmap():
    phases = db.get_roadmap_phases(conn)
    milestones = db.get_roadmap_milestones(conn)
    return phases, milestones

@st.cache_data(ttl=60)
def load_impact_indicators():
    return db.get_impact_indicators(conn)

@st.cache_data(ttl=60)
def load_social_fund():
    return db.get_social_fund_summary(conn)

@st.cache_data(ttl=60)
def load_committee():
    return db.get_committee_members(conn)

@st.cache_data(ttl=60)
def load_revenue_streams():
    return db.get_revenue_streams(conn)

# ------------------ Compute KPIs ------------------
def compute_filiere_stats():
    assets = load_assets()
    stats = {}
    
    for ftype in ['plot', 'hive', 'rabbitry', 'vivoplant']:
        subset = assets[assets['asset_type'] == ftype] if len(assets) > 0 else pd.DataFrame()
        stats[ftype] = {
            'count': len(subset),
            'area': subset['area_m2'].sum() if len(subset) > 0 and 'area_m2' in subset.columns else 0
        }
    
    # Get specific crop counts
    if len(assets) > 0:
        plots = assets[assets['asset_type'] == 'plot']
        stats['banane'] = len(plots[plots['crop_type'] == 'Banane']) if len(plots) > 0 else 0
        stats['taro'] = len(plots[plots['crop_type'] == 'Taro']) if len(plots) > 0 else 0
    else:
        stats['banane'] = 0
        stats['taro'] = 0
    
    return stats

def compute_roadmap_progress():
    phases, milestones = load_roadmap()
    if len(milestones) == 0:
        return 0
    completed = len(milestones[milestones['status'] == 'completed'])
    return round(100 * completed / len(milestones), 1)

# ------------------ UI ------------------
banner()

# Data info
assets = load_assets()
st.markdown(f'<div class="data-info">📊 <strong>{len(assets)}</strong> actifs enregistrés • Dernière mise à jour: {datetime.now().strftime("%H:%M")}</div>', unsafe_allow_html=True)

# Main tabs
tabs = st.tabs([
    "🏠 Vue Stratégique",
    "🌾 Performance Filières",
    "🗓️ Feuille de Route",
    "🌍 Impact Écosystémique",
    "💰 Modèle Économique",
    "👥 Gouvernance",
    "⚙️ Configuration"
])

# ==================== TAB 1: VUE STRATÉGIQUE ====================
with tabs[0]:
    stats = compute_filiere_stats()
    roadmap_pct = compute_roadmap_progress()
    
    # KPI row
    c1, c2, c3, c4, c5 = st.columns(5)
    kpi(c1, "Parcelles cultivées", f"{stats['plot']['count']}", f"{stats['plot']['area']:.0f} m² total", "🌱")
    kpi(c2, "Ruches actives", f"{stats['hive']['count']}", "Production apicole", "🐝")
    kpi(c3, "Élevages lapins", f"{stats['rabbitry']['count']}", "Cuniculture", "🐰")
    kpi(c4, "Lots Vivoplants", f"{stats['vivoplant']['count']}", "PIF & multiplication", "🌿")
    kpi(c5, "Feuille de route", f"{roadmap_pct}%", "Jalons complétés", "📋")
    
    st.markdown('<div class="section-header">📊 Répartition des Cultures</div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        if stats['banane'] > 0 or stats['taro'] > 0:
            fig = px.pie(
                values=[stats['banane'], stats['taro']],
                names=['Banane', 'Taro'],
                color_discrete_sequence=['#f59e0b', '#8b5cf6'],
                hole=0.4
            )
            fig = apply_chart_style(fig)
            fig.update_layout(showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">🌱</div>
                <div class="empty-state-text">Aucune parcelle enregistrée. Ajoutez des cultures via la page Agriculture.</div>
            </div>
            """, unsafe_allow_html=True)
    
    with c2:
        st.markdown('<div class="section-header">🎯 Objectifs 2030</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="impact-card">
            <strong>🎯 Vision : 1er Centre Agroécologique Data-Driven du Gabon</strong><br>
            <small>• 70% autonomie alimentaire du village<br>
            • 35 emplois directs créés<br>
            • 60% femmes bénéficiaires<br>
            • 120 tCO2/an évitées<br>
            • 15% des bénéfices → Fonds Social</small>
        </div>
        """, unsafe_allow_html=True)
    
    # Quick stats by filière
    st.markdown('<div class="section-header">🌾 Filières Actives</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.markdown(f"""
        <div class="filiere-card" style="border-left-color: #f59e0b;">
            <div class="filiere-title">🍌 Banane</div>
            <div><strong>{stats['banane']}</strong> parcelles</div>
        </div>
        """, unsafe_allow_html=True)
    
    with c2:
        st.markdown(f"""
        <div class="filiere-card" style="border-left-color: #8b5cf6;">
            <div class="filiere-title">🥔 Taro</div>
            <div><strong>{stats['taro']}</strong> parcelles associées</div>
        </div>
        """, unsafe_allow_html=True)
    
    with c3:
        st.markdown(f"""
        <div class="filiere-card" style="border-left-color: #eab308;">
            <div class="filiere-title">🐝 Apiculture</div>
            <div><strong>{stats['hive']['count']}</strong> ruches</div>
        </div>
        """, unsafe_allow_html=True)
    
    with c4:
        st.markdown(f"""
        <div class="filiere-card" style="border-left-color: #94a3b8;">
            <div class="filiere-title">🐰 Cuniculture</div>
            <div><strong>{stats['rabbitry']['count']}</strong> unités</div>
        </div>
        """, unsafe_allow_html=True)

# ==================== TAB 2: PERFORMANCE FILIÈRES ====================
with tabs[1]:
    st.markdown('<div class="section-header">📈 Performance par Filière</div>', unsafe_allow_html=True)
    
    filieres = st.tabs(["🍌 Banane & Taro", "🐝 Apiculture", "🐰 Cuniculture", "🌿 Vivoplants"])
    
    with filieres[0]:
        plots = assets[assets['asset_type'] == 'plot'] if len(assets) > 0 else pd.DataFrame()
        if len(plots) > 0:
            st.dataframe(plots[['name', 'crop_type', 'area_m2', 'location', 'created_at']], 
                        use_container_width=True, hide_index=True)
        else:
            st.info("🌱 Aucune parcelle enregistrée. Utilisez le formulaire ci-dessous.")
        
        # Quick add form
        with st.expander("➕ Ajouter une parcelle"):
            col1, col2, col3 = st.columns(3)
            with col1:
                new_name = st.text_input("Nom de la parcelle", placeholder="Ex: Parcelle Nord 1")
            with col2:
                new_crop = st.selectbox("Type de culture", ["Banane", "Taro", "Banane+Taro", "PIF"])
            with col3:
                new_area = st.number_input("Surface (m²)", min_value=0.0, step=10.0)
            
            new_location = st.text_input("Localisation", placeholder="Ex: Zone A - Bord du lac")
            
            if st.button("✅ Enregistrer la parcelle", type="primary"):
                if new_name:
                    db.create_asset(conn, "plot", new_name, crop_type=new_crop, area_m2=new_area, location=new_location)
                    st.success(f"✅ Parcelle '{new_name}' créée!")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("Le nom est requis.")
        
        # ==================== CAPTEUR 7-EN-1 ====================
        st.markdown('<div class="section-header">📡 Capteur 7-en-1 - Saisie des Données</div>', unsafe_allow_html=True)
        
        with st.expander("📊 Enregistrer une lecture capteur", expanded=False):
            if len(plots) > 0:
                selected_plot = st.selectbox("Sélectionner la parcelle", plots['name'].tolist(), key="sensor_plot")
                asset_id = plots[plots['name'] == selected_plot]['asset_id'].values[0]
                
                st.markdown("**📍 Données AIR**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    light = st.number_input("☀️ Éclairage (LUX)", min_value=0.0, max_value=100000.0, step=1.0, value=87.0)
                with col2:
                    air_temp = st.number_input("🌡️ Température Air (°C)", min_value=-10.0, max_value=60.0, step=0.1, value=26.2)
                with col3:
                    air_humidity = st.number_input("💧 Humidité Air (%)", min_value=0.0, max_value=100.0, step=0.1, value=47.0)
                
                st.markdown("**🌱 Données SOL**")
                col4, col5, col6, col7 = st.columns(4)
                with col4:
                    soil_temp = st.number_input("🌡️ Température Sol (°C)", min_value=-10.0, max_value=60.0, step=0.1, value=25.2)
                with col5:
                    soil_moisture = st.number_input("💧 Humidité Sol (%)", min_value=0.0, max_value=100.0, step=0.1, value=91.0)
                with col6:
                    soil_ph = st.number_input("⚗️ pH Sol", min_value=0.0, max_value=14.0, step=0.1, value=8.3)
                with col7:
                    fertility = st.number_input("🌿 Fertilité (µS/cm)", min_value=0.0, max_value=10000.0, step=1.0, value=3654.0)
                
                battery = st.slider("🔋 Niveau batterie capteur (%)", 0, 100, 80)
                
                if st.button("💾 Enregistrer les données capteur", type="primary", key="save_sensor"):
                    db.add_sensor_reading(conn, asset_id, datetime.now(), 
                                         light=light, air_temp=air_temp, air_humidity=air_humidity,
                                         soil_temp=soil_temp, soil_moisture=soil_moisture, 
                                         soil_ph=soil_ph, fertility=fertility, battery=battery)
                    st.success("✅ Données capteur enregistrées!")
                    st.cache_data.clear()
                    st.rerun()
            else:
                st.warning("⚠️ Créez d'abord une parcelle pour enregistrer des données capteur.")
        
        # Show latest sensor readings
        sensor_data = db.get_sensor_readings(conn)
        if len(sensor_data) > 0:
            st.markdown("**📈 Dernières lectures**")
            latest = sensor_data.sort_values('date', ascending=False).head(5)
            st.dataframe(latest[['asset_id', 'date', 'light', 'air_temp', 'air_humidity', 'soil_temp', 'soil_moisture', 'soil_ph', 'fertility']], 
                        use_container_width=True, hide_index=True)
        
        # ==================== OBSERVATIONS TERRAIN ====================
        st.markdown('<div class="section-header">🔍 Observations Terrain Qualitatives</div>', unsafe_allow_html=True)
        
        with st.expander("📝 Enregistrer une observation terrain", expanded=False):
            if len(plots) > 0:
                obs_plot = st.selectbox("Sélectionner la parcelle", plots['name'].tolist(), key="obs_plot")
                obs_asset_id = plots[plots['name'] == obs_plot]['asset_id'].values[0]
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    stage = st.selectbox("🌱 Stade phénologique", 
                                        ["Germination", "Croissance végétative", "Floraison", "Fructification", "Maturité", "Récolte"])
                with col2:
                    vigor = st.selectbox("💪 Vigueur", ["Excellent", "Bon", "Moyen", "Faible", "Critique"])
                with col3:
                    leaf_status = st.selectbox("🍃 État des feuilles", 
                                              ["Saines", "Légères taches", "Jaunissement", "Nécrose partielle", "Nécrose sévère"])
                
                col4, col5 = st.columns(2)
                with col4:
                    disease = st.checkbox("🦠 Présence de maladie")
                    disease_notes = st.text_input("Notes maladie", placeholder="Ex: Cercosporiose légère") if disease else ""
                with col5:
                    pests = st.checkbox("🐛 Présence de ravageurs")
                    pests_notes = st.text_input("Notes ravageurs", placeholder="Ex: Charançons detectés") if pests else ""
                
                obs_notes = st.text_area("📝 Notes générales", placeholder="Observations complémentaires...")
                
                if st.button("💾 Enregistrer l'observation", type="primary", key="save_obs"):
                    db.add_field_observation(conn, obs_asset_id, datetime.now(),
                                            stage=stage, vigor=vigor, leaf_status=leaf_status,
                                            disease=1 if disease else 0, disease_notes=disease_notes,
                                            pests=1 if pests else 0, pests_notes=pests_notes,
                                            notes=obs_notes)
                    st.success("✅ Observation enregistrée!")
                    st.cache_data.clear()
                    st.rerun()
            else:
                st.warning("⚠️ Créez d'abord une parcelle pour enregistrer des observations.")
        
        # Show latest observations
        obs_data = db.get_field_observations(conn)
        if len(obs_data) > 0:
            st.markdown("**📋 Dernières observations**")
            latest_obs = obs_data.sort_values('date', ascending=False).head(5)
            st.dataframe(latest_obs[['asset_id', 'date', 'stage', 'vigor', 'leaf_status', 'disease', 'pests']], 
                        use_container_width=True, hide_index=True)
    
    with filieres[1]:
        hives = assets[assets['asset_type'] == 'hive'] if len(assets) > 0 else pd.DataFrame()
        if len(hives) > 0:
            st.dataframe(hives[['name', 'location', 'notes', 'created_at']], use_container_width=True, hide_index=True)
        else:
            st.info("🐝 Aucune ruche enregistrée.")
        
        with st.expander("➕ Ajouter une ruche"):
            col1, col2 = st.columns(2)
            with col1:
                hive_name = st.text_input("Nom/numéro ruche", placeholder="Ex: Ruche 1")
            with col2:
                hive_loc = st.text_input("Emplacement", placeholder="Ex: Verger est", key="hive_loc")
            
            if st.button("✅ Enregistrer la ruche", type="primary", key="add_hive"):
                if hive_name:
                    db.create_asset(conn, "hive", hive_name, location=hive_loc)
                    st.success(f"✅ Ruche '{hive_name}' créée!")
                    st.cache_data.clear()
                    st.rerun()
    
    with filieres[2]:
        rabbits = assets[assets['asset_type'] == 'rabbitry'] if len(assets) > 0 else pd.DataFrame()
        if len(rabbits) > 0:
            st.dataframe(rabbits[['name', 'location', 'notes', 'created_at']], use_container_width=True, hide_index=True)
        else:
            st.info("🐰 Aucun élevage de lapins enregistré.")
        
        with st.expander("➕ Ajouter un élevage"):
            col1, col2 = st.columns(2)
            with col1:
                rab_name = st.text_input("Nom unité", placeholder="Ex: Clapier A")
            with col2:
                rab_loc = st.text_input("Localisation", placeholder="Ex: Bâtiment 2", key="rab_loc")
            
            if st.button("✅ Enregistrer l'élevage", type="primary", key="add_rab"):
                if rab_name:
                    db.create_asset(conn, "rabbitry", rab_name, location=rab_loc)
                    st.success(f"✅ Élevage '{rab_name}' créé!")
                    st.cache_data.clear()
                    st.rerun()
    
    with filieres[3]:
        vivo = assets[assets['asset_type'] == 'vivoplant'] if len(assets) > 0 else pd.DataFrame()
        if len(vivo) > 0:
            st.dataframe(vivo[['name', 'crop_type', 'notes', 'created_at']], use_container_width=True, hide_index=True)
        else:
            st.info("🌿 Aucun lot de vivoplants enregistré.")
        
        with st.expander("➕ Ajouter un lot vivoplants"):
            col1, col2 = st.columns(2)
            with col1:
                vivo_name = st.text_input("Nom du lot", placeholder="Ex: Lot PIF Janvier 2025")
            with col2:
                vivo_species = st.text_input("Espèce/Variété", placeholder="Ex: Plantain FHIA-21")
            
            if st.button("✅ Enregistrer le lot", type="primary", key="add_vivo"):
                if vivo_name:
                    db.create_asset(conn, "vivoplant", vivo_name, crop_type=vivo_species)
                    st.success(f"✅ Lot '{vivo_name}' créé!")
                    st.cache_data.clear()
                    st.rerun()

# ==================== TAB 3: FEUILLE DE ROUTE ====================
with tabs[2]:
    st.markdown('<div class="section-header">🗓️ Feuille de Route 2025-2030</div>', unsafe_allow_html=True)
    
    phases, milestones = load_roadmap()
    
    if len(phases) > 0:
        for _, phase in phases.iterrows():
            status_class = phase['status'] if phase['status'] in ['completed', 'in_progress'] else 'pending'
            st.markdown(f"""
            <div class="timeline-item {status_class}">
                <div class="timeline-dot"></div>
                <strong>{phase['name']}</strong> {tag(phase['status'])}
                <br><small>{phase['start_date'] or ''} → {phase['end_date'] or ''}</small>
                <br><small style="color: var(--text-secondary)">{phase['description'] or ''}</small>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("📋 Aucune phase définie. Ajoutez des phases à votre feuille de route.")
    
    # Add phase form
    with st.expander("➕ Ajouter une phase"):
        col1, col2 = st.columns(2)
        with col1:
            phase_name = st.text_input("Nom de la phase", placeholder="Ex: Préparation")
            phase_start = st.date_input("Date de début", key="phase_start")
        with col2:
            phase_status = st.selectbox("Statut", ["pending", "in_progress", "completed"])
            phase_end = st.date_input("Date de fin", key="phase_end")
        
        phase_desc = st.text_area("Description", placeholder="Actions clés de cette phase...")
        
        if st.button("✅ Ajouter la phase", type="primary"):
            if phase_name:
                db.add_roadmap_phase(conn, phase_name, phase_status, 
                                    phase_start.isoformat(), phase_end.isoformat(), phase_desc)
                st.success("✅ Phase ajoutée!")
                st.cache_data.clear()
                st.rerun()
    
    # Milestones section
    st.markdown('<div class="section-header">🎯 Jalons</div>', unsafe_allow_html=True)
    
    if len(milestones) > 0:
        st.dataframe(milestones[['title', 'target_date', 'status', 'notes']], 
                    use_container_width=True, hide_index=True)
    else:
        st.info("Aucun jalon défini.")
    
    with st.expander("➕ Ajouter un jalon"):
        col1, col2 = st.columns(2)
        with col1:
            if len(phases) > 0:
                sel_phase = st.selectbox("Phase", phases['name'].tolist())
                phase_id = phases[phases['name'] == sel_phase]['phase_id'].values[0]
            else:
                st.warning("Créez d'abord une phase.")
                phase_id = None
        with col2:
            mile_title = st.text_input("Titre du jalon", placeholder="Ex: Accord foncier signé")
            mile_date = st.date_input("Date cible", key="mile_date")
        
        if st.button("✅ Ajouter le jalon", type="primary", key="add_mile") and phase_id:
            db.add_roadmap_milestone(conn, phase_id, mile_title, mile_date.isoformat())
            st.success("✅ Jalon ajouté!")
            st.cache_data.clear()
            st.rerun()

# ==================== TAB 4: IMPACT ÉCOSYSTÉMIQUE ====================
with tabs[3]:
    st.markdown('<div class="section-header">🌍 Contrat Écosystémique – Indicateurs d\'Impact</div>', unsafe_allow_html=True)
    
    indicators = load_impact_indicators()
    
    if len(indicators) > 0:
        for domain in ['Social', 'Environnement', 'Economique']:
            domain_df = indicators[indicators['domain'] == domain]
            if len(domain_df) > 0:
                st.markdown(f"### {'👥' if domain == 'Social' else '🌿' if domain == 'Environnement' else '💰'} {domain}")
                
                cols = st.columns(len(domain_df))
                for i, (_, ind) in enumerate(domain_df.iterrows()):
                    pct = min(100, (ind['current_value'] / ind['target_2027'] * 100)) if ind['target_2027'] > 0 else 0
                    with cols[i]:
                        st.markdown(f"""
                        <div class="impact-card">
                            <strong>{ind['name']}</strong><br>
                            <span style="font-size: 1.5rem; font-weight: 800;">{format_number(ind['current_value'])}</span>
                            <span style="color: var(--text-secondary);"> / {format_number(ind['target_2027'])} {ind['unit'] or ''}</span>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: {pct}%;"></div>
                            </div>
                            <small style="color: var(--text-secondary);">{pct:.0f}% de l'objectif 2027</small>
                        </div>
                        """, unsafe_allow_html=True)
    else:
        st.info("📊 Aucun indicateur d'impact défini. Ajoutez-en ci-dessous.")
    
    # Add indicator form
    with st.expander("➕ Ajouter un indicateur d'impact"):
        col1, col2, col3 = st.columns(3)
        with col1:
            ind_domain = st.selectbox("Domaine", ["Social", "Environnement", "Economique"])
            ind_name = st.text_input("Nom de l'indicateur", placeholder="Ex: Emplois créés")
        with col2:
            ind_unit = st.text_input("Unité", placeholder="Ex: personnes, tCO2, %")
            ind_target = st.number_input("Cible 2027", min_value=0.0, step=1.0)
        with col3:
            ind_current = st.number_input("Valeur actuelle", min_value=0.0, step=1.0)
        
        if st.button("✅ Ajouter l'indicateur", type="primary", key="add_ind"):
            if ind_name:
                db.add_impact_indicator(conn, ind_domain, ind_name, ind_unit, ind_target, ind_current)
                st.success("✅ Indicateur ajouté!")
                st.cache_data.clear()
                st.rerun()
    
    # Social Fund Section
    st.markdown('<div class="section-header">💚 Fonds Social (15% des bénéfices)</div>', unsafe_allow_html=True)
    
    fund_summary = load_social_fund()
    if len(fund_summary) > 0:
        c1, c2, c3 = st.columns(3)
        for i, (_, row) in enumerate(fund_summary.iterrows()):
            cat_icons = {'sante': '🏥', 'bourses': '🎓', 'microcredits': '💳'}
            icon = cat_icons.get(row['category'], '💰')
            with [c1, c2, c3][i % 3]:
                st.markdown(f"""
                <div class="kpi">
                    <div class="kpi-icon">{icon}</div>
                    <div class="kpi-label">{row['category'].replace('_', ' ').title()}</div>
                    <div class="kpi-value">{format_number(row['total_amount'])} FCFA</div>
                    <div class="kpi-hint">{row['total_beneficiaries']} bénéficiaires</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Aucune allocation du fonds social enregistrée.")
    
    with st.expander("➕ Enregistrer une allocation"):
        col1, col2, col3 = st.columns(3)
        with col1:
            alloc_cat = st.selectbox("Catégorie", ["sante", "bourses", "microcredits"])
        with col2:
            alloc_amount = st.number_input("Montant (FCFA)", min_value=0, step=1000)
        with col3:
            alloc_benef = st.number_input("Bénéficiaires", min_value=0, step=1)
        
        alloc_notes = st.text_input("Notes", placeholder="Détails de l'allocation...")
        
        if st.button("✅ Enregistrer l'allocation", type="primary", key="add_alloc"):
            db.add_social_fund_allocation(conn, alloc_cat, alloc_amount, alloc_benef, notes=alloc_notes)
            st.success("✅ Allocation enregistrée!")
            st.cache_data.clear()
            st.rerun()

# ==================== TAB 5: MODÈLE ÉCONOMIQUE ====================
with tabs[4]:
    st.markdown('<div class="section-header">💰 Modèle Économique – Répartition des Revenus</div>', unsafe_allow_html=True)
    
    streams = load_revenue_streams()
    
    if len(streams) > 0:
        fig = px.pie(streams, values='target_pct', names='name',
                    color_discrete_sequence=['#059669', '#10b981', '#34d399', '#6ee7b7'],
                    hole=0.4)
        fig = apply_chart_style(fig)
        st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(streams[['name', 'category', 'target_pct', 'current_pct']], 
                    use_container_width=True, hide_index=True)
    else:
        st.info("Aucune source de revenus définie. Voici la répartition type :")
        st.markdown("""
        | Source | % Cible |
        |--------|---------|
        | Vente produits (marchés Libreville) | 45% |
        | Transformation (jus, chips) | 30% |
        | Éco-tourisme (pêche, pédagogique) | 15% |
        | Services (formation, conseil) | 10% |
        """)
    
    with st.expander("➕ Ajouter une source de revenus"):
        col1, col2, col3 = st.columns(3)
        with col1:
            stream_name = st.text_input("Nom", placeholder="Ex: Vente produits")
        with col2:
            stream_cat = st.selectbox("Catégorie", ["produits", "transformation", "tourisme", "services"])
        with col3:
            stream_pct = st.number_input("% Cible", min_value=0.0, max_value=100.0, step=5.0)
        
        if st.button("✅ Ajouter", type="primary", key="add_stream"):
            if stream_name:
                db.add_revenue_stream(conn, stream_name, stream_cat, stream_pct)
                st.success("✅ Source ajoutée!")
                st.cache_data.clear()
                st.rerun()
    
    # Financial targets by year
    st.markdown('<div class="section-header">📈 Objectifs Financiers par Année</div>', unsafe_allow_html=True)
    
    fin_targets = load_financial_targets()
    if len(fin_targets) > 0:
        st.dataframe(fin_targets, use_container_width=True, hide_index=True)
    
    with st.expander("➕ Définir objectifs pour une année"):
        col1, col2 = st.columns(2)
        with col1:
            target_year = st.number_input("Année", min_value=2024, max_value=2035, value=2025, step=1)
            banane_ca = st.number_input("CA Banane (FCFA)", min_value=0, step=100000)
            taro_ca = st.number_input("CA Taro (FCFA)", min_value=0, step=100000)
        with col2:
            api_ca = st.number_input("CA Apiculture (FCFA)", min_value=0, step=100000)
            cuni_ca = st.number_input("CA Cuniculture (FCFA)", min_value=0, step=100000)
            vivo_ca = st.number_input("CA Vivoplants (FCFA)", min_value=0, step=100000)
        
        if st.button("✅ Enregistrer les objectifs", type="primary", key="add_fin"):
            total = banane_ca + taro_ca + api_ca + cuni_ca + vivo_ca
            db.upsert_financial_target(conn, target_year, 
                                       banane_ca=banane_ca, taro_ca=taro_ca,
                                       apiculture_ca=api_ca, cuniculture_ca=cuni_ca,
                                       vivoplants_ca=vivo_ca, total_target=total)
            st.success("✅ Objectifs enregistrés!")
            st.cache_data.clear()
            st.rerun()

# ==================== TAB 6: GOUVERNANCE ====================
with tabs[5]:
    st.markdown('<div class="section-header">👥 Comité de Pilotage</div>', unsafe_allow_html=True)
    
    members = load_committee()
    
    if len(members) > 0:
        role_icons = {
            'comite_pilotage': '🎯',
            'chef_village': '👑',
            'agriculteur_elu': '🌾',
            'coordinateur': '📋'
        }
        
        for _, m in members.iterrows():
            icon = role_icons.get(m['role'], '👤')
            st.markdown(f"""
            <div class="filiere-card" style="margin-bottom: 12px;">
                <div class="filiere-title">{icon} {m['name'] or 'Non défini'}</div>
                <small>Rôle: <strong>{m['role'].replace('_', ' ').title()}</strong></small><br>
                <small style="color: var(--text-secondary);">Contact: {m['contact'] or '—'} | Élu le: {m['elected_date'] or '—'}</small>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("👥 Aucun membre du comité enregistré.")
    
    with st.expander("➕ Ajouter un membre"):
        col1, col2 = st.columns(2)
        with col1:
            mem_name = st.text_input("Nom complet", placeholder="Ex: Jean Ahouansou")
            mem_role = st.selectbox("Rôle", ["comite_pilotage", "chef_village", "agriculteur_elu", "coordinateur"])
        with col2:
            mem_contact = st.text_input("Contact", placeholder="Ex: +229 XX XX XX XX")
            mem_date = st.date_input("Date d'élection", key="mem_date")
        
        if st.button("✅ Ajouter le membre", type="primary", key="add_mem"):
            if mem_name:
                db.add_committee_member(conn, mem_role, mem_name, mem_contact, mem_date.isoformat())
                st.success("✅ Membre ajouté!")
                st.cache_data.clear()
                st.rerun()
    
    # Meetings
    st.markdown('<div class="section-header">📅 Réunions du Comité</div>', unsafe_allow_html=True)
    
    meetings = db.get_committee_meetings(conn)
    if len(meetings) > 0:
        st.dataframe(meetings[['date', 'attendees', 'decisions', 'next_actions']], 
                    use_container_width=True, hide_index=True)
    else:
        st.info("Aucune réunion enregistrée.")
    
    with st.expander("➕ Enregistrer une réunion"):
        meet_date = st.date_input("Date de la réunion", key="meet_date")
        meet_att = st.text_input("Participants", placeholder="Ex: Jean, Marie, Pierre...")
        meet_dec = st.text_area("Décisions prises", placeholder="Résumé des décisions...")
        meet_next = st.text_area("Prochaines actions", placeholder="Actions à mener...")
        
        if st.button("✅ Enregistrer la réunion", type="primary", key="add_meet"):
            db.add_committee_meeting(conn, meet_date.isoformat(), meet_att, meet_dec, meet_next)
            st.success("✅ Réunion enregistrée!")
            st.rerun()

# ==================== TAB 7: CONFIGURATION ====================
with tabs[6]:
    st.markdown('<div class="section-header">⚙️ Configuration & Administration</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔄 Actions Rapides")
        
        if st.button("🔄 Actualiser les données", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        if st.button("📊 Réinitialiser indicateurs par défaut", use_container_width=True):
            # Add default impact indicators
            defaults = [
                ("Social", "Emplois créés", "directs", 35, 0),
                ("Social", "Femmes formées", "% bénéficiaires", 60, 0),
                ("Social", "Déchets recyclés", "%", 95, 0),
                ("Environnement", "Émissions évitées", "tCO2/an", 120, 0),
                ("Economique", "Autonomie alimentaire", "% village", 70, 0),
            ]
            for d, n, u, t, c in defaults:
                db.add_impact_indicator(conn, d, n, u, t, c)
            st.success("✅ Indicateurs par défaut créés!")
            st.cache_data.clear()
            st.rerun()
        
        if st.button("📋 Créer feuille de route par défaut", use_container_width=True):
            phases_default = [
                ("Préparation", "completed", "2023-10-01", "2024-11-30", "Accord foncier, formation agriculteurs"),
                ("Lancement", "in_progress", "2025-01-01", "2025-03-31", "Mise en culture 0.8 ha, installation ruches"),
                ("Maturité", "pending", "2026-05-01", "2026-07-31", "Couverture 40% besoins alimentaires"),
            ]
            for name, status, start, end, desc in phases_default:
                db.add_roadmap_phase(conn, name, status, start, end, desc)
            st.success("✅ Feuille de route créée!")
            st.cache_data.clear()
            st.rerun()
        
        if st.button("💰 Créer modèle économique par défaut", use_container_width=True):
            streams_default = [
                ("Vente produits (marchés)", "produits", 45),
                ("Transformation", "transformation", 30),
                ("Éco-tourisme", "tourisme", 15),
                ("Services (formation)", "services", 10),
            ]
            for name, cat, pct in streams_default:
                db.add_revenue_stream(conn, name, cat, pct)
            st.success("✅ Sources de revenus créées!")
            st.cache_data.clear()
            st.rerun()

        st.markdown("---")
        st.subheader("🎲 Données de Démonstration")
        if st.button("🚀 Générer données fictives (Seed Data)", type="primary", use_container_width=True):
            # 1. Agriculture
            pid1 = db.create_asset(conn, "plot", "Parcelle Lac 1", crop_type="Banane", area_m2=1200, location="Zone A")
            pid2 = db.create_asset(conn, "plot", "Parcelle Sud", crop_type="Taro", area_m2=800, location="Zone B")
            
            # 2. Sensor Readings (history)
            base_time = datetime.now()
            for i in range(10):
                # Plot 1
                db.add_sensor_reading(conn, pid1, base_time, 
                                     light=45000+i*100, air_temp=28+i*0.2, air_humidity=65-i,
                                     soil_temp=24, soil_moisture=80-i*2, soil_ph=6.5, fertility=1200, battery=90)
                # Plot 2
                db.add_sensor_reading(conn, pid2, base_time,
                                     light=42000+i*50, air_temp=27+i*0.1, air_humidity=70-i,
                                     soil_temp=23, soil_moisture=85-i*1, soil_ph=6.2, fertility=1100, battery=88)

            # 3. Livestock
            db.create_asset(conn, "hive", "Ruche Reine 1", location="Verger", notes="Forte activité")
            db.create_asset(conn, "hive", "Ruche Reine 2", location="Verger", notes="A surveiller")
            db.create_asset(conn, "rabbitry", "Clapier A", location="Hangar Principal", notes="5 Mères, 30 lapereaux")
            
            # 4. Vivoplants
            db.create_asset(conn, "vivoplant", "Lot PIF 001", crop_type="Banane Plantain", notes="Stade sevrage")
            
            st.success("✅ Données fictives générées avec succès !")
            st.cache_data.clear()
            st.rerun()

        st.markdown("---")
        st.error("🚨 Zone de Danger")
        if st.button("🗑️ TOUT EFFACER (Reset Database)", type="secondary", use_container_width=True):
            tables = ["assets", "sensor_readings", "field_observations", "hive_inspections", 
                     "rabbit_logs", "vivoplant_logs", "revenue_streams", "roadmap_phases", 
                     "roadmap_milestones", "impact_indicators", "social_fund", 
                     "committee_members", "committee_meetings"]
            cur = conn.cursor()
            for t in tables:
                cur.execute(f"DELETE FROM {t}")
            conn.commit()
            st.warning("⚠️ Toutes les données ont été effacées.")
            st.cache_data.clear()
            st.rerun()
    
    with col2:
        st.subheader("📊 Statistiques Base de Données")
        
        stats_data = {
            "Table": ["Assets", "Sensor Readings", "Hive Inspections", "Rabbit Logs", "Vivoplant Logs",
                     "Revenue Streams", "Roadmap Phases", "Impact Indicators", "Committee Members"],
            "Entrées": [
                len(db.get_plots(conn)),
                len(db.get_sensor_readings(conn)),
                len(db.get_hive_inspections(conn)),
                len(db.get_rabbit_logs(conn)),
                len(db.get_vivoplant_logs(conn)),
                len(db.get_revenue_streams(conn)),
                len(db.get_roadmap_phases(conn)),
                len(db.get_impact_indicators(conn)),
                len(db.get_committee_members(conn)),
            ]
        }
        st.dataframe(pd.DataFrame(stats_data), use_container_width=True, hide_index=True)

# Sidebar navigation
st.sidebar.markdown("---")
st.sidebar.subheader("🌱 Centre Agroécologique")
st.sidebar.info("1er Centre Data-Driven du Gabon")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: var(--text-secondary); font-size: 0.85rem; padding: 16px 0;">
    🌱 CAYF Monitoring • Développé par <strong>DURABILIS & CO</strong> • 1er Centre Agroécologique Data-Driven du Gabon
</div>
""", unsafe_allow_html=True)
