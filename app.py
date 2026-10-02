import streamlit as st
import pandas as pd
from datetime import date
from PIL import Image
import os
import json

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
    nome = st.text_input("Nome", st.session_state.get("nome_user", "LORENZO"), key="nome_input")
    st.session_state["nome_user"] = nome
with col2:
    cognome = st.text_input("Cognome", st.session_state.get("cognome_user", "VALLEGGI"), key="cognome_input")
    st.session_state["cognome_user"] = cognome
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

def crea_df_iniziale():
    return pd.DataFrame([
        {
            "Data": date.today(),
            "Comune": "Come da Planning Allegato",
            "Coordinatore di Zona": "",
            "Km_A": 143,
            "Autostrade_A": 7.40,
            "Vitto_A": 0.0,
            "Varie_A": 0.0,
            "Km_B": 0,
            "Autostrade_B": 0.0,
            "Vitto_B": 0.0,
            "Varie_B": 0.0
        }
    ])

if "dati_spese_v2" not in st.session_state:
    st.session_state.dati_spese_v2 = crea_df_iniziale()

# --- CARICAMENTO BOZZA ---
with st.expander("📁 Carica una Bozza di Lavoro Salvata"):
    uploaded_file = st.file_uploader("Carica file bozza (.json o .csv)", type=["json", "csv"])
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".json"):
                data_loaded = json.load(uploaded_file)
                st.session_state.dati_spese_v2 = pd.DataFrame(data_loaded)
            else:
                st.session_state.dati_spese_v2 = pd.read_csv(uploaded_file)
            st.success("Bozza caricata con successo!")
        except Exception:
            st.error("Errore nel caricamento del file.")

st.subheader("📋 Inserimento Voci di Spesa")

# Preparo i dati aggiungendo il calcolo dinamico per gli importi chilometrici
df_display = st.session_state.dati_spese_v2.copy()
df_display["Importo_Km_A"] = pd.to_numeric(df_display.get("Km_A", 0), errors='coerce').fillna(0) * costo_km_a
df_display["Importo_Km_B"] = pd.to_numeric(df_display.get("Km_B", 0), errors='coerce').fillna(0) * costo_km_b

# --- TABELLA EDITABILE ---
df_edit = st.data_editor(
    df_display,
    num_rows="dynamic",
    use_container_width=True,
    key="editor_spese",
    column_config={
        "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
        "Comune": st.column_config.TextColumn("Comune / Note"),
        "Coordinatore di Zona": st.column_config.SelectboxColumn("Coordinatore di Zona", options=coordinatori),
        "Km_A": st.column_config.NumberColumn("Km Percorsi (0,25 €)", min_value=0, step=1),
        "Importo_Km_A": st.column_config.NumberColumn("Tot. Rimborso Km A (€)", format="%.2f €", disabled=True),
        "Autostrade_A": st.column_config.NumberColumn("Autostrade A (€)", min_value=0.0, format="%.2f €"),
        "Vitto_A": st.column_config.NumberColumn("Vitto A (€)", min_value=0.0, format="%.2f €"),
        "Varie_A": st.column_config.NumberColumn("Varie A (€)", min_value=0.0, format="%.2f €"),
        "Km_B": st.column_config.NumberColumn("Km Percorsi (0,20 €)", min_value=0, step=1),
        "Importo_Km_B": st.column_config.NumberColumn("Tot. Rimborso Km B (€)", format="%.2f €", disabled=True),
        "Autostrade_B": st.column_config.NumberColumn("Autostrade B (€)", min_value=0.0, format="%.2f €"),
        "Vitto_B": st.column_config.NumberColumn("Vitto B (€)", min_value=0.0, format="%.2f €"),
        "Varie_B": st.column_config.NumberColumn("Varie B (€)", min_value=0.0, format="%.2f €"),
    }
)

# Salvo automaticamente nella sessione senza le colonne calcolate temporanee
st.session_state.dati_spese_v2 = df_edit.drop(columns=["Importo_Km_A", "Importo_Km_B"], errors="ignore").copy()

# --- PULSANTE DI SALVATAGGIO MANUALE ---
col_salva1, col_salva2 = st.columns([1, 4])
with col_salva1:
    if st.button("💾 Salva Modifiche", type="primary"):
        st.session_state.dati_spese_v2 = df_edit.drop(columns=["Importo_Km_A", "Importo_Km_B"], errors="ignore").copy()
        st.success("Modifiche salvate nella sessione!")

# --- CALCOLI AUTOMATICI (RIEPILOGO PAGINA 2) ---
df_finale = df_edit.copy()

if not df_finale.empty:
    km_a_sum = pd.to_numeric(df_finale.get("Km_A", 0), errors='coerce').fillna(0).sum()
    km_b_sum = pd.to_numeric(df_finale.get("Km_B", 0), errors='coerce').fillna(0).sum()
    
    tot_rimborso_km_a = km_a_sum * costo_km_a
    tot_rimborso_km_b = km_b_sum * costo_km_b
    totale_rimborso_chilometrico = tot_rimborso_km_a + tot_rimborso_km_b

    auto_a = pd.to_numeric(df_finale.get("Autostrade_A", 0), errors='coerce').fillna(0).sum()
    auto_b = pd.to_numeric(df_finale.get("Autostrade_B", 0), errors='coerce').fillna(0).sum()
    vitto_a = pd.to_numeric(df_finale.get("Vitto_A", 0), errors='coerce').fillna(0).sum()
    vitto_b = pd.to_numeric(df_finale.get("Vitto_B", 0), errors='coerce').fillna(0).sum()
    varie_a = pd.to_numeric(df_finale.get("Varie_A", 0), errors='coerce').fillna(0).sum()
    varie_b = pd.to_numeric(df_finale.get("Varie_B", 0), errors='coerce').fillna(0).sum()

    totale_altri_rimborsi = auto_a + auto_b + vitto_a + vitto_b + varie_a + varie_b
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

    # --- ESPORTAZIONE ---
    st.divider()
    btn_col1, btn_col2 = st.columns(2)
    
    with btn_col1:
        csv = df_finale.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Scarica Nota Spese Finale (CSV)",
            data=csv,
            file_name=f"Nota_Spese_Pag2_{cognome}.csv",
            mime="text/csv"
        )
    
    with btn_col2:
        json_data = df_finale.to_json(orient="records", date_format="iso")
        st.download_button(
            label="💾 Scarica File Bozza (.json)",
            data=json_data,
            file_name=f"Bozza_Nota_Spese_{cognome}.json",
            mime="application/json"
        )
