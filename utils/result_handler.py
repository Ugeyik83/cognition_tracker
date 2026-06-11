# utils/result_handler.py
import streamlit as st
import json
from datetime import datetime

def send_result_to_backend(result_data: dict, result_key: str):
    """
    JavaScript bileşeninden gelen sonucu session_state'e kaydeder.
    result_key: hangi test için olduğunu belirtir (örn: 'pvt', 'go_nogo', 'dual')
    """
    if result_key not in st.session_state:
        st.session_state[result_key] = None
    
    # Eğer result_data doluysa kaydet
    if result_data and isinstance(result_data, dict):
        # Zaman damgası ekle
        result_data['received_at'] = datetime.now().isoformat()
        st.session_state[result_key] = result_data
        return True
    return False

def get_result(result_key: str):
    """Kaydedilmiş sonucu alır"""
    return st.session_state.get(result_key)

def clear_result(result_key: str):
    """Sonucu temizler (yeni test için)"""
    if result_key in st.session_state:
        st.session_state[result_key] = None

def display_result_summary(result_key: str, title: str):
    """Sonucu ekranda gösterir (opsiyonel)"""
    result = get_result(result_key)
    if result:
        st.success(f"✅ {title} sonucu alındı: {json.dumps(result, indent=2)}")
    else:
        st.info(f"⏳ {title} sonucu bekleniyor...")