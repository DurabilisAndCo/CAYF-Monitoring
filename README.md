# Monitoring Multi-Activités (V3)

App Streamlit pour le monitoring **Agriculture (Banane/Taro/PIF)** + **Apiculture (Ruches)** + **Cunicululture (Lapins)** + **Vivoplants**,
avec **tableau de bord récap** et **recommandations automatisées (règles)**.

## Lancer en local
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Déployer sur Streamlit Community Cloud
- Pousser ce dossier sur GitHub
- Streamlit Cloud: New app → repo → `app.py` → Deploy

## Données
SQLite local: `monitoring_agri.db` (créé automatiquement).
Pour un usage multi-utilisateurs durable, migrer vers Postgres (Supabase/Neon).
