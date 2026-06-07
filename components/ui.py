import base64
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageOps
import streamlit as st
from .database import UPLOAD_DIR, get_setting
from .theme import logo_data_uri


def _img_to_data_uri(path: Path, max_dim: int = 600):
    """Encode image preserving aspect ratio — no cropping."""
    img = Image.open(path).convert("RGB")
    img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=88)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def fixed_image(filename: str, height: int = 150, fallback_logo: bool = True):
    """
    Renders product image inside a constrained box.
    Image is contained (not cropped) so proportions are always preserved.
    On small screens the box shrinks but the image never distorts.
    """
    src = ""
    if filename:
        path = UPLOAD_DIR / filename
        if path.exists():
            try:
                src = _img_to_data_uri(path)
            except Exception:
                src = ""
    if not src and fallback_logo:
        src = logo_data_uri(get_setting("business_logo", ""))

    h = int(height)
    if src:
        st.markdown(
            f"""<div style="
                width:100%;
                height:{h}px;
                max-height:{h}px;
                border-radius:12px;
                overflow:hidden;
                background:#f8fafc;
                display:flex;
                align-items:center;
                justify-content:center;
            "><img src="{src}" style="
                max-width:100%;
                max-height:{h}px;
                width:auto;
                height:auto;
                object-fit:contain;
                display:block;
            "></div>""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""<div style="
                width:100%;height:{h}px;border-radius:12px;
                background:var(--accent-10,#eff6ff);
                display:flex;align-items:center;justify-content:center;
                font-size:22px;font-weight:700;color:var(--accent,#2563eb);
            ">ORDRO</div>""",
            unsafe_allow_html=True,
        )


def save_uploaded_file(uploaded, prefix="file"):
    from datetime import datetime
    if not uploaded:
        return ""
    safe = f"{prefix}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uploaded.name}".replace(" ", "_")
    path = UPLOAD_DIR / safe
    with open(path, "wb") as f:
        f.write(uploaded.getbuffer())
    return safe
