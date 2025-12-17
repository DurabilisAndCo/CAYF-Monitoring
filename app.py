import streamlit as st
import pandas as pd

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="CAFY – Data Monitoring",
    layout="wide",
    page_icon="🌱"
)

# --------------------------------------------------
# HEADER BRANDING
# --------------------------------------------------
def brand_header():
    st.markdown("""
    <style>
      .cafy-header {
        padding: 16px 20px;
        border-radius: 16px;
        background: linear-gradient(90deg, #2d3381, #2c6ea1, #44a0c9);
        margin-bottom: 18px;
      }
      .cafy-title {
        font-size: 22px;
        font-weight: 800;
        color: white;
        margin: 0;
      }
      .cafy-sub {
        font-size: 13px;
        color: rgba(255,255,255,0.95);
        margin-top: 4px;
      }
      .cafy-sub2 {
        font-size: 12px;
        color: rgba(255,255,255,0.85);
      }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 6, 1])

    with col1:
        st.image("assets/cayf.jpg", use_container_width=True)

    with col2:
        st.markdown("""
        <div class="cafy-header">
          <p class="cafy-title">CAFY – Data Monitoring Data · développé par DURABILIS &amp; CO</p>
          <p class="cafy-sub">CENTRE AGROÉCOLOGIQUE INNOVANT DE N'ZAMALIGUÉ<br>
          porté par la Coopérative Agricole Young Foundation</p>
          <p class="cafy-sub2">Localisation : N'zamaligué, Komo-Mondah, Gabon</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.image("assets/durabilis.png", use_container_width=True)

brand_header()

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------
st.sidebar.title("🧭 Navigation")
page = st.sidebar.radio(
    "Choisir une page",
    ["🏠 Tableau de bord", "📊 Objectifs & KPI", "📥 Export"]
)

st.sidebar.markdown("---")
period = st.sidebar.slider("Période d'analyse (jours)", 30, 365, 180)

# --------------------------------------------------
# MOCK DATA (MVP – à remplacer plus tard)
# --------------------------------------------------
banana_blocks = 1
taro_blocks = 1
vivoplant_lots = 0
hives_count = 2
rabbit_cycles = 0

# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------
if page == "🏠 Tableau de bord":
    st.subheader("📊 Tableau de bord – Vue d’ensemble")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("🍌 Banane (blocs)", banana_blocks)
    c2.metric("🌿 Taro (blocs)", taro_blocks)
    c3.metric("🌱 Vivoplants (lots)", vivoplant_lots)
    c4.metric("🐝 Ruches", hives_count)
    c5.metric("🐇 Lapins (cycles)", rabbit_cycles)

    st.markdown("---")

    st.subheader("🤖 Recommandations automatisées (règles)")

    recos = []

    if banana_blocks > 0:
        recos.append("🍌 Banane : vérifier humidité du sol et pression maladies fongiques.")
    if taro_blocks > 0:
        recos.append("🌿 Taro : sol humide requis – surveiller drainage.")
    if vivoplant_lots == 0:
        recos.append("🌱 Vivoplants : prévoir lancement des lots PIF.")
    if hives_count < 5:
        recos.append("🐝 Apiculture : potentiel d’extension des ruches en 2026.")
    if rabbit_cycles == 0:
        recos.append("🐇 Cunicul﻿ture : initialiser le suivi des cycles de reproduction.")

    if recos:
        for r in recos:
            st.success(r)
    else:
        st.info("Aucune recommandation critique pour la période sélectionnée.")

# --------------------------------------------------
# OBJECTIFS
# --------------------------------------------------
elif page == "📊 Objectifs & KPI":
    st.subheader("🎯 Objectifs chiffrés (pilotage & bailleurs)")

    col1, col2 = st.columns(2)

    with col1:
        st.number_input("CA Banane (FCFA/an)", value=33320000)
        st.number_input("CA Taro (FCFA/an)", value=5000000)
        st.number_input("Vivoplants / cycle", value=1000)

    with col2:
        st.number_input("Ruches cible", value=2)
        st.number_input("Lapins / cycle", value=540)
        st.slider("Pertes tolérées (%)", 0, 30, 10)

    st.success("Objectifs configurés (MVP – stockage à venir).")

# --------------------------------------------------
# EXPORT
# --------------------------------------------------
elif page == "📥 Export":
    st.subheader("📥 Export des données (CSV)")

    st.info("Les exports seront disponibles dès la saisie des données terrain.")
    st.download_button(
        "Télécharger un exemple CSV",
        data="activité,valeur\nbanane,33320000",
        file_name="cafy_export_exemple.csv",
        mime="text/csv"
    )

# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.markdown("---")
st.caption("🌍 CAFY Monitoring · Développé par DURABILIS & CO · Version V4")
