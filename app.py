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
        tryTo fix this error, you need to close the string or make it a multi-line formatted string. In Python, standard f-strings (`f"..."`) cannot span multiple lines unless you either use a triple-quoted f-string (`f"""..."""`) or close the string on the same line.

Here are two ways to fix line 234 depending on what you are trying to do:

### Option 1: Keep it on a single line (Recommended if brief)
If the string ends on that same line, ensure you add the closing double quote `"` at the end:

```python
info_text = f"**Dipendente:** {nome_dip} {cognome_dip}"
