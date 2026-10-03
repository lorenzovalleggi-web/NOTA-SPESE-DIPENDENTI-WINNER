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

# --- CONVERSIONE FILE IN BASE64 ---
def file_to_base64(file_obj):
    if file_obj is None:
        return None, None
    try:
        if hasattr(file_obj, 'getvalue'):
            bytes_data = file_obj.getvalue()
            m_type = getattr(file_obj, 'type', 'image/jpeg')
        elif isinstance(file_obj, bytes):
            bytes_data = file_obj
            m_type = 'image/jpeg'
        else:
            return None, None
            
        b64_str = base64.b64encode(bytes_data).decode('utf-8')
        return b64_str, m_type
    except Exception:
        return None, None

def base64_to_bytes(b64_str):
    if not b64_str:
        return None
    try:
        return base64.b64decode(b64_str.encode('utf-8'))
    except Exception:
        return None

# --- FUNZIONE PER RIDIMENSIONARE IMMAGINI ---
def ridimensiona_immagine(file_uploaded, max_size=(600, 600), qualita=75):
    try:
        if isinstance(file_uploaded, bytes):
            img = Image.open(io.BytesIO(file_uploaded))
        else:
            img = Image.open(file_uploaded)
            
        img = img.convert("RGB")
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=qualita, optimize=True)
        return buffer.getvalue(), "image/jpeg"
    except Exception:
        if hasattr(file_uploaded, 'getvalue'):
            return file_uploaded.getvalue(), getattr(file_uploaded, "type", "application/octet-stream")
        elif isinstance(file_uploaded, bytes):
            return file_uploaded, "application/octet-stream"
        return None, "application/octet-stream"

# --- NORMALIZZAZIONE DATAFRAME ---
def normalizza_dataframe(df):
    if df is None or df.empty:
        return pd.DataFrame(columns=["Data", "Comune", "Coordinatore", "Km", "Autostrada (€)", "Vitto (€)", "Varie (€)"])
    
    mappa_colonne = {
        "Km_A": "Km",
        "Autostrade_A": "Autostrada (€)",
        "Autostrada_A": "Autostrada (€)",
        "Vitto_A": "Vitto (€)",
        "Varie_A": "Varie (€)"
    }
    
    df = df.rename(columns=mappa_colonne)
    cols_da_rimuovere = [c for c in df.columns if c.endswith("_B") or " B" in c]
    if cols_da_rimuovere:
        df = df.drop(columns=cols_da_rimuovere, errors="ignore")
        
    return df

def calcola_somma_sicura(df, nome_colonna):
    if df is not None and not df.empty and nome_colonna in df.columns:
        return pd.to_numeric(df[nome_colonna], errors='coerce').fillna(0).sum()
    return 0.0

def elimina_scontrino(index_to_remove):
    if 0 <= index_to_remove < len(st.session_state.allegati_dkv_list):
        st.session_state.allegati_dkv_list.pop(index_to_remove)
        salva_bozza_automatica()

def elimina_telepass():
    st.session_state.pop("telepass_file_bytes", None)
    st.session_state.pop("telepass_file_type", None)
    st.session_state.pop("telepass_file_name", None)
    salva_bozza_automatica()

# --- FUNZIONI PER SALVATAGGIO E CARICAMENTO BOZZA ---
def salva_bozza_automatica():
    allegati_serializzabili = []
    for item in st.session_state.get("allegati_dkv_list", []):
        b64_data, m_type = file_to_base64(item.get("file"))
        allegati_serializzabili.append({
            "name": item.get("name"),
            "file_b64": b64_data,
            "type": m_type or item.get("type", "image/jpeg"),
            "categoria": item.get("categoria", "Varie"),
            "importo": float(item.get("importo", 0.0)),
            "data": str(item.get("data", date.today())),
            "mese_riferimento": item.get("mese_riferimento", st.session_state.get("mese_nota_spese", ""))
        })

    spese_dict = []
    if "dati_spese_v2" in st.session_state and not st.session_state.dati_spese_v2.empty:
        df_temp = normalizza_dataframe(st.session_state.dati_spese_v2.copy())
        if "Data" in df_temp.columns:
            df_temp["Data"] = df_temp["Data"].astype(str)
        spese_dict = df_temp.to_dict(orient="records")

    telepass_dict = []
    if "dati_telepass" in st.session_state and not st.session_state.dati_telepass.empty:
        df_tele = st.session_state.dati_telepass.copy()
        if "Data" in df_tele.columns:
            df_tele["Data"] = df_tele["Data"].astype(str)
        telepass_dict = df_tele.to_dict(orient="records")

    firma_dip_b64, firma_dip_type = file_to_base64(st.session_state.get("firma_dip_bytes"))
    firma_resp_b64, firma_resp_type = file_to_base64(st.session_state.get("firma_resp_bytes"))
    telepass_file_b64, telepass_file_type = file_to_base64(st.session_state.get("telepass_file_bytes"))

    dati_da_salvare = {
        "nome": st.session_state.get("nome_user", "LORENZO"),
        "cognome": st.session_state.get("cognome_user", "VALLEGGI"),
        "mese_nota_spese": st.session_state.get("mese_nota_spese", f"{MESI_ANNO[date.today().month - 1]} {date.today().year}"),
        "spese": spese_dict,
        "telepass_spese": telepass_dict,
        "allegati_info": allegati_serializzabili,
        "telepass_file_b64": telepass_file_b64,
        "telepass_file_type": telepass_file_type,
        "telepass_file_name": st.session_state.get("telepass_file_name", ""),
        "firma_dip_b64": firma_dip_b64,
        "firma_dip_type": firma_dip_type,
        "firma_resp_b64": firma_resp_b64,
        "firma_resp_type": firma_resp_type,
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

                if "telepass_spese" in dati and dati["telepass_spese"]:
                    df_telepass = pd.DataFrame(dati["telepass_spese"])
                    if "Data" in df_telepass.columns:
                        df_telepass["Data"] = pd.to_datetime(df_telepass["Data"]).dt.date
                    st.session_state.dati_telepass = df_telepass

                if "telepass_file_b64" in dati and dati["telepass_file_b64"]:
                    st.session_state["telepass_file_bytes"] = base64_to_bytes(dati["telepass_file_b64"])
                    st.session_state["telepass_file_type"] = dati.get("telepass_file_type", "image/jpeg")
                    st.session_state["telepass_file_name"] = dati.get("telepass_file_name", "Telepass")

                if "allegati_info" in dati and dati["allegati_info"]:
                    st.session_state.allegati_dkv_list = []
                    for item in dati["allegati_info"]:
                        bytes_file = base64_to_bytes(item.get("file_b64"))
                        if bytes_file:
                            st.session_state.allegati_dkv_list.append({
                                "name": item.get("name"),
                                "file": bytes_file,
                                "type": item.get("type", "image/jpeg"),
                                "categoria": item.get("categoria", "Varie"),
                                "importo": float(item.get("importo", 0.0)),
                                "data": item.get("data", str(date.today())),
                                "mese_riferimento": item.get("mese_riferimento", "")
                            })

                if "firma_dip_b64" in dati and dati["firma_dip_b64"]:
                    st.session_state["firma_dip_bytes"] = base64_to_bytes(dati["firma_dip_b64"])
                    st.session_state["firma_dip_type"] = dati.get("firma_dip_type", "image/png")
                if "firma_resp_b64" in dati and dati["firma_resp_b64"]:
                    st.session_state["firma_resp_bytes"] = base64_to_bytes(dati["firma_resp_b64"])
                    st.session_state["firma_resp_type"] = dati.get("firma_resp_type", "image/png")

        except Exception:
            pass

# --- FUNZIONI DI CALLBACK PER EVITARE IL BUG DEL DOPPIO INSERIMENTO ---
def on_change_spese():
    state = st.session_state.editor_spese_stabile
    df = st.session_state.dati_spese_v2.copy()
    
    # Gestione modifiche celle
    for row_idx, changes in state.get("edited_rows", {}).items():
        for col_name, new_val in changes.items():
            df.iat[row_idx, df.columns.get_loc(col_name)] = new_val
            
    # Gestione righe aggiunte
    for new_row in state.get("added_rows", []):
        row_data = {col: new_row.get(col, None) for col in df.columns}
        df = pd.concat([df, pd.DataFrame([row_data])], ignore_index=True)
        
    # Gestione righe eliminate
    deleted_indices = state.get("deleted_rows", [])
    if deleted_indices:
        df = df.drop(index=deleted_indices).reset_index(drop=True)

    st.session_state.dati_spese_v2 = normalizza_dataframe(df)
    salva_bozza_automatica()

def on_change_telepass():
    state = st.session_state.editor_telepass_stabile
    df = st.session_state.dati_telepass.copy()
    
    for row_idx, changes in state.get("edited_rows", {}).items():
        for col_name, new_val in changes.items():
            df.iat[row_idx, df.columns.get_loc(col_name)] = new_val
            
    for new_row in state.get("added_rows", []):
        row_data = {col: new_row.get(col, None) for col in df.columns}
        df = pd.concat([df, pd.DataFrame([row_data])], ignore_index=True)
        
    deleted_indices = state.get("deleted_rows", [])
    if deleted_indices:
        df = df.drop(index=deleted_indices).reset_index(drop=True)

    st.session_state.dati_telepass = df
    salva_bozza_automatica()

# --- VISUALIZZAZIONE SCONTRINI ---
def mostra_anteprima_scontrino(file_obj, file_name, height=110, m_type_override=None):
    if hasattr(file_obj, 'getvalue'):
        b_data = file_obj.getvalue()
        m_type = getattr(file_obj, 'type', 'image/jpeg')
    elif isinstance(file_obj, bytes):
        b_data = file_obj
        m_type = m_type_override or 'image/jpeg'
    else:
        st.info(f"📄 Allegato (`{file_name}`)")
        return

    if str(m_type).startswith("image"):
        try:
            img = Image.open(io.BytesIO(b_data))
            st.image(img, use_container_width=True)
        except Exception:
            st.info("🖼️ Immagine Scontrino")
    elif m_type == "application/pdf":
        try:
            base64_pdf = base64.b64encode(b_data).decode('utf-8')
            pdf_display = f''
            st.markdown(pdf_display, unsafe_allow_html=True)
        except Exception:
            st.info("📄 Documento PDF Allegato")
    else:
        st.info(f"📄 Allegato (`{file_name}`)")

@st.dialog("🔍 Visualizzazione Ingrandita Scontrino")
def mostra_scontrino_modal(file_obj, file_name, m_type_override=None):
    st.write(f"### 📄 **{file_name}**")
    mostra_anteprima_scontrino(file_obj, file_name, height=450, m_type_override=m_type_override)
    
    if hasattr(file_obj, 'getvalue'):
        b_data = file_obj.getvalue()
        m_type = getattr(file_obj, 'type', 'application/octet-stream')
    else:
        b_data = file_obj
        m_type = m_type_override or 'application/octet-stream'
    
    st.download_button(
        label="💾 Scarica File Originale",
        data=b_data,
        file_name=file_name,
        mime=m_type,
        use_container_width=True
    )

# --- INIZIALIZZAZIONE ---
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

def crea_df_telepass_iniziale():
    return pd.DataFrame([{
        "Data": date.today(),
        "Tratta / Descrizione": "Tratta Milano - Bologna",
        "Importo (€)": 0.0
    }])

if "primo_avvio" not in st.session_state:
    carica_bozza_automatica()
    st.session_state["primo_avvio"] = False

if "allegati_dkv_list" not in st.session_state:
    st.session_state.allegati_dkv_list = []

if "dati_spese_v2" not in st.session_state or st.session_state.dati_spese_v2 is None:
    st.session_state.dati_spese_v2 = crea_df_iniziale()
else:
    st.session_state.dati_spese_v2 = normalizza_dataframe(st.session_state.dati_spese_v2)

if "dati_telepass" not in st.session_state or st.session_state.dati_telepass is None:
    st.session_state.dati_telepass = crea_df_telepass_iniziale()

# --- HEADER LOGO ---
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

# --- ANAGRAFICA ---
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

# --- PULSANTI DI CONTROLLO BOZZA ---
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
        st.session_state.dati_telepass = crea_df_telepass_iniziale()
        st.session_state.allegati_dkv_list = []
        st.session_state.pop("telepass_file_bytes", None)
        st.session_state.pop("firma_dip_bytes", None)
        st.session_state.pop("firma_resp_bytes", None)
        st.session_state.note_finali_user = ""
        st.rerun()

st.divider()

# --- TABELLA VOCI SPESA GIORNALIERE ---
st.subheader(f"📋 1. Voci Spesa Giornaliere - {st.session_state['mese_nota_spese']}")

st.data_editor(
    st.session_state.dati_spese_v2,
    num_rows="dynamic",
    use_container_width=True,
    key="editor_spese_stabile",
    on_change=on_change_spese,
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

# --- TOTALI E METRICHE ---
km_totali = calcola_somma_sicura(st.session_state.dati_spese_v2, "Km")
totale_rimborso_km = km_totali * costo_km_a
autostrada_totale = calcola_somma_sicura(st.session_state.dati_spese_v2, "Autostrada (€)")
vitto_totale = calcola_somma_sicura(st.session_state.dati_spese_v2, "Vitto (€)")
varie_totale = calcola_somma_sicura(st.session_state.dati_spese_v2, "Varie (€)")

c_tot1, c_tot2, c_tot3, c_tot4 = st.columns(4)
c_tot1.metric("Totale Km", f"{km_totali:.0f} Km", f"€ {totale_rimborso_km:.2f}")
c_tot2.metric("Totale Autostrade", f"€ {autostrada_totale:.2f}")
c_tot3.metric("Totale Vitto", f"€ {vitto_totale:.2f}")
c_tot4.metric("Totale Varie", f"€ {varie_totale:.2f}")

st.divider()

# --- SEZIONE TELEPASS ---
st.subheader(f"🚗 2. Gestione Spese Telepass - {st.session_state['mese_nota_spese']}")

col_tele1, col_tele2 = st.columns([1, 2])

with col_tele1:
    with st.container(border=True):
        st.markdown("#### 📎 Allega Foto / PDF Spese Telepass")
        
        file_telepass = st.file_uploader(
            "Carica foto o PDF del Telepass",
            type=["jpg", "jpeg", "png", "pdf"],
            key="uploader_telepass_stabile"
        )
        
        if file_telepass is not None:
            if file_telepass.type.startswith("image"):
                bytes_t, type_t = ridimensiona_immagine(file_telepass)
            else:
                bytes_t = file_telepass.getvalue()
                type_t = file_telepass.type
                
            st.session_state["telepass_file_bytes"] = bytes_t
            st.session_state["telepass_file_type"] = type_t
            st.session_state["telepass_file_name"] = file_telepass.name
            salva_bozza_automatica()
            st.success("✅ File Telepass salvato!")

        if st.session_state.get("telepass_file_bytes"):
            t_fname = st.session_state.get("telepass_file_name", "Allegato_Telepass")
            mostra_anteprima_scontrino(
                st.session_state["telepass_file_bytes"],
                t_fname,
                height=180,
                m_type_override=st.session_state.get("telepass_file_type")
            )
            
            col_t_act1, col_t_act2 = st.columns(2)
            with col_t_act1:
                if st.button("🔍 Ingrandisci", key="zoom_telepass", use_container_width=True):
                    mostra_scontrino_modal(
                        st.session_state["telepass_file_bytes"],
                        t_fname,
                        m_type_override=st.session_state.get("telepass_file_type")
                    )
            with col_t_act2:
                st.button(
                    "🗑 Elimina File",
                    key="del_telepass_file",
                    on_click=elimina_telepass,
                    use_container_width=True
                )

with col_tele2:
    with st.container(border=True):
        st.markdown("#### 💳 Spese Mensili Telepass")
        
        st.data_editor(
            st.session_state.dati_telepass,
            num_rows="dynamic",
            use_container_width=True,
            key="editor_telepass_stabile",
            on_change=on_change_telepass,
            column_config={
                "Data": st.column_config.DateColumn("Data Spesa", format="DD/MM/YYYY"),
                "Tratta / Descrizione": st.column_config.TextColumn("Tratta / Descrizione Spesa"),
                "Importo (€)": st.column_config.NumberColumn("Importo (€)", min_value=0.0, format="%.2f €", default=0.0)
            }
        )
        
        totale_telepass = calcola_somma_sicura(st.session_state.dati_telepass, "Importo (€)")
        st.metric("🔴 TOTALE SPESE TELEPASS", f"€ {totale_telepass:.2f}")

st.divider()

# --- SINTESI REFERENTI ---
st.subheader("📊 3. Sintesi Referenti e Coordinatori")

if st.session_state.dati_spese_v2 is not None and not st.session_state.dati_spese_v2.empty:
    df_pivot = st.session_state.dati_spese_v2.copy()
    
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

# --- CARICAMENTO ALLEGATI E SCONTRINI ---
st.subheader(f"🧾 4. Allegati e Scontrini (Autostrada, Vitto, Varie) - {st.session_state['mese_nota_spese']}")

with st.container(border=True):
    st.markdown("#### ➕ Carica Nuovo Scontrino o Ricevuta Autostradale")
    
    col_up1, col_up2, col_up3, col_up4 = st.columns([2, 2, 2, 2])
    
    with col_up1:
        tipo_spesa_sel = st.selectbox(
            "Categoria Spesa", 
            options=["Autostrada", "Vitto", "Varie"], 
            key="tipo_spesa_uploader"
        )
    with col_up2:
        st.text_input("Mese di Riferimento", value=st.session_state["mese_nota_spese"], disabled=True)
    with col_up3:
        data_scontrino_sel = st.date_input("Data Scontrino", value=date.today(), key="data_scontrino_uploader")
    with col_up4:
        importo_scontrino_sel = st.number_input("Importo (€)", min_value=0.0, value=0.0, step=0.50, format="%.2f", key="importo_scontrino_uploader")

    nuovi_file = st.file_uploader(
        "📎 Seleziona Foto Scontrino Autostrada / Ricevuta (JPG, PNG, PDF)",
        type=["jpg", "jpeg", "png", "pdf"],
        accept_multiple_files=True,
        key="nuovi_scontrini_uploader"
    )

    if nuovi_file:
        for f_item in nuovi_file:
            if f_item.name not in [x["name"] for x in st.session_state.allegati_dkv_list]:
                if f_item.type.startswith("image"):
                    bytes_data, m_type = ridimensiona_immagine(f_item)
                else:
                    bytes_data = f_item.getvalue()
                    m_type = f_item.type
                    
                st.session_state.allegati_dkv_list.append({
                    "name": f_item.name,
                    "file": bytes_data,
                    "type": m_type,
                    "categoria": tipo_spesa_sel,
                    "importo": float(importo_scontrino_sel),
                    "data": str(data_scontrino_sel),
                    "mese_riferimento": st.session_state["mese_nota_spese"]
                })
        salva_bozza_automatica()
        st.rerun()

# --- ELENCO ALLEGATI CARICATI ---
if st.session_state.allegati_dkv_list:
    st.markdown(f"### 📋 Elenco Scontrini / Ricevute per {st.session_state['mese_nota_spese']}")
    
    elementi_mese = [
        (idx, item) for idx, item in enumerate(st.session_state.allegati_dkv_list)
        if item.get("mese_riferimento") == st.session_state["mese_nota_spese"]
    ]
    
    if elementi_mese:
        cols_foto = st.columns(4)
        
        for grid_idx, (real_idx, item) in enumerate(elementi_mese):
            with cols_foto[grid_idx % 4]:
                file_obj = item["file"]
                file_name = item["name"]
                m_type = item.get("type", "image/jpeg")
                cat_curr = item.get("categoria", "Varie")
                imp_curr = item.get("importo", 0.0)
                data_curr = item.get("data", str(date.today()))
                
                with st.container(border=True):
                    st.caption(f"🏷️ **{cat_curr.upper()}** | 📅 `{data_curr}`")
                    
                    nuovo_imp = st.number_input(
                        "Importo (€)",
                        min_value=0.0,
                        value=float(imp_curr),
                        step=0.50,
                        format="%.2f",
                        key=f"imp_edit_{real_idx}_{file_name}"
                    )
                    st.session_state.allegati_dkv_list[real_idx]["importo"] = nuovo_imp
                    
                    mostra_anteprima_scontrino(file_obj, file_name, height=110, m_type_override=m_type)
                    
                    col_b1, col_b2 = st.columns(2)
                    with col_b1:
                        if st.button("🔍 Ingrandisci", key=f"zoom_{real_idx}_{file_name}", use_container_width=True):
                            mostra_scontrino_modal(file_obj, file_name, m_type_override=m_type)
                    with col_b2:
                        st.button(
                            "🗑 Elimina",
                            key=f"del_{real_idx}_{file_name}",
                            on_click=elimina_scontrino,
                            args=(real_idx,),
                            use_container_width=True
                        )

st.divider()

# --- RIEPILOGO GENERALE ---
totale_generale_mese = totale_rimborso_km + autostrada_totale + vitto_totale + varie_totale + totale_telepass

st.subheader(f"📊 RIEPILOGO FINALE MENSILE - {st.session_state['mese_nota_spese']}")
st.metric(f"TOTALE COMPLESSIVO SPESE DA RIMBORSARE ({st.session_state['mese_nota_spese']})", f"€ {totale_generale_mese:.2f}")

st.divider()

# --- FIRME ---
st.subheader("✍️ Firma Dipendente e Approvazione Aziendale")

col_firma_dip, col_firma_az = st.columns(2)

with col_firma_dip:
    with st.container(border=True):
        st.markdown("#### 👤 Firma Dipendente (da File)")
        
        file_firma = st.file_uploader(
            "📁 Carica File Firma Dipendente",
            type=["png", "jpg", "jpeg", "pdf"],
            key="uploader_firma_dip_stabile"
        )
        
        if file_firma is not None:
            st.session_state["firma_dip_bytes"] = file_firma.getvalue()
            st.session_state["firma_dip_type"] = file_firma.type
            salva_bozza_automatica()
            st.success("✅ Firma caricata e salvata!")

        if st.session_state.get("firma_dip_bytes"):
            mostra_anteprima_scontrino(
                st.session_state["firma_dip_bytes"],
                "Firma_Dipendente",
                height=100,
                m_type_override=st.session_state.get("firma_dip_type")
            )
            
        data_firma_dip = st.date_input("Data Firma Dipendente", value=date.today(), key="data_firma_dip_input")

with col_firma_az:
    with st.container(border=True):
        st.markdown("#### 🏢 Approvazione Winner Soc. Coop.")
        
        st.selectbox(
            "Stato Approvazione:",
            options=["In Attesa di Verifica", "Approvato", "Rifiutato / In Revisione"],
            key="stato_approvazione_select"
        )
        
        file_firma_resp = st.file_uploader(
            "📁 Carica File Firma Responsabile (opzionale)",
            type=["png", "jpg", "jpeg", "pdf"],
            key="uploader_firma_resp_stabile"
        )
        
        if file_firma_resp is not None:
            st.session_state["firma_resp_bytes"] = file_firma_resp.getvalue()
            st.session_state["firma_resp_type"] = file_firma_resp.type
            salva_bozza_automatica()
            st.success("✅ Firma Responsabile caricata e salvata!")

        if st.session_state.get("firma_resp_bytes"):
            mostra_anteprima_scontrino(
                st.session_state["firma_resp_bytes"],
                "Firma_Responsabile",
                height=100,
                m_type_override=st.session_state.get("firma_resp_type")
            )
            
        st.date_input("Data Approvazione", value=date.today(), key="data_approvazione_input")

note_finali = st.text_area("📝 Note / Comunicazioni per l'Amministrazione", value=st.session_state.get("note_finali_user", ""), key="note_finali_input")
st.session_state["note_finali_user"] = note_finali

st.divider()

# --- ESPORTAZIONE CSV ---
st.download_button(
    label=f"📥 Scarica Nota Spese {st.session_state['mese_nota_spese']} (CSV)",
    data=st.session_state.dati_spese_v2.to_csv(index=False).encode('utf-8'),
    file_name=f"Nota_Spese_{cognome}_{st.session_state['mese_nota_spese'].replace(' ', '_')}.csv",
    mime="text/csv",
    use_container_width=True
)
