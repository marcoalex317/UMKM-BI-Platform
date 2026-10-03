"""
theme.py
========
Tampilan dashboard: warna, CSS, template grafik Plotly, dan komponen kecil
(header halaman, kartu KPI, judul seksi, catatan analis) supaya semua halaman
konsisten.

Warna dasar mengikuti tema navy gelap. Palet kategori sudah dicek dengan
validator palet (CVD dan kontras) terhadap latar #00172b.
"""
from __future__ import annotations

from html import escape

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# --------------------------------------------------------------------------- #
# Warna
# --------------------------------------------------------------------------- #
BG = "#00172b"           # latar halaman dan grafik
SIDEBAR = "#03213d"
CARD = "#0a2a47"
CARD_HEAD = "#0c3153"
SELECTED = "#154c79"
TEXT = "#e4e5e5"
TEXT_2 = "#a9b8c6"
MUTED = "#8297ab"        # label sumbu, keterangan kecil
GRID = "#12304d"         # garis bantu, sengaja samar
AXIS = "#244766"
DIM = "#3a5878"          # batang yang tidak sedang disorot
ACCENT = "#0083b8"       # warna utama satu seri

# Urutan tetap, tidak diputar ulang. Lolos validator mode gelap di #00172b.
SERIES = ["#0083b8", "#d95926", "#199e70", "#c98500",
          "#d55181", "#008300", "#9085e9", "#e66767"]

# Warna mengikuti entitas, bukan peringkat, jadi filter tidak mengubah warna.
CHANNEL_COLORS = {
    "offline": SERIES[0], "shopee": SERIES[1],
    "tokopedia": SERIES[2], "instagram": SERIES[3],
}
STATUS = {"good": "#0ca30c", "warning": "#fab219",
          "serious": "#ec835a", "critical": "#d03b3b"}


# --------------------------------------------------------------------------- #
# Format angka gaya Indonesia
# --------------------------------------------------------------------------- #
def _id(s: str) -> str:
    """Tukar pemisah: 1,234.5 menjadi 1.234,5."""
    return s.replace(",", "_").replace(".", ",").replace("_", ".")


def rp(x) -> str:
    """Rupiah ringkas: Rp 9,28 M / Rp 411,3 jt / Rp 464 rb."""
    try:
        x = float(x)
    except (TypeError, ValueError):
        return "-"
    if abs(x) >= 1e9:
        return "Rp " + _id(f"{x/1e9:,.2f}") + " M"
    if abs(x) >= 1e6:
        return "Rp " + _id(f"{x/1e6:,.1f}") + " jt"
    if abs(x) >= 1e3:
        return "Rp " + _id(f"{x/1e3:,.0f}") + " rb"
    return "Rp " + _id(f"{x:,.0f}")


def rp_full(x) -> str:
    try:
        return "Rp " + _id(f"{float(x):,.0f}")
    except (TypeError, ValueError):
        return "-"


def num(x) -> str:
    try:
        return _id(f"{float(x):,.0f}")
    except (TypeError, ValueError):
        return "-"


def pct(x, d: int = 1) -> str:
    try:
        return _id(f"{float(x):.{d}f}") + "%"
    except (TypeError, ValueError):
        return "-"


# --------------------------------------------------------------------------- #
# Template Plotly
# --------------------------------------------------------------------------- #
_axis = dict(gridcolor=GRID, gridwidth=1, linecolor=AXIS, zeroline=False,
             tickfont=dict(color=MUTED, size=11), title=dict(font=dict(color=MUTED, size=11)),
             showline=False, ticks="", separatethousands=True,
             exponentformat="none")

pio.templates["rmn"] = go.layout.Template(
    layout=dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Source Sans, Source Sans Pro, Segoe UI, system-ui, sans-serif",
                  color=TEXT_2, size=12),
        colorway=SERIES,
        separators=",.",
        xaxis=_axis,
        yaxis=_axis,
        legend=dict(orientation="h", x=0, y=1.12, xanchor="left", yanchor="bottom",
                    font=dict(color=TEXT_2, size=11), title=dict(text="")),
        hoverlabel=dict(bgcolor=CARD_HEAD, bordercolor=SELECTED,
                        font=dict(color=TEXT, size=12)),
        margin=dict(l=4, r=12, t=8, b=4),
        bargap=0.35,
    )
)
pio.templates.default = "rmn"


def style(fig: go.Figure, height: int = 320, legend: bool | None = None) -> go.Figure:
    """Rapikan grafik: tinggi, legend, sudut batang, garis tipis."""
    fig.update_layout(template="rmn", height=height)
    if legend is not None:
        fig.update_layout(showlegend=legend)
    fig.update_traces(selector=dict(type="bar"), marker_cornerradius=4,
                      marker_line_width=0)
    fig.update_traces(selector=dict(type="scatter"), line_width=2)
    title_font = dict(size=11, color=MUTED)
    fig.update_xaxes(title_font=title_font, tickfont=dict(size=11))
    fig.update_yaxes(title_font=title_font)
    return fig


def chart(fig: go.Figure) -> None:
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


# --------------------------------------------------------------------------- #
# CSS dan komponen halaman
# --------------------------------------------------------------------------- #
_CSS = f"""
<style>
  .block-container, [data-testid="stMainBlockContainer"] {{ padding-top: 3.4rem; padding-bottom: 3rem; max-width: 1400px; }}
  [data-testid="stSidebar"] {{ background: {SIDEBAR}; border-right: 1px solid rgba(255,255,255,0.05); }}
  [data-testid="stSidebarNav"] a[aria-current="page"] {{ background: {SELECTED}; }}
  [data-testid="stSidebarNavSeparator"] {{ border-color: rgba(255,255,255,0.06); }}
  h1, h2, h3 {{ letter-spacing: -0.01em; }}

  .ph-title {{ font-size: 1.75rem; font-weight: 700; color: {TEXT}; margin: 0; line-height: 1.2; }}
  .ph-sub {{ color: {TEXT_2}; font-size: 0.95rem; margin-top: 0.35rem; max-width: 95ch; }}
  .ph-meta {{ color: {MUTED}; font-size: 0.8rem; margin-top: 0.5rem; }}
  .ph-meta b {{ color: {TEXT_2}; font-weight: 600; }}

  .kpi-grid {{ display: grid; gap: 12px; margin: 1.1rem 0 0.4rem;
               grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); }}
  .kpi {{ background: {CARD}; border: 1px solid rgba(255,255,255,0.06);
          border-radius: 10px; overflow: hidden; }}
  .kpi-label {{ background: {CARD_HEAD}; border-left: 3px solid {ACCENT};
                padding: 7px 12px; font-size: 0.74rem; font-weight: 600;
                letter-spacing: 0.05em; text-transform: uppercase; color: {TEXT_2}; }}
  .kpi-value {{ padding: 12px 12px 2px; font-size: 1.6rem; font-weight: 600;
                color: {TEXT}; line-height: 1.15; white-space: nowrap;
                overflow: hidden; text-overflow: ellipsis; }}
  .kpi-note {{ padding: 2px 12px 12px; font-size: 0.78rem; color: {MUTED}; }}

  .sec-title {{ font-size: 1.02rem; font-weight: 600; color: {TEXT}; margin: 1.4rem 0 0; }}
  .sec-cap {{ font-size: 0.83rem; color: {MUTED}; margin: 0.15rem 0 0.2rem; }}

  .note {{ background: #06223b; border: 1px solid rgba(255,255,255,0.06);
           border-left: 3px solid {ACCENT}; border-radius: 8px;
           padding: 14px 18px; margin-top: 1.6rem; }}
  .note-title {{ font-size: 0.74rem; font-weight: 600; letter-spacing: 0.06em;
                 text-transform: uppercase; color: {TEXT_2}; margin-bottom: 6px; }}
  .note ul {{ margin: 0; padding-left: 1.1rem; }}
  .note li {{ color: {TEXT}; font-size: 0.92rem; margin: 4px 0; }}

  .side-label {{ font-size: 0.72rem; font-weight: 600; letter-spacing: 0.08em;
                 text-transform: uppercase; color: {MUTED}; margin: 0.4rem 0 0.2rem; }}
  .side-foot {{ font-size: 0.75rem; color: {MUTED}; line-height: 1.5;
                border-top: 1px solid rgba(255,255,255,0.06); padding-top: 0.8rem;
                margin-top: 1.2rem; }}
  .src {{ font-size: 0.75rem; color: {MUTED}; margin-top: -0.4rem; }}

  hr {{ border-color: rgba(255,255,255,0.06) !important; }}
</style>
"""


def apply_theme() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = "", meta: str = "") -> None:
    html = f'<div class="ph-title">{escape(title)}</div>'
    if subtitle:
        html += f'<div class="ph-sub">{escape(subtitle)}</div>'
    if meta:
        html += f'<div class="ph-meta">{meta}</div>'
    st.markdown(html, unsafe_allow_html=True)


def kpi_cards(items: list[tuple[str, str, str]]) -> None:
    """items: (label, nilai, keterangan kecil)."""
    cards = "".join(
        f'<div class="kpi"><div class="kpi-label">{escape(lbl)}</div>'
        f'<div class="kpi-value" title="{escape(val)}">{escape(val)}</div>'
        f'<div class="kpi-note">{escape(note)}</div></div>'
        for lbl, val, note in items
    )
    st.markdown(f'<div class="kpi-grid">{cards}</div>', unsafe_allow_html=True)


def section(title: str, caption: str = "") -> None:
    html = f'<div class="sec-title">{escape(title)}</div>'
    if caption:
        html += f'<div class="sec-cap">{escape(caption)}</div>'
    st.markdown(html, unsafe_allow_html=True)


def source(text: str) -> None:
    st.markdown(f'<div class="src">{escape(text)}</div>', unsafe_allow_html=True)


def note(points: list[str], title: str = "Catatan analis") -> None:
    """Kotak catatan. Teks boleh memuat <b> untuk angka penting."""
    items = "".join(f"<li>{p}</li>" for p in points)
    st.markdown(f'<div class="note"><div class="note-title">{escape(title)}</div>'
                f'<ul>{items}</ul></div>', unsafe_allow_html=True)


BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


def tgl(s) -> str:
    """'2025-07-01' menjadi '1 Jul 2025'."""
    from datetime import date
    d = date.fromisoformat(str(s)[:10])
    return f"{d.day} {BULAN[d.month-1]} {d.year}"


def filter_meta(f: dict) -> str:
    """Ringkasan filter aktif untuk ditampilkan di bawah judul halaman."""
    parts = [f"Periode <b>{tgl(f['date_from'])} - {tgl(f['date_to'])}</b>"]
    parts.append("Cabang <b>" + (escape(", ".join(f["stores"])) if f.get("stores") else "semua") + "</b>")
    parts.append("Channel <b>" + (escape(", ".join(f["channels"])) if f.get("channels") else "semua") + "</b>")
    return " &nbsp;·&nbsp; ".join(parts)


# --------------------------------------------------------------------------- #
# Pembuat grafik yang sering dipakai
# --------------------------------------------------------------------------- #
def bar_h(labels, values, text=None, hover=None, colors=None, height=None,
          xtitle="Rp juta", label_room=0.32) -> go.Figure:
    """Batang horizontal, nilai terbesar di atas, label di ujung batang.

    labels/values/text/colors diterima dalam urutan besar ke kecil.
    """
    labels, values = list(labels), list(values)
    n = len(labels)
    rev = slice(None, None, -1)
    fig = go.Figure(go.Bar(
        y=labels[rev], x=values[rev], orientation="h",
        marker_color=(list(colors)[rev] if colors is not None else ACCENT),
        text=(list(text)[rev] if text is not None else None),
        textposition="outside", cliponaxis=False,
        textfont=dict(color=TEXT_2, size=11),
        hovertext=(list(hover)[rev] if hover is not None else None),
        hoverinfo="text" if hover is not None else None,
        hovertemplate=None if hover is not None else "%{y}: %{x:,.1f}<extra></extra>",
    ))
    vmax = max(values) if values else 1
    fig.update_xaxes(title_text=xtitle, range=[0, vmax * (1 + label_room)])
    fig.update_yaxes(gridcolor="rgba(0,0,0,0)", tickfont=dict(color=TEXT_2, size=12))
    return style(fig, height=height or max(220, 40 * n + 60), legend=False)


def bar_v(labels, values, text=None, hover=None, colors=None, height=300,
          ytitle="Rp juta") -> go.Figure:
    """Batang vertikal untuk kategori yang punya urutan (bulan, hari, ukuran)."""
    fig = go.Figure(go.Bar(
        x=list(labels), y=list(values),
        marker_color=(list(colors) if colors is not None else ACCENT),
        text=(list(text) if text is not None else None),
        textposition="outside", cliponaxis=False,
        textfont=dict(color=TEXT_2, size=11),
        hovertext=(list(hover) if hover is not None else None),
        hoverinfo="text" if hover is not None else None,
        hovertemplate=None if hover is not None else "%{x}: %{y:,.1f}<extra></extra>",
    ))
    vmax = max(values) if len(values) else 1
    fig.update_yaxes(title_text=ytitle, range=[0, vmax * 1.18])
    fig.update_xaxes(gridcolor="rgba(0,0,0,0)", tickfont=dict(color=TEXT_2, size=12))
    return style(fig, height=height, legend=False)


def empty_state(msg: str = "Tidak ada transaksi untuk kombinasi filter ini. "
                           "Coba perlebar periode atau kosongkan pilihan cabang dan channel.") -> None:
    st.info(msg)
    st.stop()
