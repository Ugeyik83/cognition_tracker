# pages/4_dashboard.py
import streamlit as st
import pandas as pd
from utils.data_logger import load_all, export_csv


st.set_page_config(page_title="Dashboard | CognitionTracker", layout="wide")
st.title("📊 Test Sonuçları Dashboard'u")

# Mevcut oturumdaki sonuçları göster
st.subheader("🔹 Bu Oturumdaki Sonuçlar")

col1, col2, col3 = st.columns(3)
pvt = st.session_state.get("pvt_result")
gonogo = get_result("gonogo_result")
dual = get_result("dual_result")

with col1:
    if pvt:
        st.metric("PVT Ortalama Tepki", f"{pvt.get('mean_rt', '?')} ms")
    else:
        st.info("PVT testi henüz yapılmadı.")

with col2:
    if gonogo:
        st.metric("Go/No-Go Hit Oranı", f"{gonogo.get('hit_rate', 0):.1%}")
    else:
        st.info("Go/No-Go testi henüz yapılmadı.")

with col3:
    if dual:
        st.metric("Dual Task - Renk", f"{dual.get('primary_accuracy', 0):.1%}")
        st.metric("Dual Task - Şekil", f"{dual.get('secondary_accuracy', 0):.1%}")
    else:
        st.info("Dual Task testi henüz yapılmadı.")

# Geçmiş kayıtları göster
st.subheader("📁 Geçmiş Tüm Kayıtlar")
df = load_all()
if not df.empty:
    st.dataframe(df, use_container_width=True)
    
    # İndirme butonu
    csv_data = export_csv()
    st.download_button(
        label="📥 Tüm verileri CSV olarak indir",
        data=csv_data,
        file_name="cognition_results.csv",
        mime="text/csv",
    )
    
    # Basit görselleştirme (PVT ortalama süreler)
    if "pvt_mean_rt" in df.columns:
        df_time = df.dropna(subset=["pvt_mean_rt"]).copy()
        if not df_time.empty:
            df_time["timestamp"] = pd.to_datetime(df_time["timestamp"])
            df_time = df_time.sort_values("timestamp")
            st.subheader("📈 PVT Ortalama Tepki Süresi (ms) - Zaman içinde")
            st.line_chart(df_time.set_index("timestamp")["pvt_mean_rt"])
else:
    st.info("Henüz hiç kayıt yok. Testleri yapıp sonuçları kaydedin.")