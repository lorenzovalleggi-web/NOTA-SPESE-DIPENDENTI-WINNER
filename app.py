import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Nota Spese Dipendenti", layout="wide")

st.title("📄 Nota Spese Dipendenti")

col1, col2, col3 = st.columns(3)
with col1:
    nome = st.text_input("Nome", "LORENZO")
with col2:
    cognome = st.text_input("Cognome", "VALLEGGI")
with col3:
    costo_km = st.number_input("Rimborsabilita Km (€)", value=0.25, step=0.01)

st.divider()

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

if "dati_spese" not in st.session_state:
    st.session_state.dati_spese = pd.DataFrame([
        {"Data": date.today(), "Comune": "", "Coordinatore di Zona": "", "Tipologia Ispettore": "PISA", "Km": 0, "Autostrade": 0.0, "Vitto": 0.0, "Varie": 0.0}
    ])

st.subheader("Inserisci o modifica le voci di spesa")

df_edit = st.data_editor(
    st.session_state.dati_spese,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
        "Comune": st.column_config.TextColumn("Comune"),
        "Coordinatore di Zona": st.column_config.SelectboxColumn("Coordinatore di Zona", options=coordinatori),
        "Tipologia Ispettore": st.column_config.TextColumn("Tipologia Ispettore"),
        "Km": st.column_config.NumberColumn("Km", min_value=0, step=1),
        "Autostrade": st.column_config.NumberColumn("Autostrade (€)", min_value=0.0, format="%.2f €"),
        "Vitto": st.column_config.NumberColumn("Vitto (€)", min_value=0.0, format="%.2f €"),
        "Varie": st.column_config.NumberColumn("Varie (€)", min_value=0.0, format="%.2f €"),
    }
)

df_finale = df_edit.copy()

if not df_finale.empty:
    df_finale["Nome Cognome"] = f"{nome.upper()} {cognome.upper()}"
    df_finale["Tot. Km/€"] = df_finale["Km"].fillna(0) * costo_km
    df_finale["Totale €"] = (
        df_finale["Tot. Km/€"] + 
        df_finale["Autostrade"].fillna(0) + 
        df_finale["Vitto"].fillna(0) + 
        df_finale["Varie"].fillna(0)
    )

    ordine = ["Data", "Comune", "Coordinatore di Zona", "Nome Cognome", "Tipologia Ispettore", "Km", "Tot. Km/€", "Autostrade", "Vitto", "Varie", "Totale €"]
    df_finale = df_finale.reindex(columns=ordine)

    st.divider()
    totale_generale = df_finale["Totale €"].sum()
    totale_km = df_finale["Km"].sum()

    m1, m2 = st.columns(2)
    m1.metric("Totale Chilometri", f"{totale_km:.0f} km")
    m2.metric("TOTALE DA RIMBORSARE", f"€ {totale_generale:.2f}")

    st.divider()
    csv = df_finale.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Scarica Nota Spese in CSV",
        data=csv,
        file_name=f"Nota_Spese_{cognome}.csv",
        mime="text/csv"
    )
