"""Testes da análise de gaps e do roadmap."""
import pytest

from motor import top_n
from roadmap import analisar_gaps, formatar_roadmap, gerar_roadmap, roadmaps_top3


def competencias_da_trilha(regras, trilha_id):
    trilha = next(t for t in regras["trilhas"] if t["id"] == trilha_id)
    return [c["id"] for c in trilha["competencias_junior"]]


def test_sem_respostas_prontidao_zero_e_tudo_e_lacuna(regras):
    lacunas, ok, prontidao = analisar_gaps("qa", {}, regras)
    assert prontidao == 0
    assert ok == []
    assert len(lacunas) == len(competencias_da_trilha(regras, "qa"))
    assert all(not l.informado for l in lacunas)


def test_dominio_total_da_prontidao_100_e_sem_lacunas(regras):
    respostas = {cid: 5 for cid in competencias_da_trilha(regras, "mobile")}
    lacunas, ok, prontidao = analisar_gaps("mobile", respostas, regras)
    assert lacunas == []
    assert prontidao == 100
    assert len(ok) == len(respostas)


def test_nivel_no_minimo_conta_como_atendido(regras):
    minimo = regras["metodologia"]["nivel_dominio_minimo"]
    respostas = {cid: minimo for cid in competencias_da_trilha(regras, "qa")}
    lacunas, _, prontidao = analisar_gaps("qa", respostas, regras)
    assert lacunas == [] and prontidao == 100


def test_lacunas_e_atendidas_cobrem_todas_as_competencias(regras):
    ids = competencias_da_trilha(regras, "devops_sre")
    respostas = {ids[0]: 5, ids[1]: 2}
    lacunas, ok, _ = analisar_gaps("devops_sre", respostas, regras)
    assert len(lacunas) + len(ok) == len(ids)


def test_lacunas_ordenadas_por_prioridade_decrescente(regras):
    lacunas, _, _ = analisar_gaps("backend", {}, regras)
    prioridades = [l.prioridade for l in lacunas]
    assert prioridades == sorted(prioridades, reverse=True)


def test_competencia_respondida_e_marcada_como_informada(regras):
    lacunas, _, _ = analisar_gaps("qa", {"C21": 2}, regras)
    c21 = next(l for l in lacunas if l.id == "C21")
    assert c21.informado and c21.nivel_atual == 2


def test_prontidao_cresce_com_o_conhecimento(regras):
    ids = competencias_da_trilha(regras, "backend")
    menor = analisar_gaps("backend", {ids[0]: 1}, regras)[2]
    maior = analisar_gaps("backend", {ids[0]: 3}, regras)[2]
    assert maior > menor


def test_roadmap_divide_lacunas_em_duas_fases_sem_perder_nenhuma(regras):
    rm = gerar_roadmap("backend", {}, regras)
    assert len(rm.fase_1_comece_por) + len(rm.fase_2_em_seguida) == len(rm.lacunas)
    assert rm.fase_1_comece_por and rm.fase_1_comece_por[0] == rm.lacunas[0]


def test_roadmap_com_uma_unica_lacuna_coloca_na_fase_1(regras):
    ids = competencias_da_trilha(regras, "qa")
    respostas = {cid: 5 for cid in ids[1:]}
    rm = gerar_roadmap("qa", respostas, regras)
    assert len(rm.lacunas) == 1
    assert len(rm.fase_1_comece_por) == 1 and rm.fase_2_em_seguida == []


@pytest.mark.parametrize("nivel, quantidade", [(1, 1), (3, 2), (5, 3)])
def test_quantidade_de_projetos_acompanha_a_prontidao(nivel, quantidade, regras):
    # Em "mobile" o 1 deixa prontidão 0 (1 projeto); 5 deixa 100 (todos os 3 projetos).
    ids = competencias_da_trilha(regras, "mobile")
    if nivel == 3:
        respostas = {ids[0]: 3, ids[1]: 3, ids[2]: 3}
    else:
        respostas = {cid: nivel for cid in ids}
    rm = gerar_roadmap("mobile", respostas, regras)
    assert len(rm.projetos) == quantidade, rm.prontidao


def test_roadmap_sempre_traz_certificacoes_e_recursos(regras):
    for trilha in regras["trilhas"]:
        rm = gerar_roadmap(trilha["id"], {}, regras)
        assert rm.certificacoes and rm.recursos_gratuitos and rm.projetos


def test_trilha_inexistente_gera_erro(regras):
    with pytest.raises(ValueError, match="Trilha inexistente"):
        gerar_roadmap("nao_existe", {}, regras)


def test_roadmaps_top3_segue_a_ordem_do_ranking(regras):
    respostas = {f"A{i:02d}": 2 for i in range(1, 13)} | {"A05": 5, "A07": 5}
    esperado = [r.id for r in top_n(respostas, 3, regras)]
    assert [rm.trilha_id for rm in roadmaps_top3(respostas, regras)] == esperado


def test_texto_formatado_menciona_a_trilha_e_o_primeiro_estudo(regras):
    rm = gerar_roadmap("qa", {}, regras)
    texto = formatar_roadmap(rm)
    assert rm.trilha_nome in texto
    assert rm.fase_1_comece_por[0].nome in texto
