"""
Centralised, professional icon system for ORDRO.

Two icon families are used so every surface looks like a real product:

1. Material Symbols  -> used inside native Streamlit widgets (buttons, headings).
   Streamlit renders the token ``:material/<name>:`` as a clean vector glyph,
   the same icon set used by Google / Android / many professional dashboards.

2. Lucide SVG paths  -> used inside raw HTML we render ourselves (the dashboard
   cards live in an isolated iframe where Material tokens are unavailable).

Keeping every glyph in one file means the look stays consistent everywhere.
"""

# ──────────────────────────────────────────────────────────────────────────
# Material Symbol tokens for the sidebar navigation + page accents.
# ──────────────────────────────────────────────────────────────────────────
NAV_ICONS = {
    "Dashboard":            ":material/space_dashboard:",
    "Point of Sale":        ":material/point_of_sale:",
    "Inventory":            ":material/inventory_2:",
    "Customers":            ":material/groups:",
    "Suppliers":            ":material/local_shipping:",
    "Expenses":             ":material/account_balance_wallet:",
    "Delivery Board":       ":material/local_shipping:",
    "Completed Deliveries": ":material/task_alt:",
    "Pending Deliveries":   ":material/local_shipping:",
    "Completed Orders":     ":material/task_alt:",
    "Pending Orders":       ":material/receipt_long:",
    "Orders":               ":material/receipt_long:",
    "Reports":              ":material/monitoring:",
    "Activity Log":         ":material/history:",
    "Settings":             ":material/settings:",
}

# Material tokens used inline (page headings, list rows, etc.)
M = {
    "order":      ":material/receipt_long:",
    "customer":   ":material/person:",
    "delivery":   ":material/local_shipping:",
    "supplier":   ":material/local_shipping:",
    "product":    ":material/inventory_2:",
    "money":      ":material/payments:",
    "user":       ":material/account_circle:",
    "edit":       ":material/edit:",
    "save":       ":material/save:",
    "add":        ":material/add:",
    "logout":     ":material/logout:",
    "login":      ":material/login:",
    "warning":    ":material/warning:",
    "check":      ":material/check_circle:",
    "search":     ":material/search:",
    "cart":       ":material/shopping_cart:",
    "history":    ":material/history:",
}


# ──────────────────────────────────────────────────────────────────────────
# Lucide-style stroke icons for self-rendered HTML (dashboard cards, slips).
# ──────────────────────────────────────────────────────────────────────────
_LUCIDE_PATHS = {
    "trending-up":   '<polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/>',
    "bar-chart":     '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>',
    "calendar":      '<rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>',
    "clipboard":     '<path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/><line x1="12" y1="11" x2="16" y2="11"/><line x1="12" y1="16" x2="16" y2="16"/><line x1="8" y1="11" x2="8.01" y2="11"/><line x1="8" y1="16" x2="8.01" y2="16"/>',
    "alert":         '<path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
    "package":       '<path d="M16.5 9.4 7.5 4.21"/><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/>',
    "truck":         '<rect x="1" y="3" width="15" height="13"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/>',
    "check-circle":  '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>',
}


def svg(name: str, size: int = 20, stroke: str = "currentColor", width: float = 2) -> str:
    """Return an inline Lucide-style SVG string for use inside our own HTML."""
    paths = _LUCIDE_PATHS.get(name, _LUCIDE_PATHS["package"])
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{stroke}" stroke-width="{width}" '
        f'stroke-linecap="round" stroke-linejoin="round">{paths}</svg>'
    )
