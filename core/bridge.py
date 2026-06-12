# core/bridge.py
"""iframe (components.html) → Python veri köprüsü.

KÖK NEDEN ÇÖZÜMÜ: components.html sandbox'lı iframe'de çalışır; iframe içindeki
DOM, sayfadaki st.text_area'ya ulaşamaz. Bunun yerine:

  1. Test JS'i sonucu localStorage'a yazar (srcdoc iframe ana origin'i paylaşır).
  2. Python tarafı st_autorefresh ile 1.5 sn'de bir rerun tetikler.
  3. st_javascript localStorage'dan değeri okuyup Python'a döndürür.
  4. run_id eşleşirse sonuç kabul edilir, anahtar temizlenir.

run_id, eski/yabancı bir sonucun yanlışlıkla kabul edilmesini önler.
"""

import json
import uuid

from streamlit_autorefresh import st_autorefresh
from streamlit_javascript import st_javascript


def new_run_id() -> str:
    return uuid.uuid4().hex[:12]


def poll_result(storage_key: str, run_id: str, widget_key: str):
    """localStorage'daki sonucu yoklar.

    Döndürür: dict (run_id eşleşen geçerli sonuç) veya None.
    """
    st_autorefresh(interval=1500, key=f"refresh_{widget_key}")

    raw = st_javascript(
        f"localStorage.getItem({json.dumps(storage_key)});",
        key=f"poll_{widget_key}",
    )
    # st_javascript ilk render'da 0 döndürür; null/0/boş → henüz sonuç yok
    if not raw or raw == 0:
        return None
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return None
    if data.get("run_id") != run_id:
        return None  # eski oturumdan kalmış veri — yok say
    return data


def clear_key(storage_key: str, widget_key: str):
    """Kabul edilen sonucu localStorage'dan siler (tek seferlik)."""
    st_javascript(
        f"localStorage.removeItem({json.dumps(storage_key)});",
        key=f"clear_{widget_key}",
    )
