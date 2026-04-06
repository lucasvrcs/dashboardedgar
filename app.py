import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings, os, pathlib
warnings.filterwarnings("ignore")

# ──────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Painel de Pacientes · dr.edgar",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# PALETTE
# ──────────────────────────────────────────────────────────────────────────────
BG     = "#FAF7F2"
CARD   = "#FFFFFF"
BORDER = "#EDE9E1"
TDARK  = "#2E2B28"
TMID   = "#6B6560"
ACCENT = "#B8835A"

P = [
    "#F2A7BB",  # rosa
    "#8FC8E8",  # azul-céu
    "#92D4AD",  # menta
    "#FFCB96",  # pêssego
    "#C7B6EC",  # lavanda
    "#FFE49C",  # amarelo
    "#A6D9F0",  # azul-claro
    "#B7E4B2",  # verde-claro
    "#F8C19A",  # laranja
    "#E0C4EC",  # lilás
    "#F7B7A5",  # salmão
    "#9ED8C8",  # turquesa
]

# ──────────────────────────────────────────────────────────────────────────────
# LOGO (base64 embedded)
# ──────────────────────────────────────────────────────────────────────────────
_logo_path = pathlib.Path(__file__).parent / "logo_b64_clean.txt"
LOGO_B64 = _logo_path.read_text().strip() if _logo_path.exists() else ""

# ──────────────────────────────────────────────────────────────────────────────
# CSS
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [data-testid="stAppViewContainer"] {{
    background: {BG}; font-family: 'Inter', sans-serif; color: {TDARK};
}}
[data-testid="stSidebar"] {{
    background: #F0EBE3; border-right: 1px solid {BORDER};
}}
.stTabs [data-baseweb="tab-list"] {{
    gap: 3px; background: {BORDER}; padding: 4px; border-radius: 10px;
}}
.stTabs [data-baseweb="tab"] {{
    background: transparent; border: none; border-radius: 8px;
    color: {TMID}; font-size: 13px; font-weight: 500; padding: 6px 14px;
}}
.stTabs [aria-selected="true"] {{
    background: {CARD} !important; color: {TDARK} !important;
    box-shadow: 0 1px 4px rgba(0,0,0,.07);
}}
.kpi-card {{
    background: {CARD}; border: 1px solid {BORDER}; border-radius: 14px;
    padding: 18px 20px; text-align: center;
}}
.kpi-value {{ font-size: 2.1rem; font-weight: 700; color: {TDARK}; line-height: 1.1; }}
.kpi-label {{ font-size: 11px; font-weight: 600; color: {TMID}; margin-top: 6px;
              letter-spacing: .05em; text-transform: uppercase; }}
.kpi-sub   {{ font-size: 11px; color: {ACCENT}; margin-top: 3px; }}
.sec-title {{ font-size: 15px; font-weight: 600; color: {TDARK};
              border-left: 3px solid {ACCENT}; padding-left: 10px; margin-bottom: 3px; }}
.sec-sub   {{ font-size: 12px; color: {TMID}; margin-bottom: 14px; padding-left: 13px; }}
.block-container {{ padding-top: 1.8rem; }}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# CHART HELPERS
# ──────────────────────────────────────────────────────────────────────────────
_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color=TDARK),
    margin=dict(t=44, b=14, l=14, r=14),
    legend=dict(font=dict(size=11, color=TDARK)),
    title_font=dict(size=13, color=TDARK),
)
_AX      = dict(showgrid=False, color=TDARK, tickfont=dict(size=11, color=TDARK))
_AX_GRID = dict(showgrid=True, gridcolor=BORDER, color=TDARK, tickfont=dict(size=11, color=TDARK))

def _lay(fig, title="", h=280, grid_y=False):
    fig.update_layout(**_LAYOUT, height=h,
                      title=dict(text=title, font=dict(size=13, color=TDARK), x=0, xref="paper"))
    fig.update_xaxes(**_AX)
    fig.update_yaxes(**(_AX_GRID if grid_y else _AX))
    return fig

def donut(s, title, colors=None, h=280):
    if s.empty: return go.Figure()
    c = (colors or P)[:len(s)]
    fig = go.Figure(go.Pie(
        labels=s.index, values=s.values, hole=0.55,
        textinfo="percent", textfont=dict(size=12, color="#000"),
        marker=dict(colors=c, line=dict(color="white", width=2)),
        hovertemplate="%{label}: %{value:.1f}%<extra></extra>",
    ))
    return _lay(fig, title, h)

def hbar(s, title, color=None, h=None):
    if s.empty: return go.Figure()
    s = s.sort_values()
    h = h or max(160, len(s) * 52)
    fig = go.Figure(go.Bar(
        x=s.values, y=s.index, orientation="h",
        marker_color=color or P[1],
        text=[f"<b>{v:.0f}%</b>" for v in s.values],
        textposition="outside", textfont=dict(size=12, color="#000"),
        hovertemplate="%{y}: %{x:.1f}%<extra></extra>",
    ))
    _lay(fig, title, h)
    fig.update_xaxes(showticklabels=False, range=[0, s.max() * 1.3])
    return fig

def vbar(s, title, colors=None, h=260):
    if s.empty: return go.Figure()
    c = colors or [P[i % len(P)] for i in range(len(s))]
    fig = go.Figure(go.Bar(
        x=s.index, y=s.values,
        marker_color=c if isinstance(c, list) else c,
        text=[f"<b>{v:.0f}%</b>" for v in s.values],
        textposition="outside", textfont=dict(size=12, color="#000"),
        hovertemplate="%{x}: %{y:.1f}%<extra></extra>",
    ))
    _lay(fig, title, h)
    fig.update_yaxes(showticklabels=False, range=[0, s.max() * 1.25])
    return fig

def stacked(data, x_col, color_col, title, h=300, order=None):
    ct = data.groupby([x_col, color_col]).size().unstack(fill_value=0)
    ct_pct = ct.div(ct.sum(axis=1), axis=0).mul(100).round(1)
    if order:
        ct_pct = ct_pct.reindex([r for r in order if r in ct_pct.index])
    fig = go.Figure()
    for i, col in enumerate(ct_pct.columns):
        vals = ct_pct[col]
        fig.add_trace(go.Bar(
            name=col, x=ct_pct.index, y=vals,
            marker_color=P[i % len(P)],
            text=[f"<b>{v:.0f}%</b>" if v >= 7 else "" for v in vals],
            textposition="inside", textfont=dict(size=11, color="#000"),
            hovertemplate=f"{col}: %{{y:.1f}}%<extra></extra>",
        ))
    _lay(fig, title, h)
    fig.update_layout(barmode="stack",
                      yaxis=dict(showticklabels=False, range=[0, 110], showgrid=False))
    return fig

# ──────────────────────────────────────────────────────────────────────────────
# DATA
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data
def load():
    df = pd.read_excel("pacientes_edgar_200.xlsx")

    def bmi_cat(b):
        if b < 18.5: return "Abaixo do peso"
        if b < 25:   return "Peso normal"
        if b < 30:   return "Sobrepeso"
        if b < 35:   return "Obesidade I"
        return "Obesidade II/III"

    def age_grp(a):
        if a < 30: return "< 30"
        if a < 40: return "30–39"
        if a < 50: return "40–49"
        if a < 60: return "50–59"
        if a < 70: return "60–69"
        return "70+"

    def risco_grp(r):
        if r < 15:  return "Baixo (<15%)"
        if r < 30:  return "Moderado (15–30%)"
        if r < 50:  return "Alto (30–50%)"
        return "Muito Alto (≥50%)"

    df["bmi_cat"]    = df["IMC"].apply(bmi_cat)
    df["age_group"]  = df["Idade"].apply(age_grp)
    df["risco_grp"]  = df["Risco de Internação 10 anos (%)"].apply(risco_grp)
    df["internado"]  = df["Última Internação"].ne("Nenhuma").map(
        {True: "Já internado", False: "Sem internação"}
    )
    df["Sexo_full"]  = df["Sexo"].map({"M": "Masculino", "F": "Feminino"})

    return df

df = load()

COMP_COLS = [c for c in df.columns if "Comprometimento" in c]
COMP_LABELS = [c.replace("Comprometimento ", "") for c in COMP_COLS]

def pct(col):
    return df[col].value_counts(normalize=True).mul(100).round(1)

def split_expand(col, sep="; "):
    return df[col].dropna().str.split(sep).explode().str.strip()

# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    if LOGO_B64:
        st.markdown(
            f'<img src="data:image/jpeg;base64,{LOGO_B64}" '
            f'style="width:100%;border-radius:10px;margin-bottom:8px;">',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    pct_f  = (df["Sexo"] == "F").mean() * 100
    pct_m  = (df["Sexo"] == "M").mean() * 100
    pct_cr = (df["Doenças Crônicas"] != "Nenhuma doença crônica").mean() * 100
    risco_m = df["Risco de Internação 10 anos (%)"].mean()

    st.markdown(f"""
    <div style="font-size:11px;font-weight:600;color:{TMID};letter-spacing:.05em;
                text-transform:uppercase;margin-bottom:10px;">Resumo da base</div>
    """, unsafe_allow_html=True)

    for label, val in [
        ("Total de pacientes", "200"),
        ("Feminino / Masculino", f"{pct_f:.0f}% / {pct_m:.0f}%"),
        ("Com doença crónica", f"{pct_cr:.0f}%"),
        ("Idade média", f"{df['Idade'].mean():.0f} anos"),
        ("IMC médio", f"{df['IMC'].mean():.1f}"),
        ("Risco médio de internação", f"{risco_m:.0f}%"),
        ("DALY médio", f"{df['DALY Estimado'].mean():.1f}"),
    ]:
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;padding:7px 0;
                    border-bottom:1px solid {BORDER};font-size:13px;">
          <span style="color:{TMID}">{label}</span>
          <span style="font-weight:600;color:{TDARK}">{val}</span>
        </div>
        """, unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="margin-bottom:20px;">
  <h1 style="font-size:22px;font-weight:700;margin:0;color:{TDARK};">Painel de Pacientes</h1>
  <p style="font-size:13px;color:{TMID};margin:3px 0 0;">
    Telemedicina · dr.edgar · 200 pacientes
  </p>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# KPI STRIP
# ──────────────────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5, k6 = st.columns(6)
kpis = [
    ("200",                                              "Pacientes",           "na base"),
    (f"{pct_f:.0f}% / {pct_m:.0f}%",                   "F / M",               "distribuição"),
    (f"{df['Idade'].mean():.0f}",                        "Idade média",         "anos"),
    (f"{(df['IMC'] >= 25).mean()*100:.0f}%",            "Excesso de peso",     "IMC ≥ 25"),
    (f"{risco_m:.0f}%",                                  "Risco de internação", "média 10 anos"),
    (f"{df['DALY Estimado'].mean():.1f}",                "DALY médio",          "anos de vida ajustados"),
]
for col, (val, label, sub) in zip([k1,k2,k3,k4,k5,k6], kpis):
    with col:
        st.markdown(f"""
        <div class="kpi-card">
          <div class="kpi-value">{val}</div>
          <div class="kpi-label">{label}</div>
          <div class="kpi-sub">{sub}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<div style='margin-top:22px'></div>", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# TABS
# ──────────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "👤 Demográfico",
    "🌿 Estilo de Vida",
    "🏥 Histórico Médico",
    "🫀 Comprometimentos",
    "🔗 Análises Cruzadas",
    "📈 Indicadores Clínicos",
    "🔬 Explorador",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — DEMOGRÁFICO
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="sec-title">Perfil Demográfico</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Caracterização da base de 200 pacientes</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)

    with c1:
        s = pct("Sexo_full")
        st.plotly_chart(donut(s, "Sexo", [P[1], P[0]]), key="d_sexo", use_container_width=True)

    with c2:
        # Age distribution
        fig_age = go.Figure(go.Histogram(
            x=df["Idade"], nbinsx=10,
            marker_color=P[3], marker_line_color="white", marker_line_width=1.5,
            hovertemplate="Idade: %{x}<br>Qtd: %{y}<extra></extra>",
        ))
        _lay(fig_age, "Distribuição de Idades", 280)
        fig_age.update_xaxes(title="Idade")
        fig_age.update_yaxes(showticklabels=False)
        st.plotly_chart(fig_age, key="d_age", use_container_width=True)

    with c3:
        age_pct = df["age_group"].value_counts(normalize=True).mul(100).round(1)
        age_order = ["< 30","30–39","40–49","50–59","60–69","70+"]
        age_pct = age_pct.reindex([a for a in age_order if a in age_pct.index])
        st.plotly_chart(vbar(age_pct, "Faixa Etária (%)", colors=P), key="d_agegrp", use_container_width=True)

    c4, c5 = st.columns(2)

    with c4:
        bmi_order = ["Abaixo do peso","Peso normal","Sobrepeso","Obesidade I","Obesidade II/III"]
        bmi_pct = df["bmi_cat"].value_counts(normalize=True).mul(100).round(1)
        bmi_pct = bmi_pct.reindex([b for b in bmi_order if b in bmi_pct.index])
        fig_bmi = go.Figure(go.Bar(
            x=bmi_pct.index, y=bmi_pct.values,
            marker_color=[P[2], P[5], P[3], P[9], P[0]],
            text=[f"<b>{v:.0f}%</b>" for v in bmi_pct.values],
            textposition="outside", textfont=dict(size=12, color="#000"),
        ))
        _lay(fig_bmi, "Categorias de IMC", 280)
        fig_bmi.update_yaxes(showticklabels=False, range=[0, bmi_pct.max() * 1.25])
        st.plotly_chart(fig_bmi, key="d_bmicat", use_container_width=True)

    with c5:
        # IMC vs Idade scatter
        fig_sc = px.scatter(
            df, x="Idade", y="IMC", color="Sexo_full",
            color_discrete_map={"Masculino": P[1], "Feminino": P[0]},
            labels={"Sexo_full":"Sexo"},
            opacity=0.7,
        )
        fig_sc.add_hline(y=25, line_dash="dot", line_color="#888",
                         annotation_text="Sobrepeso", annotation_font_size=10,
                         annotation_font_color="#000")
        fig_sc.add_hline(y=30, line_dash="dot", line_color="#c88",
                         annotation_text="Obesidade", annotation_font_size=10,
                         annotation_font_color="#000")
        _lay(fig_sc, "IMC × Idade", 280, grid_y=True)
        st.plotly_chart(fig_sc, key="d_scatter", use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — ESTILO DE VIDA
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="sec-title">Estilo de Vida</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Hábitos e comportamentos dos pacientes</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.plotly_chart(donut(pct("Tabagismo"), "Tabagismo", [P[2], P[3], P[0]]),
                        key="ev_tab", use_container_width=True)
    with c2:
        st.plotly_chart(donut(pct("Etilismo"), "Etilismo", [P[2], P[5], P[0]]),
                        key="ev_etil", use_container_width=True)
    with c3:
        st.plotly_chart(donut(pct("Suplementação"), "Suplementação",
                              [P[2], P[1]]), key="ev_supl", use_container_width=True)

    c4, c5 = st.columns(2)
    with c4:
        atv_order = ["Moderada (3-5x/semana)", "Leve (1-2x/semana)", "Sedentário"]
        atv_pct = pct("Atividade Física").reindex(
            [a for a in atv_order if a in pct("Atividade Física").index]
        )
        st.plotly_chart(donut(atv_pct, "Atividade Física",
                              [P[2], P[5], P[0]]), key="ev_atv", use_container_width=True)
    with c5:
        st.plotly_chart(donut(pct("Qualidade da Dieta"), "Qualidade da Dieta",
                              [P[2], P[5], P[0]]), key="ev_diet", use_container_width=True)

    sono_order = ["Bom (7-9h/noite)", "Regular (6-7h/noite)", "Ruim (<6h/noite)"]
    sono_pct = pct("Qualidade do Sono").reindex(
        [s for s in sono_order if s in pct("Qualidade do Sono").index]
    )
    st.plotly_chart(donut(sono_pct, "Qualidade do Sono",
                          [P[2], P[5], P[0]], h=260), key="ev_sono", use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — HISTÓRICO MÉDICO
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="sec-title">Histórico Médico</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Doenças crónicas, antecedentes e internações</div>', unsafe_allow_html=True)

    # Doenças crônicas expandidas
    doencas = split_expand("Doenças Crônicas").value_counts(normalize=True).mul(100).round(1)
    doencas = doencas[doencas.index != "Nenhuma doença crônica"].sort_values()
    fig_dc = go.Figure(go.Bar(
        x=doencas.values, y=doencas.index, orientation="h",
        marker_color=P[0],
        text=[f"<b>{v:.0f}%</b>" for v in doencas.values],
        textposition="outside", textfont=dict(size=12, color="#000"),
    ))
    _lay(fig_dc, "Prevalência de Doenças Crónicas (% dos pacientes)", max(220, len(doencas)*54))
    fig_dc.update_xaxes(showticklabels=False, range=[0, doencas.max() * 1.3])
    st.plotly_chart(fig_dc, key="hm_dc", use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        hf = split_expand("Histórico Familiar").value_counts(normalize=True).mul(100).round(1).sort_values()
        st.plotly_chart(hbar(hf, "Histórico Familiar", P[4]), key="hm_hf", use_container_width=True)
    with c2:
        st.plotly_chart(donut(pct("internado"), "Histórico de Internação",
                              [P[3], P[2]]), key="hm_int", use_container_width=True)

    # Número de doenças por paciente
    c3, c4 = st.columns(2)
    with c3:
        n_doencas = df["Doenças Crônicas"].apply(
            lambda x: 0 if x == "Nenhuma doença crônica" else len(str(x).split("; "))
        )
        nd_pct = n_doencas.value_counts(normalize=True).sort_index().mul(100).round(1)
        nd_pct.index = nd_pct.index.astype(str)
        fig_nd = go.Figure(go.Bar(
            x=nd_pct.index, y=nd_pct.values,
            marker_color=P[:len(nd_pct)],
            text=[f"<b>{v:.0f}%</b>" for v in nd_pct.values],
            textposition="outside", textfont=dict(size=12, color="#000"),
        ))
        _lay(fig_nd, "Número de Doenças Crónicas por Paciente", 280)
        fig_nd.update_xaxes(title="Nº de doenças")
        fig_nd.update_yaxes(showticklabels=False, range=[0, nd_pct.max()*1.25])
        st.plotly_chart(fig_nd, key="hm_nd", use_container_width=True)
    with c4:
        st.plotly_chart(donut(pct("risco_grp"), "Risco de Internação em 10 Anos",
                              [P[2], P[5], P[3], P[0]]), key="hm_risco", use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — COMPROMETIMENTOS
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="sec-title">Comprometimentos por Sistema Orgânico</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Scores de 0 a 100 por sistema (média dos pacientes)</div>', unsafe_allow_html=True)

    # Radar chart — médias gerais
    means = df[COMP_COLS].mean().round(1)

    fig_radar = go.Figure(go.Scatterpolar(
        r=list(means.values) + [means.values[0]],
        theta=COMP_LABELS + [COMP_LABELS[0]],
        fill="toself",
        fillcolor=f"rgba(143,200,232,0.25)",
        line=dict(color=P[1], width=2),
        marker=dict(size=6, color=P[1]),
        name="Média geral",
    ))
    fig_radar.update_layout(
        **_LAYOUT, height=420,
        title=dict(text="Perfil Médio de Comprometimento por Sistema", font=dict(size=13, color=TDARK), x=0),
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=9, color=TDARK),
                            gridcolor=BORDER),
            angularaxis=dict(tickfont=dict(size=11, color=TDARK), gridcolor=BORDER),
        ),
    )
    st.plotly_chart(fig_radar, key="comp_radar", use_container_width=True)

    # Bar — ranking dos comprometimentos
    means_sorted = means.sort_values()
    means_sorted.index = [l.replace("Comprometimento ", "") for l in means_sorted.index]
    fig_comp_bar = go.Figure(go.Bar(
        x=means_sorted.values, y=means_sorted.index, orientation="h",
        marker_color=P[1],
        text=[f"<b>{v:.1f}</b>" for v in means_sorted.values],
        textposition="outside", textfont=dict(size=12, color="#000"),
    ))
    _lay(fig_comp_bar, "Comprometimento Médio por Sistema (score 0–100)", max(300, len(means_sorted)*52))
    fig_comp_bar.update_xaxes(showticklabels=False, range=[0, means_sorted.max()*1.2])
    st.plotly_chart(fig_comp_bar, key="comp_bar", use_container_width=True)

    # Box plots dos comprometimentos
    fig_box = go.Figure()
    for i, (col, label) in enumerate(zip(COMP_COLS, COMP_LABELS)):
        fig_box.add_trace(go.Box(
            y=df[col], name=label,
            marker_color=P[i % len(P)],
            line=dict(color=P[i % len(P)]),
            boxmean=True,
            hovertemplate=f"{label}<br>Score: %{{y}}<extra></extra>",
        ))
    _lay(fig_box, "Distribuição dos Scores de Comprometimento", 400, grid_y=True)
    fig_box.update_xaxes(tickangle=-30)
    fig_box.update_yaxes(title="Score (0–100)", range=[-5, 110])
    st.plotly_chart(fig_box, key="comp_box", use_container_width=True)

    # Radar por sexo
    means_m = df[df["Sexo"]=="M"][COMP_COLS].mean().round(1)
    means_f = df[df["Sexo"]=="F"][COMP_COLS].mean().round(1)
    fig_r2 = go.Figure()
    for vals, name, color in [(means_m, "Masculino", P[1]), (means_f, "Feminino", P[0])]:
        fig_r2.add_trace(go.Scatterpolar(
            r=list(vals.values) + [vals.values[0]],
            theta=COMP_LABELS + [COMP_LABELS[0]],
            fill="toself",
            fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:],16)},0.18)",
            line=dict(color=color, width=2),
            name=name,
        ))
    fig_r2.update_layout(
        **_LAYOUT, height=400,
        title=dict(text="Comprometimento por Sistema × Sexo", font=dict(size=13, color=TDARK), x=0),
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=9, color=TDARK),
                            gridcolor=BORDER),
            angularaxis=dict(tickfont=dict(size=11, color=TDARK), gridcolor=BORDER),
        ),
    )
    st.plotly_chart(fig_r2, key="comp_radar2", use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — ANÁLISES CRUZADAS
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown('<div class="sec-title">Análises Cruzadas</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Relações entre variáveis clínicas e comportamentais</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    # IMC × Sexo
    with c1:
        d = df[["Sexo_full","bmi_cat"]].dropna()
        bmi_order = ["Abaixo do peso","Peso normal","Sobrepeso","Obesidade I","Obesidade II/III"]
        st.plotly_chart(stacked(d, "Sexo_full", "bmi_cat", "IMC por Sexo",
                                order=["Masculino","Feminino"]),
                        key="cr_bmi_sex", use_container_width=True)

    # Atividade Física × Qualidade do Sono
    with c2:
        d = df[["Atividade Física","Qualidade do Sono"]].dropna()
        st.plotly_chart(stacked(d, "Atividade Física", "Qualidade do Sono",
                                "Qualidade do Sono × Atividade Física", h=320),
                        key="cr_atv_sono", use_container_width=True)

    c3, c4 = st.columns(2)

    # Tabagismo × Risco de Internação
    with c3:
        d = df[["Tabagismo","risco_grp"]].dropna()
        st.plotly_chart(stacked(d, "Tabagismo", "risco_grp",
                                "Risco de Internação × Tabagismo", h=300),
                        key="cr_tab_risco", use_container_width=True)

    # Faixa etária × Doenças
    with c4:
        d = df[["age_group"]].copy()
        d["n_doencas"] = df["Doenças Crônicas"].apply(
            lambda x: "Nenhuma" if x=="Nenhuma doença crônica"
                      else ("1 doença" if len(str(x).split("; "))==1 else "2+ doenças")
        )
        age_order = ["< 30","30–39","40–49","50–59","60–69","70+"]
        st.plotly_chart(stacked(d, "age_group", "n_doencas",
                                "Número de Doenças × Faixa Etária",
                                order=age_order, h=300),
                        key="cr_age_doencas", use_container_width=True)

    c5, c6 = st.columns(2)

    # Dieta × IMC
    with c5:
        d = df[["Qualidade da Dieta","bmi_cat"]].dropna()
        bmi_order2 = ["Peso normal","Sobrepeso","Obesidade I","Obesidade II/III"]
        st.plotly_chart(stacked(d, "Qualidade da Dieta", "bmi_cat",
                                "IMC × Qualidade da Dieta", h=300),
                        key="cr_diet_bmi", use_container_width=True)

    # Comprometimento cardiovascular × risco
    with c6:
        fig_cv = px.scatter(
            df, x="Risco de Internação 10 anos (%)",
            y="Comprometimento Cardiovascular",
            color="Sexo_full",
            color_discrete_map={"Masculino": P[1], "Feminino": P[0]},
            opacity=0.65,
            labels={"Sexo_full":"Sexo",
                    "Risco de Internação 10 anos (%)":"Risco de Internação 10a (%)",
                    "Comprometimento Cardiovascular":"Compr. Cardiovascular"},
        )
        _lay(fig_cv, "Comprometimento Cardiovascular × Risco de Internação", 300, grid_y=True)
        st.plotly_chart(fig_cv, key="cr_cv_risco", use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — INDICADORES CLÍNICOS
# ══════════════════════════════════════════════════════════════════════════════
with tab6:
    st.markdown('<div class="sec-title">Indicadores Clínicos</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">DALY, expectativa de vida ajustada e risco de internação</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)

    # DALY distribution
    with c1:
        fig_daly = go.Figure(go.Histogram(
            x=df["DALY Estimado"], nbinsx=12,
            marker_color=P[4], marker_line_color="white", marker_line_width=1.5,
        ))
        _lay(fig_daly, f"DALY Estimado (média {df['DALY Estimado'].mean():.1f})", 280)
        fig_daly.update_xaxes(title="DALY (anos)")
        fig_daly.update_yaxes(showticklabels=False)
        st.plotly_chart(fig_daly, key="ic_daly", use_container_width=True)

    # Expectativa de Vida
    with c2:
        fig_ev = go.Figure(go.Histogram(
            x=df["Expectativa de Vida Ajustada"], nbinsx=12,
            marker_color=P[2], marker_line_color="white", marker_line_width=1.5,
        ))
        _lay(fig_ev, f"Expectativa de Vida Ajustada (média {df['Expectativa de Vida Ajustada'].mean():.1f}a)", 280)
        fig_ev.update_xaxes(title="Anos")
        fig_ev.update_yaxes(showticklabels=False)
        st.plotly_chart(fig_ev, key="ic_ev", use_container_width=True)

    # Risco de Internação
    with c3:
        fig_ri = go.Figure(go.Histogram(
            x=df["Risco de Internação 10 anos (%)"], nbinsx=12,
            marker_color=P[3], marker_line_color="white", marker_line_width=1.5,
        ))
        _lay(fig_ri, f"Risco de Internação 10 anos (média {df['Risco de Internação 10 anos (%)'].mean():.0f}%)", 280)
        fig_ri.update_xaxes(title="%")
        fig_ri.update_yaxes(showticklabels=False)
        st.plotly_chart(fig_ri, key="ic_ri", use_container_width=True)

    # DALY × Idade scatter (por sexo)
    fig_dy_age = px.scatter(
        df, x="Idade", y="DALY Estimado",
        color="Sexo_full",
        color_discrete_map={"Masculino": P[1], "Feminino": P[0]},
        size="Risco de Internação 10 anos (%)",
        size_max=18,
        opacity=0.7,
        labels={"Sexo_full":"Sexo","DALY Estimado":"DALY"},
        hover_data={"Doenças Crônicas": True, "IMC": True},
    )
    _lay(fig_dy_age, "DALY × Idade — tamanho = Risco de Internação", 360, grid_y=True)
    st.plotly_chart(fig_dy_age, key="ic_daly_age", use_container_width=True)

    # DALY × sexo + atividade física
    c4, c5 = st.columns(2)
    with c4:
        fig_daly_sex = go.Figure()
        for i, sexo in enumerate(["Masculino","Feminino"]):
            vals = df[df["Sexo_full"]==sexo]["DALY Estimado"]
            fig_daly_sex.add_trace(go.Box(
                y=vals, name=sexo,
                marker_color=P[i], line=dict(color=P[i]),
                boxmean=True,
            ))
        _lay(fig_daly_sex, "DALY por Sexo", 300, grid_y=True)
        fig_daly_sex.update_yaxes(title="DALY")
        st.plotly_chart(fig_daly_sex, key="ic_daly_sex", use_container_width=True)

    with c5:
        fig_daly_atv = go.Figure()
        atv_order2 = ["Moderada (3-5x/semana)","Leve (1-2x/semana)","Sedentário"]
        for i, atv in enumerate(atv_order2):
            vals = df[df["Atividade Física"]==atv]["DALY Estimado"]
            fig_daly_atv.add_trace(go.Box(
                y=vals, name=atv.split(" (")[0],
                marker_color=P[i], line=dict(color=P[i]),
                boxmean=True,
            ))
        _lay(fig_daly_atv, "DALY × Atividade Física", 300, grid_y=True)
        fig_daly_atv.update_yaxes(title="DALY")
        st.plotly_chart(fig_daly_atv, key="ic_daly_atv", use_container_width=True)

    # Expectativa de vida × nº de doenças
    df_ev = df.copy()
    df_ev["n_doencas_grp"] = df_ev["Doenças Crônicas"].apply(
        lambda x: "0" if x=="Nenhuma doença crônica"
                  else ("1" if len(str(x).split("; "))==1
                  else ("2" if len(str(x).split("; "))==2 else "3+"))
    )
    fig_ev_nd = go.Figure()
    for i, nd in enumerate(["0","1","2","3+"]):
        vals = df_ev[df_ev["n_doencas_grp"]==nd]["Expectativa de Vida Ajustada"]
        if vals.empty: continue
        fig_ev_nd.add_trace(go.Box(
            y=vals, name=f"{nd} {'doença' if nd=='1' else 'doenças'}",
            marker_color=P[i], line=dict(color=P[i]),
            boxmean=True,
        ))
    _lay(fig_ev_nd, "Expectativa de Vida Ajustada × Nº de Doenças Crónicas", 320, grid_y=True)
    fig_ev_nd.update_yaxes(title="Anos")
    st.plotly_chart(fig_ev_nd, key="ic_ev_nd", use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 7 — EXPLORADOR INTERATIVO
# ══════════════════════════════════════════════════════════════════════════════
with tab7:
    st.markdown('<div class="sec-title">Explorador de Variáveis</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Escolha as variáveis e o tipo de visualização para explorar relações</div>', unsafe_allow_html=True)

    # ── Definição das variáveis disponíveis ───────────────────────────────────
    CATS = {
        "Sexo":              "Sexo_full",
        "Faixa Etária":      "age_group",
        "IMC (categoria)":   "bmi_cat",
        "Tabagismo":         "Tabagismo",
        "Etilismo":          "Etilismo",
        "Atividade Física":  "Atividade Física",
        "Qualidade da Dieta":"Qualidade da Dieta",
        "Qualidade do Sono": "Qualidade do Sono",
        "Suplementação":     "Suplementação",
        "Risco de Internação":"risco_grp",
        "Histórico de Internação":"internado",
    }
    NUMS = {
        "Idade":                          "Idade",
        "IMC":                            "IMC",
        "DALY Estimado":                  "DALY Estimado",
        "Expectativa de Vida Ajustada":   "Expectativa de Vida Ajustada",
        "Risco de Internação 10 anos (%)":"Risco de Internação 10 anos (%)",
        "Compr. Cardiovascular":          "Comprometimento Cardiovascular",
        "Compr. Endócrino":               "Comprometimento Endócrino",
        "Compr. Respiratório":            "Comprometimento Respiratório",
        "Compr. Digestivo":               "Comprometimento Digestivo",
        "Compr. Urinário":                "Comprometimento Urinário",
        "Compr. Osteoarticular":          "Comprometimento Osteoarticular",
        "Compr. Muscular":                "Comprometimento Muscular",
        "Compr. Neurológico":             "Comprometimento Neurológico",
        "Compr. Psicológico":             "Comprometimento Psicológico",
    }
    ALL_VARS = {**CATS, **NUMS}
    CAT_KEYS = list(CATS.keys())
    NUM_KEYS = list(NUMS.keys())
    ALL_KEYS = list(ALL_VARS.keys())

    # ── Seletores ─────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="background:{CARD};border:1px solid {BORDER};border-radius:14px;
                padding:20px 24px;margin-bottom:20px;">
    """, unsafe_allow_html=True)

    col_tipo, col_x, col_y, col_cor = st.columns([1.2, 1.5, 1.5, 1.5])

    with col_tipo:
        tipo = st.selectbox(
            "Tipo de gráfico",
            ["Barras empilhadas", "Barras agrupadas", "Dispersão (scatter)",
             "Boxplot", "Histograma", "Violino"],
            key="exp_tipo",
        )

    # Defaults inteligentes por tipo
    if tipo in ["Barras empilhadas", "Barras agrupadas"]:
        default_x  = CAT_KEYS.index("Atividade Física")
        default_y  = CAT_KEYS.index("Qualidade do Sono")
        default_cor = 0
        x_options  = CAT_KEYS
        y_options  = CAT_KEYS
        cor_options = ["(nenhuma)"] + CAT_KEYS
    elif tipo == "Dispersão (scatter)":
        default_x  = NUM_KEYS.index("Idade")
        default_y  = NUM_KEYS.index("DALY Estimado")
        default_cor = 0
        x_options  = NUM_KEYS
        y_options  = NUM_KEYS
        cor_options = ["(nenhuma)"] + CAT_KEYS
    elif tipo == "Boxplot":
        default_x  = CAT_KEYS.index("Atividade Física")
        default_y  = NUM_KEYS.index("DALY Estimado")
        default_cor = 0
        x_options  = CAT_KEYS
        y_options  = NUM_KEYS
        cor_options = ["(nenhuma)"] + CAT_KEYS
    elif tipo == "Violino":
        default_x  = CAT_KEYS.index("Tabagismo")
        default_y  = NUM_KEYS.index("Comprometimento Cardiovascular")
        default_cor = 0
        x_options  = CAT_KEYS
        y_options  = NUM_KEYS
        cor_options = ["(nenhuma)"] + CAT_KEYS
    else:  # Histograma
        default_x  = NUM_KEYS.index("Idade")
        default_y  = 0
        default_cor = 0
        x_options  = NUM_KEYS
        y_options  = NUM_KEYS          # ignorado
        cor_options = ["(nenhuma)"] + CAT_KEYS

    with col_x:
        label_x = st.selectbox(
            "Eixo X" if tipo != "Histograma" else "Variável",
            x_options,
            index=min(default_x, len(x_options)-1),
            key="exp_x",
        )
    with col_y:
        if tipo not in ["Histograma"]:
            label_y = st.selectbox(
                "Eixo Y" if tipo != "Barras empilhadas" else "Cor / Segmento",
                y_options,
                index=min(default_y, len(y_options)-1),
                key="exp_y",
            )
        else:
            label_y = None
            st.selectbox("Eixo Y", ["(automático)"], key="exp_y_dummy", disabled=True)

    with col_cor:
        if tipo not in ["Barras empilhadas"]:
            label_cor = st.selectbox(
                "Colorir por",
                cor_options,
                index=0,
                key="exp_cor",
            )
        else:
            label_cor = "(nenhuma)"
            st.selectbox("Colorir por", ["(automático)"], key="exp_cor_dummy", disabled=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Resolução das colunas reais ───────────────────────────────────────────
    col_x   = ALL_VARS.get(label_x, label_x)
    col_y   = ALL_VARS.get(label_y, label_y) if label_y else None
    col_cor = ALL_VARS.get(label_cor) if label_cor and label_cor != "(nenhuma)" else None

    # Gerar paleta de cor dinâmica
    def make_color_map(series):
        cats = series.dropna().unique()
        return {c: P[i % len(P)] for i, c in enumerate(sorted(cats))}

    # ── Renderização ──────────────────────────────────────────────────────────
    try:
        if tipo in ["Barras empilhadas", "Barras agrupadas"]:
            grp = [col_x, col_y]
            ct = df[grp].dropna().groupby(grp).size().unstack(fill_value=0)
            if tipo == "Barras empilhadas":
                ct = ct.div(ct.sum(axis=1), axis=0).mul(100).round(1)
            fig_exp = go.Figure()
            for i, col in enumerate(ct.columns):
                vals = ct[col]
                fig_exp.add_trace(go.Bar(
                    name=str(col),
                    x=ct.index.astype(str),
                    y=vals.values,
                    marker_color=P[i % len(P)],
                    text=[f"<b>{v:.0f}{'%' if tipo=='Barras empilhadas' else ''}</b>"
                          if v >= (5 if tipo=="Barras empilhadas" else 1) else ""
                          for v in vals],
                    textposition="inside",
                    textfont=dict(size=11, color="#000"),
                ))
            _lay(fig_exp,
                 f"{label_x} × {label_y}" + (" (%)" if tipo=="Barras empilhadas" else ""),
                 380)
            fig_exp.update_layout(
                barmode="stack" if tipo=="Barras empilhadas" else "group",
                xaxis_tickangle=-20,
                yaxis=dict(showgrid=False,
                           showticklabels=tipo!="Barras empilhadas",
                           range=[0, 110] if tipo=="Barras empilhadas" else None),
            )

        elif tipo == "Dispersão (scatter)":
            plot_df = df[[col_x, col_y] + ([col_cor] if col_cor else [])].dropna()
            if col_cor:
                cmap = make_color_map(plot_df[col_cor])
                fig_exp = px.scatter(
                    plot_df, x=col_x, y=col_y, color=col_cor,
                    color_discrete_map=cmap,
                    opacity=0.7,
                    labels={col_cor: label_cor},
                    trendline="ols",
                )
            else:
                fig_exp = px.scatter(
                    plot_df, x=col_x, y=col_y,
                    opacity=0.7,
                    trendline="ols",
                    color_discrete_sequence=[P[1]],
                )
            _lay(fig_exp, f"{label_x} × {label_y}", 420, grid_y=True)
            fig_exp.update_traces(selector=dict(mode="lines"),
                                  line=dict(dash="dot", width=1.5))

        elif tipo == "Boxplot":
            plot_df = df[[col_x, col_y] + ([col_cor] if col_cor else [])].dropna()
            cats = sorted(plot_df[col_x].unique())
            if col_cor:
                fig_exp = px.box(
                    plot_df, x=col_x, y=col_y, color=col_cor,
                    color_discrete_sequence=P,
                    labels={col_cor: label_cor},
                )
            else:
                cmap = {c: P[i % len(P)] for i, c in enumerate(cats)}
                fig_exp = go.Figure()
                for i, cat in enumerate(cats):
                    vals = plot_df[plot_df[col_x] == cat][col_y]
                    fig_exp.add_trace(go.Box(
                        y=vals, name=str(cat),
                        marker_color=P[i % len(P)],
                        line=dict(color=P[i % len(P)]),
                        boxmean=True,
                    ))
            _lay(fig_exp, f"{label_y} por {label_x}", 420, grid_y=True)
            fig_exp.update_xaxes(tickangle=-20)
            fig_exp.update_yaxes(title=label_y)

        elif tipo == "Violino":
            plot_df = df[[col_x, col_y] + ([col_cor] if col_cor else [])].dropna()
            cats = sorted(plot_df[col_x].unique())
            fig_exp = go.Figure()
            for i, cat in enumerate(cats):
                vals = plot_df[plot_df[col_x] == cat][col_y]
                fig_exp.add_trace(go.Violin(
                    y=vals, name=str(cat),
                    box_visible=True, meanline_visible=True,
                    fillcolor=P[i % len(P)],
                    line_color=P[i % len(P)],
                    opacity=0.8,
                ))
            _lay(fig_exp, f"{label_y} por {label_x}", 420, grid_y=True)
            fig_exp.update_xaxes(tickangle=-20)
            fig_exp.update_yaxes(title=label_y)

        else:  # Histograma
            plot_df = df[[col_x] + ([col_cor] if col_cor else [])].dropna()
            if col_cor:
                fig_exp = px.histogram(
                    plot_df, x=col_x, color=col_cor,
                    color_discrete_sequence=P,
                    barmode="overlay",
                    opacity=0.75,
                    histnorm="percent",
                    labels={col_cor: label_cor},
                )
            else:
                fig_exp = go.Figure(go.Histogram(
                    x=plot_df[col_x], nbinsx=15,
                    marker_color=P[1],
                    marker_line_color="white", marker_line_width=1.5,
                    histnorm="percent",
                ))
            _lay(fig_exp, f"Distribuição de {label_x}", 380, grid_y=False)
            fig_exp.update_xaxes(title=label_x)
            fig_exp.update_yaxes(showticklabels=False, title="")

        st.plotly_chart(fig_exp, key="exp_chart", use_container_width=True)

        # ── Tabela resumo ─────────────────────────────────────────────────────
        with st.expander("Ver tabela de dados resumida"):
            cols_show = [col_x] + ([col_y] if col_y else []) + ([col_cor] if col_cor else [])
            cols_show = list(dict.fromkeys(cols_show))  # dedup mantendo ordem
            resumo = df[cols_show].dropna()
            if col_x in NUMS.values() and col_y and col_y in NUMS.values():
                st.dataframe(
                    resumo.describe().round(2),
                    use_container_width=True,
                )
            else:
                st.dataframe(resumo.head(50), use_container_width=True, hide_index=True)

    except Exception as e:
        st.warning(f"Não foi possível gerar o gráfico com esta combinação: {e}")