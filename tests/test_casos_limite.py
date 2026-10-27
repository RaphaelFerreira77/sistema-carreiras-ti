"""Fase 5: perfis ambíguos, empates parciais e justificativas coerentes."""
from conftest import afinidades
from motor import calcular_ranking


def ids_top(ranking, n=3):
    return [r.id for r in ranking[:n]]


def test_perfil_dados_e_web_mantem_as_duas_areas_no_top3(regras):
    """Gosta tanto de dados quanto de desenvolvimento web/design."""
    respostas = afinidades(3, A01=5, A02=5, A03=5, A12=5, A04=5, A05=1)
    top3 = ids_top(calcular_ranking(respostas, regras))
    assert "frontend" in top3
    assert {"ciencia_dados", "engenharia_dados"} & set(top3)


def test_perfil_ambiguo_tem_justificativa_para_cada_trilha_do_top3(regras):
    respostas = afinidades(3, A01=5, A02=5, A03=5, A12=5, A04=5, A05=1)
    for r in calcular_ranking(respostas, regras)[:3]:
        assert r.justificativas, f"{r.nome} sem justificativa"
        assert all(isinstance(j, str) and j for j in r.justificativas)


def test_justificativa_cita_apenas_perguntas_com_nota_alta(regras):
    respostas = afinidades(1, A04=5)
    frontend = next(r for r in calcular_ranking(respostas, regras) if r.id == "frontend")
    assert any("design visual" in j for j in frontend.justificativas)
    assert not any("matemática" in j for j in frontend.justificativas)


def test_perfil_totalmente_neutro_marca_empate_parcial(regras):
    ranking = calcular_ranking(afinidades(3), regras)
    assert all(r.compatibilidade == 50 for r in ranking)
    assert all(r.empate_parcial for r in ranking)


def test_empate_e_desfeito_pelo_objetivo_declarado(regras):
    respostas = {**afinidades(3), "O08": 5}
    assert calcular_ranking(respostas, regras)[0].id == "mobile"


def test_ordem_em_empate_total_e_estavel(regras):
    """Sem nenhum desempate possível, a ordem alfabética garante resultado repetível."""
    nomes = [r.nome for r in calcular_ranking(afinidades(3), regras)]
    assert nomes == sorted(nomes)


def test_trilhas_distantes_nao_sao_marcadas_como_empate(regras):
    ranking = calcular_ranking(afinidades(2, A05=5, A07=5), regras)
    assert not ranking[0].empate_parcial


def test_empate_parcial_respeita_a_tolerancia_da_base(regras):
    """Com tolerância enorme, qualquer vizinha vira empate parcial."""
    regras["metodologia"]["tolerancia_empate_pontos_percentuais"] = 1000
    assert all(r.empate_parcial for r in calcular_ranking(afinidades(2, A05=5), regras))


def test_perfil_contraditorio_nao_gera_nota_fora_da_faixa(regras):
    respostas = afinidades(1, A04=5, A06=5, A10=5)
    for r in calcular_ranking(respostas, regras):
        assert 0 <= r.compatibilidade <= 100


def test_baixa_afinidade_em_area_central_gera_aviso_de_ajuste(regras):
    """Quem gosta de dados mas rejeita matemática recebe a penalidade explicada."""
    respostas = afinidades(3, A03=5, A02=1)
    ds = next(r for r in calcular_ranking(respostas, regras) if r.id == "ciencia_dados")
    assert ds.penalidades and "Estatística" in ds.penalidades[0]
