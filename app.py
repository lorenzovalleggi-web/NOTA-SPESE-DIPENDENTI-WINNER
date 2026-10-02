# --- GESTIONE ALLEGATI / SCONTRINI (AUTOSTRADA, VITTO, VARIE) CON ANTEPRIMA IMMEDIATA ---
st.subheader("🧾 Gestione Allegati / Scontrini (Autostrada, Vitto, Varie)")
st.info("Carica gli scontrini selezionando categoria, data, importo e mese. L'anteprima verrà mostrata subito dopo la selezione del file.")

# 1. FORM CARICAMENTO SCONTRINI CON ANTEPRIMA LIVE INSERITA NEL FORM
with st.container(border=True):
    st.markdown("#### ➕ Carica Nuovo Scontrino o Ricevuta")
    
    col_up1, col_up2, col_up3, col_up4 = st.columns([2, 2, 2, 2])
    
    with col_up1:
        tipo_spesa_sel = st.selectbox(
            "Categoria Spesa",
            options=["Autostrada", "Vitto", "Varie"],
            key="tipo_spesa_uploader"
        )
    
    with col_up2:
        anno_corrente = date.today().year
        opzioni_mesi = [f"{m} {anno_corrente}" for m in MESI_ANNO]
        mese_corrente_idx = date.today().month - 1
        
        mese_rif_sel = st.selectbox(
            "Mese di Riferimento",
            options=opzioni_mesi,
            index=mese_corrente_idx,
            key="mese_rif_uploader"
        )
        
    with col_up3:
        data_scontrino_sel = st.date_input("Data Scontrino", value=date.today(), key="data_scontrino_uploader")
        
    with col_up4:
        importo_scontrino_sel = st.number_input("Importo (€)", min_value=0.0, step=0.50, format="%.2f", key="importo_scontrino_uploader")

    nuovi_file = st.file_uploader(
        "📎 Seleziona File Scontrino (JPG, PNG, PDF)",
        type=["jpg", "jpeg", "png", "pdf"],
        accept_multiple_files=True,
        key="nuovi_scontrini_uploader"
    )

    # ANTEPRIMA IMMEDIATA DEI FILE SELEZIONATI
    if nuovi_file:
        st.markdown("##### 👁️ Anteprima File Selezionati in Caricamento:")
        cols_preview = st.columns(min(len(nuovi_file), 3))
        
        for idx_f, f_item in enumerate(nuovi_file):
            with cols_preview[idx_f % 3]:
                with st.container(border=True):
                    st.caption(f"📄 `{f_item.name}`")
                    mostra_anteprima_scontrino(f_item, f_item.name, height=200)

            # Aggiunta automatica alla sessione se non presente
            if f_item.name not in [x["name"] for x in st.session_state.allegati_dkv_list]:
                st.session_state.allegati_dkv_list.append({
                    "name": f_item.name,
                    "file": f_item,
                    "categoria": tipo_spesa_sel,
                    "importo": float(importo_scontrino_sel),
                    "data": data_scontrino_sel,
                    "mese_riferimento": mese_rif_sel
                })
        salva_bozza_automatica()
        st.success("✅ Scontrino/i caricati e salvati correttamente!")
