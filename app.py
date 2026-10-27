"""Interface web em etapas (wizard) do consultor de carreiras - Fase 4.

Execute com:  streamlit run app.py

Etapas, perguntas e escalas são lidas do regras_carreiras.json; o cálculo vem de
motor.py e o plano de estudo de roadmap.py.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from motor import calcular_ranking
from roadmap import gerar_roadmap
from validar_base import carregar_regras

st.set_page_config(page_title="Consultor de Carreiras em TI", page_icon="🧭", layout="wide")


@st.cache_data
def regras_base() -> dict:
    return carregar_regras()


# ---------------------------------------------------------------- estado

def iniciar_estado() -> None:
    st.session_state.setdefault("passo", 0)
    st.session_state.setdefault("perfil", {})
    st.session_state.setdefault("respostas", {})


def reiniciar() -> None:
    for chave in list(st.session_state.keys()):
        del st.session_state[chave]


def avancar() -> None:
    st.session_state.passo += 1


def voltar() -> None:
    st.session_state.passo -= 1


# ---------------------------------------------------------------- perguntas por etapa

def perguntas_da_etapa(etapa_id: str, regras: dict) -> list[dict]:
    """Lista de {id, texto} da etapa. Os ids de etapa são os definidos no JSON."""
    if etapa_id == "afinidades":
        return regras["perguntas_afinidade"]
    if etapa_id == "conhecimentos":
        return [{"id": cid, "texto": comp["nome"]} for cid, comp in regras["competencias"].items()]
    if etapa_id == "objetivos":
        return [t["pergunta_objetivo"] for t in regras["trilhas"]]
    return []


def etapa_completa(etapa_id: str, regras: dict) -> bool:
    if etapa_id == "perfil":
        return all(st.session_state.perfil.get(c["id"]) for c in regras["campos_perfil"] if c["obrigatorio"])
    if etapa_id == "conhecimentos":
        return True  # sem resposta, o motor assume "nunca estudei"
    return all(p["id"] in st.session_state.respostas for p in perguntas_da_etapa(etapa_id, regras))


# ---------------------------------------------------------------- etapas do wizard

def tela_perfil(regras: dict) -> None:
    for campo in regras["campos_perfil"]:
        atual = st.session_state.perfil.get(campo["id"])
        if campo["tipo"] == "texto":
            valor = st.text_input(campo["rotulo"], value=atual or "", key=f"perfil_{campo['id']}")
        else:
            indice = campo["opcoes"].index(atual) if atual in campo["opcoes"] else None
            valor = st.selectbox(campo["rotulo"], campo["opcoes"], index=indice,
                                 placeholder="Selecione...", key=f"perfil_{campo['id']}")
        st.session_state.perfil[campo["id"]] = valor.strip() if isinstance(valor, str) else valor


def tela_likert(etapa_id: str, regras: dict) -> None:
    escala = regras["escala"]
    nome_escala = {"afinidades": "afinidade", "conhecimentos": "conhecimento", "objetivos": "objetivo"}[etapa_id]
    rotulos = escala[nome_escala]
    st.caption("Escala: " + " · ".join(f"**{n}** = {texto}" for n, texto in rotulos.items()))

    respostas = st.session_state.respostas
    opcoes = list(range(escala["minimo"], escala["maximo"] + 1))
    for pergunta in perguntas_da_etapa(etapa_id, regras):
        # Em conhecimentos a resposta é opcional; a pré-seleção é "nunca estudei".
        padrao = respostas.get(pergunta["id"], opcoes[0] if etapa_id == "conhecimentos" else None)
        escolha = st.radio(
            pergunta["texto"], opcoes, horizontal=True, key=f"r_{pergunta['id']}",
            index=None if padrao is None else opcoes.index(padrao),
            help=rotulos[str(padrao)] if padrao else None,
        )
        if escolha is not None:
            respostas[pergunta["id"]] = escolha


# ---------------------------------------------------------------- resultados

def grafico_radar(ranking) -> go.Figure:
    nomes = [r.nome for r in ranking]
    valores = [r.compatibilidade for r in ranking]
    fig = go.Figure(go.Scatterpolar(
        r=valores + valores[:1], theta=nomes + nomes[:1], fill="toself", name="Compatibilidade (%)",
    ))
    fig.update_layout(polar={"radialaxis": {"range": [0, 100], "ticksuffix": "%"}},
                      showlegend=False, margin={"t": 30, "b": 30})
    return fig


def grafico_barras(ranking) -> go.Figure:
    ordem = list(reversed(ranking))
    fig = go.Figure(go.Bar(
        x=[r.compatibilidade for r in ordem], y=[r.nome for r in ordem], orientation="h",
        text=[f"{r.compatibilidade:.0f}%" for r in ordem], textposition="outside",
    ))
    fig.update_layout(xaxis={"range": [0, 105], "ticksuffix": "%"}, margin={"t": 30, "b": 30})
    return fig


def tabela_componentes(ranking) -> pd.DataFrame:
    def fmt(valor):
        return "—" if valor is None else f"{valor:.0f}%"
    return pd.DataFrame([{
        "Trilha": r.nome, "Compatibilidade": f"{r.compatibilidade:.0f}%",
        "Afinidade": fmt(r.afinidade), "Objetivo": fmt(r.objetivo), "Conhecimento": fmt(r.conhecimento),
    } for r in ranking])


def painel_trilha(resultado, regras: dict) -> None:
    rm = gerar_roadmap(resultado.id, st.session_state.respostas, regras)
    trilha = next(t for t in regras["trilhas"] if t["id"] == resultado.id)

    st.write(trilha["descricao"])
    col1, col2 = st.columns(2)
    col1.metric("Compatibilidade", f"{resultado.compatibilidade:.0f}%")
    col2.metric("Prontidão para Júnior", f"{rm.prontidao:.0f}%")

    if resultado.justificativas:
        st.markdown("**Por que esta trilha?**")
        for texto in resultado.justificativas:
            st.markdown(f"- {texto}")
    for texto in resultado.penalidades:
        st.warning(f"Ajuste aplicado: {texto}")

    st.subheader("Lacunas para o nível Júnior")
    if rm.lacunas:
        st.dataframe(pd.DataFrame([{
            "Competência": l.nome, "Nível atual": l.nivel_atual, "Necessário": l.nivel_necessario,
            "Prioridade": l.prioridade, "Como estudar": l.recurso,
        } for l in rm.lacunas]), hide_index=True, width="stretch")
    else:
        st.success("Você já atende a todas as competências Júnior desta trilha.")
    if rm.competencias_ok:
        st.caption("Já atendidas: " + "; ".join(rm.competencias_ok))

    st.subheader("Plano de ação")
    if rm.fase_1_comece_por:
        st.markdown("**1) Estude primeiro**")
        for l in rm.fase_1_comece_por:
            st.markdown(f"- {l.nome} — _{l.recurso}_")
    if rm.fase_2_em_seguida:
        st.markdown("**2) Em seguida**")
        for l in rm.fase_2_em_seguida:
            st.markdown(f"- {l.nome} — _{l.recurso}_")
    st.markdown("**Certificações**")
    for c in rm.certificacoes:
        st.markdown(f"- {c['nome']}" + (" (obrigatória)" if c["obrigatoria"] else ""))
    st.markdown("**Projetos para o portfólio no GitHub**")
    for p in rm.projetos:
        st.markdown(f"- {p}")
    with st.expander("Mais recursos gratuitos"):
        for r in rm.recursos_gratuitos:
            st.markdown(f"- {r}")


def tela_resultados(regras: dict) -> None:
    nome = st.session_state.perfil.get("nome", "")
    ranking = calcular_ranking(st.session_state.respostas, regras)
    top3 = ranking[:3]

    st.header(f"Resultado{', ' + nome if nome else ''}")
    st.caption(regras["metadados"]["observacao"])

    colunas = st.columns(3)
    for posicao, (coluna, r) in enumerate(zip(colunas, top3), start=1):
        coluna.metric(f"{posicao}º lugar", r.nome, f"{r.compatibilidade:.0f}%", delta_color="off")

    if any(r.empate_parcial for r in top3):
        st.info("Há empate parcial entre trilhas próximas no ranking (diferença menor que "
                f"{regras['metodologia']['tolerancia_empate_pontos_percentuais']} ponto percentual). "
                "Considere as duas como boas opções e compare os planos abaixo.")

    aba_radar, aba_barras, aba_tabela = st.tabs(["Radar", "Barras", "Detalhamento"])
    aba_radar.plotly_chart(grafico_radar(ranking), width="stretch")
    aba_barras.plotly_chart(grafico_barras(ranking), width="stretch")
    aba_tabela.dataframe(tabela_componentes(ranking), hide_index=True, width="stretch")

    st.header("Plano de ação por trilha")
    abas = st.tabs([f"{i}º {r.nome}" for i, r in enumerate(top3, start=1)])
    for aba, r in zip(abas, top3):
        with aba:
            painel_trilha(r, regras)

    st.button("Refazer o questionário", on_click=reiniciar)


# ---------------------------------------------------------------- fluxo principal

def main() -> None:
    regras = regras_base()
    iniciar_estado()
    etapas = regras["etapas"]
    total = len(etapas)
    passo = st.session_state.passo

    st.title("🧭 Consultor de Carreiras em TI")

    if passo >= total:
        tela_resultados(regras)
        return

    etapa = etapas[passo]
    st.progress(passo / total, text=f"Passo {passo + 1} de {total}: {etapa['titulo']}")
    st.subheader(etapa["titulo"])
    st.write(etapa["descricao"])

    if etapa["id"] == "perfil":
        tela_perfil(regras)
    else:
        tela_likert(etapa["id"], regras)

    completa = etapa_completa(etapa["id"], regras)
    if not completa:
        st.caption("Responda todas as perguntas para continuar.")

    col_voltar, _, col_avancar = st.columns([1, 4, 1])
    col_voltar.button("← Voltar", on_click=voltar, disabled=passo == 0)
    col_avancar.button("Ver resultado" if passo == total - 1 else "Avançar →",
                       on_click=avancar, disabled=not completa, type="primary")


main()
