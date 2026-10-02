# --- FUNZIONE DI CALLBACK PER RIMUOVERE L'ALLEGATO ---
def rimuovi_allegato(indice):
    st.session_state.allegati_dkv_list.pop(indice)

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
                
                # Pulsante 1: Ingrandisci nel popup
                if st.button("🔍 Ingrandisci", key=f"zoom_{idx}_{file_name}", use_container_width=True):
                    mostra_scontrino_modal(file_obj, file_name)
                
                # Pulsante 2: Scarica / Apri
                st.download_button(
                    label="📥 Scarica / Apri",
                    data=file_obj.getvalue(),
                    file_name=file_name,
                    mime=file_obj.type,
                    key=f"dl_{idx}_{file_name}",
                    use_container_width=True
                )
                
                # Pulsante 3: Rimuovi (usando il callback on_click)
                st.button(
                    "🗑️ Rimuovi", 
                    key=f"del_{idx}_{file_name}", 
                    on_click=rimuovi_allegato, 
                    args=(idx,), 
                    use_container_width=True
                )
