import streamlit as st
import os
import json
import pandas as pd
from agent import build_graph

st.set_page_config(page_title="KÜB Yan Etki Çıkarım Ajanı", layout="wide")

st.title("💊 KÜB Yan Etki Çıkarım Ajanı (Actor-Critic)")

st.markdown("""
Bu sistem, KÜB belgelerindeki **4.8. İstenmeyen Etkiler** bölümünü T.C. Sağlık Bakanlığı kurallarına göre analiz eder.
İki ajan (Çıkarıcı ve Denetleyici) hata bulamayana kadar kendi aralarında tartışır ve en doğru veriyi sunar.
""")

uploaded_file = st.file_uploader("KÜB PDF Dosyasını Yükleyin", type=["pdf"])

if "workflow" not in st.session_state:
    st.session_state.workflow = build_graph()

if "final_result" not in st.session_state:
    st.session_state.final_result = None

if "final_log_text" not in st.session_state:
    st.session_state.final_log_text = None

if uploaded_file is not None:
    if st.button("Çıkarımı Başlat (Agent Loop)"):
        # Save uploaded file temporarily ONLY when button is clicked
        temp_pdf_path = f"temp_{uploaded_file.name}"
        with open(temp_pdf_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        st.session_state.final_result = None
        
        with st.spinner("Ajanlar çalışıyor... (Bu işlem birkaç dakika sürebilir)"):
            initial_state = {
                "pdf_path": temp_pdf_path,
                "pdf_bytes": None,
                "extraction_result": None,
                "review_report": None,
                "iteration": 0,
                "max_iterations": 5,
                "log": []
            }
            
            # Stream events from the graph
            log_container = st.empty()
            
            try:
                for event in st.session_state.workflow.stream(initial_state):
                    for key, value in event.items():
                        if "log" in value:
                            # Print latest logs
                            log_text = "\n".join(value["log"])
                            log_container.text_area("Ajan Konsolu", log_text, height=300)
                            st.session_state.final_log_text = log_text
                            
                        if "extraction_result" in value:
                            st.session_state.final_result = value["extraction_result"]
                
                if st.session_state.final_result:
                    os.makedirs("results", exist_ok=True)
                    json_filename = f"results/{uploaded_file.name}_yan_etkiler.json"
                    data = [effect.model_dump() for effect in st.session_state.final_result.adverse_effects]
                    with open(json_filename, "w", encoding="utf-8") as json_file:
                        json.dump(data, json_file, ensure_ascii=False, indent=2)

                if st.session_state.final_log_text:
                    os.makedirs("audit_logs", exist_ok=True)
                    log_filename = f"audit_logs/{uploaded_file.name}_audit.txt"
                    with open(log_filename, "w", encoding="utf-8") as log_file:
                        log_file.write(st.session_state.final_log_text)
                    st.success(f"Çıkarım işlemi tamamlandı! (Sonuçlar 'results/', tartışma geçmişi 'audit_logs/' klasörüne kaydedildi.)")
                else:
                    st.success("Çıkarım işlemi tamamlandı!")
            finally:
                # Always clean up the temporary file
                if os.path.exists(temp_pdf_path):
                    os.remove(temp_pdf_path)

    if st.session_state.final_result:
        st.subheader("📊 Final Çıkarım Sonucu")
        
        # Convert Pydantic models to dicts
        data = [effect.model_dump() for effect in st.session_state.final_result.adverse_effects]
        df = pd.DataFrame(data)
        
        st.dataframe(df, use_container_width=True)
        
        # Download buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "CSV Olarak İndir",
                csv,
                f"{uploaded_file.name}_yan_etkiler.csv",
                "text/csv",
                key='download-csv'
            )
        with col2:
            json_str = json.dumps(data, ensure_ascii=False, indent=2)
            st.download_button(
                "JSON Olarak İndir",
                json_str,
                f"{uploaded_file.name}_yan_etkiler.json",
                "application/json",
                key='download-json'
            )
        with col3:
            if st.session_state.final_log_text:
                st.download_button(
                    "Tartışma Geçmişini İndir (TXT)",
                    st.session_state.final_log_text.encode('utf-8'),
                    f"{uploaded_file.name}_audit_log.txt",
                    "text/plain",
                    key='download-txt'
                )
