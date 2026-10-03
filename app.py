import streamlit as st
import pandas as pd
from datetime import date
from PIL import Image
import os
import json
import base64

# 1. Configurazione della pagina Streamlit
st.set_page_config(page_title="Nota Spese Mensile - Winner", layout="wide")

PATH_BOZZA_LOCALE = "bozza_automatica.json"

MESI_ANNO = [
    "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
    "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
]

# --- FUNZIONI DI SUPPORTO ---
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

    dati_da_salvare = {
        "nome": st.session_state.get("nome_user", "LORENZO"),
        "cognome": st.session_state.get("cognome_user", "VALLEGGI"),
        "mese_nota_spese": st.session_state.get("mese_nota_spese", f"{MESI_ANNO[date.today().month - 1]} {date.today().year}"),
        "spese": st.session_state.dati_spese_v2.to_dict(orient="records") if "dati_spese_v2" in st.session_state else [],
        "rifornimenti": st.session_state.rifornimenti_dkv.to_dict(orient="records") if "rifornimenti_dkv" in st.session_state else [],
        "telepass": st.session_state.dati_telepass.to_dict(orient="records") if "dati_telepass" in st.session_state else [],
        "allegati_info": allegati_serializzabili,
        "firma_dipendente": st.session_state.get("firma_dipendente", ""),
        "firma_approvatore": st.session_state.get("firma_approvatore", "")
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
                if "firma_dipendente" in dati:
                    st.session_state["firma_dipendente"] = dati["firma_dipendente"]
                if "firma_approvatore" in dati:
                    st.session_state["firma_approvatore"] = dati["firma_approvatore"]
                if "spese" in dati and dati["spese"]:
                    df_spese = pd.DataFrame(dati["spese"])
                    if "Data" in df_spese.columns:
                        df_spese["Data"] = pd.to_datetime(df_spese["Data"]).dt.date
                    st.session_state.dati_spese_v2 = df_spese
                if "rifornimenti" in dati and dati["rifornimenti"]:
                    df_rif = pd.DataFrame(dati["rifornimenti"])
                    if "Data" in df_rif.columns:
                        df_rif["Data"] = pd.to_datetime(df_rif["Data"]).dt.date
                    st.session_state.rifornimenti_dkv = df_rif
                if "telepass" in dati and dati["telepass"]:
                    df_tel = pd.DataFrame(dati["telepass"])
                    if "Data" in df_tel.columns:
                        df_tel["Data"] = pd.to_datetime(df_tel["Data"]).dt.date
                    cols_tot = [c for c in ["Data", "Importo (€)", "Categoria"] if c in df_tel.columns]
                    st.session_state.dati_telepass = df_tel[cols_tot]
        except Exception:
            pass

def rimuovi_allegato(indice):
    st.session_state.allegati_dkv_list.pop(indice)

# --- VISUALIZZATORE ANTEPRIMA MULTI-FORMATO (IMMAGINI E PDF) ---
def mostra_anteprima_scontrino(file_obj, file_name, file_bytes=None, mime_type=None, height=220):
    b_data = file_obj.getvalue() if file_obj is not None else file_bytes
    m_type = file_obj.type if file_obj is not None else (mime_type or "application/octet-stream")

    if m_type.startswith("image"):
        if file_obj is not None:
            img = Image.open(file_obj)
        else:
            import io
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
    m_type = file_obj.type if file_obj is not None else (mime_type or "application/octet-stream")
    
    st.download_button(
        label="💾 Scarica File Originale",
        data=b_data,
        file_name=file_name,
        mime=m_type,
        use_container_width=True
    )

# --- INIZIALIZZAZIONE STATO ---
if "primo_avvio" not in st.session_state:
    carica_bozza_automatica()
    st.session_state["primo_avvio"] = False

if "allegati_dkv_list" not in st.session_state:
    st.session_state.allegati_dkv_list = []

if "dati_telepass" not in st.session_state:
    st.session_state.dati_telepass = pd.DataFrame(columns=["Data", "Importo (€)", "Categoria"])

if "prospetto_telepass_originale" not in st.session_state:
    st.session_state.prospetto_telepass_originale = None

if "file_telepass_info" not in st.session_state:
    st.session_state.file_telepass_info = None

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

# --- ANAGRAFICA E SELEZIONE MESE RIFERIMENTO ---
st.subheader("👤 Anagrafica e Periodo di Riferimento")

col_a1, col_a2, col_a3, col_a4 = st.columns([2, 2, 3, 2])

with col_a1:
    nome = st.text_input("Nome", st.session_state.get("nome_user", "LORENZO"), key="nome_input")
    st.session_state["nome_user"] = nome

with col_a2:
    cognome = st.text_input("Cognome", st.session_state.get("cognome_user", "VALLEGGI"), key="cognome_input")
    st.session_state["cognome_user"] = cognome

with col_a3:
    # Selezione del MESE E ANNO DI RIFERIMENTO
    anno_corrente = date.today().year
    opzioni_mesi_anno = [f"{m} {anno_corrente}" for m in MESI_ANNO] + [f"{m} {anno_corrente-1}" for m in MESI_ANNO]
    idx_default = date.today().month - 1
    
    mese_selezionato = st.selectbox(
        "📅 MESE DI RIFERIMENTO NOTA SPESE",
        options=opzioni_mesi_anno,
        index=st.session_state.get("idx_mese_pref", idx_default),
        key="select_mese_principale"
    )
    st.session_state["mese_nota_spese"] = mese_selezionato

with col_a4:
    costo_km_a = st.number_input("Rimborso Km Cat. A (€)", value=0.25, disabled=True)

# Evidenziatore Visuale del Mese
st.info(f"📌 **Nota Spese Mensile in elaborazione per il periodo:** `{st.session_state['mese_nota_spese']}`")

st.divider()

coordinatori = [
    "", "Coordinatore Bruscolini", "Coordinatore Calzetta", "Coordinatore Casaburi",
    "Coordinatore Ceniti", "Coordinatore Ledda", "Coordinatore Mazzoleni",
    "Coordinatore Migliaccio", "Coordinatore Piccinetti", "Coordinatore Vendemini", "Coordinatore Stella"
]

def crea_df_iniziale():
    return pd.DataFrame([{
        "Data": date.today(), "Comune": "Come da Planning Allegato",
        "Coordinatore di Zona": "", "Km_A": 143, "Autostrade_A": 7.40,
        "Vitto_A": 0.0, "Varie_A": 0.0, "Km_B": 0, "Autostrade_B": 0.0,
        "Vitto_B": 0.0, "Varie_B": 0.0
    }])

if "dati_spese_v2" not in st.session_state:
    st.session_state.dati_spese_v2 = crea_df_iniziale()

if "rifornimenti_dkv" not in st.session_state:
    st.session_state.rifornimenti_dkv = pd.DataFrame([
        {"Data": date.today(), "Importo (€)": 0.0, "Litri": 0.0, "Distributore / Note": "Stazione DKV"}
    ])

# --- BARRA SALVATAGGIO ---
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
        st.session_state.rifornimenti_dkv = pd.DataFrame([])
        st.session_state.dati_telepass = pd.DataFrame(columns=["Data", "Importo (€)", "Categoria"])
        st.session_state.allegati_dkv_list = []
        st.rerun()

st.divider()

# --- TABELLA PRINCIPALE VOCI DI SPESA ---
st.subheader(f"📋 1. Voci Spesa Giornaliere - {st.session_state['mese_nota_spese']}")

df_display = st.session_state.dati_spese_v2.copy()
df_display["Importo_Km_A"] = pd.to_numeric(df_display.get("Km_A", 0), errors='coerce').fillna(0) * costo_km_a

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
        "Importo_Km_A": st.column_config.NumberColumn("Tot. Rimborso Km (€)", format="%.2f €", disabled=True),
        "Autostrade_A": st.column_config.NumberColumn("Autostrade (€)", min_value=0.0, format="%.2f €"),
        "Vitto_A": st.column_config.NumberColumn("Vitto (€)", min_value=0.0, format="%.2f €"),
        "Varie_A": st.column_config.NumberColumn("Varie (€)", min_value=0.0, format="%.2f €"),
    }
)

st.session_state.dati_spese_v2 = df_edit.drop(columns=["Importo_Km_A"], errors="ignore").copy()
salva_bozza_automatica()

st.divider()

# --- GESTIONE ALLEGATI E SCONTRINI MENSILE CON ANTEPRIMA ---
st.subheader(f"🧾 2. Allegati e Scontrini - {st.session_state['mese_nota_spese']}")

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
        "📎 Seleziona Scontrini (JPG, PNG, PDF)",
        type=["jpg", "jpeg", "png", "pdf"],
        accept_multiple_files=True,
        key="nuovi_scontrini_uploader"
    )

    if nuovi_file:
        st.markdown("##### 👁️ Anteprima Immediata File Selezionati:")
        cols_preview = st.columns(min(len(nuovi_file), 3))
        
        for idx_f, f_item in enumerate(nuovi_file):
            with cols_preview[idx_f % 3]:
                with st.container(border=True):
                    st.caption(f"📄 `{f_item.name}`")
                    mostra_anteprima_scontrino(f_item, f_item.name, height=180)

            if f_item.name not in [x["name"] for x in st.session_state.allegati_dkv_list]:
                st.session_state.allegati_dkv_list.append({
                    "name": f_item.name,
                    "file": f_item,
                    "categoria": tipo_spesa_sel,
                    "importo": float(importo_scontrino_sel),
                    "data": data_scontrino_sel,
                    "mese_riferimento": st.session_state["mese_nota_spese"]
                })
        salva_bozza_automatica()

# ANTEPRIMA E SCHEDE SCONTRINI CARICATI
if st.session_state.allegati_dkv_list:
    st.markdown(f"### 🖼️ Elenco Scontrini per {st.session_state['mese_nota_spese']}")
    
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
                    
                    # ANTEPRIMA VISIVA SCONTRINO
                    mostra_anteprima_scontrino(file_obj, file_name, height=220)
                    
                    if st.button("🔍 Ingrandisci", key=f"zoom_{real_idx}_{file_name}", use_container_width=True):
                        mostra_scontrino_modal(file_obj, file_name)
                        
                    st.button("🗑 Elimina", key=f"del_{real_idx}_{file_name}", on_click=rimuovi_allegato, args=(real_idx,), use_container_width=True)

st.divider()

# --- RIEPILOGO FINALE MESE ---
df_finale = df_edit.copy()
km_sum = pd.to_numeric(df_finale.get("Km_A", 0), errors='coerce').fillna(0).sum()
tot_km = km_sum * costo_km_a

auto = pd.to_numeric(df_finale.get("Autostrade_A", 0), errors='coerce').fillna(0).sum()
vitto = pd.to_numeric(df_finale.get("Vitto_A", 0), errors='coerce').fillna(0).sum()
varie = pd.to_numeric(df_finale.get("Varie_A", 0), errors='coerce').fillna(0).sum()
totale_generale_mese = tot_km + auto + vitto + varie

st.subheader(f"📊 RIEPILOGO FINALE MENSILE - {st.session_state['mese_nota_spese']}")
st.metric(f"TOTALE SPESE DA RIMBORSARE ({st.session_state['mese_nota_spese']})", f"€ {totale_generale_mese:.2f}")

st.download_button(
    label=f"📥 Scarica Nota Spese {st.session_state['mese_nota_spese']} (CSV)",
    data=df_finale.to_csv(index=False).encode('utf-8'),
    file_name=f"Nota_Spese_{cognome}_{st.session_state['mese_nota_spese'].replace(' ', '_')}.csv",
    mime="text/csv",
    use_container_width=True
)
