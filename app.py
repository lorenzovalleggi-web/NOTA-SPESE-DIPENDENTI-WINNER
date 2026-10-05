import streamlit as st
import pandas as pd
from datetime import date, datetime
import calendar
from PIL import Image
import os
import json
import base64
import io

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
        # Forza il reset del file_uploader per evitare il ricaricamento
        st.session_state.uploader_key_counter += 1

def elimina_telepass():
    st.session_state.pop("telepass_file_bytes", None)
    st.session_state.pop("telepass_file_type", None)
    st.session_state.pop("telepass_file_name", None)

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

# --- FUNZIONALITÀ SALVATAGGIO PERMANENTE BOZZA ---
def salva_stato_completo():
    """Salva su disco locale tutti i dati correnti, compresi gli scontrini in Base64."""
    try:
        allegati_salvabili = []
        for item in st.session_state.get("allegati_dkv_list", []):
            item_copy = item.copy()
            if isinstance(item_copy.get("file"), bytes):
                item_copy["file"] = base64.b64encode(item_copy["file"]).decode('utf-8')
            allegati_salvabili.append(item_copy)

        telepass_bytes_b64 = None
        if st.session_state.get("telepass_file_bytes"):
            telepass_bytes_b64 = base64.b64encode(st.session_state["telepass_file_bytes"]).decode('utf-8')

        data_to_save = {
            "nome": st.session_state.get("nome_user", "LORENZO"),
            "cognome": st.session_state.get("cognome_user", "VALLEGGI"),
            "mese": st.session_state.get("mese_nota_spese", default_mese),
            "spese": st.session_state.dati_spese_v2.to_dict(orient="records") if st.session_state.get("dati_spese_v2") is not None else [],
            "telepass": st.session_state.dati_telepass.to_dict(orient="records") if st.session_state.get("dati_telepass") is not None else [],
            "telepass_file": {
                "bytes": telepass_bytes_b64,
                "type": st.session_state.get("telepass_file_type"),
                "name": st.session_state.get("telepass_file_name")
            },
            "allegati_dkv": allegati_salvabili,
            "note": st.session_state.get("note_finali_user", "")
        }
        for row in data_to_save["spese"]:
            row["Data"] = str(row["Data"])
        for row in data_to_save["telepass"]:
            row["Data"] = str(row["Data"])

        with open(FILE_SALVATAGGIO, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        st.error(f"Errore durante il salvataggio: {e}")
        return False

def carica_stato_completo():
    """Carica i dati e ripristina anche gli scontrini convertendo da Base64."""
    if os.path.exists(FILE_SALVATAGGIO):
        try:
            with open(FILE_SALVATAGGIO, "r", encoding="utf-8") as f:
                dati = json.load(f)
                
            if "spese" in dati and dati["spese"]:
                df_spese = pd.DataFrame(dati["spese"])
                df_spese["Data"] = df_spese["Data"].apply(assicura_formato_data)
                st.session_state.dati_spese_v2 = normalizza_dataframe(df_spese)
                
            if "telepass" in dati and dati["telepass"]:
                df_tel = pd.DataFrame(dati["telepass"])
                if "Tratta / Descrizione" in df_tel.columns:
                    df_tel = df_tel.drop(columns=["Tratta / Descrizione"])
                df_tel["Data"] = df_tel["Data"].apply(assicura_formato_data)
                st.session_state.dati_telepass = df_tel

            if "allegati_dkv" in dati and dati["allegati_dkv"]:
                allegati_ripristinati = []
                for item in dati["allegati_dkv"]:
                    item_copy = item.copy()
                    if isinstance(item_copy.get("file"), str):
                        item_copy["file"] = base64.b64decode(item_copy["file"].encode('utf-8'))
                    allegati_ripristinati.append(item_copy)
                st.session_state.allegati_dkv_list = allegati_ripristinati

            if "telepass_file" in dati and dati["telepass_file"] and dati["telepass_file"].get("bytes"):
                tf = dati["telepass_file"]
                st.session_state["telepass_file_bytes"] = base64.b64decode(tf["bytes"].encode('utf-8'))
                st.session_state["telepass_file_type"] = tf.get("type")
                st.session_state["telepass_file_name"] = tf.get("name")

            if "nome" in dati:
                st.session_state["nome_user"] = dati["nome"]
            if "cognome" in dati:
                st.session_state["cognome_user"] = dati["cognome"]
            if "mese" in dati:
                st.session_state["mese_nota_spese"] = dati["mese"]
            if "note" in dati:
                st.session_state["note_finali_user"] = dati["note"]
            return True
        except Exception as e:
            st.error(f"Errore nel caricamento della bozza: {e}")
    return False

# Inizializzazione automatico all'avvio
if not st.session_state["primo_avvio"]:
    carica_stato_completo()
    st.session_state["primo_avvio"] = True

# Inizializzazione dataframe spese
if "dati_spese_v2" not in st.session_state or st.session_state.dati_spese_v2 is None:
    st.session_state.dati_spese_v2 = genera_df_mese_completo(st.session_state["mese_nota_spese"])
else:
    st.session_state.dati_spese_v2 = normalizza_dataframe(st.session_state.dati_spese_v2)

# Inizializzazione Telepass
if "dati_telepass" not in st.session_state or st.session_state.dati_telepass is None:
    st.session_state.dati_telepass = pd.DataFrame(columns=["Data", "Importo (€)"])
else:
    if "Tratta / Descrizione" in st.session_state.dati_telepass.columns:
        st.session_state.dati_telepass = st.session_state.dati_telepass.drop(columns=["Tratta / Descrizione"])
    if "Data" in st.session_state.dati_telepass.columns:
        st.session_state.dati_telepass["Data"] = st.session_state.dati_telepass["Data"].apply(assicura_formato_data)

# Callback per memorizzazione istantanea Telepass
def aggiorna_telepass():
    if "editor_telepass_stabile" in st.session_state:
        edited_data = st.session_state["editor_telepass_stabile"]
        df_temp = st.session_state.dati_telepass.copy()
        
        for row_idx, changes in edited_data.get("edited_rows", {}).items():
            for k, v in changes.items():
                df_temp.iloc[row_idx, df_temp.columns.get_loc(k)] = v
                
        for new_row in edited_data.get("added_rows", []):
            df_temp = pd.concat([df_temp, pd.DataFrame([new_row])], ignore_index=True)
            
        deleted_indices = edited_data.get("deleted_rows", [])
        if deleted_indices:
            df_temp = df_temp.drop(index=deleted_indices).reset_index(drop=True)
            
        if "Data" in df_temp.columns:
            df_temp["Data"] = df_temp["Data"].apply(assicura_formato_data)
            
        st.session_state.dati_telepass = df_temp

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
    nome = st.text_input("Nome", value=st.session_state.get("nome_user", "LORENZO"), key="nome_input")
    st.session_state["nome_user"] = nome

with col_a2:
    cognome = st.text_input("Cognome", value=st.session_state.get("cognome_user", "VALLEGGI"), key="cognome_input")
    st.session_state["cognome_user"] = cognome

with col_a3:
    opzioni_mesi_anno = [f"{m} {anno}" for anno in ANNI_DISPONIBILI for m in MESI_ANNO]
    idx_default = opzioni_mesi_anno.index(st.session_state["mese_nota_spese"]) if st.session_state["mese_nota_spese"] in opzioni_mesi_anno else 0
    
    mese_selezionato = st.selectbox(
        "📅 MESE DI RIFERIMENTO NOTA SPESE",
        options=opzioni_mesi_anno,
        index=idx_default,
        key="select_mese_principale"
    )
    
    if mese_selezionato != st.session_state["mese_nota_spese"]:
        st.session_state["mese_nota_spese"] = mese_selezionato
        st.session_state.dati_spese_v2 = genera_df_mese_completo(mese_selezionato, st.session_state.dati_spese_v2)
        st.rerun()

with col_a4:
    costo_km_a = st.number_input("Rimborso Km (€)", value=0.25, disabled=True)

st.info(f"📌 **Nota Spese Mensile in elaborazione per il periodo:** `{st.session_state['mese_nota_spese']}`")

# --- PULSANTI DI CONTROLLO BOZZA ---
col_salva1, col_salva2, col_salva3 = st.columns([2, 2, 2])
with col_salva1:
    if st.button("💾 SALVA BOZZA (Permanente)", type="primary", use_container_width=True):
        if salva_stato_completo():
            st.success("✅ Dati e Scontrini salvati con successo!")
with col_salva2:
    if st.button("🔄 CARICA ULTIMA BOZZA SALVATA", use_container_width=True):
        if carica_stato_completo():
            st.success("✅ Bozza e Scontrini ripristinati correttamente!")
            st.rerun()
with col_salva3:
    if st.button("🗑 Svuota Mese Corrente", use_container_width=True):
        st.session_state.dati_spese_v2 = genera_df_mese_completo(st.session_state["mese_nota_spese"])
        st.rerun()

st.divider()

# --- TABELLA VOCI SPESA GIORNALIERE ---
st.subheader(f"📋 1. Voci Spesa Giornaliere - Mese Completo ({st.session_state['mese_nota_spese']})")

spese_modificate = st.data_editor(
    st.session_state.dati_spese_v2,
    num_rows="fixed",
    use_container_width=True,
    key="editor_spese_stabile",
    column_config={
        "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY", disabled=True),
        "Comune": st.column_config.TextColumn("Comune / Note"),
        "Coordinatore": st.column_config.SelectboxColumn("Coordinatore di Zona", options=COORDINATORI),
        "Km": st.column_config.NumberColumn("Km Percorsi", min_value=0, step=1, default=0),
        "Autostrada (€)": st.column_config.NumberColumn("Autostrade (€)", min_value=0.0, format="%.2f €", default=0.0),
        "Vitto (€)": st.column_config.NumberColumn("Vitto (€)", min_value=0.0, format="%.2f €", default=0.0),
        "Varie (€)": st.column_config.NumberColumn("Varie (€)", min_value=0.0, format="%.2f €", default=0.0),
    }
)

st.session_state.dati_spese_v2 = normalizza_dataframe(spese_modificate)

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
        
        # Tabella Telepass
        st.data_editor(
            st.session_state.dati_telepass,
            num_rows="dynamic",
            use_container_width=True,
            key="editor_telepass_stabile",
            on_change=aggiorna_telepass,
            column_config={
                "Data": st.column_config.DateColumn("Data Spesa", format="DD/MM/YYYY", default=date.today()),
                "Importo (€)": st.column_config.NumberColumn("Importo (€)", min_value=0.0, format="%.2f €", default=0.0)
            }
        )
        
        st.divider()
        
        # Modulo rapido per Aggiungere / Modificare
        st.markdown("##### ✏️ Modifica o Aggiungi Riga Spesa")
        
        col_m1, col_m2, col_m3 = st.columns([2, 2, 3])
        
        with col_m1:
            data_telepass_nuova = st.date_input("Data Spesa", value=date.today(), key="in_data_telepass")
        with col_m2:
            importo_telepass_nuovo = st.number_input("Importo (€)", min_value=0.0, step=0.50, format="%.2f", key="in_imp_telepass")
            
        with col_m3:
            st.write("")
            st.write("")
            if st.button("➕ Aggiungi Voce Telepass", type="primary", use_container_width=True):
                nuova_riga = pd.DataFrame([{
                    "Data": data_telepass_nuova,
                    "Importo (€)": importo_telepass_nuovo
                }])
                st.session_state.dati_telepass = pd.concat([st.session_state.dati_telepass, nuova_riga], ignore_index=True)
                st.success("Riga aggiunta con successo!")
                st.rerun()

        # Gestione/Pulizia Righe
        col_btn_t1, col_btn_t2 = st.columns(2)
        with col_btn_t1:
            if st.button("🧹 Rimuovi Righe Vuote / a Zero", use_container_width=True):
                df_temp = st.session_state.dati_telepass.copy()
                df_temp["Importo (€)"] = pd.to_numeric(df_temp["Importo (€)"], errors='coerce').fillna(0)
                st.session_state.dati_telepass = df_temp[df_temp["Importo (€)"] > 0].reset_index(drop=True)
                st.rerun()
                
        with col_btn_t2:
            if st.button("🗑️ Elimina Ultima Riga", use_container_width=True):
                if not st.session_state.dati_telepass.empty:
                    st.session_state.dati_telepass = st.session_state.dati_telepass.iloc[:-1].reset_index(drop=True)
                    st.rerun()

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
    
    col_up1, col_up2, col_up3 = st.columns([3, 3, 3])
    
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

    # Uploader con chiave dinamica per resettarlo quando si cancella uno scontrino
    uploader_key = f"nuovi_scontrini_uploader_{st.session_state.uploader_key_counter}"
    
    nuovi_file = st.file_uploader(
        "📎 Seleziona Foto Scontrino Autostrada / Ricevuta (JPG, PNG, PDF)",
        type=["jpg", "jpeg", "png", "pdf"],
        accept_multiple_files=True,
        key=uploader_key
    )

    if nuovi_file:
        file_aggiunti = False
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
                    "data": str(data_scontrino_sel),
                    "mese_riferimento": st.session_state["mese_nota_spese"]
                })
                file_aggiunti = True
        
        if file_aggiunti:
            st.rerun()

# --- ELENCO SCONTRINI IN ELENCO ORDINATO ---
if st.session_state.allegati_dkv_list:
    st.markdown(f"### 📋 Elenco Scontrini / Ricevute per {st.session_state['mese_nota_spese']}")
    
    elementi_mese = [
        (idx, item) for idx, item in enumerate(st.session_state.allegati_dkv_list)
        if item.get("mese_riferimento") == st.session_state["mese_nota_spese"]
    ]
    
    if elementi_mese:
        for real_idx, item in elementi_mese:
            file_obj = item["file"]
            file_name = item["name"]
            m_type = item.get("type", "image/jpeg")
            cat_curr = item.get("categoria", "Varie")
            data_curr = item.get("data", str(date.today()))
            
            with st.container(border=True):
                col_img, col_info, col_azioni = st.columns([2, 5, 2])
                
                with col_img:
                    mostra_anteprima_scontrino(file_obj, file_name, height=130, m_type_override=m_type)
                
                with col_info:
                    st.markdown(f"#### 📄 `{file_name}`")
                    st.markdown(f"🏷️ **Categoria:** `{cat_curr.upper()}`")
                    st.markdown(f"📅 **Data Scontrino:** `{data_curr}`")
                
                with col_azioni:
                    st.write("")
                    if st.button("🔍 Ingrandisci", key=f"zoom_lst_{real_idx}_{file_name}", use_container_width=True):
                        mostra_scontrino_modal(file_obj, file_name, m_type_override=m_type)
                    
                    if st.button("🗑 Elimina", key=f"del_lst_{real_idx}_{file_name}", use_container_width=True):
                        elimina_scontrino(real_idx)
                        st.rerun()

st.divider()

# --- RIEPILOGO GENERALE MENSILE ---
totale_generale_mese = totale_rimborso_km + autostrada_totale + vitto_totale + varie_totale + totale_telepass

st.subheader(f"📊 RIEPILOGO FINALE MENSILE - {st.session_state['mese_nota_spese']}")
st.metric(f"TOTALE COMPLESSIVO SPESE DA RIMBORSARE ({st.session_state['mese_nota_spese']})", f"€ {totale_generale_mese:.2f}")

st.divider()

# --- FIRME E APPROVAZIONE ---
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
            st.success("✅ Firma caricata e salvata!")

        if st.session_state.get("firma_dip_bytes"):
            mostra_anteprima_scontrino(
                st.session_state["firma_dip_bytes"],
                "Firma_Dipendente",
                height=100,
                m_type_override=st.session_state.get("firma_dip_type")
            )
            
        st.date_input("Data Firma Dipendente", value=date.today(), key="data_firma_dip_input")

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

# --- ESPORTAZIONE SETTIMANALE / MENSILE ---
st.subheader("📦 ESPORTAZIONE E INVIO NOTA SPESE")

tab_settimanale, tab_mensile = st.tabs(["🗓️ INVIO SETTIMANALE", "📅 INVIO MENSILE FINALE"])

with tab_settimanale:
    st.markdown("#### 📤 Estrai Spese della Settimana")
    st.info("Seleziona l'intervallo di date per esportare solo i giorni della settimana corrente da inviare.")
    
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        data_inizio_sett = st.date_input("Data Inizio Settimana", value=date.today(), key="w_start")
    with col_w2:
        data_fine_sett = st.date_input("Data Fine Settimana", value=date.today(), key="w_end")
        
    if st.session_state.dati_spese_v2 is not None and not st.session_state.dati_spese_v2.empty:
        df_spese_curr = st.session_state.dati_spese_v2.copy()
        
        df_settimana = df_spese_curr[
            (df_spese_curr["Data"] >= data_inizio_sett) & 
            (df_spese_curr["Data"] <= data_fine_sett)
        ]
        
        km_sett = pd.to_numeric(df_settimana["Km"], errors='coerce').fillna(0).sum()
        auto_sett = pd.to_numeric(df_settimana["Autostrada (€)"], errors='coerce').fillna(0).sum()
        vitto_sett = pd.to_numeric(df_settimana["Vitto (€)"], errors='coerce').fillna(0).sum()
        varie_sett = pd.to_numeric(df_settimana["Varie (€)"], errors='coerce').fillna(0).sum()
        tot_sett = (km_sett * costo_km_a) + auto_sett + vitto_sett + varie_sett
        
        st.markdown(f"**Giorni nel periodo:** `{len(df_settimana)}` | **Km:** `{km_sett:.0f}` | **Totale Settimana:** `€ {tot_sett:.2f}`")
        
        csv_settimana = df_settimana.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label=f"📥 Scarica Report Settimanale ({data_inizio_sett.strftime('%d/%m')} - {data_fine_sett.strftime('%d/%m')})",
            data=csv_settimana,
            file_name=f"Nota_Spese_Settimanale_{cognome}_{data_inizio_sett}_{data_fine_sett}.csv",
            mime="text/csv",
            type="primary",
            use_container_width=True
        )

with tab_mensile:
    st.markdown("#### 📜 Esportazione Mensile Completa")
    st.warning("Assicurati di aver salvato la bozza e verificato i dati prima di scaricare la versione finale del mese.")
    
    csv_mensile = st.session_state.dati_spese_v2.to_csv(index=False).encode('utf-8')
    
    st.download_button(
        label=f"🏆 Scarica NOTA SPESE COMPLETA MENSILE - {st.session_state['mese_nota_spese']} (CSV)",
        data=csv_mensile,
        file_name=f"Nota_Spese_MENSILE_{cognome}_{st.session_state['mese_nota_spese'].replace(' ', '_')}.csv",
        mime="text/csv",
        type="primary",
        use_container_width=True
    )
