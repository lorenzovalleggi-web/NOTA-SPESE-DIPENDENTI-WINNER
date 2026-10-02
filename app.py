import streamlit as st
import pandas as pd
from datetime import date
from PIL import Image
import os
import json

# Configurazione della pagina
st.set_page_config(page_title="Nota Spese - Winner", layout="wide")

# --- INTESTAZIONE CON LOGO E DATI AZIENDALI COMPLETI ---
col_logo, col_intestazione = st.columns([1, 3])

with col_logo:
    for logo_name in ["logo.jpg", "logo.png", "logo.jpeg"]:
        if os.path.exists(logo_name):
            try:
                img = Image.open(logo_name)
                st.image(img, width=220)
                break
            except Exception:
                pass

with col_intestazione:
    st.title("📄 NOTA SPESE DIPENDENTI E COLLABORATORI")
    st.markdown("""
    **WINNER SOCIETÀ COOPERATIVA**  
    *Sede Legale / Operativa:* Civitavecchia (RM)  
    *P.IVA / Codice Fiscale:* 01234567890  
    *Telefono:* 0766 505 197 | *Email:* info@winnercoop.it
    """)

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

if "rifornimenti_dkv" not in st.session_state:
    st.session_state.rifornimenti_dkv = pd.DataFrame([
        {"Data": date.today(), "Importo (€)": 0.0, "Litri": 0.0, "Distributore / Note": "Stazione DKV"}
    ])

if "allegati_dkv_list" not in st.session_state:
    st.session_state.allegati_dkv_list = []

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

# --- TABELLA EDITABILE SPESE ---
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
    if st.button("💾 Salva Modifiche Spese", type="primary"):
        st.session_state.dati_spese_v2 = df_edit.drop(columns=["Importo_Km_A", "Importo_Km_B"], errors="ignore").copy()
        st.success("Modifiche salvate nella sessione!")

st.divider()

# --- SEZIONE RIFORNIMENTI CARTA DKV E TOTALE GIORNALIERO ---
st.subheader("⛽ Registrazione Rifornimenti Carta DKV & Totali del Giorno")

df_rifornimenti = st.data_editor(
    st.session_state.rifornimenti_dkv,
    num_rows="dynamic",
    use_container_width=True,
    key="editor_rifornimenti",
    column_config={
        "Data": st.column_config.DateColumn("Data Rifornimento", format="DD/MM/YYYY"),
        "Importo (€)": st.column_config.NumberColumn("Importo Speso (€)", min_value=0.0, format="%.2f €"),
        "Litri": st.column_config.NumberColumn("Litri Carburante", min_value=0.0, format="%.2f L"),
        "Distributore / Note": st.column_config.TextColumn("Distributore / Note"),
    }
)

st.session_state.rifornimenti_dkv = df_rifornimenti.copy()

# Calcolo totale giorno specifico
if not df_rifornimenti.empty:
    col_giorno, col_risultato = st.columns([2, 2])
    with col_giorno:
        giorno_selezionato = st.date_input("Seleziona il giorno per vedere il totale speso:", date.today())
    
    with col_risultato:
        df_rifornimenti["Data_dt"] = pd.to_datetime(df_rifornimenti["Data"]).dt.date
        totale_giorno = df_rifornimenti[df_rifornimenti["Data_dt"] == giorno_selezionato]["Importo (€)"].sum()
        st.metric(f"Totale DKV del {giorno_selezionato.strftime('%d/%m/%Y')}", f"€ {totale_giorno:.2f}")

st.divider()

# --- SEZIONE ALLEGATI CON RIMOZIONE E REINSERIMENTO FOTO ---
st.subheader("🧾 Gestione Foto Scontrini Cartacei / DKV")
st.info("Carica le foto degli scontrini. Puoi eliminarle singolarmente e caricare nuove immagini in qualsiasi momento.")

nuovi_file = st.file_uploader(
    "📎 Aggiungi Foto/Scontrini (JPG, PNG, PDF)",
    type=["jpg", "jpeg", "png", "pdf"],
    accept_multiple_files=True,
    key="nuovi_scontrini_uploader"
)

if nuovi_file:
    for f in nuovi_file:
        if f.name not in [x["name"] for x in st.session_state.allegati_dkv_list]:
            st.session_state.allegati_dkv_list.append({"name": f.name, "file": f})

# MOSTRA E ELIMINA FOTO
if st.session_state.allegati_dkv_list:
    st.write(f"**Scontrini allegati in memoria:** {len(st.session_state.allegati_dkv_list)}")
    
    cols_foto = st.columns(min(len(st.session_state.allegati_dkv_list), 4))
    
    indici_da_rimuovere = []
    for idx, item in enumerate(st.session_state.allegati_dkv_list):
        col_curr = cols_foto[idx % 4]
        with col_curr:
            file_obj = item["file"]
            file_name = item["name"]
            
            if file_obj.type.startswith("image"):
                st.image(Image.open(file_obj), caption=file_name, use_container_width=True)
            else:
                st.success(f"📄 PDF: {file_name}")
            
            if st.button(f"🗑️ Rimuovi", key=f"del_{idx}_{file_name}"):
                indici_da_rimuovere.append(idx)
    
    if indici_da_rimuovere:
        for index in sorted(indici_da_rimuovere, reverse=True):
            st.session_state.allegati_dkv_list.pop(index)
        st.rerun()

st.divider()

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

    st.subheader("📊 RIEPILOGO TOTALE PAGAMENTO (PAGINA 2)")

    # --- TOTALI RIMBORSI ---
    st.write("### Totali Rimborsi")
    c_tot1, c_tot2, c_tot3 = st.columns(3)
    with c_tot1:
        st.metric("TOTALE Rimb. Chilometrico", f"€ {totale_rimborso_chilometrico:.2f}")
    with c_tot2:
        st.metric("TOTALE Altri Rimborsi", f"€ {totale_altri_rimborsi:.2f}")
    with c_tot3:
        st.metric("TOTALE GENERALE PAGATO", f"€ {totale_generale_pagato:.2f}")

    st.divider()

    # --- SEZIONE AUTORIZZAZIONI E FIRME ---
    st.subheader("✍️ Autorizzazioni e Firme")
    col_dichiarante, col_amministratore = st.columns(2)

    with col_dichiarante:
        st.markdown("#### 1. Il Dichiarante")
        st.text_input("Nome e Cognome Dichiarante", f"{nome.upper()} {cognome.upper()}", key="nome_dichiarante")
        
        firma_dichiarante = st.file_uploader(
            "📎 Allegato Firma Dichiarante (PNG/JPG/PDF)", 
            type=["png", "jpg", "jpeg", "pdf"],
            key="firma_dichiarante_file"
        )
        if firma_dichiarante is not None:
            if firma_dichiarante.type.startswith("image"):
                st.image(Image.open(firma_dichiarante), caption="Firma Dichiarante Allegata", width=200)
            else:
                st.success(f"File allegato: {firma_dichiarante.name}")

    with col_amministratore:
        st.markdown("#### 2. L'Amministratore")
        st.caption("Per Autorizzazione Incarico")
        
        timbro_firma_admin = st.file_uploader(
            "📎 Allegato Timbro e Firma Amministratore (PNG/JPG/PDF)", 
            type=["png", "jpg", "jpeg", "pdf"],
            key="timbro_admin_file"
        )
        if timbro_firma_admin is not None:
            if timbro_firma_admin.type.startswith("image"):
                st.image(Image.open(timbro_firma_admin), caption="Timbro e Firma Amministratore Allegati", width=200)
            else:
                st.success(f"File allegato: {timbro_firma_admin.name}")

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
