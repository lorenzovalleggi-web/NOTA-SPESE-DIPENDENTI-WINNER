import streamlit as st
import pandas as pd
from datetime import date
from PIL import Image
import os
import json
import base64
import io

# 1. Configurazione della pagina Streamlit
st.set_page_config(page_title="Nota Spese Mensile - Winner", layout="wide")

PATH_BOZZA_LOCALE = "bozza_automatica.json"

MESI_ANNO = [
    "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
    "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
]

ANNI_DISPONIBILI = [str(a) for a in range(2025, date.today().year + 3)]

COORDINATORI = [
    "", "Coordinatore Bruscolini", "Coordinatore Calzetta", "Coordinatore Casaburi",
    "Coordinatore Ceniti", "Coordinatore Ledda", "Coordinatore Mazzoleni",
    "Coordinatore Migliaccio", "Coordinatore Piccinetti", "Coordinatore Vendemini", "Coordinatore Stella"
]

# --- FUNZIONE PER COMPRIMERE E RIDIMENSIONARE LE IMMAGINI CARICATE ---
def ridimensiona_immagine(file_uploaded, max_size=(800, 800), qualita=80):
    try:
        img = Image.open(file_uploaded)
        img = img.convert("RGB") # Conversione per salvare in JPEG ed eliminare l'alpha channel se PNG
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=qualita, optimize=True)
        buffer.seek(0)
        return buffer, "image/jpeg"
    except Exception:
        file_uploaded.seek(0)
        return file_uploaded, file_uploaded.type

# --- FUNZIONE PER NORMALIZZARE E RINOMINARE LE COLONNE VECCHIE ---
def normalizza_dataframe(df):
    if df is None or df.empty:
        return df
    
    mappa_colonne = {
        "Km_A": "Km",
        "Autostrade_A": "Autostrada (€)",
        "Autostrada_A": "Autostrada (€)",
        "Vitto_A": "Vitto (€)",
        "Varie_A": "Varie (€)",
        "Km": "Km",
        "Autostrada (€)": "Autostrada (€)",
        "Vitto (€)": "Vitto (€)",
        "Varie (€)": "Varie (€)"
    }
    
    df = df.rename(columns=mappa_colonne)
    
    cols_da_rimuovere = [c for c in df.columns if c.endswith("_B") or " B" in c]
    if cols_da_rimuovere:
        df = df.drop(columns=cols_da_rimuovere, errors="ignore")
        
    return df

# --- FUNZIONE SICURA PER CALCOLARE LA SOMMA DELLE COLONNE ---
def calcola_somma_sicura(df, nome_colonna):
    if nome_colonna in df.columns:
        return pd.to_numeric(df[nome_colonna], errors='coerce').fillna(0).sum()
    return 0.0

# --- FUNZIONI DI SUPPORTO PER LA BOZZA ---
def salva_bozza_automatica():
    allegati_serializzabili = []
    for item in st.session_state.get("allegati_dkv_list", []):
        allegati_serializzabili.append({
            "name": item.get("name"),
            "categoria": item.get("categoria", "Varie"),
            "importo": item.get("importo", 0.0),
            "data": str(item.get("data", date.today())),
            "mese_riferimento": item.get("mese_riferimento", st.session_state.get("mese_nota_spese", ""))
        })

    spese_dict = []
    if "dati_spese_v2" in st.session_state and not st.session_state.dati_spese_v2.empty:
        df_temp = normalizza_dataframe(st.session_state.dati_spese_v2.copy())
        if "Data" in df_temp.columns:
            df_temp["Data"] = df_temp["Data"].astype(str)
        spese_dict = df_temp.to_dict(orient="records")

    dati_da_salvare = {
        "nome": st.session_state.get("nome_user", "LORENZO"),
        "cognome": st.session_state.get("cognome_user", "VALLEGGI"),
        "mese_nota_spese": st.session_state.get("mese_nota_spese", f"{MESI_ANNO[date.today().month - 1]} {date.today().year}"),
        "spese": spese_dict,
        "allegati_info": allegati_serializzabili,
        "note_finali": st.session_state.get("note_finali_user", "")
    }
    try:
        with open(PATH_BOZZA_LOCALE, "w", encoding="utf-8") as f:
            json.dump(dati_da_salvare, f, default=str, ensure_ascii=False, indent=2)
    except Exception:
        pass

def carica_bozza_automatica():
    if os.path.exists(PATH_BOZZA_LOCALE):
        try:
            with open(PATH_BOZZA_LOCALE, "r", encoding="utf-8") as f:
                dati = json.load(f)
                if "nome" in dati:
                    st.session_state["nome_user"] = dati["nome"]
                if "cognome" in dati:
                    st.session_state["cognome_user"] = dati["cognome"]
                if "mese_nota_spese" in dati:
                    st.session_state["mese_nota_spese"] = dati["mese_nota_spese"]
                if "note_finali" in dati:
                    st.session_state["note_finali_user"] = dati["note_finali"]
                if "spese" in dati and dati["spese"]:
                    df_spese = pd.DataFrame(dati["spese"])
                    if "Data" in df_spese.columns:
                        df_spese["Data"] = pd.to_datetime(df_spese["Data"]).dt.date
                    df_spese = normalizza_dataframe(df_spese)
                    st.session_state.dati_spese_v2 = df_spese
        except Exception:
            pass

def rimuovi_allegato(indice):
    st.session_state.allegati_dkv_list.pop(indice)

# --- VISUALIZZATORE ANTEPRIMA MULTI-FORMATO ---
def mostra_anteprima_scontrino(file_obj, file_name, file_bytes=None, mime_type=None, height=220):
    b_data = file_obj.getvalue() if file_obj is not None else file_bytes
    m_type = file_obj.type if hasattr(file_obj, 'type') else (mime_type or "application/octet-stream")

    if m_type.startswith("image"):
        img = Image.open(io.BytesIO(b_data))
        st.image(img, use_container_width=True)
    elif m_type == "application/pdf":
        try:
            base64_pdf = base64.b64encode(b_data).decode('utf-8')
            pdf_display = f''
            st.markdown(pdf_display, unsafe_allow_html=True)
        except Exception:
            st.info("📄 Documento PDF Allegato")
    else:
        st.info(f"📄 Documento allegato (`{file_name}`)")

@st.dialog("🔍 Visualizzazione Ingrandita Scontrino")
def mostra_scontrino_modal(file_obj, file_name, file_bytes=None, mime_type=None):
    st.write(f"### 📄 **{file_name}**")
    mostra_anteprima_scontrino(file_obj, file_name, file_bytes, mime_type, height=500)
    
    b_data = file_obj.getvalue() if file_obj is not None else file_bytes
    m_type = file_obj.type if hasattr(file_obj, 'type') else (mime_type or "application/octet-stream")
    
    st.download_button(
        label="💾 Scarica File Originale",
        data=b_data,
        file_name=file_name,
        mime=m_type,
        use_container_width=True
    )

# --- INIZIALIZZAZIONE STRUTTURA DATI ---
def crea_df_iniziale():
    return pd.DataFrame([{
        "Data": date.today(), 
        "Comune": "Come da Planning Allegato",
        "Coordinatore": "Coordinatore Bruscolini", 
        "Km": 143, 
        "Autostrada (€)": 7.40,
        "Vitto (€)": 0.0, 
        "Varie (€)": 0.0
    }])

if "primo_avvio" not in st.session_state:
    carica_bozza_automatica()
    st.session_state["primo_avvio"] = False

if "allegati_dkv_list" not in st.session_state:
    st.session_state.allegati_dkv_list = []

if "dati_spese_v2" not in st.session_state:
    st.session_state.dati_spese_v2 = crea_df_iniziale()
else:
    st.session_state.dati_spese_v2 = normalizza_dataframe(st.session_state.dati_spese_v2)

# --- INTESTAZIONE CON LOGO ---
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
    st.title("📄 NOTA SPESE MENSILE DIPENDENTI")
    st.markdown("""
    **WINNER SOCIETÀ COOPERATIVA**  
    *Sede Legale / Operativa:* Civitavecchia (RM) | *Tel:* 0766 505 197
    """)

st.divider()

# --- ANAGRAFICA E MESE DI RIFERIMENTO ---
st.subheader("👤 Anagrafica e Periodo di Riferimento")

col_a1, col_a2, col_a3, col_a4 = st.columns([2, 2, 3, 2])

with col_a1:
    nome = st.text_input("Nome", st.session_state.get("nome_user", "LORENZO"), key="nome_input")
    st.session_state["nome_user"] = nome

with col_a2:
    cognome = st.text_input("Cognome", st.session_state.get("cognome_user", "VALLEGGI"), key="cognome_input")
    st.session_state["cognome_user"] = cognome

with col_a3:
    opzioni_mesi_anno = [f"{m} {anno}" for anno in ANNI_DISPONIBILI for m in MESI_ANNO]
    default_mese_anno = f"{MESI_ANNO[date.today().month - 1]} {date.today().year}"
    idx_default = opzioni_mesi_anno.index(default_mese_anno) if default_mese_anno in opzioni_mesi_anno else 0
    
    mese_selezionato = st.selectbox(
        "📅 MESE DI RIFERIMENTO NOTA SPESE",
        options=opzioni_mesi_anno,
        index=st.session_state.get("idx_mese_pref", idx_default),
        key="select_mese_principale"
    )
    st.session_state["mese_nota_spese"] = mese_selezionato

with col_a4:
    costo_km_a = st.number_input("Rimborso Km (€)", value=0.25, disabled=True)

st.info(f"📌 **Nota Spese Mensile in elaborazione per il periodo:** `{st.session_state['mese_nota_spese']}`")

# --- BARRA AZIONI BOZZA ---
col_salva1, col_salva2, col_salva3 = st.columns([2, 2, 2])
with col_salva1:
    if st.button("💾 Salva Bozza Mensile", type="primary", use_container_width=True):
        salva_bozza_automatica()
        st.success(f"Bozza per **{st.session_state['mese_nota_spese']}** salvata!")
with col_salva2:
    if st.button("🔄 Ripristina Dati Salvati", use_container_width=True):
        carica_bozza_automatica()
        st.rerun()
with col_salva3:
    if st.button("🗑 Svuota Tutto", use_container_width=True):
        if os.path.exists(PATH_BOZZA_LOCALE):
            os.remove(PATH_BOZZA_LOCALE)
        st.session_state.dati_spese_v2 = crea_df_iniziale()
        st.session_state.allegati_dkv_list = []
        st.session_state.note_finali_user = ""
        st.rerun()

st.divider()

# --- TABELLA PRINCIPALE VOCI DI SPESA ---
st.subheader(f"📋 1. Voci Spesa Giornaliere - {st.session_state['mese_nota_spese']}")

df_da_mostrare = normalizza_dataframe(st.session_state.dati_spese_v2)

editor_key = f"editor_{st.session_state['mese_nota_spese'].replace(' ', '_')}"

df_edit = st.data_editor(
    df_da_mostrare,
    num_rows="dynamic",
    use_container_width=True,
    key=editor_key,
    column_config={
        "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
        "Comune": st.column_config.TextColumn("Comune / Note"),
        "Coordinatore": st.column_config.SelectboxColumn("Coordinatore di Zona", options=COORDINATORI),
        "Km": st.column_config.NumberColumn("Km Percorsi", min_value=0, step=1, default=0),
        "Autostrada (€)": st.column_config.NumberColumn("Autostrade (€)", min_value=0.0, format="%.2f €", default=0.0),
        "Vitto (€)": st.column_config.NumberColumn("Vitto (€)", min_value=0.0, format="%.2f €", default=0.0),
        "Varie (€)": st.column_config.NumberColumn("Varie (€)", min_value=0.0, format="%.2f €", default=0.0),
    }
)

st.session_state.dati_spese_v2 = df_edit

# --- CALCOLO E AGGIORNAMENTO TOTALI IN TEMPO REALE ---
km_totali = calcola_somma_sicura(df_edit, "Km")
totale_rimborso_km = km_totali * costo_km_a
autostrada_totale = calcola_somma_sicura(df_edit, "Autostrada (€)")
vitto_totale = calcola_somma_sicura(df_edit, "Vitto (€)")
varie_totale = calcola_somma_sicura(df_edit, "Varie (€)")

c_tot1, c_tot2, c_tot3, c_tot4 = st.columns(4)
c_tot1.metric("Totale Km", f"{km_totali:.0f} Km", f"€ {totale_rimborso_km:.2f}")
c_tot2.metric("Totale Autostrade", f"€ {autostrada_totale:.2f}")
c_tot3.metric("Totale Vitto", f"€ {vitto_totale:.2f}")
c_tot4.metric("Totale Varie", f"€ {varie_totale:.2f}")

st.divider()

# --- SEZIONE SINTESI REFERENTI (TABELLA PIVOT PER COORDINATORE) ---
st.subheader("📊 2. Sintesi Referenti e Coordinatori")
st.caption("Resoconto aggregato per Coordinatore (Km, Rimborso Km, Autostrade, Vitto, Varie e Totale (€)).")

if not df_edit.empty:
    df_pivot = df_edit.copy()
    
    df_pivot["Km"] = pd.to_numeric(df_pivot["Km"], errors='coerce').fillna(0)
    df_pivot["Tot. Km/€"] = df_pivot["Km"] * costo_km_a
    df_pivot["Autostrade"] = pd.to_numeric(df_pivot["Autostrada (€)"], errors='coerce').fillna(0)
    df_pivot["Vitto"] = pd.to_numeric(df_pivot["Vitto (€)"], errors='coerce').fillna(0)
    df_pivot["Varie"] = pd.to_numeric(df_pivot["Varie (€)"], errors='coerce').fillna(0)
    df_pivot["Totale €"] = df_pivot["Tot. Km/€"] + df_pivot["Autostrade"] + df_pivot["Vitto"] + df_pivot["Varie"]
    
    df_grouped = df_pivot.groupby("Coordinatore", as_index=False).agg({
        "Km": "sum",
        "Tot. Km/€": "sum",
        "Autostrade": "sum",
        "Vitto": "sum",
        "Varie": "sum",
        "Totale €": "sum"
    })
    
    df_grouped = df_grouped.rename(columns={
        "Coordinatore": "Etichette di riga",
        "Km": "Somma di Km",
        "Tot. Km/€": "Somma di Tot. Km/€",
        "Autostrade": "Somma di Autostrade",
        "Vitto": "Somma di Vitto",
        "Varie": "Somma di Varie",
        "Totale €": "Somma di Totale €"
    })
    
    riga_totale = pd.DataFrame([{
        "Etichette di riga": "Totale complessivo",
        "Somma di Km": df_grouped["Somma di Km"].sum(),
        "Somma di Tot. Km/€": df_grouped["Somma di Tot. Km/€"].sum(),
        "Somma di Autostrade": df_grouped["Somma di Autostrade"].sum(),
        "Somma di Vitto": df_grouped["Somma di Vitto"].sum(),
        "Somma di Varie": df_grouped["Somma di Varie"].sum(),
        "Somma di Totale €": df_grouped["Somma di Totale €"].sum()
    }])
    
    df_sintesi_finale = pd.concat([df_grouped, riga_totale], ignore_index=True)
    
    st.dataframe(
        df_sintesi_finale,
        use_container_width=True,
        column_config={
            "Etichette di riga": st.column_config.TextColumn("Etichette di riga"),
            "Somma di Km": st.column_config.NumberColumn("Somma di Km", format="%d"),
            "Somma di Tot. Km/€": st.column_config.NumberColumn("Somma di Tot. Km/€", format="%.2f €"),
            "Somma di Autostrade": st.column_config.NumberColumn("Somma di Autostrade", format="%.2f €"),
            "Somma di Vitto": st.column_config.NumberColumn("Somma di Vitto", format="%.2f €"),
            "Somma di Varie": st.column_config.NumberColumn("Somma di Varie", format="%.2f €"),
            "Somma di Totale €": st.column_config.NumberColumn("Somma di Totale €", format="%.2f €")
        },
        hide_index=True
    )

st.divider()

# --- GESTIONE ALLEGATI E SCONTRINI CON RIDIMENSIONAMENTO AUTOMATICO ---
st.subheader(f"🧾 3. Allegati e Scontrini - {st.session_state['mese_nota_spese']}")

with st.container(border=True):
    st.markdown("#### ➕ Carica Scontrino per questo Mese")
    
    col_up1, col_up2, col_up3, col_up4 = st.columns([2, 2, 2, 2])
    
    with col_up1:
        tipo_spesa_sel = st.selectbox(
            "Categoria Spesa",
            options=["Autostrada", "Vitto", "Varie"],
            key="tipo_spesa_uploader"
        )
    
    with col_up2:
        mese_rif_scontrino = st.text_input(
            "Mese di Riferimento",
            value=st.session_state["mese_nota_spese"],
            disabled=True
        )
        
    with col_up3:
        data_scontrino_sel = st.date_input("Data Scontrino", value=date.today(), key="data_scontrino_uploader")
        
    with col_up4:
        importo_scontrino_sel = st.number_input("Importo (€)", min_value=0.0, step=0.50, format="%.2f", key="importo_scontrino_uploader")

    nuovi_file = st.file_uploader(
        "📎 Seleziona Scontrini (JPG, PNG, PDF) - *Verranno ottimizzati automaticamente*",
        type=["jpg", "jpeg", "png", "pdf"],
        accept_multiple_files=True,
        key="nuovi_scontrini_uploader"
    )

    if nuovi_file:
        for f_item in nuovi_file:
            if f_item.name not in [x["name"] for x in st.session_state.allegati_dkv_list]:
                # Se è un'immagine, la ridimensiona e comprime subito per alleggerire la memoria
                if f_item.type.startswith("image"):
                    file_processato, m_type = ridimensiona_immagine(f_item)
                    file_processato.type = m_type
                else:
                    file_processato = f_item
                    
                st.session_state.allegati_dkv_list.append({
                    "name": f_item.name,
                    "file": file_processato,
                    "categoria": tipo_spesa_sel,
                    "importo": float(importo_scontrino_sel),
                    "data": data_scontrino_sel,
                    "mese_riferimento": st.session_state["mese_nota_spese"]
                })

# MOSTRA GLI SCONTRINI CARICATI
if st.session_state.allegati_dkv_list:
    st.markdown(f"### 🖼 Elenco Scontrini per {st.session_state['mese_nota_spese']}")
    
    elementi_mese = [
        (idx, item) for idx, item in enumerate(st.session_state.allegati_dkv_list)
        if item.get("mese_riferimento") == st.session_state["mese_nota_spese"]
    ]
    
    if elementi_mese:
        cols_foto = st.columns(3)
        for grid_idx, (real_idx, item) in enumerate(elementi_mese):
            with cols_foto[grid_idx % 3]:
                file_obj = item["file"]
                file_name = item["name"]
                cat_curr = item.get("categoria", "Varie")
                imp_curr = item.get("importo", 0.0)
                data_curr = item.get("data", date.today())
                
                with st.container(border=True):
                    st.markdown(f"🏷️ **{cat_curr.upper()}** | 📅 `{data_curr}`")
                    st.markdown(f"💶 **Importo:** € `{imp_curr:.2f}`")
                    
                    mostra_anteprima_scontrino(file_obj, file_name, height=220)
                    
                    if st.button("🔍 Ingrandisci", key=f"zoom_{real_idx}_{file_name}", use_container_width=True):
                        mostra_scontrino_modal(file_obj, file_name)
                        
                    st.button("🗑 Elimina", key=f"del_{real_idx}_{file_name}", on_click=rimuovi_allegato, args=(real_idx,), use_container_width=True)

st.divider()

# --- RIEPILOGO FINALE GENERALE MENSILE ---
totale_generale_mese = totale_rimborso_km + autostrada_totale + vitto_totale + varie_totale

st.subheader(f"📊 RIEPILOGO FINALE MENSILE - {st.session_state['mese_nota_spese']}")
st.metric(f"TOTALE COMPLESSIVO SPESE DA RIMBORSARE ({st.session_state['mese_nota_spese']})", f"€ {totale_generale_mese:.2f}")

st.divider()

# --- SEZIONE FIRMA CON CARICAMENTO FILE ---
st.subheader("✍️ Firma Dipendente e Approvazione Aziendale")

col_firma_dip, col_firma_az = st.columns(2)

with col_firma_dip:
    with st.container(border=True):
        st.markdown("#### 👤 Firma Dipendente (da File)")
        st.caption("Carica l'immagine o il file con la tua firma (PNG, JPG, PDF)")
        
        file_firma = st.file_uploader(
            "📁 Carica File Firma Dipendente",
            type=["png", "jpg", "jpeg", "pdf"],
            key=f"uploader_firma_dip_{st.session_state['mese_nota_spese'].replace(' ', '_')}"
        )
        
        if file_firma is not None:
            st.success("✅ Firma caricata correttamente!")
            if file_firma.type.startswith("image"):
                file_firma_proc, _ = ridimensiona_immagine(file_firma, max_size=(400, 200))
                mostra_anteprima_scontrino(file_firma_proc, file_firma.name, height=120)
            else:
                mostra_anteprima_scontrino(file_firma, file_firma.name, height=120)
            
        data_firma_dip = st.date_input("Data Firma Dipendente", value=date.today(), key="data_firma_dip_input")

with col_firma_az:
    with st.container(border=True):
        st.markdown("#### 🏢 Approvazione Winner Soc. Coop.")
        st.caption("Spazio riservato alla direzione / amministrazione.")
        
        st.selectbox(
            "Stato Approvazione:",
            options=["In Attesa di Verifica", "Approvato", "Rifiutato / In Revisione"],
            key="stato_approvazione_select"
        )
        
        file_firma_resp = st.file_uploader(
            "📁 Carica File Firma Responsabile (opzionale)",
            type=["png", "jpg", "jpeg", "pdf"],
            key=f"uploader_firma_resp_{st.session_state['mese_nota_spese'].replace(' ', '_')}"
        )
        
        if file_firma_resp is not None:
            st.success("✅ Firma Responsabile caricata!")
            if file_firma_resp.type.startswith("image"):
                file_resp_proc, _ = ridimensiona_immagine(file_firma_resp, max_size=(400, 200))
                mostra_anteprima_scontrino(file_resp_proc, file_firma_resp.name, height=120)
            else:
                mostra_anteprima_scontrino(file_firma_resp, file_firma_resp.name, height=120)
            
        st.date_input("Data Approvazione", value=date.today(), key="data_approvazione_input")

# --- NOTE E CONFERMA ---
note_finali = st.text_area("📝 Note / Comunicazioni per l'Amministrazione", value=st.session_state.get("note_finali_user", ""), key="note_finali_input")
st.session_state["note_finali_user"] = note_finali

st.divider()

# --- DOWNLOAD FINALE ---
st.download_button(
    label=f"📥 Scarica Nota Spese {st.session_state['mese_nota_spese']} (CSV)",
    data=df_edit.to_csv(index=False).encode('utf-8'),
    file_name=f"Nota_Spese_{cognome}_{st.session_state['mese_nota_spese'].replace(' ', '_')}.csv",
    mime="text/csv",
    use_container_width=True
)
