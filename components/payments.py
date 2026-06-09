from datetime import datetime
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import base64
import streamlit as st
from .database import query_df, execute, UPLOAD_DIR, get_setting, fmt_date
from .theme import COLORS, get_branding


def clean(value):
    if value is None:
        return "-"
    text = str(value).strip()
    return "-" if text == "" or text.lower() == "nan" else text


def add_payment_verification(order_id: int, image_path: str, uploaded_by: str):
    if image_path:
        execute(
            "INSERT INTO payment_verifications (order_id,image_path,uploaded_by,uploaded_at) VALUES (?,?,?,?)",
            (int(order_id), image_path, uploaded_by or "user", datetime.now().isoformat()),
        )
        execute("UPDATE orders SET payment_verification_image=? WHERE id=?",
                (image_path, int(order_id)))


def verification_images(order_id: int):
    return query_df(
        "SELECT * FROM payment_verifications WHERE order_id=? ORDER BY uploaded_at DESC",
        (int(order_id),),
    )


def _image_data_uri(path: Path):
    try:
        suffix = path.suffix.lower().replace(".", "") or "png"
        if suffix == "jpg":
            suffix = "jpeg"
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:image/{suffix};base64,{data}"
    except Exception:
        return ""


@st.dialog("Payment Verification", width="large")
def _payment_image_dialog(uri: str, by: str, uploaded_at: str):
    """Native Streamlit modal — guaranteed to work in all Streamlit versions."""
    st.image(uri, use_container_width=True)
    st.caption(f"Uploaded by **{by}** · {uploaded_at}")


def render_verification_previews(order_id: int, max_preview: int = 4):
    rows = verification_images(order_id)
    if rows.empty:
        return

    _, preview_col = st.columns([2.65, 1.2])
    with preview_col:
        st.markdown(
            "<div style='font-size:11px;font-weight:700;color:#4f8ef7;"
            "margin-bottom:6px;'>💳 Payment Verification</div>",
            unsafe_allow_html=True,
        )
        for i, (_, r) in enumerate(rows.head(max_preview).iterrows()):
            fpath = UPLOAD_DIR / str(r["image_path"])
            if not fpath.exists():
                continue
            uri     = _image_data_uri(fpath)
            caption = clean(r.get("uploaded_by") or "user")
            at_str  = str(r.get("uploaded_at") or "")[:16]
            if not uri:
                continue

            # Thumbnail via native st.image (reliable)
            st.image(uri, use_container_width=True)
            st.caption(f"By {caption}")
            # Button opens Streamlit native dialog — no JS needed
            if st.button(
                "🔍 View Full Size",
                key=f"view_proof_{order_id}_{i}",
                use_container_width=True,
            ):
                _payment_image_dialog(uri, caption, at_str)

# ─── Font helpers ─────────────────────────────────────────────────────────────

def _font(size=24, bold=False, italic=False):
    """Return best available Pillow font at given size."""
    if bold and italic:
        candidates = [
            "/usr/share/fonts/truetype/lato/Lato-BoldItalic.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-BoldItalic.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf",
        ]
    elif bold:
        candidates = [
            "/usr/share/fonts/truetype/lato/Lato-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
    elif italic:
        candidates = [
            "/usr/share/fonts/truetype/lato/Lato-Italic.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
        ]
    else:
        candidates = [
            "/usr/share/fonts/truetype/lato/Lato-Regular.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    for c in candidates:
        if Path(c).exists():
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _hex_to_rgb(hex_color: str):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _wrap_text(text, font, max_width):
    """Simple word-wrap returning list of lines."""
    words = str(text).split()
    lines, current = [], ""
    for word in words:
        test = (current + " " + word).strip()
        bbox = font.getbbox(test)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def _draw_text_shadow(d, xy, text, font, fill, shadow_color="#00000022", offset=(2, 2)):
    """Draw text with a subtle drop shadow."""
    d.text((xy[0]+offset[0], xy[1]+offset[1]), text, font=font, fill=shadow_color)
    d.text(xy, text, font=font, fill=fill)


# ─── Payment Slip PDF (Pillow-based, no extra dependencies) ──────────────────

def payment_slip_pdf(order, items, currency=None):
    """
    Professional A4-style payment receipt as PDF.
    Uses Pillow only — no reportlab required.
    Canvas: 1680 × dynamic height px at 200 DPI = 8.4 × ? inches
    """
    currency = currency or get_setting("currency", "MVR")
    brand    = get_branding()
    accent   = COLORS.get(brand.get("accent_color"), "#1e3a5f")
    acc_rgb  = _hex_to_rgb(accent)
    business = brand.get("business_name") or "Your Business"
    logo_file = brand.get("business_logo") or ""

    biz_address   = brand.get("business_address") or ""
    biz_phone     = brand.get("business_phone") or ""
    biz_email     = brand.get("business_email") or ""
    biz_website   = brand.get("business_website") or ""
    fb_id         = brand.get("facebook_id") or ""
    ig_id         = brand.get("instagram_id") or ""
    tt_id         = brand.get("tiktok_id") or ""
    wa_contact    = brand.get("whatsapp_contact") or ""
    viber_contact = brand.get("viber_contact") or ""

    W      = 1680
    PAD    = 60
    INNER  = W - 2 * PAD

    num_items    = sum(1 for _ in items.iterrows()) if hasattr(items, "iterrows") else len(items)
    social_count = sum(1 for x in [wa_contact, viber_contact, fb_id, ig_id, tt_id] if x)
    contact_count= sum(1 for x in [biz_address, biz_phone, biz_email, biz_website] if x)

    HEADER_H  = 220
    INFO_H    = 180
    TABLE_HDR = 60
    ROW_H     = 64
    TOTALS_H  = 280
    FOOTER_H  = 120 + contact_count * 38 + (50 if social_count else 0) + social_count * 34
    H = PAD + HEADER_H + 32 + INFO_H + 32 + TABLE_HDR + num_items * ROW_H + TOTALS_H + FOOTER_H + PAD

    img = Image.new("RGB", (W, H), "#f0f2f5")
    d   = ImageDraw.Draw(img, "RGBA")

    # White card
    d.rounded_rectangle((PAD, PAD, W - PAD, H - PAD), radius=32, fill="#ffffff", outline="#d0d8e4", width=2)

    # ── HEADER BAND ───────────────────────────────────────────────────────
    HDR_Y2 = PAD + HEADER_H
    d.rounded_rectangle((PAD, PAD, W - PAD, HDR_Y2), radius=32, fill=accent)
    stripe_col = (*acc_rgb, 18)
    for sx in range(-200, W + 200, 70):
        d.line([(sx, PAD), (sx + 360, HDR_Y2)], fill=stripe_col, width=34)
    d.rounded_rectangle((PAD, PAD, W - PAD, HDR_Y2), radius=32, outline=accent, width=3)

    # Logo
    LOGO_SZ = 140
    LX, LY  = PAD + 40, PAD + 40
    logo_path = UPLOAD_DIR / logo_file if logo_file else None
    if logo_path and logo_path.exists():
        try:
            logo_img = Image.open(logo_path).convert("RGBA")
            logo_img.thumbnail((LOGO_SZ, LOGO_SZ), Image.LANCZOS)
            bg = Image.new("RGBA", (LOGO_SZ, LOGO_SZ), (255, 255, 255, 240))
            px = (LOGO_SZ - logo_img.width) // 2
            py = (LOGO_SZ - logo_img.height) // 2
            bg.paste(logo_img, (px, py), logo_img)
            mask = Image.new("L", (LOGO_SZ, LOGO_SZ), 0)
            ImageDraw.Draw(mask).rounded_rectangle((0, 0, LOGO_SZ, LOGO_SZ), radius=24, fill=255)
            img.paste(bg.convert("RGB"), (LX, LY), mask)
        except Exception:
            d.rounded_rectangle((LX, LY, LX+LOGO_SZ, LY+LOGO_SZ), radius=24, fill="#fff")
            d.text((LX+LOGO_SZ//2, LY+LOGO_SZ//2), business[:1].upper(), fill=accent, font=_font(64, True), anchor="mm")
    else:
        d.rounded_rectangle((LX, LY, LX+LOGO_SZ, LY+LOGO_SZ), radius=24, fill="#fff")
        d.text((LX+LOGO_SZ//2, LY+LOGO_SZ//2), business[:1].upper(), fill=accent, font=_font(64, True), anchor="mm")

    TX = LX + LOGO_SZ + 32
    d.text((TX, LY + 4),  business.upper(),             fill="#ffffff", font=_font(46, True))
    d.text((TX, LY + 60), "OFFICIAL PAYMENT RECEIPT",   fill="#ffffffcc", font=_font(24, True))
    if biz_address:
        d.text((TX, LY + 98), biz_address[:70],         fill="#ffffffaa", font=_font(20))

    slip_no    = clean(order.get("payment_slip_no") or f"PS-{order.get('order_no','')}")
    order_date = fmt_date(str(order.get("created_at",""))[:19])
    RX = W - PAD - 40
    d.text((RX, LY + 4),   slip_no,                          fill="#ffffff",   font=_font(30, True), anchor="ra")
    d.text((RX, LY + 50),  f"Order: {order.get('order_no','')}", fill="#ffffffcc", font=_font(22), anchor="ra")
    d.text((RX, LY + 86),  f"Date: {order_date}",            fill="#ffffffaa", font=_font(20), anchor="ra")
    d.text((RX, LY + 122), "ORDRO SYSTEM",                   fill="#ffffff55", font=_font(16, True), anchor="ra")

    # ── INFO CARDS ────────────────────────────────────────────────────────
    y = HDR_Y2 + 32
    COL_W  = (INNER - 24) // 2
    CARD_H = INFO_H

    for cx, lbl, lines in [
        (PAD, "CUSTOMER DETAILS", [
            ("Customer", clean(order.get("customer_name"))),
            ("Phone",    clean(order.get("customer_phone"))),
            ("City",     clean(order.get("customer_city"))),
            ("Address",  clean(order.get("customer_address"))),
        ]),
        (PAD + COL_W + 24, "ORDER DETAILS", [
            ("Order Type", clean(order.get("order_type"))),
            ("Payment",    clean(order.get("payment_method"))),
            ("Status",     clean(order.get("payment_status") or "Unpaid")),
            ("Seller",     clean(order.get("seller"))),
        ]),
    ]:
        d.rounded_rectangle((cx, y, cx + COL_W, y + CARD_H), radius=18, fill="#f8faff", outline="#dde4f0", width=1)
        d.rounded_rectangle((cx, y, cx + 8, y + CARD_H), radius=8, fill=accent)
        d.text((cx + 24, y + 16), lbl, fill=accent, font=_font(20, True))
        for k, (key, val) in enumerate(lines):
            fy = y + 52 + k * 32
            d.text((cx + 24, fy), f"{key}:", fill="#94a3b8", font=_font(18))
            d.text((cx + 190, fy), val[:42], fill="#1e293b", font=_font(18, True))

    # ── ITEMS TABLE ───────────────────────────────────────────────────────
    y += CARD_H + 32
    d.text((PAD, y), "ITEMS", fill="#1e293b", font=_font(26, True))
    y += 42

    d.rounded_rectangle((PAD, y, W - PAD, y + TABLE_HDR), radius=12, fill=accent)
    COL_POSITIONS = [
        (PAD + 18,               "#"),
        (PAD + 80,               "PRODUCT NAME"),
        (PAD + int(INNER * .52), "QTY"),
        (PAD + int(INNER * .62), "UNIT PRICE"),
        (PAD + int(INNER * .78), "AMOUNT"),
    ]
    for cx, hdr in COL_POSITIONS:
        d.text((cx, y + 16), hdr, fill="#ffffff", font=_font(19, True))
    y += TABLE_HDR

    for idx, (_, it) in enumerate(items.iterrows()):
        row_fill = "#f0f4fb" if idx % 2 == 0 else "#ffffff"
        d.rectangle((PAD + 2, y, W - PAD - 2, y + ROW_H - 1), fill=row_fill)
        d.line((PAD + 18, y + ROW_H - 1, W - PAD - 18, y + ROW_H - 1), fill="#dde4f0", width=1)
        ry = y + (ROW_H - 22) // 2
        unit = float(it.get("unit_price", 0))
        amt  = float(it.get("line_total", 0))
        d.text((PAD + 18,               ry), str(idx + 1),                       fill="#94a3b8", font=_font(18))
        d.text((PAD + 80,               ry), str(it.get("product_name",""))[:50], fill="#1e293b", font=_font(19, True))
        d.text((PAD + int(INNER * .52), ry), str(int(it.get("qty", 0))),          fill="#475569", font=_font(19))
        d.text((PAD + int(INNER * .62), ry), f"{currency} {unit:,.2f}",           fill="#475569", font=_font(19))
        d.text((PAD + int(INNER * .78), ry), f"{currency} {amt:,.2f}",            fill="#1e293b", font=_font(19, True))
        y += ROW_H

    d.line((PAD + 2, y, W - PAD - 2, y), fill="#dde4f0", width=2)

    # ── TOTALS ────────────────────────────────────────────────────────────
    y += 24
    subtotal = float(order.get("subtotal") or 0)
    discount = float(order.get("discount") or 0)
    tax      = float(order.get("tax")      or 0)
    total    = float(order.get("total")    or 0)
    RX = W - PAD - 24
    LX_LABEL = PAD + int(INNER * .60)

    for lbl, val, is_total in [
        ("Subtotal",     subtotal, False),
        ("Discount",     discount, False),
        ("Tax",          tax,      False),
        ("TOTAL AMOUNT", total,    True),
    ]:
        if is_total:
            d.rounded_rectangle((LX_LABEL - 18, y - 10, W - PAD, y + 58), radius=14, fill=accent)
            tf, vf, tc = _font(27, True), _font(27, True), "#ffffff"
        else:
            tf, vf, tc = _font(20), _font(20, True), "#475569"
        d.text((LX_LABEL, y + 12), lbl,                      fill=tc, font=tf)
        d.text((RX,        y + 12), f"{currency} {val:,.2f}", fill=tc, font=vf, anchor="ra")
        y += 64 if is_total else 50

    # ── FOOTER ────────────────────────────────────────────────────────────
    y += 28
    d.line((PAD + 28, y, W - PAD - 28, y), fill="#dde4f0", width=1)
    y += 26
    d.text((W // 2, y), "Thank you for your order — We appreciate your business!", fill="#1e293b", font=_font(24, True), anchor="mm")
    y += 44

    for item_txt in [biz_phone and f"Tel: {biz_phone}",
                     biz_email and f"Email: {biz_email}",
                     biz_website and f"Web: {biz_website}",
                     biz_address and f"Address: {biz_address}"]:
        if item_txt:
            d.text((W // 2, y), item_txt, fill="#64748b", font=_font(19), anchor="mm")
            y += 36

    socials = []
    if wa_contact:    socials.append(f"WhatsApp: {wa_contact}")
    if viber_contact: socials.append(f"Viber: {viber_contact}")
    if fb_id:         socials.append(f"fb: {fb_id}")
    if ig_id:         socials.append(f"IG: @{ig_id}")
    if tt_id:         socials.append(f"TikTok: @{tt_id}")
    if socials:
        y += 8
        d.text((W // 2, y), "  ·  ".join(socials[:4]), fill="#94a3b8", font=_font(18), anchor="mm")
        y += 32

    y += 14
    d.line((PAD + 28, y, W - PAD - 28, y), fill="#dde4f0", width=1)
    y += 18
    gen_time = datetime.now().strftime("Generated %d-%m-%y  %H:%M")
    d.text((PAD + 28, y),     "Powered by ORDRO · Keep this receipt for your records.", fill="#94a3b8", font=_font(16))
    d.text((W - PAD - 28, y), gen_time, fill="#94a3b8", font=_font(16), anchor="ra")

    out = BytesIO()
    img.save(out, format="PDF", resolution=200)
    out.seek(0)
    return out.getvalue()


# ─── Delivery Sticker PDF (Pillow-based) ──────────────────────────────────────

def delivery_sticker_pdf(order, items, currency=None):
    """
    A6-landscape delivery sticker as PDF.
    Canvas: 1920 × 960 px at 200 DPI = 9.6 × 4.8 inches.
    """
    currency  = currency or get_setting("currency", "MVR")
    brand     = get_branding()
    accent    = COLORS.get(brand.get("accent_color"), "#1e3a5f")
    acc_rgb   = _hex_to_rgb(accent)
    business  = brand.get("business_name") or "Your Business"
    logo_file = brand.get("business_logo") or ""
    biz_phone = brand.get("business_phone") or ""

    W, H = 1920, 960
    PAD  = 44

    img = Image.new("RGB", (W, H), "#ffffff")
    d   = ImageDraw.Draw(img, "RGBA")

    # Outer border
    d.rounded_rectangle((4, 4, W - 4, H - 4), radius=32, outline=accent, width=7)
    d.rounded_rectangle((4, 4, W - 4, H - 4), radius=32, outline="#000",  width=2)

    # ── LEFT PANEL (business branding) ────────────────────────────────────
    LPANEL_W = 420
    d.rounded_rectangle((4, 4, LPANEL_W, H - 4), radius=32, fill=accent)
    d.ellipse((LPANEL_W - 200, -100, LPANEL_W + 80, 180), fill=(*acc_rgb, 28))
    d.ellipse((-50, H - 220, 220, H + 70), fill=(*acc_rgb, 24))

    # Logo
    LSZ = 130
    LX, LY = (LPANEL_W - LSZ) // 2, 60
    logo_path = UPLOAD_DIR / logo_file if logo_file else None
    if logo_path and logo_path.exists():
        try:
            logo_img = Image.open(logo_path).convert("RGBA")
            logo_img.thumbnail((LSZ, LSZ), Image.LANCZOS)
            bg = Image.new("RGBA", (LSZ, LSZ), (255, 255, 255, 230))
            px = (LSZ - logo_img.width) // 2
            py = (LSZ - logo_img.height) // 2
            bg.paste(logo_img, (px, py), logo_img)
            mask = Image.new("L", (LSZ, LSZ), 0)
            ImageDraw.Draw(mask).rounded_rectangle((0, 0, LSZ, LSZ), radius=22, fill=255)
            img.paste(bg.convert("RGB"), (LX, LY), mask)
        except Exception:
            d.rounded_rectangle((LX, LY, LX+LSZ, LY+LSZ), radius=22, fill="#fff")
            d.text((LX+LSZ//2, LY+LSZ//2), business[:1].upper(), fill=accent, font=_font(52, True), anchor="mm")
    else:
        d.rounded_rectangle((LX, LY, LX+LSZ, LY+LSZ), radius=22, fill="#fff")
        d.text((LX+LSZ//2, LY+LSZ//2), business[:1].upper(), fill=accent, font=_font(52, True), anchor="mm")

    d.text((LPANEL_W // 2, LY + LSZ + 24), business, fill="#ffffff", font=_font(26, True), anchor="mm")
    d.text((LPANEL_W // 2, LY + LSZ + 60), "DELIVERY",  fill="#ffffffcc", font=_font(22, True), anchor="mm")
    if biz_phone:
        d.text((LPANEL_W // 2, LY + LSZ + 96), biz_phone, fill="#ffffffaa", font=_font(18), anchor="mm")

    # Order number badge at bottom of left panel
    ON = str(order.get("order_no") or "")
    d.rounded_rectangle((28, H - 110, LPANEL_W - 28, H - 28), radius=14, fill="#ffffff22")
    d.text((LPANEL_W // 2, H - 75), ON, fill="#ffffff", font=_font(30, True), anchor="mm")
    d.text((LPANEL_W // 2, H - 40), fmt_date(order.get("created_at"), show_time=False), fill="#ffffffaa", font=_font(16), anchor="mm")

    # ── RIGHT PANEL (delivery address) ────────────────────────────────────
    RX = LPANEL_W + PAD
    RW = W - RX - PAD

    # "DELIVER TO:" header
    d.text((RX, 32), "DELIVER TO:", fill=accent, font=_font(24, True))
    d.line((RX, 70, W - PAD, 70), fill=accent, width=4)

    name    = clean(order.get("customer_name"))
    phone   = clean(order.get("customer_phone"))
    city    = clean(order.get("customer_city"))
    address = clean(order.get("customer_address"))

    # Customer Name — very large
    name_font = _font(72, True)
    name_lines = _wrap_text(name, name_font, RW - 20)
    ny = 88
    for nl in name_lines[:2]:
        d.text((RX, ny), nl, fill="#0f172a", font=name_font)
        ny += 84

    # Phone — prominent
    d.text((RX, ny), phone, fill="#1e3a5f", font=_font(52, True))
    ny += 66

    # City / Island
    d.text((RX, ny), city, fill="#475569", font=_font(40, True))
    ny += 54

    # Address — wrapped, clear size
    addr_font  = _font(34)
    addr_lines = _wrap_text(address, addr_font, RW - 20)
    for al in addr_lines[:3]:
        d.text((RX, ny), al, fill="#334155", font=addr_font)
        ny += 42

    # Divider
    ny += 10
    d.line((RX, ny, W - PAD, ny), fill="#e2e8f0", width=2)
    ny += 18

    # Items summary
    d.text((RX, ny), "ITEMS:", fill=accent, font=_font(22, True))
    ny += 30
    item_list = []
    for _, it in items.iterrows():
        item_list.append(f"• {str(it.get('product_name',''))[:34]}  ×{int(it.get('qty',0))}")
    for itxt in item_list[:4]:
        d.text((RX, ny), itxt, fill="#334155", font=_font(20))
        ny += 28
    if len(item_list) > 4:
        d.text((RX, ny), f"  + {len(item_list)-4} more item(s)", fill="#94a3b8", font=_font(18))

    # Bottom: total + payment status
    total    = float(order.get("total", 0))
    pay_stat = order.get("payment_status") or "Unpaid"
    pay_col  = "#16a34a" if pay_stat == "Paid" else "#dc2626"

    d.line((RX, H - 100, W - PAD, H - 100), fill="#e2e8f0", width=1)
    d.text((RX,      H - 78), f"Total: {currency} {total:,.2f}", fill="#0f172a", font=_font(26, True))
    d.text((RX,      H - 44), f"Payment: {pay_stat}",            fill=pay_col,   font=_font(24, True))
    d.text((W - PAD, H - 40), "Powered by ORDRO",                fill="#cbd5e1", font=_font(16), anchor="ra")

    out = BytesIO()
    img.save(out, format="PDF", resolution=200)
    out.seek(0)
    return out.getvalue()


# ─── Backwards-compatible aliases ─────────────────────────────────────────────
payment_slip_jpg    = payment_slip_pdf
delivery_sticker_jpg = delivery_sticker_pdf


# ─── HTML Payment Slip & Delivery Sticker (on-screen preview + Print) ─────────
# Matches the A5 invoice / A6 sticker design, filled from real order data.

def _esc(v):
    s = "" if v is None else str(v)
    if s.strip().lower() == "nan":
        s = ""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _doc_brand():
    from .database import get_setting
    from .theme import logo_data_uri, COLORS
    name    = _esc(get_setting("business_name", "Your Business"))
    accent  = COLORS.get(get_setting("accent_color", "Royal Blue"), "#2563eb")
    logo    = logo_data_uri(get_setting("business_logo", ""))
    phone   = _esc(get_setting("business_phone", ""))
    address = _esc(get_setting("business_address", ""))
    return name, accent, logo, phone, address


def _customer_block(order):
    parts = [f"<strong>{_esc(order.get('customer_name'))}</strong>"]
    for f in ("customer_address", "customer_city", "customer_phone"):
        v = _esc(order.get(f))
        if v:
            parts.append(v)
    return "<br>".join(parts)


_SLIP_CSS = """<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{background:#eef2f5;font-family:'Inter','Helvetica Neue',Arial,sans-serif;padding:22px 14px;display:flex;flex-direction:column;align-items:center;}
.bar{width:100%;max-width:14.8cm;text-align:right;margin-bottom:12px;}
.btn{background:__ACCENT__;color:#fff;border:none;padding:8px 16px;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;}
.a5-slip{width:14.8cm;max-width:100%;background:#fff;border-radius:16px;box-shadow:0 20px 35px -12px rgba(0,0,0,.15);overflow:hidden;}
.payment-slip{padding:1.2cm 1cm;}
.slip-header{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:28px;padding-bottom:18px;border-bottom:2px solid #e2e8f0;}
.brand h1{font-size:26px;font-weight:800;color:#0f172a;letter-spacing:-.5px;}
.brand p{font-size:11px;color:#475569;margin-top:2px;}
.invoice-title{text-align:right;}
.invoice-title h2{font-size:22px;font-weight:600;color:__ACCENT__;}
.invoice-title p{font-size:11px;color:#475569;margin-top:2px;}
.two-columns{display:flex;gap:32px;margin-bottom:28px;}
.col{flex:1;}
.col h3{font-size:13px;font-weight:700;text-transform:uppercase;color:#64748b;letter-spacing:1px;margin-bottom:10px;}
.col p{font-size:12px;line-height:1.6;color:#1e293b;}
table{width:100%;border-collapse:collapse;margin:22px 0;}
th{text-align:left;font-size:11px;font-weight:700;text-transform:uppercase;color:#64748b;padding-bottom:12px;border-bottom:1px solid #e2e8f0;}
th.c,td.c{text-align:center;}th.r,td.r{text-align:right;}
td{padding:11px 0;font-size:12px;color:#1e293b;border-bottom:1px solid #f1f5f9;}
.totals{text-align:right;margin-top:18px;padding-top:16px;border-top:1px solid #e2e8f0;}
.totals p{font-size:12px;margin-bottom:6px;color:#475569;}
.grand-total{font-size:18px;font-weight:800;color:#0f172a;margin-top:8px;}
.footer-note{margin-top:30px;text-align:center;font-size:9px;color:#94a3b8;border-top:1px solid #e2e8f0;padding-top:18px;}
@media print{body{background:#fff;padding:0;margin:0;}.a5-slip{box-shadow:none;border-radius:0;}.no-print{display:none!important;}}
</style>"""


def payment_slip_html(order, items, currency=None):
    from .database import get_setting, fmt_date
    if currency is None:
        currency = get_setting("currency", "MVR")
    name, accent, logo, phone, address = _doc_brand()
    tagline = address or phone or ""

    rows, calc_sub = "", 0.0
    if items is not None and not items.empty:
        for _, it in items.iterrows():
            lt = float(it.get("line_total") or 0); calc_sub += lt
            rows += (f"<tr><td>{_esc(it.get('product_name'))}</td>"
                     f"<td class='c'>{int(it.get('qty') or 0)}</td>"
                     f"<td class='r'>{currency} {float(it.get('unit_price') or 0):,.2f}</td>"
                     f"<td class='r'>{currency} {lt:,.2f}</td></tr>")
    if not rows:
        rows = "<tr><td colspan='4'>No items</td></tr>"

    subtotal = float(order.get("subtotal") or calc_sub)
    discount = float(order.get("discount") or 0)
    tax      = float(order.get("tax") or 0)
    total    = float(order.get("total") or (subtotal - discount + tax))
    cust     = _customer_block(order)
    disc_p   = f"<p>Discount: - {currency} {discount:,.2f}</p>" if discount > 0 else ""
    css      = _SLIP_CSS.replace("__ACCENT__", accent)

    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">{css}</head><body>
<div class="bar no-print"><button class="btn" onclick="window.print()">&#128424; Print</button></div>
<div class="a5-slip"><div class="payment-slip">
  <div class="slip-header">
    <div class="brand"><h1>{name}</h1><p>{tagline}</p></div>
    <div class="invoice-title"><h2>INVOICE</h2><p>#{_esc(order.get('order_no'))}<br>Date: {fmt_date(order.get('created_at'), show_time=False)}</p></div>
  </div>
  <div class="two-columns">
    <div class="col"><h3>Billing details</h3><p>{cust}</p></div>
    <div class="col"><h3>Shipping details</h3><p>{cust}</p></div>
  </div>
  <table><thead><tr><th>Item</th><th class="c">Qty</th><th class="r">Unit Price</th><th class="r">Total</th></tr></thead>
  <tbody>{rows}</tbody></table>
  <div class="totals">
    <p>Subtotal: {currency} {subtotal:,.2f}</p>
    {disc_p}
    <p>Tax: {currency} {tax:,.2f}</p>
    <div class="grand-total">Grand Total: {currency} {total:,.2f}</div>
  </div>
  <div class="footer-note">Thank you for shopping with {name}. This is a system-generated invoice.</div>
</div></div></body></html>"""


_STICKER_CSS = """<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{background:#eef2f5;font-family:'Inter','Helvetica Neue',Arial,sans-serif;padding:22px 14px;display:flex;flex-direction:column;align-items:center;}
.bar{width:100%;max-width:10.5cm;text-align:right;margin-bottom:12px;}
.btn{background:__ACCENT__;color:#fff;border:none;padding:8px 16px;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;}
.a6-sticker{width:10.5cm;max-width:100%;background:#fff;border-radius:16px;box-shadow:0 20px 35px -12px rgba(0,0,0,.15);overflow:hidden;}
.delivery-sticker{padding:.7cm .8cm;}
.sticker-top{display:flex;justify-content:space-between;align-items:flex-start;gap:15px;margin-bottom:20px;}
.customer-info{flex:2;}
.name-phone{display:flex;gap:20px;flex-wrap:wrap;margin-bottom:16px;}
.name-phone div{font-size:22px;font-weight:800;color:#0f172a;}
.address-line{font-size:18px;font-weight:600;color:#1e293b;margin-bottom:8px;}
.city-line{font-size:18px;font-weight:600;color:#1e293b;}
.brand-side{flex:1;text-align:center;}
.logo-placeholder{background:#f8fafc;padding:12px;border-radius:16px;display:inline-block;margin-bottom:10px;}
.square-logo{width:70px;height:70px;background:linear-gradient(135deg,__ACCENT__,#1e40af);color:#fff;display:flex;align-items:center;justify-content:center;font-size:18px;font-weight:700;border-radius:12px;margin:0 auto;overflow:hidden;}
.square-logo img{width:100%;height:100%;object-fit:cover;border-radius:12px;}
.business-name{font-size:14px;font-weight:700;color:#334155;margin-top:8px;}
.powered{font-size:8px;color:#94a3b8;letter-spacing:.5px;margin-top:5px;}
.sticker-bottom{margin-top:20px;padding-top:12px;border-top:1px dashed #cbd5e1;text-align:center;font-size:10px;color:#dc2626;font-weight:500;}
@media print{body{background:#fff;padding:0;margin:0;}.a6-sticker{box-shadow:none;border-radius:0;}.no-print{display:none!important;}}
</style>"""


def delivery_sticker_html(order, items=None, currency=None):
    from .database import get_setting, fmt_date
    name, accent, logo, phone, address = _doc_brand()
    cust_name = _esc(order.get("customer_name"))
    cust_phone = _esc(order.get("customer_phone"))
    addr = _esc(order.get("customer_address"))
    city = _esc(order.get("customer_city"))
    initials = (cust_name[:1] or name[:1] or "O").upper()
    if logo:
        logo_inner = f'<img src="{logo}" alt="logo">'
    else:
        logo_inner = (name[:1].upper() or "O")
    css = _STICKER_CSS.replace("__ACCENT__", accent)
    bottom = (f"&#9888; if not delivered to above customer, please call {phone}"
              if phone else "&#9888; if not delivered to the above customer, please contact the sender")
    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">{css}</head><body>
<div class="bar no-print"><button class="btn" onclick="window.print()">&#128424; Print</button></div>
<div class="a6-sticker"><div class="delivery-sticker">
  <div class="sticker-top">
    <div class="customer-info">
      <div class="name-phone"><div>{cust_name}</div><div>{cust_phone}</div></div>
      <div class="address-line">{addr}</div>
      <div class="city-line">{city}</div>
    </div>
    <div class="brand-side">
      <div class="logo-placeholder"><div class="square-logo">{logo_inner}</div></div>
      <div class="business-name">{name}</div>
      <div class="powered">powered by ordro</div>
    </div>
  </div>
  <div class="sticker-bottom">{bottom}</div>
</div></div></body></html>"""
