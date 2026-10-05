import streamlit as st
import pandas as pd
from datetime import date, datetime
import calendar
from PIL import Image
import os
import json
import base64
import io

# Import per la generazione del PDF con ReportLab
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# 1. Configurazione della pagina Streamlit
st.set_page_config(page_title="Nota Spese Mensile - Winner", layout="wide")

FILE_SALVATAGGIO = "nota_spese_dati.json"

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

# --- INIZIALIZZAZIONE SESSION STATE ---
if "primo_avvio" not in st.session_state:
    st.session_state["primo_avvio"] = False

if "allegati_dkv_list" not in st.session_state:
    st.session_state.allegati_dkv_list = []

if "uploader_key_counter" not in st.session_state:
    st.session_state.uploader_key_counter = 0

default_mese = f"{MESI_ANNO[date.today().month - 1]} {date.today().year}"
if "mese_nota_spese" not in st.session_state:
    st.session_state["mese_nota_spese"] = default_mese

# --- CONVERSIONE E NORMALIZZAZIONE DATE ---
def assicura_formato_data(val):
    if pd.isna(val) or val is None or str(val).strip() == "":
        return date.today()
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, pd.Timestamp):
        return val.date()
    if isinstance(val, str):
        try:
            return pd.to_datetime(val).date()
        except Exception:
            return date.today()
    return date.today()

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

    if "Data" in df.columns:
        df["Data"] = df["Data"].apply(assicura_formato_data)
        
    return df

def genera_df_mese_completo(str_mese_anno, df_esistente=None):
    try:
        parti = str_mese_anno.split()
        nome_mese = parti[0]
        anno = int(parti[1])
        idx_mese = MESI_ANNO.index(nome_mese) + 1
    except Exception:
        idx_mese = date.today().month
        anno = date.today().year

    num_giorni = calendar.monthrange(anno, idx_mese)[1]
    
    mappa_dati = {}
    if df_esistente is not None and not df_esistente.empty:
        for _, row in df_esistente.iterrows():
            d_val = assicura_formato_data(row.get("Data"))
            mappa_dati[d_val] = row

    righe = []
    for g in range(1, num_giorni + 1):
        cur_date = date(anno, idx_mese, g)
        if cur_date in mappa_dati:
            r = mappa_dati[cur_date].to_dict()
            r["Data"] = cur_date
            righe.append(r)
        else:
            righe.append({
                "Data": cur_date,
                "Comune": "",
                "Coordinatore": "",
                "Km": 0,
                "Autostrada (€)": 0.0,
                "Vitto (€)": 0.0,
                "Varie (€)": 0.0
            })
            
    df_res = pd.DataFrame(righe)
    return normalizza_dataframe(df_res)

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
        if isinstance(file_uploaded, bytes):
            return file_uploaded, "application/octet-stream"
        elif hasattr(file_uploaded, 'getvalue'):
            return file_uploaded.getvalue(), getattr(file_uploaded, "type", "application/octet-stream")
        return None, "application/octet-stream"

def calcola_somma_sicura(df, nome_colonna):
    if df is not None and not df.empty and nome_colonna in df.columns:
        return pd.to_numeric(df[nome_colonna], errors='coerce').fillna(0).sum()
    return 0.0

def elimina_scontrino(index_to_remove):
    if 0 <= index_to_remove < len(st.session_state.allegati_dkv_list):
        st.session_state.allegati_dkv_list.pop(index_to_remove)
        st.session_state.uploader_key_counter += 1

def elimina_telepass():
    st.session_state.pop("telepass_file_bytes", None)
    st.session_state.pop("telepass_file_type", None)
    st.session_state.pop("telepass_file_name", None)

def elimina_firma_dip():
    st.session_state.pop("firma_dip_bytes", None)
    st.session_state.pop("firma_dip_type", None)

def elimina_firma_resp():
    st.session_state.pop("firma_resp_bytes", None)
    st.session_state.pop("firma_resp_type", None)

def mostra_anteprima_scontrino(file_obj, file_name, height=130, m_type_override=None):
    if isinstance(file_obj, bytes):
        b_data = file_obj
        m_type = m_type_override or 'image/jpeg'
    elif hasattr(file_obj, 'getvalue'):
        b_data = file_obj.getvalue()
        m_type = getattr(file_obj, 'type', 'image/jpeg')
    else:
        st.info(f"📄 Allegato (`{file_name}`)")
        return

    if str(m_type).startswith("image"):
        try:
            img = Image.open(io.BytesIO(b_data))
            st.image(img, use_container_width=True)
        except Exception:
            st.info("🖼️ Immagine Allegata")
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
    
    if isinstance(file_obj, bytes):
        b_data = file_obj
        m_type = m_type_override or 'application/octet-stream'
    elif hasattr(file_obj, 'getvalue'):
        b_data = file_obj.getvalue()
        m_type = getattr(file_obj, 'type', 'application/octet-stream')
    else:
        return
    
    st.download_button(
        label="💾 Scarica File Originale",
        data=b_data,
        file_name=file_name,
        mime=m_type,
        use_container_width=True
    )

# --- FUNZIONE GENERAZIONE PDF SETTIMANALE ---
def genera_pdf_settimanale(df_settimana, nome_dip, cognome_dip, d_inizio, d_fine, costo_km=0.25):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, leading=20, textColor=colors.HexColor("#1A365D"))
    subtitle_style = ParagraphStyle('SubTitleStyle', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.gray)
    cell_style = ParagraphStyle('Cell', parent=styles['Normal'], fontSize=8, leading=10)
    
    story.append(Paragraph("**WINNER SOCIETÀ COOPERATIVA**", title_style))
    story.append(Paragraph("REPORT SETTIMANALE NOTA SPESE", ParagraphStyle('Sub', parent=title_style, fontSize=12, textColor=colors.HexColor("#2B6CB0"))))
    story.append(Spacer(1, 10))
    
    str_d_start = d_inizio.strftime('%d/%m/%Y')
    str_d_end = d_fine.strftime('%d/%m/%Y')
    str_now = datetime.now().strftime('%d/%m/%Y %H:%M')
    info_text = "**Dipendente:** " + str(nome_dip) + " " + str(cognome_dip) + "
