import streamlit as st
import pandas as pd
from datetime import date
from PIL import Image
import os
import json

# 1. Configurazione della pagina
st.set_page_config(page_title="Nota Spese - Winner", layout="wide")

PATH_BOZZA_LOCALE = "bozza_automatica.json"

# --- FUNZIONI DI SUPPORTO E CALLBACK ---
def salva_bozza_automatica():
    dati_da_salvare = {
        "nome": st.session_state.get("nome_user", "LORENZO"),
        "cognome": st.session_state.get("cognome_user", "VALLEGGI"),
        "spese": st.session_state.dati_spese_v2.to_dict(orient="records") if "dati_spese_v2" in st.session_state else [],
        "rifornimenti": st.session_state.rifornimenti_dkv.to_dict(orient="records") if "rifornimenti_dkv" in st.session_state else [],
        "telepass": st.session_state.dati_telepass.to_dict(orient="records") if "dati_telepass" in st.session_state else [],
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
                    st.session_state.dati_telepass = df_tel
        except Exception:
            pass

def rimuovi_allegato(indice):
    st.session_state.allegati_dkv_list.pop(indice)

@st.dialog("🔍 Visualizzazione Ingrandita Scontrino")
def mostra_scontrino_modal(file_obj, file_name):
    st.write(f"**{file_name}**")
    if file_obj.type.startswith("image"):
        img = Image.open(file_obj)
        st.image(img, use_container_width=True)
    else:
        st.info("Questo allegato è un file PDF.")
    
    st.download_button(
        label="💾 Scarica / Apri file",
        data=file_obj.getvalue(),
        file_name=file_name,
        mime=file_obj.type,
        use_container_width=True
    )

# --- INIZIALIZZAZIONE STATO DI SESSIONE ---
if "primo_avvio" not in st.session_state:
    carica_bozza_automatica()
    st.session_state["primo_avvio"] = False

if "allegati_dkv_list" not in st.session_state:
    st.session_state.allegati_dkv_list = []

if "dati_telepass" not in st.session_state:
    st.session_state.dati_telepass = pd.DataFrame(columns=["Data", "Tratta / Casello", "Importo (€)", "Categoria"])

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
    st.title("📄 NOTA SPESE DIPENDENTI E COLLABORATORI")
    st.markdown("""
    **WINNER SOCIETÀ COOPERATIVA**  
    *Sede Legale / Operativa:* Civitavecchia (RM) | *Tel:* 0766 505 197
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

# --- BARRA DI RIPRISTINO/SALVATAGGIO ---
col_salva1, col_salva2, col_salva3 = st.columns([2, 2, 2])
with col_salva1:
    if st.button("💾 Salva Dati Correnti", type="primary", use_container_width=True):
        salva_bozza_automatica()
        st.success("Dati salvati con successo!")
with col_salva2:
    if st.button("🔄 Ripristina Dati Salvati", use_container_width=True):
        carica_bozza_automatica()
        st.rerun()
with col_salva3:
    if st.button("🗑️ Svuota Tutto", use_container_width=True):
        if os.path.exists(PATH_BOZZA_LOCALE):
            os.remove(PATH_BOZZA_LOCALE)
        st.session_state.dati_spese_v2 = crea_df_iniziale()
        st.session_state.rifornimenti_dkv = pd.DataFrame([])
        st.session_state.dati_telepass = pd.DataFrame(columns=["Data", "Tratta / Casello", "Importo (€)", "Categoria"])
        st.session_state.prospetto_telepass_originale = None
        st.session_state.file_telepass_info = None
        st.session_state.allegati_dkv_list = []
        st.session_state.firma_dipendente = ""
        st.session_state.firma_approvatore = ""
        st.rerun()

st.divider()

# --- SEZIONE TELEPASS: CARICAMENTO E PROSPETTO DETTAGLIATO ---
st.subheader("🚗 1. Prospetto e Gestione Pedaggi Telepass")

file_telepass = st.file_uploader(
    "📎 Carica Prospetto / File Telepass (CSV, Excel o PDF)",
    type=["csv", "xlsx", "xls", "pdf"],
    key="uploader_telepass"
)

if file_telepass is not None:
    try:
        if file_telepass.name.endswith('.csv'):
            st.session_state.prospetto_telepass_originale = pd.read_csv(file_telepass)
            st.session_state.file_telepass_info = {"type": "csv", "name": file_telepass.name}
        elif file_telepass.name.endswith(('.xlsx', '.xls')):
            st.session_state.prospetto_telepass_originale = pd.read_excel(file_telepass)
            st.session_state.file_telepass_info = {"type": "excel", "name": file_telepass.name}
        elif file_telepass.name.endswith('.pdf'):
            st.session_state.prospetto_telepass_originale = None
            st.session_state.file_telepass_info = {
                "type": "pdf",
                "name": file_telepass.name,
                "bytes": file_telepass.getvalue()
            }
    except Exception as e:
        st.error(f"Errore nella lettura del file Telepass: {e}")

# Visualizzazione SEMPRE ATTIVA del prospetto caricato
if st.session_state.prospetto_telepass_originale is not None:
    st.markdown("### 📊 Prospetto Spese Telepass Caricato")
    st.dataframe(st.session_state.prospetto_telepass_originale, use_container_width=True)
elif st.session_state.file_telepass_info and st.session_state.file_telepass_info.get("type") == "pdf":
    st.markdown("### 📄 Documento Telepass PDF Caricato")
    info = st.session_state.file_telepass_info
    st.success(f"File allegato: **{info['name']}**")
    st.download_button(
        label="📥 Apri / Scarica PDF Telepass Caricato",
        data=info["bytes"],
        file_name=info["name"],
        mime="application/pdf"
    )

st.markdown("#### 📝 Dettaglio e Totale Spese Telepass")

# Calcolo totale spese Telepass
totale_telepass_calc = 0.0
if not st.session_state.dati_telepass.empty and "Importo (€)" in st.session_state.dati_telepass.columns:
    totale_telepass_calc = pd.to_numeric(st.session_state.dati_telepass["Importo (€)"], errors='coerce').fillna(0).sum()

col_tele_tot1, col_tele_tot2 = st.columns([1, 2])
with col_tele_tot1:
    st.metric("TOTALE SPESE TELEPASS", f"€ {totale_telepass_calc:.2f}")

# Tabella interattiva per imputazione giorno per giorno o dettaglio
df_telepass_edited = st.data_editor(
    st.session_state.dati_telepass,
    num_rows="dynamic",
    use_container_width=True,
    key="editor_telepass",
    column_config={
        "Data": st.column_config.DateColumn("Data Pedaggio", format="DD/MM/YYYY"),
        "Tratta / Casello": st.column_config.TextColumn("Tratta / Note"),
        "Importo (€)": st.column_config.NumberColumn("Importo (€)", min_value=0.0, format="%.2f €"),
        "Categoria": st.column_config.SelectboxColumn("Categoria Spesa", options=["Cat. A", "Cat. B"])
    }
)
st.session_state.dati_telepass = df_telepass_edited.copy()

# Pulsanti per riportare le spese nella nota generale
btn_col_t1, btn_col_t2 = st.columns(2)

with btn_col_t1:
    if st.button("➕ Aggiungi Totale Telepass in Nota Spese", type="primary", use_container_width=True):
        if totale_telepass_calc > 0:
            df_spese_curr = st.session_state.dati_spese_v2.copy()
            nuova_riga = {
                "Data": date.today(),
                "Comune": "Totale Prospetto Telepass",
                "Coordinatore di Zona": "",
                "Km_A": 0, "Autostrade_A": totale_telepass_calc,
                "Vitto_A": 0.0, "Varie_A": 0.0,
                "Km_B": 0, "Autostrade_B": 0.0,
                "Vitto_B": 0.0, "Varie_B": 0.0
            }
            df_spese_curr = pd.concat([df_spese_curr, pd.DataFrame([nuova_riga])], ignore_index=True)
            st.session_state.dati_spese_v2 = df_spese_curr
            salva_bozza_automatica()
            st.success(f"Totale Telepass (€ {totale_telepass_calc:.2f}) aggiunto alla nota spese!")
            st.rerun()

with btn_col_t2:
    if st.button("🔄 Trasferisci Pedaggi Giornalieri nella Nota Spese", use_container_width=True):
        if not df_telepass_edited.empty and "Data" in df_telepass_edited.columns:
            df_tel_clean = df_telepass_edited.dropna(subset=["Data"]).copy()
            df_spese_curr = st.session_state.dati_spese_v2.copy()
            
            for idx, row in df_tel_clean.iterrows():
                data_pedaggio = row["Data"]
                importo = float(row.get("Importo (€)", 0.0) or 0.0)
                categoria = row.get("Categoria", "Cat. A")
                
                mask = df_spese_curr["Data"] == data_pedaggio
                if mask.any():
                    if categoria == "Cat. B":
                        df_spese_curr.loc[mask, "Autostrade_B"] = df_spese_curr.loc[mask, "Autostrade_B"] + importo
                    else:
                        df_spese_curr.loc[mask, "Autostrade_A"] = df_spese_curr.loc[mask, "Autostrade_A"] + importo
                else:
                    nuova_riga = {
                        "Data": data_pedaggio,
                        "Comune": "Da Prospetto Telepass",
                        "Coordinatore di Zona": "",
                        "Km_A": 0, "Autostrade_A": importo if categoria != "Cat. B" else 0.0,
                        "Vitto_A": 0.0, "Varie_A": 0.0,
                        "Km_B": 0, "Autostrade_B": importo if categoria == "Cat. B" else 0.0,
                        "Vitto_B": 0.0, "Varie_B": 0.0
                    }
                    df_spese_curr = pd.concat([df_spese_curr, pd.DataFrame([nuova_riga])], ignore_index=True)
                    
            st.session_state.dati_spese_v2 = df_spese_curr
            salva_bozza_automatica()
            st.success("Spese autostradali aggiunte correttamente alla nota spese!")
            st.rerun()

st.divider()

# --- TABELLA PRINCIPALE VOCI DI SPESA ---
st.subheader("📋 2. Inserimento Voci di Spesa Giornaliere")

df_display = st.session_state.dati_spese_v2.copy()
df_display["Importo_Km_A"] = pd.to_numeric(df_display.get("Km_A", 0), errors='coerce').fillna(0) * costo_km_a
df_display["Importo_Km_B"] = pd.to_numeric(df_display.get("Km_B", 0), errors='coerce').fillna(0) * costo_km_b

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

st.session_state.dati_spese_v2 = df_edit.drop(columns=["Importo_Km_A", "Importo_Km_B"], errors="ignore").copy()
salva_bozza_automatica()

st.divider()

# --- SEZIONE RIFORNIMENTI CARTA DKV ---
st.subheader("⛽ Registrazione Rifornimenti Carta DKV")

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

st.divider()

# --- GESTIONE ALLEGATI / SCONTRINI ---
st.subheader("🧾 Gestione Allegati / Scontrini")
st.info("Le immagini sono visualizzate in formato compatto. Usa **🔍 Ingrandisci** per il popup a schermo intero o **📥 Scarica / Apri** per visualizzarle con l'applicazione del computer.")

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

if st.session_state.allegati_dkv_list:
    st.write(f"**Scontrini allegati:** {len(st.session_state.allegati_dkv_list)}")
    cols_foto = st.columns(4)

    for idx, item in enumerate(st.session_state.allegati_dkv_list):
        col_curr = cols_foto[idx % 4]
        with col_curr:
            file_obj = item["file"]
            file_name = item["name"]
            
            with st.container(border=True):
                if file_obj.type.startswith("image"):
                    img = Image.open(file_obj)
                    st.image(img, use_container_width=True)
                else:
                    st.markdown("📄 **Allegato PDF**")

                st.caption(file_name)
                
                if st.button("🔍 Ingrandisci", key=f"zoom_{idx}_{file_name}", use_container_width=True):
                    mostra_scontrino_modal(file_obj, file_name)
                
                st.download_button(
                    label="📥 Scarica / Apri",
                    data=file_obj.getvalue(),
                    file_name=file_name,
                    mime=file_obj.type,
                    key=f"dl_{idx}_{file_name}",
                    use_container_width=True
                )
                
                st.button(
                    "🗑️ Rimuovi", 
                    key=f"del_{idx}_{file_name}", 
                    on_click=rimuovi_allegato, 
                    args=(idx,), 
                    use_container_width=True
                )

st.divider()

# --- SEZIONE FIRME ---
st.subheader("✍️ Firme e Approvazione")

col_firma1, col_firma2 = st.columns(2)

with col_firma1:
    st.markdown("**Firma del Dipendente / Collaboratore**")
    firma_dip = st.text_input(
        "Nome e Cognome per Firma Digitale / Sigla Dipendente",
        value=st.session_state.get("firma_dipendente", f"{st.session_state.get('nome_user', '')} {st.session_state.get('cognome_user', '')}"),
        key="firma_dipendente_input"
    )
    st.session_state["firma_dipendente"] = firma_dip
    if firma_dip:
        st.info(f"Signed digitally by: **{firma_dip}** in data {date.today().strftime('%d/%m/%Y')}")

with col_firma2:
    st.markdown("**Firma per Approvazione / Responsabile**")
    firma_appr = st.text_input(
        "Nome e Cognome Responsabile / Coordinatore",
        value=st.session_state.get("firma_approvatore", ""),
        key="firma_approvatore_input",
        placeholder="Es. Coordinatore di Zona / Direzione"
    )
    st.session_state["firma_approvatore"] = firma_appr
    if firma_appr:
        st.success(f"Approved by: **{firma_appr}** in data {date.today().strftime('%d/%m/%Y')}")

st.divider()

# --- TOTALE E ESPORTAZIONE ---
df_finale = df_edit.copy()
if not df_finale.empty:
    km_a_sum = pd.to_numeric(df_finale.get("Km_A", 0), errors='coerce').fillna(0).sum()
    km_b_sum = pd.to_numeric(df_finale.get("Km_B", 0), errors='coerce').fillna(0).sum()
    totale_rimborso_km = (km_a_sum * costo_km_a) + (km_b_sum * costo_km_b)

    auto = pd.to_numeric(df_finale.get("Autostrade_A", 0), errors='coerce').fillna(0).sum() + pd.to_numeric(df_finale.get("Autostrade_B", 0), errors='coerce').fillna(0).sum()
    vitto = pd.to_numeric(df_finale.get("Vitto_A", 0), errors='coerce').fillna(0).sum() + pd.to_numeric(df_finale.get("Vitto_B", 0), errors='coerce').fillna(0).sum()
    varie = pd.to_numeric(df_finale.get("Varie_A", 0), errors='coerce').fillna(0).sum() + pd.to_numeric(df_finale.get("Varie_B", 0), errors='coerce').fillna(0).sum()

    totale_generale = totale_rimborso_km + auto + vitto + varie

    st.subheader("📊 RIEPILOGO TOTALE")
    st.metric("TOTALE GENERALE PAGATO", f"€ {totale_generale:.2f}")

    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        st.download_button(
            label="📥 Scarica Nota Spese Finale (CSV)",
            data=df_finale.to_csv(index=False).encode('utf-8'),
            file_name=f"Nota_Spese_{cognome}.csv",
            mime="text/csv"
        )
    with btn_col2:
        st.download_button(
            label="💾 Scarica File Bozza (.json)",
            data=df_finale.to_json(orient="records", date_format="iso"),
            file_name=f"Bozza_Nota_Spese_{cognome}.json",
            mime="application/json"
        )
