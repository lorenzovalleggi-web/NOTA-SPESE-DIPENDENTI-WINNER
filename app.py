# --- ELENCO ALLEGATI CARICATI (LAYOUT IN ELENCO/LISTA) ---
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
                # Disposizione orizzontale a righe: Immagine a sinistra, Info e controlli a destra
                col_img, col_info, col_azioni = st.columns([2, 4, 2])
                
                with col_img:
                    mostra_anteprima_scontrino(file_obj, file_name, height=140, m_type_override=m_type)
                
                with col_info:
                    st.markdown(f"#### 📄 `{file_name}`")
                    st.markdown(f"🏷️ **Categoria:** `{cat_curr.upper()}`")
                    st.markdown(f"📅 **Data Scontrino:** `{data_curr}`")
                
                with col_azioni:
                    st.write("") # Spaziatore
                    if st.button("🔍 Ingrandisci", key=f"zoom_lst_{real_idx}_{file_name}", use_container_width=True):
                        mostra_scontrino_modal(file_obj, file_name, m_type_override=m_type)
                    
                    st.button(
                        "🗑 Elimina",
                        key=f"del_lst_{real_idx}_{file_name}",
                        on_click=elimina_scontrino,
                        args=(real_idx,),
                        use_container_width=True
                    )
