# pages/4_dashboard.py
import streamlit as st
import pandas as pd
from utils.data_logger import load_all, export_csv

st.set_page_config(page_title="Dashboard | CognitionTracker", layout="wide")
st.title("📊 Test Sonuçları Dashboard'u")

# Mevcut oturumdaki sonuçları göster
st.subheader("🔹 Bu Oturumdaki Sonuçlar")

col1, col2, col3 = st.columns(3)

# Doğrudan session_state'den al (get_result kullanmadan)
pvt = st.session_state.get("pvt_result")
gonogo = st.session_state.get("gonogo_result")
dual = st.session_state.get("dual_result")

with col1:
    if pvt:
        # PVT'de 'average' anahtarı var (ms cinsinden)
        avg_rt = pvt.get('average') or pvt.get('mean_rt', '?')
        st.metric("PVT Ortalama Tepki", f"{avg_rt} ms")
    else:
        st.info("PVT testi henüz yapılmadı.")

with col2:
    if gonogo:
        # Go/No-Go'da 'accuracy' % olarak veya 'hit_rate' ondalık olabilir
        acc = gonogo.get('accuracy')
        if acc is not None:
            # Eğer 1'den büyükse yüzde olarak kabul et
            if acc > 1:
                acc = acc / 100.0
        else:
            acc = gonogo.get('hit_rate', 0)
        st.metric("Go/No-Go Doğruluk", f"{acc:.1%}")
    else:
        st.info("Go/No-Go testi henüz yapılmadı.")

with col3:
    if dual:
        prim = dual.get('primary_accuracy', 0)
        sec = dual.get('secondary_accuracy', 0)
        st.metric("Dual Task - Renk", f"{prim:.1%}")
        st.metric("Dual Task - Şekil", f"{sec:.1%}")
    else:
        st.info("Dual Task testi henüz yapılmadı.")

# Geçmiş kayıtları göster
st.subheader("📁 Geçmiş Tüm Kayıtlar")
df = load_all()
if not df.empty:
    st.dataframe(df, use_container_width=True)
    
    csv_data = export_csv()
    st.download_button(
        label="📥 Tüm verileri CSV olarak indir",
        data=csv_data,
        file_name="cognition_results.csv",
        mime="text/csv",
    )
    
    if "pvt_mean_rt" in df.columns:
        df_time = df.dropna(subset=["pvt_mean_rt"]).copy()
        if not df_time.empty:
            df_time["timestamp"] = pd.to_datetime(df_time["timestamp"])
            df_time = df_time.sort_values("timestamp")
            st.subheader("📈 PVT Ortalama Tepki Süresi (ms) - Zaman içinde")
            st.line_chart(df_time.set_index("timestamp")["pvt_mean_rt"])
else:
    st.info("Henüz hiç kayıt yok. Testleri yapıp sonuçları kaydedin.")