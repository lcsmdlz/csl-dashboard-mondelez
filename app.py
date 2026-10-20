
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io

st.set_page_config(page_title="CS&L — Mondelēz", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

P = "#4F2170"
PL = "#F3EDF7"
O = "#E18719"
OL = "#FFF3E0"
G = "#287819"
GL = "#E8F5E9"
B = "#2D6EAA"
R = "#A52323"
RL = "#FDEAEA"
BR = "#623E23"
TX = "#3D3D3D"
BW = "#FFFFFF"
BG = "#F8F6FA"
BL = "#E8E0F0"
SC = [P, O, G, B, R, BR]
MO, MF, MA, MC, MD = 95.0, 97.0, 93.0, 48.0, 30.0
MP = {1:"Jan",2:"Fev",3:"Mar",4:"Abr",5:"Mai",6:"Jun",7:"Jul",8:"Ago",9:"Set",10:"Out",11:"Nov",12:"Dez"}

def mpt(dt):
    t = pd.Timestamp(dt)
    return f"{MP[t.month]}/{t.year}"

st.markdown(f"""<style>
.stApp{{background:{BG};font-family:Calibri,Arial,sans-serif}}
.main .block-container{{padding-top:0.5rem;max-width:1400px}}
div[data-testid="stSidebar"]{{background:linear-gradient(180deg,{P} 0%,#3A1855 100%)}}
div[data-testid="stSidebar"] *{{color:white !important;font-size:1rem !important}}
div[data-testid="stSidebar"] label{{font-size:1.05rem !important;font-weight:600 !important}}
div[data-testid="stSidebar"] .stMultiSelect span{{font-size:0.95rem !important}}
.stTabs [data-baseweb="tab-list"]{{gap:4px;background:{BW};border-radius:12px;padding:4px}}
.stTabs [data-baseweb="tab"]{{border-radius:8px;color:{TX};padding:14px 20px;font-weight:700;font-size:1.15rem}}
.stTabs [aria-selected="true"]{{background-color:{P} !important;color:white !important}}
.mdlz-cc{{background:{BW};border-radius:12px;padding:18px;box-shadow:0 2px 12px rgba(79,33,112,0.06);border:1px solid {BL}}}
.mdlz-st{{color:{P};font-size:1.4rem;font-weight:700;margin:28px 0 14px 0;padding-bottom:8px;border-bottom:3px solid {P};display:inline-block}}
.mdlz-rs{{border-radius:12px;padding:20px 16px;text-align:center;min-height:140px;display:flex;flex-direction:column;justify-content:center;box-shadow:0 2px 10px rgba(0,0,0,0.06);border:1px solid {BL}}}
.mdlz-rs h4{{margin:0 0 10px 0;font-size:1.15rem;font-weight:700}}
.mdlz-rs p{{margin:0;font-size:1.05rem;line-height:1.6;color:{TX}}}
.stDataFrame{{font-size:1rem !important}}
.stDataFrame td,.stDataFrame th{{font-size:0.95rem !important;padding:8px 12px !important}}
.stSelectbox label,.stMultiSelect label{{font-size:1.05rem !important}}
</style>""", unsafe_allow_html=True)

FS = 18
FT = 22
FA = 17
FB = 18
FP = 16
FL = 16
CL = dict(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
          font=dict(family="Calibri,Arial,sans-serif", color=TX, size=FS),
          margin=dict(l=10, r=20, t=60, b=20))

def stl(t):
    return dict(text=f"<b>{t}</b>", font=dict(color=P, size=FT, family="Arial,sans-serif"))

def sem(v, m, inv=False):
    if inv:
        if v <= m: return G, "✅ Na meta"
        elif v <= m * 1.15: return O, "⚠️ Atenção"
        else: return R, "🔴 Fora da meta"
    else:
        if v >= m: return G, "✅ Na meta"
        elif v >= m * 0.97: return O, "⚠️ Atenção"
        else: return R, "🔴 Fora da meta"

def rkpi(col, nome, val, meta, suf, desc, inv=False):
    cor, status = sem(val, meta, inv)
    with col:
        st.markdown(f"""
        <div style="background:{BW};border-radius:12px;padding:24px 16px;text-align:center;border-top:5px solid {cor};box-shadow:0 2px 12px rgba(79,33,112,0.08);margin-bottom:8px">
            <span style="font-size:1.05rem;color:#666;text-transform:uppercase;letter-spacing:0.5px;font-weight:700;display:block">{nome}</span>
            <span style="font-size:2.8rem;font-weight:700;display:block;margin:12px 0 8px 0;line-height:1.2;color:{cor}">{val}{suf}</span>
            <span style="font-size:1.05rem;font-weight:700;display:block;color:{cor}">{status}</span>
            <span style="font-size:0.95rem;color:#888;display:block;margin-top:6px">{desc}</span>
        </div>""", unsafe_allow_html=True)

def rch(fig):
    st.markdown('<div class="mdlz-cc">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

def calc_kpis(d):
    tp = d["total_pedidos"].sum()
    if tp == 0: return 0,0,0,0,0,0
    vo = round(d["entregues_otif"].sum()/tp*100, 1)
    vf = round(d["entregues_fill"].sum()/tp*100, 1)
    va = round(d["osa_pct"].mean(), 1)
    vd = round(d["doh"].mean(), 1)
    vc = round(d["cycle_time_hrs"].mean(), 1)
    vs = round(vo*0.35 + vf*0.25 + va*0.25 + min(100, (MD/max(vd,1))*100)*0.15, 1)
    return vo, vf, va, vd, vc, vs

def make_hbar(x_vals, y_vals, title, meta=None, xrange=None, h=440):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=x_vals, y=y_vals, orientation="h", marker_color=P,
        text=[f"<b>{v}</b>" for v in x_vals], textposition="outside",
        textfont=dict(color=TX, size=FB)))
    if meta:
        fig.add_vline(x=meta, line_dash="dash", line_color=O, line_width=2,
            annotation_text=f"Meta {meta}%", annotation_font_color=O, annotation_font_size=FA)
    fig.update_layout(**CL, height=h, title=stl(title),
        xaxis=dict(range=xrange, gridcolor="#f0e8f5", tickfont=dict(size=FA)),
        yaxis=dict(tickfont=dict(color=TX, size=FA)))
    return fig

def make_vbar(x_vals, y_vals, title, meta_txt=None, yrange=None, h=440, labels=None):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=x_vals, y=y_vals, marker_color=P,
        text=[f"<b>{t}</b>" for t in (labels or y_vals)], textposition="outside",
        textfont=dict(color=TX, size=FB)))
    if meta_txt:
        try:
            mv = float(str(meta_txt).replace("≤","").replace("d","").replace("h","").replace("%",""))
            fig.add_hline(y=mv, line_dash="dash", line_color=O, line_width=2,
                annotation_text=f"Meta {meta_txt}", annotation_font_color=O, annotation_font_size=FA)
        except: pass
    fig.update_layout(**CL, height=h, title=stl(title), showlegend=False,
        xaxis=dict(tickfont=dict(size=FA)),
        yaxis=dict(range=yrange, gridcolor="#f0e8f5", tickfont=dict(size=FA)))
    return fig

def make_pie(labels, values, title, h=440):
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.5,
        marker=dict(colors=SC+["#8B6C5C","#5C7C8B"], line=dict(color=BW, width=2)),
        textfont=dict(color=TX, size=FP), textinfo="label+percent")])
    fig.update_layout(**CL, height=h, title=stl(title), legend=dict(font=dict(size=FL)))
    return fig

def make_lines(data, cols, names, title, h=440, yr=None):
    colors = [P, G, B, O, R]
    fig = go.Figure()
    for i, (col, name) in enumerate(zip(cols, names)):
        fig.add_trace(go.Scatter(x=data["lbl"], y=data[col], name=name,
            line=dict(color=colors[i % 5], width=3), mode="lines+markers",
            marker=dict(size=11), hovertemplate=f"<b>{name}</b><br>%{{x}}<br>%{{y:.1f}}%<extra></extra>"))
    fig.add_hline(y=MO, line_dash="dot", line_color=O, line_width=1.5,
        annotation_text=f"Meta {MO}%", annotation_font_color=O, annotation_font_size=FA)
    fig.update_layout(**CL, height=h, title=stl(title),
        xaxis=dict(tickfont=dict(size=FA)),
        yaxis=dict(range=yr, gridcolor="#f0e8f5", tickfont=dict(size=FA)),
        legend=dict(font=dict(size=FL), bgcolor="rgba(0,0,0,0)",
            orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5))
    return fig

@st.cache_data
def gen_data():
    np.random.seed(42)
    clis = ["Carrefour","GPA","Atacadão","Assaí","Grupo Mateus","Dia","Roldão","Sonda"]
    cats = ["Chocolates","Biscoitos","Gomas & Balas","Bebidas em Pó"]
    regs = ["Sudeste","Sul","Nordeste","Centro-Oeste","Norte"]
    meses = pd.date_range("2026-05-01", "2026-10-31", freq="MS")
    cp = {"Carrefour":(0.94,0.99,0.96,0.99,92,97), "GPA":(0.93,0.98,0.95,0.99,91,96),
          "Atacadão":(0.92,0.97,0.95,0.99,90,95), "Assaí":(0.93,0.98,0.96,0.99,91,96),
          "Grupo Mateus":(0.91,0.96,0.94,0.98,89,94), "Dia":(0.88,0.94,0.93,0.97,87,93),
          "Roldão":(0.92,0.97,0.95,0.99,90,95), "Sonda":(0.91,0.96,0.94,0.98,89,94)}
    rows = []
    for m in meses:
        for c in clis:
            p = cp[c]
            for cat in cats:
                for r in regs:
                    n = np.random.randint(20, 80)
                    rows.append({"mes":m, "cliente":c, "categoria":cat, "regiao":r,
                        "total_pedidos":n,
                        "entregues_otif":int(n * np.random.uniform(p[0], p[1])),
                        "entregues_fill":int(n * np.random.uniform(p[2], p[3])),
                        "osa_pct":round(np.random.uniform(p[4], p[5]), 1),
                        "cycle_time_hrs":round(np.random.uniform(24, 72), 1),
                        "doh":round(np.random.uniform(18, 42), 1),
                        "valor_brl":round(np.random.uniform(50000, 500000), 2)})
    dp = pd.DataFrame(rows)
    dp["otif_pct"] = round(dp["entregues_otif"]/dp["total_pedidos"]*100, 1)
    dp["fill_pct"] = round(dp["entregues_fill"]/dp["total_pedidos"]*100, 1)
    mots = ["Atraso na entrega","Produto divergente","Avaria no transporte","Falta parcial",
            "NF incorreta","Prazo de validade curto","Pedido duplicado","Temperatura inadequada"]
    recs = []
    for i in range(350):
        dt = datetime(2026,5,1) + timedelta(days=np.random.randint(0, 183))
        sr = np.random.choice(["Aberta","Em análise","Resolvida","Encerrada"], p=[0.12,0.18,0.45,0.25])
        recs.append({"id":f"REC-2026{i+1:04d}", "data":dt,
            "cliente":np.random.choice(clis), "categoria":np.random.choice(cats),
            "regiao":np.random.choice(regs),
            "motivo":np.random.choice(mots, p=[0.30,0.18,0.15,0.14,0.10,0.06,0.04,0.03]),
            "status":sr,
            "dias_res":np.random.randint(1, 15) if np.random.random() > 0.3 else None,
            "credito":round(np.random.uniform(500, 25000), 2) if sr in ["Resolvida","Encerrada"] else 0,
            "prioridade":np.random.choice(["Alta","Média","Baixa"], p=[0.25,0.50,0.25])})
    dr = pd.DataFrame(recs)
    dr["mes"] = pd.to_datetime(dr["data"]).dt.to_period("M").dt.to_timestamp()
    promos = []
    for pr in ["Black Friday","Páscoa","Volta às Aulas","Dia das Mães","São João","Natal Antecipado"]:
        for c in clis:
            for cat in cats:
                sr2 = np.random.uniform(0.55, 0.95)
                v = np.random.randint(1000, 10000)
                promos.append({"promocao":pr, "cliente":c, "categoria":cat,
                    "vol_plan":v, "vol_vend":int(v*sr2),
                    "st_pct":round(sr2*100, 1),
                    "receita":round(v*sr2*np.random.uniform(8, 35), 2)})
    dpr = pd.DataFrame(promos)
    return dp, dr, dpr, clis, cats, regs

def mk_tpl(cols, row):
    buf = io.BytesIO()
    pd.DataFrame([row], columns=cols).to_excel(buf, index=False)
    return buf.getvalue()

st.sidebar.markdown(f'<div style="text-align:center;padding:18px 0 22px 0;border-bottom:1px solid rgba(255,255,255,0.2);margin-bottom:18px"><div style="font-size:2.4rem;margin-bottom:6px">📊</div><h2 style="margin:0;font-size:1.4rem;font-weight:700">CS&L Dashboard</h2><p style="margin:6px 0 0 0;font-size:1rem;opacity:0.8">Mondelēz International</p></div>', unsafe_allow_html=True)

st.sidebar.markdown("#### 📂 Fonte de dados")
fonte = st.sidebar.radio("", ["Dados de demonstração","Carregar Excel"], label_visibility="collapsed")
up1 = up2 = up3 = None
if fonte == "Carregar Excel":
    up1 = st.sidebar.file_uploader("Pedidos", type=["xlsx"], key="u1")
    up2 = st.sidebar.file_uploader("Reclamações", type=["xlsx"], key="u2")
    up3 = st.sidebar.file_uploader("Promoções", type=["xlsx"], key="u3")
    st.sidebar.markdown("##### 📥 Templates")
    st.sidebar.download_button("Pedidos", mk_tpl(
        ["mes","cliente","categoria","regiao","total_pedidos","entregues_otif","entregues_fill","osa_pct","cycle_time_hrs","doh","valor_brl"],
        ["2026-10-01","Carrefour","Chocolates","Sudeste",100,96,98,94.2,36,28,150000]), "tpl_pedidos.xlsx")
    st.sidebar.download_button("Reclamações", mk_tpl(
        ["id","data","cliente","categoria","regiao","motivo","status","dias_res","credito","prioridade"],
        ["REC-20260001","2026-10-01","Carrefour","Chocolates","Sudeste","Atraso na entrega","Aberta",None,0,"Alta"]), "tpl_rec.xlsx")
    st.sidebar.download_button("Promoções", mk_tpl(
        ["promocao","cliente","categoria","vol_plan","vol_vend","st_pct","receita"],
        ["Páscoa","Carrefour","Chocolates",5000,4200,84.0,210000]), "tpl_promo.xlsx")

if fonte == "Carregar Excel" and up1 and up2 and up3:
    dp = pd.read_excel(up1)
    dp["mes"] = pd.to_datetime(dp["mes"])
    dp["otif_pct"] = round(dp["entregues_otif"]/dp["total_pedidos"]*100, 1)
    dp["fill_pct"] = round(dp["entregues_fill"]/dp["total_pedidos"]*100, 1)
    dr = pd.read_excel(up2)
    dr["data"] = pd.to_datetime(dr["data"])
    dr["mes"] = dr["data"].dt.to_period("M").dt.to_timestamp()
    dpr = pd.read_excel(up3)
    acli = sorted(dp["cliente"].unique().tolist())
    acat = sorted(dp["categoria"].unique().tolist())
    areg = sorted(dp["regiao"].unique().tolist())
    st.sidebar.success("✅ Dados carregados!")
else:
    dp, dr, dpr, acli, acat, areg = gen_data()

st.sidebar.markdown("---")
st.sidebar.markdown("#### 🔎 Filtros")
fp = st.sidebar.select_slider("📅 Período", options=sorted(dp["mes"].unique()),
    value=(dp["mes"].min(), dp["mes"].max()), format_func=lambda x: mpt(x))
fc = st.sidebar.multiselect("🏢 Clientes", acli, default=acli)
fcat = st.sidebar.multiselect("📦 Categorias", acat, default=acat)
fr = st.sidebar.multiselect("🗺️ Regiões", areg, default=areg)

df = dp[(dp["mes"]>=fp[0]) & (dp["mes"]<=fp[1]) & (dp["cliente"].isin(fc)) & (dp["categoria"].isin(fcat)) & (dp["regiao"].isin(fr))]
drf = dr[(dr["mes"]>=fp[0]) & (dr["mes"]<=fp[1]) & (dr["cliente"].isin(fc)) & (dr["categoria"].isin(fcat)) & (dr["regiao"].isin(fr))]
dpf = dpr[(dpr["cliente"].isin(fc)) & (dpr["categoria"].isin(fcat))]

if len(df) == 0:
    st.warning("⚠️ Nenhum dado encontrado para os filtros selecionados. Ajuste os filtros na barra lateral.")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.markdown(f'<div style="text-align:center;padding:14px;background:rgba(255,255,255,0.1);border-radius:10px"><p style="font-size:0.9rem;opacity:0.7;margin:0">Analista responsável</p><p style="font-size:1.1rem;font-weight:700;margin:6px 0 0 0">Lucas Rabello</p><p style="font-size:0.9rem;opacity:0.7;margin:2px 0 0 0">Customer Service & Logistics</p></div>', unsafe_allow_html=True)

st.markdown(f'<div style="background:{P};padding:24px 32px;border-radius:0 0 16px 16px;margin:-1rem -1rem 28px -1rem"><h1 style="color:white;margin:0;font-size:2.1rem;font-weight:700;font-family:Arial,sans-serif">Painel de Customer Service & Logistics</h1><p style="color:rgba(255,255,255,0.85);margin:8px 0 0 0;font-size:1.1rem">Mondelēz International — Brasil  •  {datetime.now().strftime("%d/%m/%Y")}</p></div>', unsafe_allow_html=True)

t1, t2, t3, t4, t5 = st.tabs(["📈 Visão Executiva","🔍 Análise Operacional","🔬 Causa Raiz","📋 Reclamações","👤 Carteira"])

with t1:
    vo, vf, va, vd, vc, vs = calc_kpis(df)
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    rkpi(c1,"Entrega no Prazo (OTIF)",vo,MO,"%",f"Meta {MO}%")
    rkpi(c2,"Taxa de Atendimento (Fill Rate)",vf,MF,"%",f"Meta {MF}%")
    rkpi(c3,"Disponib. Gôndola (OSA)",va,MA,"%",f"Meta {MA}%")
    rkpi(c4,"Dias de Estoque (DOH)",vd,MD," dias",f"Meta ≤{MD}d",True)
    rkpi(c5,"Tempo de Ciclo",vc,MC,"h",f"Meta ≤{MC}h",True)
    rkpi(c6,"Nível de Serviço",vs,93.0,"%","Composto ponderado")
    st.markdown("<br>", unsafe_allow_html=True)
    cl, cri = st.columns(2)
    with cl:
        d = df.groupby("cliente").agg(t=("total_pedidos","sum"), o=("entregues_otif","sum")).reset_index()
        d["p"] = round(d["o"]/d["t"]*100, 1)
        d = d.sort_values("p", ascending=True)
        rch(make_hbar(d["p"].tolist(), d["cliente"].tolist(), "Entrega no Prazo (OTIF) por Cliente", MO, [80,102]))
    with cri:
        d = df.groupby("mes").agg(t=("total_pedidos","sum"), o=("entregues_otif","sum"),
            fl=("entregues_fill","sum"), os=("osa_pct","mean")).reset_index()
        d["otif"] = round(d["o"]/d["t"]*100, 1)
        d["fill"] = round(d["fl"]/d["t"]*100, 1)
        d["osa"] = round(d["os"], 1)
        d["lbl"] = d["mes"].apply(mpt)
        rch(make_lines(d, ["otif","fill","osa"], ["Entrega no Prazo (OTIF)","Taxa de Atendimento","Disponib. Gôndola (OSA)"], "Evolução Mensal dos Indicadores", 440, [83,102]))
    st.markdown("<br>", unsafe_allow_html=True)
    b1, b2, b3 = st.columns(3)
    with b1:
        d = df.groupby("regiao").agg(t=("total_pedidos","sum"), o=("entregues_otif","sum"),
            fl=("entregues_fill","sum"), os=("osa_pct","mean")).reset_index()
        d["otif"] = round(d["o"]/d["t"]*100, 1)
        d["fill"] = round(d["fl"]/d["t"]*100, 1)
        d["osa"] = round(d["os"], 1)
        fig = go.Figure(data=[
            go.Bar(name="Entrega no Prazo", x=d["regiao"], y=d["otif"], marker_color=P, textfont=dict(size=FB)),
            go.Bar(name="Taxa Atendimento", x=d["regiao"], y=d["fill"], marker_color=G, textfont=dict(size=FB)),
            go.Bar(name="Gôndola", x=d["regiao"], y=d["osa"], marker_color=B, textfont=dict(size=FB))])
        fig.add_hline(y=MO, line_dash="dash", line_color=O, line_width=1.5)
        fig.update_layout(**CL, height=440, title=stl("Indicadores por Região"), barmode="group",
            xaxis=dict(tickfont=dict(size=14)),
            yaxis=dict(range=[85,102], gridcolor="#f0e8f5", tickfont=dict(size=FA)),
            legend=dict(font=dict(size=FL), bgcolor="rgba(0,0,0,0)", orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5))
        rch(fig)
    with b2:
        d = df.groupby("mes").agg(d2=("doh","mean")).reset_index()
        d["d2"] = round(d["d2"], 1)
        d["lbl"] = d["mes"].apply(mpt)
        rch(make_vbar(d["lbl"].tolist(), d["d2"].tolist(), "Dias de Estoque (DOH) Mensal", f"≤{MD}d", None, 440, [f"{v}d" for v in d["d2"]]))
    with b3:
        d = df.groupby("categoria").agg(v=("valor_brl","sum")).reset_index()
        rch(make_pie(d["categoria"].tolist(), d["v"].tolist(), "Volume por Categoria (R$)"))


with t2:
    st.markdown('<p class="mdlz-st">Análise Operacional</p>', unsafe_allow_html=True)
    o1, o2 = st.columns(2)
    with o1:
        d = df.groupby("mes").agg(o=("entregues_otif","sum"), t=("total_pedidos","sum")).reset_index()
        d["at"] = d["t"] - d["o"]
        d["lbl"] = d["mes"].apply(mpt)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=d["lbl"], y=d["o"], name="No prazo", marker_color=G))
        fig.add_trace(go.Bar(x=d["lbl"], y=d["at"], name="Com atraso", marker_color=O))
        fig.update_layout(**CL, height=440, title=stl("Pedidos por Status de Entrega"), barmode="stack",
            xaxis=dict(tickfont=dict(size=FA)), yaxis=dict(gridcolor="#f0e8f5", tickfont=dict(size=FA)),
            legend=dict(font=dict(size=FL), bgcolor="rgba(0,0,0,0)", orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5))
        rch(fig)
    with o2:
        d = drf.groupby("motivo").size().reset_index(name="q").sort_values("q", ascending=False)
        if len(d) > 0:
            rch(make_pie(d["motivo"].tolist(), d["q"].tolist(), "Motivos de Reclamações"))
        else:
            st.info("Nenhuma reclamação no período.")
    st.markdown('<p class="mdlz-st">Plano de Ação por Cliente</p>', unsafe_allow_html=True)
    da = df.groupby("cliente").agg(t=("total_pedidos","sum"), o=("entregues_otif","sum"),
        fl=("entregues_fill","sum"), os=("osa_pct","mean"), cy=("cycle_time_hrs","mean"), dh=("doh","mean")).reset_index()
    da["otif_pct"] = round(da["o"]/da["t"]*100, 1)
    da["fill_pct"] = round(da["fl"]/da["t"]*100, 1)
    da["osa_pct"] = round(da["os"], 1)
    da["cycle"] = round(da["cy"], 1)
    da["doh"] = round(da["dh"], 1)
    rab = drf[drf["status"].isin(["Aberta","Em análise"])].groupby("cliente").size().reset_index(name="ra")
    da = da.merge(rab, on="cliente", how="left").fillna(0)
    da["ra"] = da["ra"].astype(int)
    def calc_risco(row):
        s = 0
        if row["otif_pct"] < MO: s += 2
        if row["fill_pct"] < MF: s += 1
        if row["osa_pct"] < MA: s += 1
        if row["ra"] > 5: s += 2
        if row["doh"] > MD: s += 1
        return "🔴 Crítico" if s >= 4 else "🟡 Atenção" if s >= 2 else "🟢 Saudável"
    def calc_acao(row):
        a = []
        if row["otif_pct"] < MO: a.append("Reunião alinhamento logístico")
        if row["osa_pct"] < MA: a.append("Revisão reposição e estoque")
        if row["ra"] > 5: a.append("Plano de ação reclamações")
        if row["fill_pct"] < MF: a.append("Análise disponibilidade CD")
        if row["doh"] > MD: a.append("Revisar política estoque")
        return " | ".join(a) if a else "Manter acompanhamento"
    da["risco"] = da.apply(calc_risco, axis=1)
    da["acao"] = da.apply(calc_acao, axis=1)
    ds = da[["cliente","otif_pct","fill_pct","osa_pct","doh","cycle","ra","risco","acao"]].sort_values("otif_pct")
    ds.columns = ["Cliente","Entrega no Prazo (OTIF) %","Taxa Atend. (Fill) %","Gôndola (OSA) %","Estoque (dias)","Ciclo (h)","Recl. Abertas","Risco","Ação Sugerida"]
    st.dataframe(ds, use_container_width=True, hide_index=True, height=380)
    st.markdown('<p class="mdlz-st">Aproveitamento Promocional</p>', unsafe_allow_html=True)
    p1, p2 = st.columns(2)
    with p1:
        d = dpf.groupby("promocao").agg(p=("vol_plan","sum"), v=("vol_vend","sum")).reset_index()
        d["s"] = round(d["v"]/d["p"]*100, 1)
        d = d.sort_values("s", ascending=True)
        rch(make_hbar(d["s"].tolist(), d["promocao"].tolist(), "Aproveitamento por Promoção", 75, [50,100], 400))
    with p2:
        d = dpf.groupby("cliente").agg(p=("vol_plan","sum"), v=("vol_vend","sum")).reset_index()
        d["s"] = round(d["v"]/d["p"]*100, 1)
        d = d.sort_values("s", ascending=False)
        rch(make_vbar(d["cliente"].tolist(), d["s"].tolist(), "Aproveitamento por Cliente", "75%", [50,100], 400, [f"{v}%" for v in d["s"]]))

with t3:
    st.markdown('<p class="mdlz-st">Análise de Causa Raiz</p>', unsafe_allow_html=True)
    rca_sel = st.selectbox("Selecione o indicador", ["Entrega no Prazo (OTIF)","Taxa de Atendimento (Fill Rate)","Disponibilidade em Gôndola (OSA)"])
    km = {"Entrega no Prazo (OTIF)":("otif_pct",MO,"Entrega no Prazo (OTIF)"), "Taxa de Atendimento (Fill Rate)":("fill_pct",MF,"Taxa de Atendimento (Fill Rate)"), "Disponibilidade em Gôndola (OSA)":("osa_pct",MA,"Disponib. Gôndola (OSA)")}
    kc_col, ms2, ks = km[rca_sel]
    dr2 = df.groupby("regiao").agg(t=("total_pedidos","sum"), o=("entregues_otif","sum"),
        fl=("entregues_fill","sum"), os=("osa_pct","mean")).reset_index()
    dr2["otif_pct"] = round(dr2["o"]/dr2["t"]*100, 1)
    dr2["fill_pct"] = round(dr2["fl"]/dr2["t"]*100, 1)
    dr2["osa_pct"] = round(dr2["os"], 1)
    rp = dr2.loc[dr2[kc_col].idxmin()]
    tp2 = df["total_pedidos"].sum()
    if kc_col == "otif_pct": kv = round(df["entregues_otif"].sum()/tp2*100, 1)
    elif kc_col == "fill_pct": kv = round(df["entregues_fill"].sum()/tp2*100, 1)
    else: kv = round(df["osa_pct"].mean(), 1)
    dc = df[df["regiao"]==rp["regiao"]].groupby("cliente").agg(t=("total_pedidos","sum"), o=("entregues_otif","sum"),
        fl=("entregues_fill","sum"), os=("osa_pct","mean")).reset_index()
    dc["otif_pct"] = round(dc["o"]/dc["t"]*100, 1)
    dc["fill_pct"] = round(dc["fl"]/dc["t"]*100, 1)
    dc["osa_pct"] = round(dc["os"], 1)
    cpb = dc.loc[dc[kc_col].idxmin()]
    dm = drf[(drf["regiao"]==rp["regiao"]) & (drf["cliente"]==cpb["cliente"])].groupby("motivo").size().reset_index(name="q").sort_values("q", ascending=False)
    mp2 = dm.iloc[0]["motivo"] if len(dm) > 0 else "Sem dados"
    mpc = round(dm.iloc[0]["q"]/dm["q"].sum()*100, 0) if len(dm) > 0 else 0
    cau = {"Atraso na entrega":"Capacidade reduzida no CD por manutenção","Produto divergente":"Erro na separação do armazém",
        "Avaria no transporte":"Acondicionamento inadequado pela transportadora","Falta parcial":"Ruptura de estoque no CD regional",
        "NF incorreta":"Divergência entre SAP e conferência manual","Prazo de validade curto":"FIFO não respeitado",
        "Pedido duplicado":"Falha na integração EDI","Temperatura inadequada":"Problema na cadeia de frio"}
    act = {"Atraso na entrega":"Ativar CD alternativo, comunicar cliente, replanejar rotas","Produto divergente":"Auditoria no picking, dupla conferência",
        "Avaria no transporte":"Reunião com transportadora, revisar embalagem","Falta parcial":"Antecipar reposição, estoque de segurança",
        "NF incorreta":"Alinhar cadastro SAP, validação automática","Prazo de validade curto":"FIFO rigoroso, alerta de vencimento",
        "Pedido duplicado":"Revisar integração EDI, regra de bloqueio","Temperatura inadequada":"Sensores de temperatura, SLA cadeia fria"}
    st.markdown(f"""<div style="display:flex;gap:14px;margin:18px 0;flex-wrap:wrap">
    <div class="mdlz-rs" style="flex:1;min-width:180px;background:{RL};border-left:5px solid {R}"><h4 style="color:{R}">🚨 1. ALERTA</h4><p>{ks}: <b>{kv}%</b><br>Meta: {ms2}%</p></div>
    <div style="display:flex;align-items:center;color:{P};font-size:2rem">→</div>
    <div class="mdlz-rs" style="flex:1;min-width:180px;background:{OL};border-left:5px solid {O}"><h4 style="color:{O}">📍 2. ONDE?</h4><p>Pior região:<br><b>{rp['regiao']}</b> ({rp[kc_col]}%)</p></div>
    <div style="display:flex;align-items:center;color:{P};font-size:2rem">→</div>
    <div class="mdlz-rs" style="flex:1;min-width:180px;background:{PL};border-left:5px solid {P}"><h4 style="color:{P}">👤 3. QUEM?</h4><p>Cliente:<br><b>{cpb['cliente']}</b> ({cpb[kc_col]}%)</p></div></div>
    <div style="display:flex;gap:14px;margin:0 0 24px 0;flex-wrap:wrap">
    <div class="mdlz-rs" style="flex:1;min-width:180px;background:#E8F0FE;border-left:5px solid {B}"><h4 style="color:{B}">🔎 4. O QUÊ?</h4><p>Motivo principal:<br><b>{mp2}</b> ({mpc:.0f}%)</p></div>
    <div style="display:flex;align-items:center;color:{P};font-size:2rem">→</div>
    <div class="mdlz-rs" style="flex:1;min-width:180px;background:{OL};border-left:5px solid {BR}"><h4 style="color:{BR}">❓ 5. POR QUÊ?</h4><p>{cau.get(mp2,"Investigação necessária")}</p></div>
    <div style="display:flex;align-items:center;color:{P};font-size:2rem">→</div>
    <div class="mdlz-rs" style="flex:1;min-width:180px;background:{GL};border-left:5px solid {G}"><h4 style="color:{G}">✅ 6. AÇÃO</h4><p>{act.get(mp2,"Definir plano específico")}</p></div></div>""", unsafe_allow_html=True)
    r1, r2 = st.columns(2)
    with r1:
        rch(make_hbar(dc[kc_col].tolist(), dc["cliente"].tolist(), f"{ks} por Cliente — {rp['regiao']}", ms2, [80,102], 400))
    with r2:
        if len(dm) > 0:
            rch(make_pie(dm["motivo"].tolist(), dm["q"].tolist(), f"Reclamações — {cpb['cliente']} ({rp['regiao']})", 400))

with t4:
    st.markdown('<p class="mdlz-st">Gestão de Reclamações e Disputas</p>', unsafe_allow_html=True)
    tr = len(drf)
    ab = len(drf[drf["status"]=="Aberta"])
    ea = len(drf[drf["status"]=="Em análise"])
    tm = round(drf["dias_res"].dropna().mean(), 1) if len(drf) > 0 else 0
    tc = drf["credito"].sum()
    q1,q2,q3,q4 = st.columns(4)
    cor_tm, st_tm = sem(tm, 5, True)
    with q1:
        st.markdown(f'<div style="background:{BW};border-radius:12px;padding:24px 16px;text-align:center;border-top:5px solid {P};box-shadow:0 2px 12px rgba(79,33,112,0.08)"><span style="font-size:1.05rem;color:#666;text-transform:uppercase;font-weight:700;display:block">Total Reclamações</span><span style="font-size:2.8rem;font-weight:700;display:block;margin:12px 0;color:{P}">{tr}</span><span style="font-size:0.95rem;color:#888;display:block">No período</span></div>', unsafe_allow_html=True)
    with q2:
        st.markdown(f'<div style="background:{BW};border-radius:12px;padding:24px 16px;text-align:center;border-top:5px solid {R};box-shadow:0 2px 12px rgba(79,33,112,0.08)"><span style="font-size:1.05rem;color:#666;text-transform:uppercase;font-weight:700;display:block">Abertas + Em Análise</span><span style="font-size:2.8rem;font-weight:700;display:block;margin:12px 0;color:{R}">{ab+ea}</span><span style="font-size:1rem;font-weight:700;color:{R};display:block">{ab} abertas | {ea} em análise</span></div>', unsafe_allow_html=True)
    with q3:
        st.markdown(f'<div style="background:{BW};border-radius:12px;padding:24px 16px;text-align:center;border-top:5px solid {cor_tm};box-shadow:0 2px 12px rgba(79,33,112,0.08)"><span style="font-size:1.05rem;color:#666;text-transform:uppercase;font-weight:700;display:block">Tempo Médio Resolução</span><span style="font-size:2.8rem;font-weight:700;display:block;margin:12px 0;color:{cor_tm}">{tm} dias</span><span style="font-size:0.95rem;color:#888;display:block">Meta ≤ 5 dias</span></div>', unsafe_allow_html=True)
    with q4:
        st.markdown(f'<div style="background:{BW};border-radius:12px;padding:24px 16px;text-align:center;border-top:5px solid {O};box-shadow:0 2px 12px rgba(79,33,112,0.08)"><span style="font-size:1.05rem;color:#666;text-transform:uppercase;font-weight:700;display:block">Créditos Emitidos</span><span style="font-size:2.8rem;font-weight:700;display:block;margin:12px 0;color:{O}">R$ {tc:,.0f}</span><span style="font-size:0.95rem;color:#888;display:block">Notas de crédito</span></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    e1, e2 = st.columns(2)
    with e1:
        d = drf.groupby([drf["mes"],"status"]).size().reset_index(name="q")
        d["lbl"] = d["mes"].apply(mpt)
        sc2 = {"Aberta":R, "Em análise":O, "Resolvida":G, "Encerrada":B}
        fig = go.Figure()
        for s in ["Aberta","Em análise","Resolvida","Encerrada"]:
            ds2 = d[d["status"]==s]
            if len(ds2) > 0:
                fig.add_trace(go.Bar(x=ds2["lbl"], y=ds2["q"], name=s, marker_color=sc2.get(s, P)))
        fig.update_layout(**CL, height=440, title=stl("Reclamações por Mês e Status"), barmode="stack",
            xaxis=dict(tickfont=dict(size=FA)), yaxis=dict(gridcolor="#f0e8f5", tickfont=dict(size=FA)),
            legend=dict(font=dict(size=FL), bgcolor="rgba(0,0,0,0)", orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5))
        rch(fig)
    with e2:
        d = drf.groupby("cliente").size().reset_index(name="q").sort_values("q", ascending=True)
        if len(d) > 0:
            rch(make_hbar(d["q"].tolist(), d["cliente"].tolist(), "Reclamações por Cliente", None, None, 440))
    st.markdown('<p class="mdlz-st">Detalhamento de Reclamações</p>', unsafe_allow_html=True)
    f1,f2,f3 = st.columns(3)
    with f1: fst = st.multiselect("Status", ["Aberta","Em análise","Resolvida","Encerrada"], default=["Aberta","Em análise"])
    with f2: fpr = st.multiselect("Prioridade", ["Alta","Média","Baixa"], default=["Alta","Média"])
    mot_list = drf["motivo"].unique().tolist() if len(drf) > 0 else []
    with f3: fmt = st.multiselect("Motivo", mot_list, default=mot_list)
    dd = drf[(drf["status"].isin(fst)) & (drf["prioridade"].isin(fpr)) & (drf["motivo"].isin(fmt))].sort_values(["prioridade","data"], ascending=[True,False])
    if len(dd) > 0:
        dd2 = dd[["id","data","cliente","categoria","regiao","motivo","status","prioridade","dias_res","credito"]].copy()
        dd2.columns = ["ID","Data","Cliente","Categoria","Região","Motivo","Status","Prioridade","Dias Res.","Crédito R$"]
        dd2["Data"] = pd.to_datetime(dd2["Data"]).dt.strftime("%d/%m/%Y")
        st.dataframe(dd2, use_container_width=True, hide_index=True, height=400)
    else:
        st.info("Nenhuma reclamação encontrada com os filtros atuais.")

with t5:
    st.markdown('<p class="mdlz-st">Visão 360° do Cliente</p>', unsafe_allow_html=True)
    cli_list = sorted(df["cliente"].unique().tolist())
    if len(cli_list) == 0:
        st.warning("Nenhum cliente disponível. Ajuste os filtros.")
        st.stop()
    cli_sel = st.selectbox("Selecione o cliente", cli_list)
    dfc = df[df["cliente"]==cli_sel]
    drc = drf[drf["cliente"]==cli_sel]
    dpc = dpf[dpf["cliente"]==cli_sel]
    vo2, vf2, va2, vd2, vc2, vs2 = calc_kpis(dfc)
    rab2 = len(drc[drc["status"].isin(["Aberta","Em análise"])])
    sc_r = 0
    if vo2 < MO: sc_r += 2
    if vf2 < MF: sc_r += 1
    if va2 < MA: sc_r += 1
    if rab2 > 5: sc_r += 2
    if vd2 > MD: sc_r += 1
    rt = "🔴 Crítico" if sc_r >= 4 else "🟡 Atenção" if sc_r >= 2 else "🟢 Saudável"
    tpc = dfc["total_pedidos"].sum()
    st.markdown(f'<div style="background:{P};color:white;padding:20px 26px;border-radius:12px;margin-bottom:18px"><h2 style="margin:0;color:white;font-size:1.6rem">{cli_sel}</h2><p style="margin:6px 0 0 0;color:rgba(255,255,255,0.8);font-size:1.1rem">Risco: {rt}  •  {tpc:,} pedidos  •  {len(drc)} reclamações</p></div>', unsafe_allow_html=True)
    k1,k2,k3,k4,k5,k6 = st.columns(6)
    rkpi(k1,"Entrega no Prazo (OTIF)",vo2,MO,"%",f"Meta {MO}%")
    rkpi(k2,"Taxa Atend. (Fill Rate)",vf2,MF,"%",f"Meta {MF}%")
    rkpi(k3,"Gôndola (OSA)",va2,MA,"%",f"Meta {MA}%")
    rkpi(k4,"Estoque (DOH)",vd2,MD," dias",f"Meta ≤{MD}d",True)
    rkpi(k5,"Ciclo",vc2,MC,"h",f"Meta ≤{MC}h",True)
    rkpi(k6,"Recl. Abertas",rab2,5,"","Meta ≤ 5",True)
    st.markdown("<br>", unsafe_allow_html=True)
    v1, v2 = st.columns(2)
    with v1:
        d = dfc.groupby("mes").agg(t=("total_pedidos","sum"), o=("entregues_otif","sum"),
            fl=("entregues_fill","sum"), os=("osa_pct","mean")).reset_index()
        d["otif"] = round(d["o"]/d["t"]*100, 1)
        d["fill"] = round(d["fl"]/d["t"]*100, 1)
        d["osa"] = round(d["os"], 1)
        d["lbl"] = d["mes"].apply(mpt)
        rch(make_lines(d, ["otif","fill","osa"], ["Entrega no Prazo","Taxa Atend.","Gôndola"], f"Evolução — {cli_sel}", 440, [78,102]))
    with v2:
        d = drc.groupby("motivo").size().reset_index(name="q").sort_values("q", ascending=False)
        if len(d) > 0:
            rch(make_pie(d["motivo"].tolist(), d["q"].tolist(), f"Reclamações — {cli_sel}"))
        else:
            st.info("Nenhuma reclamação registrada.")
    st.markdown("<br>", unsafe_allow_html=True)
    w1, w2 = st.columns(2)
    with w1:
        d = dfc.groupby("mes").agg(d2=("doh","mean")).reset_index()
        d["d2"] = round(d["d2"], 1)
        d["lbl"] = d["mes"].apply(mpt)
        rch(make_vbar(d["lbl"].tolist(), d["d2"].tolist(), f"Dias de Estoque (DOH) — {cli_sel}", f"≤{MD}d", None, 420, [f"{v}d" for v in d["d2"]]))
    with w2:
        if len(dpc) > 0:
            d = dpc.groupby("promocao").agg(p=("vol_plan","sum"), v=("vol_vend","sum")).reset_index()
            d["s"] = round(d["v"]/d["p"]*100, 1)
            d = d.sort_values("s", ascending=True)
            rch(make_hbar(d["s"].tolist(), d["promocao"].tolist(), f"Aproveitamento Promocional — {cli_sel}", 75, [40,100], 420))
        else:
            st.info("Sem dados promocionais.")
    st.markdown(f'<p class="mdlz-st">Reclamações Recentes — {cli_sel}</p>', unsafe_allow_html=True)
    if len(drc) > 0:
        drc2 = drc[["id","data","categoria","regiao","motivo","status","prioridade","dias_res","credito"]].copy()
        drc2.columns = ["ID","Data","Categoria","Região","Motivo","Status","Prioridade","Dias Res.","Crédito R$"]
        drc2["Data"] = pd.to_datetime(drc2["Data"]).dt.strftime("%d/%m/%Y")
        drc2 = drc2.sort_values("Data", ascending=False)
        st.dataframe(drc2, use_container_width=True, hide_index=True, height=320)
    else:
        st.info("Nenhuma reclamação registrada para este cliente.")

st.markdown(f'<div style="text-align:center;padding:18px;margin-top:32px;border-top:3px solid {P};color:#888;font-size:0.95rem">CS&L Dashboard — Mondelēz International — Desenvolvido por Lucas Rabello</div>', unsafe_allow_html=True)

