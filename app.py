import streamlit as st
import pandas as pd
from datetime import date
from PIL import Image
import os

# Configurazione della pagina
st.set_page_config(page_title="Nota Spese - Winner", layout="wide")

# --- INTESTAZIONE CON LOGO E RAGIONE SOCIALE ---
col_logo, col_titolo = st.columns([1, 4])

with col_logo:
    for logo_name in ["logo.jpg", "logo.png", "logo.jpeg"]:
        if os.path.exists(logo_name):
            try:
                img = Image.open(logo_name)
                st.image(img, width=200)
                break
            except Exception:
                pass

with col_titolo:
    st.title("📄 Nota Spese Dipendenti")
    st.caption("Winner Società Cooperativa | Tel: 0766 505 197")

st.divider()

# --- ANAGRAFICA DIPENDENTE ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    nome = st.text_input("Nome", "LORENZO")
with col2:
    cognome = st.text_input("Cognome", "VALLEGGI")
with col3:
    costo_km_a = st.number_input("Rimborsabilità Km Cat. A (€)", value=0.25, disabled=True)
with col4:
    costo_km_b = st.number_input("Rimborsabilità Km Cat. B (€)", value=0.20, disabled=True)

st.divider()

# --- LISTA COORDINATORI ---
coordinatori = [
    "",
    "Coordinatore Bruscolini",
    "Coordinatore Calzetta",
    "Coordinatore Casaburi",
    "Coordinatore Ceniti",
    "Coordinatore Ledda",
    "Coordinatore Mazzoleni",
    "Coordinatore Migliaccio",
    "Coordinatore Piccinetti",
    "Coordinatore Vendemini",
    "Coordinatore Stella"
]

# --- TABELLA INIZIALE ---
if "dati_spese" not in st.session_state:
    st.session_state.dati_spese = pd.DataFrame([
        {
            "Data": date.today(),
            "Comune / Note": "Come da Planning Allegato",
            "Coordinatore di Zona": "",
            "Km Percorsi (0,25 €)": 143,
            "Importi Autostradali": 7.40,
            "Vitto": 0.0,
            "Varie": 0.0,
            "Km Percorsi (0,20 €)": 0,
            "Importi Autostradali B": 0.0,
            "Vitto B": 0.0,
            "Varie B": 0.0
        }
    ])

st.subheader("📋 Inserimento Voci di Spesa")

# --- TABELLA EDITABILE ---
df_edit = st.data_editor(
    st.session_state.dati_spese,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
        "Comune / Note": st.column_config.TextColumn("Comune / Planning"),
        "Coordinatore di Zona": st.column_config.SelectboxColumn("Coordinatore di Zona", options=coordinatori),
        "Km Percorsi (0,25 €)": st.column_config.NumberColumn("Km (0,25 €)", min_value=0, step=1),
        "Importi Autostradali": st.column_config.NumberColumn("Autostrade (€)", min_value=0.0, format="%.2f €"),
        "Vitto": st.column_config.NumberColumn("Vitto (€)", min_value=0.0, format="%.2f €"),
        "Varie": st.column_config.NumberColumn("Varie (€)", min_value=0.0, format="%.2f €"),
        "Km Percorsi (0,20 €)": st.column_config.NumberColumn("Km (0,20 €)", min_value=0.0, step=1),
        "Importi Autostradali B": st.column_config.NumberColumn("Autostrade B (€)", min_value=0.0, format="%.2f €"),
        "Vitto B": st.column_config.NumberColumn("Vitto B (€)", min_value=0.0, format="%.2f €"),
        "Varie B": st.column_config.NumberColumn("Varie B (€)", min_value=0.0, format="%.2f €"),
    }
)

# --- CALCOLI AUTOMATICI (RIEPILOGO PAGINA 2) ---
df_finale = df_edit.copy()

if not df_finale.empty:
    # Calcolo rimborsi chilometrici
    tot_rimborso_km_a = df_finale["Km Percorsi (0,25 €)"].fillna(0).sum() * costo_km_a
    tot_rimborso_km_b = df_finale["Km Percorsi (0,20 €)"].fillna(0).sum() * costo_km_b
    totale_rimborso_chilometrico = tot_rimborso_km_a + tot_rimborso_km_b

    # Calcolo altri rimborsi
    tot_autostrade = df_finale["Importi Autostradali"].fillna(0).sum() + df_finale["Importi Autostradali B"].fillna(0).sum()
    tot_vitto = df_finale["Vitto"].fillna(0).sum() + df_finale["Vitto B"].fillna(0).sum()
    tot_varie = df_finale["Varie"].fillna(0).sum() + df_finale["Varie B"].fillna(0).sum()
    totale_altri_rimborsi = tot_autostrade + tot_vitto + tot_varie

    # Totale generale
    totale_generale_pagato = totale_rimborso_chilometrico + totale_altri_rimborsi

    st.divider()
    st.subheader("📊 RIEPILOGO TOTALE PAGAMENTO (PAGINA 2)")

    c1, c2 = st.columns(2)

    with c1:
        st.write("### Totali Rimborsi")
        st.metric("TOTALE Rimb. Chilometrico", f"€ {totale_rimborso_chilometrico:.2f}")
        st.metric("TOTALE Altri Rimborsi", f"€ {totale_altri_rimborsi:.2f}")
        st.subheader(f"TOTALE GENERALE PAGATO: € {totale_generale_pagato:.2f}")

    with c2:
        st.write("### Autorizzazioni e Firme")
        st.text_input("Il Dichiarante", f"{nome.upper()} {cognome.upper()}")
        st.caption("Timbro e Firma (L'Amministratore) - Per Autorizzazione Incarico")

    # --- ESPORTAZIONE CSV ---
    st.divider()
    csv = df_finale.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Scarica Nota Spese Completata (CSV)",
        data=csv,
        file_name=f"Nota_Spese_Pag2_{cognome}_{date.today().strftime('%B%Y')}.csv",
        mime="text/csv"
    )
