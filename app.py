import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings, os, pathlib, json
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
    "#F2A7BB", "#8FC8E8", "#92D4AD", "#FFCB96", "#C7B6EC",
    "#FFE49C", "#A6D9F0", "#B7E4B2", "#F8C19A", "#E0C4EC",
    "#F7B7A5", "#9ED8C8",
]

# ──────────────────────────────────────────────────────────────────────────────
# LOGO
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
# DATA — Excel
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

    df["bmi_cat"]   = df["IMC"].apply(bmi_cat)
    df["age_group"] = df["Idade"].apply(age_grp)
    df["risco_grp"] = df["Risco de Internação 10 anos (%)"].apply(risco_grp)
    df["internado"] = df["Última Internação"].ne("Nenhuma").map(
        {True: "Já internado", False: "Sem internação"}
    )
    df["Sexo_full"] = df["Sexo"].map({"M": "Masculino", "F": "Feminino"})
    return df

# ──────────────────────────────────────────────────────────────────────────────
# DATA — Avatares
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data
def load_avatares():
    path = pathlib.Path(__file__).parent / "avatares_unificados.json"
    if not path.exists():
        return None, pd.DataFrame(), pd.DataFrame()

    content = path.read_text(encoding="utf-8").strip()
    if not content:
        return None, pd.DataFrame(), pd.DataFrame()
    try:
        raw = json.loads(content)
    except json.JSONDecodeError:
        return None, pd.DataFrame(), pd.DataFrame()
    pacientes = raw.get("pacientes", [])

    rows_presente = []
    for p in pacientes:
        dp = p.get("dados_paciente", {})
        row = {
            "cpf":                     str(dp.get("cpf", p["cpf"])),
            "nome":                    dp.get("nome", ""),
            "idade":                   dp.get("idade"),
            "expectativa_vida_oms":    dp.get("expectativa_vida_oms"),
            "expectativa_vida_riscos": dp.get("expectativa_vida_riscos"),
            "hbi_presente":           dp.get("health_burden_index"),
            "risco_internacao_10a":    dp.get("risco_internacao_10_anos"),
        }
        for s in p.get("presente", {}).get("sistemas", []):
            if not isinstance(s, dict):
                continue
            nome_s = (s.get("sistema") or s.get("nome") or "").replace("sistema ", "").title()
            if nome_s:
                row[f"pres_{nome_s}"] = s.get("nivel_comprometimento")
        rows_presente.append(row)

    df_pres = pd.DataFrame(rows_presente)

    rows_proj = []
    for p in pacientes:
        proj = p.get("projecoes")
        if not proj:
            continue
        cpf = str(p["cpf"])
        dp   = p.get("dados_paciente", {})
        # estrutura real: {cenario: {horizonte: valor}}
        ev   = proj.get("expectativa_vida") or {}
        ri   = proj.get("risco_internacao") or {}
        hbi = proj.get("health_burden_index") or {}
        # sistemas: dict {nome_sistema: {cenario: {horizonte: valor}}}
        sistemas_proj = proj.get("sistemas") or {}

        for horizonte in ["5_anos", "10_anos", "20_anos"]:
            for cenario in ["seguindo_recomendacoes", "nao_seguindo_recomendacoes"]:
                row = {
                    "cpf":               cpf,
                    "nome":              dp.get("nome", ""),
                    "idade":             dp.get("idade"),
                    "horizonte":         horizonte,
                    "cenario":           cenario,
                    "hbi_seguindo":     hbi.get("seguindo_recomendacoes") if isinstance(hbi, dict) else None,
                    "hbi_nao_seguindo": hbi.get("nao_seguindo_recomendacoes") if isinstance(hbi, dict) else None,
                    "expectativa_vida":  (ev.get(cenario) or {}).get(horizonte) if isinstance(ev, dict) else None,
                    "risco_internacao":  (ri.get(cenario) or {}).get(horizonte) if isinstance(ri, dict) else None,
                }
                if isinstance(sistemas_proj, dict):
                    for nome_sistema, nc in sistemas_proj.items():
                        nome_s = nome_sistema.replace("sistema ", "").title()
                        val = None
                        if isinstance(nc, dict):
                            val = (nc.get(cenario) or {}).get(horizonte)
                        row[f"proj_{nome_s}"] = val
                rows_proj.append(row)

    df_proj = pd.DataFrame(rows_proj) if rows_proj else pd.DataFrame()
    return pacientes, df_pres, df_proj


df = load()
pacientes_raw, df_avatares_pres, df_avatares_proj = load_avatares()

COMP_COLS   = [c for c in df.columns if "Comprometimento" in c]
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
        ("HBI médio", f"{df['DALY Estimado'].mean():.1f}"),
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
    ("200",                                            "Pacientes",           "na base"),
    (f"{pct_f:.0f}% / {pct_m:.0f}%",                 "F / M",               "distribuição"),
    (f"{df['Idade'].mean():.0f}",                      "Idade média",         "anos"),
    (f"{(df['IMC'] >= 25).mean()*100:.0f}%",          "Excesso de peso",     "IMC ≥ 25"),
    (f"{risco_m:.0f}%",                                "Risco de internação", "média 10 anos"),
    (f"{df['DALY Estimado'].mean():.1f}",              "HBI médio",          "índice de carga de saúde"),
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
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "👤 Demográfico",
    "🌿 Estilo de Vida",
    "🏥 Histórico Médico",
    "🫀 Comprometimentos",
    "🔗 Análises Cruzadas",
    "📈 Indicadores Clínicos",
    "🔬 Explorador",
    "🧬 Avatares",
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
        fig_age = go.Figure(go.Histogram(
            x=df["Idade"], nbinsx=10,
            marker_color=P[3], marker_line_color="white", marker_line_width=1.5,
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
        fig_sc = px.scatter(
            df, x="Idade", y="IMC", color="Sexo_full",
            color_discrete_map={"Masculino": P[1], "Feminino": P[0]},
            labels={"Sexo_full":"Sexo"}, opacity=0.7,
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
        st.plotly_chart(donut(pct("Suplementação"), "Suplementação", [P[2], P[1]]),
                        key="ev_supl", use_container_width=True)

    c4, c5 = st.columns(2)
    with c4:
        atv_order = ["Moderada (3-5x/semana)", "Leve (1-2x/semana)", "Sedentário"]
        atv_pct = pct("Atividade Física").reindex([a for a in atv_order if a in pct("Atividade Física").index])
        st.plotly_chart(donut(atv_pct, "Atividade Física", [P[2], P[5], P[0]]),
                        key="ev_atv", use_container_width=True)
    with c5:
        st.plotly_chart(donut(pct("Qualidade da Dieta"), "Qualidade da Dieta", [P[2], P[5], P[0]]),
                        key="ev_diet", use_container_width=True)

    sono_order = ["Bom (7-9h/noite)", "Regular (6-7h/noite)", "Ruim (<6h/noite)"]
    sono_pct = pct("Qualidade do Sono").reindex([s for s in sono_order if s in pct("Qualidade do Sono").index])
    st.plotly_chart(donut(sono_pct, "Qualidade do Sono", [P[2], P[5], P[0]], h=260),
                    key="ev_sono", use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — HISTÓRICO MÉDICO
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="sec-title">Histórico Médico</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Doenças crónicas, antecedentes e internações</div>', unsafe_allow_html=True)

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
        st.plotly_chart(donut(pct("internado"), "Histórico de Internação", [P[3], P[2]]),
                        key="hm_int", use_container_width=True)

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
        st.plotly_chart(donut(pct("risco_grp"), "Risco de Internação em 10 Anos", [P[2], P[5], P[3], P[0]]),
                        key="hm_risco", use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — COMPROMETIMENTOS
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="sec-title">Comprometimentos por Sistema Orgânico</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Scores de 0 a 100 por sistema (média dos pacientes)</div>', unsafe_allow_html=True)

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
            radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=9, color=TDARK), gridcolor=BORDER),
            angularaxis=dict(tickfont=dict(size=11, color=TDARK), gridcolor=BORDER),
        ),
    )
    st.plotly_chart(fig_radar, key="comp_radar", use_container_width=True)

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

    fig_box = go.Figure()
    for i, (col, label) in enumerate(zip(COMP_COLS, COMP_LABELS)):
        fig_box.add_trace(go.Box(
            y=df[col], name=label,
            marker_color=P[i % len(P)], line=dict(color=P[i % len(P)]),
            boxmean=True,
        ))
    _lay(fig_box, "Distribuição dos Scores de Comprometimento", 400, grid_y=True)
    fig_box.update_xaxes(tickangle=-30)
    fig_box.update_yaxes(title="Score (0–100)", range=[-5, 110])
    st.plotly_chart(fig_box, key="comp_box", use_container_width=True)

    means_m = df[df["Sexo"]=="M"][COMP_COLS].mean().round(1)
    means_f = df[df["Sexo"]=="F"][COMP_COLS].mean().round(1)
    fig_r2 = go.Figure()
    for vals, name, color in [(means_m, "Masculino", P[1]), (means_f, "Feminino", P[0])]:
        fig_r2.add_trace(go.Scatterpolar(
            r=list(vals.values) + [vals.values[0]],
            theta=COMP_LABELS + [COMP_LABELS[0]],
            fill="toself",
            fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:],16)},0.18)",
            line=dict(color=color, width=2), name=name,
        ))
    fig_r2.update_layout(
        **_LAYOUT, height=400,
        title=dict(text="Comprometimento por Sistema × Sexo", font=dict(size=13, color=TDARK), x=0),
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=9, color=TDARK), gridcolor=BORDER),
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
    with c1:
        d = df[["Sexo_full","bmi_cat"]].dropna()
        st.plotly_chart(stacked(d, "Sexo_full", "bmi_cat", "IMC por Sexo",
                                order=["Masculino","Feminino"]),
                        key="cr_bmi_sex", use_container_width=True)
    with c2:
        d = df[["Atividade Física","Qualidade do Sono"]].dropna()
        st.plotly_chart(stacked(d, "Atividade Física", "Qualidade do Sono",
                                "Qualidade do Sono × Atividade Física", h=320),
                        key="cr_atv_sono", use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        d = df[["Tabagismo","risco_grp"]].dropna()
        st.plotly_chart(stacked(d, "Tabagismo", "risco_grp",
                                "Risco de Internação × Tabagismo", h=300),
                        key="cr_tab_risco", use_container_width=True)
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
    with c5:
        d = df[["Qualidade da Dieta","bmi_cat"]].dropna()
        st.plotly_chart(stacked(d, "Qualidade da Dieta", "bmi_cat",
                                "IMC × Qualidade da Dieta", h=300),
                        key="cr_diet_bmi", use_container_width=True)
    with c6:
        fig_cv = px.scatter(
            df, x="Risco de Internação 10 anos (%)", y="Comprometimento Cardiovascular",
            color="Sexo_full", color_discrete_map={"Masculino": P[1], "Feminino": P[0]},
            opacity=0.65, labels={"Sexo_full":"Sexo"},
        )
        _lay(fig_cv, "Comprometimento Cardiovascular × Risco de Internação", 300, grid_y=True)
        st.plotly_chart(fig_cv, key="cr_cv_risco", use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — INDICADORES CLÍNICOS
# ══════════════════════════════════════════════════════════════════════════════
with tab6:
    st.markdown('<div class="sec-title">Indicadores Clínicos</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">HBI, expectativa de vida ajustada e risco de internação</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        fig_daly = go.Figure(go.Histogram(
            x=df["DALY Estimado"], nbinsx=12,
            marker_color=P[4], marker_line_color="white", marker_line_width=1.5,
        ))
        _lay(fig_daly, f"Health Burden Index (média {df['DALY Estimado'].mean():.1f})", 280)
        fig_daly.update_xaxes(title="HBI (anos)")
        fig_daly.update_yaxes(showticklabels=False)
        st.plotly_chart(fig_daly, key="ic_daly", use_container_width=True)
    with c2:
        fig_ev = go.Figure(go.Histogram(
            x=df["Expectativa de Vida Ajustada"], nbinsx=12,
            marker_color=P[2], marker_line_color="white", marker_line_width=1.5,
        ))
        _lay(fig_ev, f"Expectativa de Vida Ajustada (média {df['Expectativa de Vida Ajustada'].mean():.1f}a)", 280)
        fig_ev.update_xaxes(title="Anos")
        fig_ev.update_yaxes(showticklabels=False)
        st.plotly_chart(fig_ev, key="ic_ev", use_container_width=True)
    with c3:
        fig_ri = go.Figure(go.Histogram(
            x=df["Risco de Internação 10 anos (%)"], nbinsx=12,
            marker_color=P[3], marker_line_color="white", marker_line_width=1.5,
        ))
        _lay(fig_ri, f"Risco de Internação 10 anos (média {df['Risco de Internação 10 anos (%)'].mean():.0f}%)", 280)
        fig_ri.update_xaxes(title="%")
        fig_ri.update_yaxes(showticklabels=False)
        st.plotly_chart(fig_ri, key="ic_ri", use_container_width=True)

    fig_dy_age = px.scatter(
        df, x="Idade", y="DALY Estimado", color="Sexo_full",
        color_discrete_map={"Masculino": P[1], "Feminino": P[0]},
        size="Risco de Internação 10 anos (%)", size_max=18, opacity=0.7,
        labels={"Sexo_full":"Sexo","DALY Estimado":"HBI"},
        hover_data={"Doenças Crônicas": True, "IMC": True},
    )
    _lay(fig_dy_age, "HBI × Idade — tamanho = Risco de Internação", 360, grid_y=True)
    st.plotly_chart(fig_dy_age, key="ic_daly_age", use_container_width=True)

    c4, c5 = st.columns(2)
    with c4:
        fig_daly_sex = go.Figure()
        for i, sexo in enumerate(["Masculino","Feminino"]):
            vals = df[df["Sexo_full"]==sexo]["DALY Estimado"]
            fig_daly_sex.add_trace(go.Box(y=vals, name=sexo,
                                          marker_color=P[i], line=dict(color=P[i]), boxmean=True))
        _lay(fig_daly_sex, "HBI por Sexo", 300, grid_y=True)
        fig_daly_sex.update_yaxes(title="HBI")
        st.plotly_chart(fig_daly_sex, key="ic_daly_sex", use_container_width=True)
    with c5:
        fig_daly_atv = go.Figure()
        atv_order2 = ["Moderada (3-5x/semana)","Leve (1-2x/semana)","Sedentário"]
        for i, atv in enumerate(atv_order2):
            vals = df[df["Atividade Física"]==atv]["DALY Estimado"]
            fig_daly_atv.add_trace(go.Box(y=vals, name=atv.split(" (")[0],
                                          marker_color=P[i], line=dict(color=P[i]), boxmean=True))
        _lay(fig_daly_atv, "HBI × Atividade Física", 300, grid_y=True)
        fig_daly_atv.update_yaxes(title="HBI")
        st.plotly_chart(fig_daly_atv, key="ic_daly_atv", use_container_width=True)

    df_ev2 = df.copy()
    df_ev2["n_doencas_grp"] = df_ev2["Doenças Crônicas"].apply(
        lambda x: "0" if x=="Nenhuma doença crônica"
                  else ("1" if len(str(x).split("; "))==1
                  else ("2" if len(str(x).split("; "))==2 else "3+"))
    )
    fig_ev_nd = go.Figure()
    for i, nd in enumerate(["0","1","2","3+"]):
        vals = df_ev2[df_ev2["n_doencas_grp"]==nd]["Expectativa de Vida Ajustada"]
        if vals.empty: continue
        fig_ev_nd.add_trace(go.Box(y=vals, name=f"{nd} {'doença' if nd=='1' else 'doenças'}",
                                   marker_color=P[i], line=dict(color=P[i]), boxmean=True))
    _lay(fig_ev_nd, "Expectativa de Vida Ajustada × Nº de Doenças Crónicas", 320, grid_y=True)
    fig_ev_nd.update_yaxes(title="Anos")
    st.plotly_chart(fig_ev_nd, key="ic_ev_nd", use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 7 — EXPLORADOR
# ══════════════════════════════════════════════════════════════════════════════
with tab7:
    st.markdown('<div class="sec-title">Explorador de Variáveis</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Escolha as variáveis e o tipo de visualização para explorar relações</div>',
                unsafe_allow_html=True)

    CATS = {
        "Sexo": "Sexo_full", "Faixa Etária": "age_group", "IMC (categoria)": "bmi_cat",
        "Tabagismo": "Tabagismo", "Etilismo": "Etilismo", "Atividade Física": "Atividade Física",
        "Qualidade da Dieta": "Qualidade da Dieta", "Qualidade do Sono": "Qualidade do Sono",
        "Suplementação": "Suplementação", "Risco de Internação": "risco_grp",
        "Histórico de Internação": "internado",
    }
    NUMS = {
        "Idade": "Idade", "IMC": "IMC", "Health Burden Index": "DALY Estimado",
        "Expectativa de Vida Ajustada": "Expectativa de Vida Ajustada",
        "Risco de Internação 10 anos (%)": "Risco de Internação 10 anos (%)",
        "Compr. Cardiovascular": "Comprometimento Cardiovascular",
        "Compr. Endócrino": "Comprometimento Endócrino",
        "Compr. Respiratório": "Comprometimento Respiratório",
        "Compr. Digestivo": "Comprometimento Digestivo",
        "Compr. Urinário": "Comprometimento Urinário",
        "Compr. Osteoarticular": "Comprometimento Osteoarticular",
        "Compr. Muscular": "Comprometimento Muscular",
        "Compr. Neurológico": "Comprometimento Neurológico",
        "Compr. Psicológico": "Comprometimento Psicológico",
    }
    ALL_VARS = {**CATS, **NUMS}
    CAT_KEYS = list(CATS.keys()); NUM_KEYS = list(NUMS.keys())

    col_tipo, col_x, col_y, col_cor = st.columns([1.2, 1.5, 1.5, 1.5])
    with col_tipo:
        tipo = st.selectbox("Tipo de gráfico",
            ["Barras empilhadas","Barras agrupadas","Dispersão (scatter)","Boxplot","Histograma","Violino"],
            key="exp_tipo")

    if tipo in ["Barras empilhadas","Barras agrupadas"]:
        default_x, default_y, x_options, y_options = CAT_KEYS.index("Atividade Física"), CAT_KEYS.index("Qualidade do Sono"), CAT_KEYS, CAT_KEYS
        cor_options = ["(nenhuma)"] + CAT_KEYS
    elif tipo == "Dispersão (scatter)":
        default_x, default_y, x_options, y_options = NUM_KEYS.index("Idade"), NUM_KEYS.index("Health Burden Index"), NUM_KEYS, NUM_KEYS
        cor_options = ["(nenhuma)"] + CAT_KEYS
    elif tipo in ["Boxplot","Violino"]:
        default_x, default_y, x_options, y_options = CAT_KEYS.index("Atividade Física"), NUM_KEYS.index("Health Burden Index"), CAT_KEYS, NUM_KEYS
        cor_options = ["(nenhuma)"] + CAT_KEYS
    else:
        default_x, default_y, x_options, y_options = NUM_KEYS.index("Idade"), 0, NUM_KEYS, NUM_KEYS
        cor_options = ["(nenhuma)"] + CAT_KEYS

    with col_x:
        label_x = st.selectbox("Eixo X" if tipo != "Histograma" else "Variável", x_options,
                                index=min(default_x, len(x_options)-1), key="exp_x")
    with col_y:
        if tipo != "Histograma":
            label_y = st.selectbox("Eixo Y", y_options,
                                   index=min(default_y, len(y_options)-1), key="exp_y")
        else:
            label_y = None
            st.selectbox("Eixo Y", ["(automático)"], key="exp_y_dummy", disabled=True)
    with col_cor:
        if tipo != "Barras empilhadas":
            label_cor = st.selectbox("Colorir por", cor_options, index=0, key="exp_cor")
        else:
            label_cor = "(nenhuma)"
            st.selectbox("Colorir por", ["(automático)"], key="exp_cor_dummy", disabled=True)

    col_x_d = ALL_VARS.get(label_x, label_x)
    col_y_d = ALL_VARS.get(label_y, label_y) if label_y else None
    col_cor_d = ALL_VARS.get(label_cor) if label_cor and label_cor != "(nenhuma)" else None

    try:
        if tipo in ["Barras empilhadas","Barras agrupadas"]:
            grp = [col_x_d, col_y_d]
            ct = df[grp].dropna().groupby(grp).size().unstack(fill_value=0)
            if tipo == "Barras empilhadas":
                ct = ct.div(ct.sum(axis=1), axis=0).mul(100).round(1)
            fig_exp = go.Figure()
            for i, col in enumerate(ct.columns):
                vals = ct[col]
                fig_exp.add_trace(go.Bar(
                    name=str(col), x=ct.index.astype(str), y=vals.values,
                    marker_color=P[i % len(P)],
                    text=[f"<b>{v:.0f}{'%' if tipo=='Barras empilhadas' else ''}</b>"
                          if v >= (5 if tipo=="Barras empilhadas" else 1) else "" for v in vals],
                    textposition="inside", textfont=dict(size=11, color="#000"),
                ))
            _lay(fig_exp, f"{label_x} × {label_y}", 380)
            fig_exp.update_layout(
                barmode="stack" if tipo=="Barras empilhadas" else "group",
                xaxis_tickangle=-20,
                yaxis=dict(showgrid=False, showticklabels=tipo!="Barras empilhadas",
                           range=[0, 110] if tipo=="Barras empilhadas" else None),
            )
        elif tipo == "Dispersão (scatter)":
            plot_df = df[[col_x_d, col_y_d] + ([col_cor_d] if col_cor_d else [])].dropna()
            if col_cor_d:
                cmap = {c: P[i % len(P)] for i, c in enumerate(sorted(plot_df[col_cor_d].unique()))}
                fig_exp = px.scatter(plot_df, x=col_x_d, y=col_y_d, color=col_cor_d,
                                     color_discrete_map=cmap, opacity=0.7, trendline="ols")
            else:
                fig_exp = px.scatter(plot_df, x=col_x_d, y=col_y_d, opacity=0.7,
                                     trendline="ols", color_discrete_sequence=[P[1]])
            _lay(fig_exp, f"{label_x} × {label_y}", 420, grid_y=True)
            fig_exp.update_traces(selector=dict(mode="lines"), line=dict(dash="dot", width=1.5))
        elif tipo == "Boxplot":
            plot_df = df[[col_x_d, col_y_d] + ([col_cor_d] if col_cor_d else [])].dropna()
            cats = sorted(plot_df[col_x_d].unique())
            fig_exp = go.Figure()
            for i, cat in enumerate(cats):
                vals = plot_df[plot_df[col_x_d] == cat][col_y_d]
                fig_exp.add_trace(go.Box(y=vals, name=str(cat),
                                         marker_color=P[i % len(P)], line=dict(color=P[i % len(P)]), boxmean=True))
            _lay(fig_exp, f"{label_y} por {label_x}", 420, grid_y=True)
            fig_exp.update_xaxes(tickangle=-20); fig_exp.update_yaxes(title=label_y)
        elif tipo == "Violino":
            plot_df = df[[col_x_d, col_y_d] + ([col_cor_d] if col_cor_d else [])].dropna()
            cats = sorted(plot_df[col_x_d].unique())
            fig_exp = go.Figure()
            for i, cat in enumerate(cats):
                vals = plot_df[plot_df[col_x_d] == cat][col_y_d]
                fig_exp.add_trace(go.Violin(y=vals, name=str(cat), box_visible=True,
                                            meanline_visible=True, fillcolor=P[i % len(P)],
                                            line_color=P[i % len(P)], opacity=0.8))
            _lay(fig_exp, f"{label_y} por {label_x}", 420, grid_y=True)
            fig_exp.update_xaxes(tickangle=-20); fig_exp.update_yaxes(title=label_y)
        else:
            plot_df = df[[col_x_d] + ([col_cor_d] if col_cor_d else [])].dropna()
            if col_cor_d:
                fig_exp = px.histogram(plot_df, x=col_x_d, color=col_cor_d,
                                       color_discrete_sequence=P, barmode="overlay",
                                       opacity=0.75, histnorm="percent")
            else:
                fig_exp = go.Figure(go.Histogram(x=plot_df[col_x_d], nbinsx=15,
                                                  marker_color=P[1], marker_line_color="white",
                                                  marker_line_width=1.5, histnorm="percent"))
            _lay(fig_exp, f"Distribuição de {label_x}", 380)
            fig_exp.update_xaxes(title=label_x); fig_exp.update_yaxes(showticklabels=False)

        st.plotly_chart(fig_exp, key="exp_chart", use_container_width=True)

        with st.expander("Ver tabela de dados resumida"):
            cols_show = list(dict.fromkeys([col_x_d] + ([col_y_d] if col_y_d else []) + ([col_cor_d] if col_cor_d else [])))
            resumo = df[cols_show].dropna()
            if col_x_d in NUMS.values() and col_y_d and col_y_d in NUMS.values():
                st.dataframe(resumo.describe().round(2), use_container_width=True)
            else:
                st.dataframe(resumo.head(50), use_container_width=True, hide_index=True)
    except Exception as e:
        st.warning(f"Não foi possível gerar o gráfico com esta combinação: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 8 — AVATARES
# ══════════════════════════════════════════════════════════════════════════════
with tab8:
    if pacientes_raw is None:
        st.warning("Ficheiro `avatares_unificados.json` não encontrado. "
                   "Corre `python unificar_avatares.py` para o gerar.")
    else:
        df_pres = df_avatares_pres
        df_proj = df_avatares_proj
        SISTEMAS_COLS   = [c for c in df_pres.columns if c.startswith("pres_")]
        SISTEMAS_LABELS = [c.replace("pres_", "") for c in SISTEMAS_COLS]

        sub1, sub2, sub3 = st.tabs([
            "🔍 Ficha Individual",
            "📊 Análise Comparativa",
            "🔗 Correlações Clínicas",
        ])

        # ── SUBTAB 1 — FICHA INDIVIDUAL ──────────────────────────────────────
        with sub1:
            st.markdown('<div class="sec-title">Ficha do Paciente</div>', unsafe_allow_html=True)
            st.markdown('<div class="sec-sub">Selecione um paciente para ver o avatar completo</div>',
                        unsafe_allow_html=True)

            cpf_options = df_pres["cpf"].tolist()
            nome_map = {row["cpf"]: f"{row['cpf']} — {row['nome']} ({row['idade']} anos)"
                        for _, row in df_pres.iterrows()}

            cpf_sel = st.selectbox("Selecionar paciente por CPF", options=cpf_options,
                                   format_func=lambda x: nome_map.get(x, x), key="av_cpf_sel")

            paciente_raw = next((p for p in pacientes_raw if str(p["cpf"]) == str(cpf_sel)), None)
            row_pres_df  = df_pres[df_pres["cpf"] == cpf_sel]
            row_pres = row_pres_df.iloc[0] if not row_pres_df.empty else None

            if paciente_raw and row_pres is not None:
                dp = paciente_raw.get("dados_paciente", {})

                k1, k2, k3, k4, k5 = st.columns(5)
                for col, (val, label, sub) in zip([k1,k2,k3,k4,k5], [
                    (str(dp.get("idade","—")), "Idade", "anos"),
                    (str(dp.get("expectativa_vida_oms","—")), "Expectativa OMS", "anos"),
                    (str(dp.get("expectativa_vida_riscos","—")), "Exp. c/ riscos", "anos"),
                    (str(dp.get("health_burden_index","—")), "Health Burden Index presente", "anos ajustados"),
                    (f"{dp.get('risco_internacao_10_anos','—')}%", "Risco internação", "10 anos"),
                ]):
                    with col:
                        st.markdown(f"""
                        <div class="kpi-card">
                          <div class="kpi-value">{val}</div>
                          <div class="kpi-label">{label}</div>
                          <div class="kpi-sub">{sub}</div>
                        </div>""", unsafe_allow_html=True)

                st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)

                # História do paciente
                mensagem = paciente_raw.get("mensagem_original", "")
                if mensagem:
                    with st.expander("📋 História clínica do paciente", expanded=False):
                        linhas = mensagem.strip().split("\n")
                        for linha in linhas:
                            if ":" in linha:
                                label, _, valor = linha.partition(":")
                                st.markdown(
                                    f"<div style='display:flex;gap:12px;padding:5px 0;"
                                    f"border-bottom:1px solid {BORDER};font-size:13px;'>"
                                    f"<span style='color:{TMID};font-weight:500;min-width:200px;flex-shrink:0'>{label.strip()}</span>"
                                    f"<span style='color:{TDARK}'>{valor.strip()}</span>"
                                    f"</div>",
                                    unsafe_allow_html=True
                                )
                            elif linha.strip():
                                st.markdown(
                                    f"<div style='padding:5px 0;font-size:13px;color:{TDARK}'>{linha.strip()}</div>",
                                    unsafe_allow_html=True
                                )

                st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)


                # Radar presente
                s_vals   = [row_pres.get(c) for c in SISTEMAS_COLS]
                valid    = [(l, v) for l, v in zip(SISTEMAS_LABELS, s_vals) if v is not None and not pd.isna(v)]
                if valid:
                    labels_v, vals_v = zip(*valid)
                    labels_v, vals_v = list(labels_v), list(vals_v)
                    fig_rp = go.Figure(go.Scatterpolar(
                        r=vals_v + [vals_v[0]], theta=labels_v + [labels_v[0]],
                        fill="toself", fillcolor="rgba(184,131,90,0.2)",
                        line=dict(color=ACCENT, width=2), marker=dict(size=6, color=ACCENT),
                    ))
                    fig_rp.update_layout(
                        **_LAYOUT, height=420,
                        title=dict(text="Comprometimento por Sistema — Presente",
                                   font=dict(size=13, color=TDARK), x=0),
                        polar=dict(bgcolor="rgba(0,0,0,0)",
                                   radialaxis=dict(visible=True, range=[0,100],
                                                   tickfont=dict(size=9, color=TDARK), gridcolor=BORDER),
                                   angularaxis=dict(tickfont=dict(size=10, color=TDARK), gridcolor=BORDER)),
                    )
                    st.plotly_chart(fig_rp, key="av_radar_pac", use_container_width=True)

                # Projeções
                proj = paciente_raw.get("projecoes")
                if proj:
                    st.markdown('<div class="sec-title" style="margin-top:24px">Projeções Temporais</div>',
                                unsafe_allow_html=True)

                    ev_p = proj.get("expectativa_vida") or {}
                    ri_p = proj.get("risco_internacao") or {}
                    horizontes_labels = ["Presente","5 anos","10 anos","20 anos"]
                    horizontes_keys   = ["5_anos","10_anos","20_anos"]

                    def get_ev(cenario):
                        base = dp.get("expectativa_vida_riscos")
                        vals = [base] + [(ev_p.get(cenario) or {}).get(h) for h in horizontes_keys]
                        return vals

                    def get_ri(cenario):
                        base = dp.get("risco_internacao_10_anos")
                        vals = [base] + [(ri_p.get(cenario) or {}).get(h) for h in horizontes_keys]
                        return vals

                    c1, c2 = st.columns(2)
                    with c1:
                        fig_ev2 = go.Figure()
                        fig_ev2.add_trace(go.Scatter(
                            x=horizontes_labels, y=get_ev("seguindo_recomendacoes"),
                            name="Seguindo", line=dict(color=P[2], width=2.5), marker=dict(size=8, color=P[2]), mode="lines+markers"))
                        fig_ev2.add_trace(go.Scatter(
                            x=horizontes_labels, y=get_ev("nao_seguindo_recomendacoes"),
                            name="Sem mudanças", line=dict(color=P[0], width=2.5, dash="dash"), marker=dict(size=8, color=P[0]), mode="lines+markers"))
                        fig_ev2.update_layout(**_LAYOUT, height=300,
                            title=dict(text="Expectativa de Vida Ajustada", font=dict(size=13, color=TDARK), x=0),
                            yaxis=dict(showgrid=True, gridcolor=BORDER, title="Anos"))
                        st.plotly_chart(fig_ev2, key="av_ev", use_container_width=True)
                    with c2:
                        fig_ri2 = go.Figure()
                        fig_ri2.add_trace(go.Scatter(
                            x=horizontes_labels, y=get_ri("seguindo_recomendacoes"),
                            name="Seguindo", line=dict(color=P[2], width=2.5), marker=dict(size=8, color=P[2]), mode="lines+markers"))
                        fig_ri2.add_trace(go.Scatter(
                            x=horizontes_labels, y=get_ri("nao_seguindo_recomendacoes"),
                            name="Sem mudanças", line=dict(color=P[0], width=2.5, dash="dash"), marker=dict(size=8, color=P[0]), mode="lines+markers"))
                        fig_ri2.update_layout(**_LAYOUT, height=300,
                            title=dict(text="Risco de Internação (%)", font=dict(size=13, color=TDARK), x=0),
                            yaxis=dict(showgrid=True, gridcolor=BORDER, title="%", range=[0, 100]))
                        st.plotly_chart(fig_ri2, key="av_ri", use_container_width=True)

                    # Evolução por sistema
                    st.markdown('<div class="sec-title" style="margin-top:8px">Evolução por Sistema</div>',
                                unsafe_allow_html=True)
                    # sistemas é dict: {nome_sistema: {cenario: {horizonte: valor}}}
                    proj_sistemas = proj.get("sistemas") or {}
                    if isinstance(proj_sistemas, dict) and proj_sistemas:
                        sistema_sel = st.selectbox(
                            "Selecionar sistema",
                            list(proj_sistemas.keys()),
                            format_func=lambda x: x.replace("sistema ","").title(),
                            key="av_sistema_sel")

                        nc_pres_val = next(
                            (s.get("nivel_comprometimento")
                             for s in paciente_raw.get("presente",{}).get("sistemas",[])
                             if isinstance(s, dict) and s.get("sistema") == sistema_sel), None)

                        nc = proj_sistemas.get(sistema_sel) or {}
                        seg = [nc_pres_val] + [(nc.get("seguindo_recomendacoes") or {}).get(h) for h in horizontes_keys]
                        nao = [nc_pres_val] + [(nc.get("nao_seguindo_recomendacoes") or {}).get(h) for h in horizontes_keys]

                        fig_sis = go.Figure()
                        fig_sis.add_trace(go.Scatter(
                            x=horizontes_labels, y=seg, name="Seguindo",
                            line=dict(color=P[2], width=2.5), marker=dict(size=9, color=P[2]),
                            mode="lines+markers", fill="tozeroy", fillcolor="rgba(146,212,173,0.12)"))
                        fig_sis.add_trace(go.Scatter(
                            x=horizontes_labels, y=nao, name="Sem mudanças",
                            line=dict(color=P[0], width=2.5, dash="dash"), marker=dict(size=9, color=P[0]),
                            mode="lines+markers", fill="tozeroy", fillcolor="rgba(242,167,187,0.12)"))
                        fig_sis.update_layout(**_LAYOUT, height=320,
                            title=dict(text=f"Evolução — {sistema_sel.replace('sistema ','').title()}",
                                       font=dict(size=13, color=TDARK), x=0),
                            yaxis=dict(showgrid=True, gridcolor=BORDER,
                                       title="Comprometimento (0–100)", range=[0, 105]))
                        st.plotly_chart(fig_sis, key="av_sis_evol", use_container_width=True)

                        # Radar presente vs 20 anos
                        st.markdown('<div class="sec-title" style="margin-top:8px">Presente vs 20 Anos</div>',
                                    unsafe_allow_html=True)
                        cenario_radar = st.radio("Cenário", ["Seguindo recomendações","Sem mudanças"],
                                                 horizontal=True, key="av_cenario_radar")
                        cenario_key = "seguindo_recomendacoes" if "Seguindo" in cenario_radar else "nao_seguindo_recomendacoes"

                        labels_r, vals_pres_r, vals_20_r = [], [], []
                        for nome_sistema, nc in proj_sistemas.items():
                            nome_s = nome_sistema.replace("sistema ","").title()
                            val_20 = (nc.get(cenario_key) or {}).get("20_anos") if isinstance(nc, dict) else None
                            val_pre = next((ss.get("nivel_comprometimento")
                                           for ss in paciente_raw.get("presente",{}).get("sistemas",[])
                                           if isinstance(ss, dict) and ss.get("sistema") == nome_sistema), None)
                            if val_20 is not None and val_pre is not None:
                                labels_r.append(nome_s)
                                vals_pres_r.append(val_pre)
                                vals_20_r.append(val_20)


                        if labels_r:
                            fig_rc = go.Figure()
                            for vals, name, color in [(vals_pres_r, "Presente", P[1]),
                                                       (vals_20_r, f"20 anos ({cenario_radar})",
                                                        P[2] if "Seguindo" in cenario_radar else P[0])]:
                                r, g, b = int(color[1:3],16), int(color[3:5],16), int(color[5:],16)
                                fig_rc.add_trace(go.Scatterpolar(
                                    r=vals+[vals[0]], theta=labels_r+[labels_r[0]],
                                    fill="toself", fillcolor=f"rgba({r},{g},{b},0.2)",
                                    line=dict(color=color, width=2), name=name))
                            fig_rc.update_layout(
                                **_LAYOUT, height=420,
                                title=dict(text="Radar: Presente vs 20 Anos", font=dict(size=13, color=TDARK), x=0),
                                polar=dict(bgcolor="rgba(0,0,0,0)",
                                           radialaxis=dict(visible=True, range=[0,100],
                                                           tickfont=dict(size=9, color=TDARK), gridcolor=BORDER),
                                           angularaxis=dict(tickfont=dict(size=10, color=TDARK), gridcolor=BORDER)),
                            )
                            st.plotly_chart(fig_rc, key="av_radar_comp", use_container_width=True)
                else:
                    st.info("Sem dados de projeção para este paciente.")

        # ── SUBTAB 2 — ANÁLISE COMPARATIVA ───────────────────────────────────
        with sub2:
            st.markdown('<div class="sec-title">Análise Comparativa dos Avatares</div>', unsafe_allow_html=True)
            st.markdown('<div class="sec-sub">Distribuição dos comprometimentos na população</div>',
                        unsafe_allow_html=True)

            if not df_pres.empty and SISTEMAS_COLS:
                means_av = df_pres[SISTEMAS_COLS].mean().round(1)
                means_av.index = SISTEMAS_LABELS
                means_av_s = means_av.sort_values()

                fig_av_bar = go.Figure(go.Bar(
                    x=means_av_s.values, y=means_av_s.index, orientation="h",
                    marker_color=ACCENT,
                    text=[f"<b>{v:.1f}</b>" for v in means_av_s.values],
                    textposition="outside", textfont=dict(size=12, color="#000"),
                ))
                fig_av_bar.update_layout(**_LAYOUT, height=max(300, len(means_av_s)*50),
                    title=dict(text="Comprometimento Médio por Sistema — Avatares",
                               font=dict(size=13, color=TDARK), x=0))
                fig_av_bar.update_xaxes(showticklabels=False, range=[0, means_av_s.max()*1.2])
                st.plotly_chart(fig_av_bar, key="av_comp_bar", use_container_width=True)

                fig_av_box = go.Figure()
                for i, (col, label) in enumerate(zip(SISTEMAS_COLS, SISTEMAS_LABELS)):
                    fig_av_box.add_trace(go.Box(y=df_pres[col].dropna(), name=label,
                                                marker_color=P[i%len(P)], line=dict(color=P[i%len(P)]), boxmean=True))
                _lay(fig_av_box, "Distribuição dos Comprometimentos — Avatares", 420, grid_y=True)
                fig_av_box.update_xaxes(tickangle=-30)
                fig_av_box.update_yaxes(title="Score (0–100)", range=[-5, 110])
                st.plotly_chart(fig_av_box, key="av_box", use_container_width=True)

                if not df_proj.empty:
                    st.markdown('<div class="sec-title" style="margin-top:16px">Evolução Média das Projeções</div>',
                                unsafe_allow_html=True)
                    proj_cols   = [c for c in df_proj.columns if c.startswith("proj_")]
                    proj_labels = [c.replace("proj_","") for c in proj_cols]

                    if proj_labels:
                        sistema_comp = st.selectbox("Sistema a analisar", proj_labels, key="av_comp_sistema")
                        col_s = f"proj_{sistema_comp}"

                        if col_s in df_proj.columns:
                            df_h = df_proj.groupby(["horizonte","cenario"])[col_s].mean().reset_index()
                            hmap = {"5_anos":"5 anos","10_anos":"10 anos","20_anos":"20 anos"}
                            df_h["hl"] = df_h["horizonte"].map(hmap)
                            media_pres_col = f"pres_{sistema_comp}"
                            media_pres = df_pres[media_pres_col].mean() if media_pres_col in df_pres.columns else None

                            fig_pe = go.Figure()
                            for cenario, color, name in [
                                ("seguindo_recomendacoes",    P[2], "Seguindo"),
                                ("nao_seguindo_recomendacoes", P[0], "Sem mudanças"),
                            ]:
                                d_c = df_h[df_h["cenario"]==cenario].sort_values("horizonte")
                                x = (["Presente"] + d_c["hl"].tolist()) if media_pres is not None else d_c["hl"].tolist()
                                y = ([media_pres] + d_c[col_s].tolist()) if media_pres is not None else d_c[col_s].tolist()
                                fig_pe.add_trace(go.Scatter(x=x, y=y, name=name,
                                    line=dict(color=color, width=2.5), marker=dict(size=9, color=color), mode="lines+markers"))
                            fig_pe.update_layout(**_LAYOUT, height=340,
                                title=dict(text=f"Evolução Média — {sistema_comp} (população)",
                                           font=dict(size=13, color=TDARK), x=0),
                                yaxis=dict(showgrid=True, gridcolor=BORDER, title="Score médio", range=[0,105]))
                            st.plotly_chart(fig_pe, key="av_proj_evol", use_container_width=True)

        # ── SUBTAB 3 — CORRELAÇÕES CLÍNICAS ──────────────────────────────────
        with sub3:
            st.markdown('<div class="sec-title">Correlações Clínicas dos Avatares</div>', unsafe_allow_html=True)
            st.markdown('<div class="sec-sub">Impacto de comportamentos e doenças nos comprometimentos</div>',
                        unsafe_allow_html=True)

            if not df_pres.empty and SISTEMAS_COLS and "hbi_presente" in df_pres.columns:
                corrs = df_pres[SISTEMAS_COLS + ["hbi_presente"]].corr()["hbi_presente"].drop("hbi_presente")
                corrs.index = SISTEMAS_LABELS
                corrs_s = corrs.sort_values()

                fig_corr = go.Figure(go.Bar(
                    x=corrs_s.values, y=corrs_s.index, orientation="h",
                    marker_color=[P[0] if v > 0 else P[2] for v in corrs_s.values],
                    text=[f"<b>{v:.2f}</b>" for v in corrs_s.values],
                    textposition="outside", textfont=dict(size=12, color="#000"),
                ))
                fig_corr.update_layout(**_LAYOUT, height=max(280, len(corrs_s)*48),
                    title=dict(text="Correlação: Comprometimento × HBI Presente",
                               font=dict(size=13, color=TDARK), x=0),
                    xaxis=dict(range=[-1,1], showgrid=True, gridcolor=BORDER,
                               zeroline=True, zerolinecolor="#aaa", zerolinewidth=1.5))
                st.plotly_chart(fig_corr, key="av_corr_daly", use_container_width=True)

            # Scatter interactivo
            st.markdown("#### Explorador de Correlações")
            eixo_opts = (["hbi_presente","risco_internacao_10a","expectativa_vida_riscos"]
                         + SISTEMAS_COLS)

            c1, c2 = st.columns(2)
            with c1:
                eixo_x = st.selectbox("Eixo X", eixo_opts,
                    format_func=lambda c: c.replace("pres_","").replace("_"," ").title(),
                    key="av_corr_x")
            with c2:
                eixo_y = st.selectbox("Eixo Y", SISTEMAS_COLS + ["hbi_presente","risco_internacao_10a"],
                    format_func=lambda c: c.replace("pres_","").replace("_"," ").title(),
                    index=1, key="av_corr_y")

            if eixo_x in df_pres.columns and eixo_y in df_pres.columns:
                df_sc2 = df_pres[[eixo_x, eixo_y, "idade"]].dropna()
                fig_sc_av = px.scatter(df_sc2, x=eixo_x, y=eixo_y, size="idade", size_max=14,
                    opacity=0.65, color_discrete_sequence=[ACCENT], trendline="ols",
                    labels={eixo_x: eixo_x.replace("pres_","").replace("_"," ").title(),
                            eixo_y: eixo_y.replace("pres_","").replace("_"," ").title()})
                _lay(fig_sc_av, "Correlação entre variáveis (tamanho = idade)", 380, grid_y=True)
                fig_sc_av.update_traces(selector=dict(mode="lines"), line=dict(dash="dot", color="#aaa", width=1.5))
                st.plotly_chart(fig_sc_av, key="av_scatter_corr", use_container_width=True)

            # Ganho expectativa de vida
            if not df_proj.empty and "expectativa_vida" in df_proj.columns:
                st.markdown("#### Ganho de Expectativa de Vida — Seguindo vs Sem Mudanças (20 anos)")
                df_ev_20 = df_proj[df_proj["horizonte"]=="20_anos"]
                df_seg = df_ev_20[df_ev_20["cenario"]=="seguindo_recomendacoes"][["cpf","expectativa_vida"]].rename(columns={"expectativa_vida":"ev_seg"})
                df_nao = df_ev_20[df_ev_20["cenario"]=="nao_seguindo_recomendacoes"][["cpf","expectativa_vida"]].rename(columns={"expectativa_vida":"ev_nao"})
                df_ganho = df_seg.merge(df_nao, on="cpf")
                df_ganho["ganho"] = df_ganho["ev_seg"] - df_ganho["ev_nao"]
                df_ganho = df_ganho.dropna(subset=["ganho"])

                if not df_ganho.empty:
                    fig_ganho = go.Figure(go.Histogram(
                        x=df_ganho["ganho"], nbinsx=15,
                        marker_color=P[2], marker_line_color="white", marker_line_width=1.5))
                    fig_ganho.update_layout(**_LAYOUT, height=300,
                        title=dict(
                            text=f"Ganho médio em expectativa de vida: +{df_ganho['ganho'].mean():.1f} anos",
                            font=dict(size=13, color=TDARK), x=0),
                        xaxis=dict(title="Anos ganhos"), yaxis=dict(showticklabels=False))
                    st.plotly_chart(fig_ganho, key="av_ganho_ev", use_container_width=True)