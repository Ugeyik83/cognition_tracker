# utils/result_handler.py
import streamlit as st
from datetime import datetime

def send_result_to_backend(result_data: dict, result_key: str):
    if result_key not in st.session_state:
        st.session_state[result_key] = None
    if result_data and isinstance(result_data, dict):
        result_data['received_at'] = datetime.now().isoformat()
        st.session_state[result_key] = result_data
        return True
    return False

def get_result(result_key: str):
    return st.session_state.get(result_key)

def clear_result(result_key: str):
    if result_key in st.session_state:
        st.session_state[result_key] = None