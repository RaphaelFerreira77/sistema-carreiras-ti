"""Testes do motor de inferência: cálculo, ranking, penalidades e entradas inválidas."""
import pytest

from conftest import afinidades
from motor import calcular_ranking, top_n, validar_respostas


def por_id(ranking, trilha_id):
    return next(r for r in ranking if r.id == trilha_id)


# ---------------------------------------------------------------- cálculo básico

def test_retorna_as_dez_trilhas_ordenadas(regras):
    ranking = calcular_ranking(afinidades(3, A07=5, A05=5), regras)
    notas = [r.compatibilidade for r in ranking]
    assert len(ranking) == 10
    assert notas == sorted(notas, reverse=True)


def test_top3_tem_tres_itens(regras):
    assert len(top_n(afinidades(3, A07=5), 3, regras)) == 3


def test_compatibilidade_fica_entre_0_e_100(regras):
    for valor in (1, 3, 5):
        for r in calcular_ranking(afinidades(valor), regras):
            assert 0 <= r.compatibilidade <= 100


def test_tudo_no_minimo_da_0_e_tudo_no_maximo_da_100(regras):
    assert all(r.compatibilidade == 0 for r in calcular_ranking(afinidades(1), regras))
    assert all(r.compatibilidade == 100 for r in calcular_ranking(afinidades(5), regras))


def test_perfil_de_infraestrutura_favorece_devops(regras):
    respostas = afinidades(2, A05=5, A07=5, A01=4, A09=4, A11=4)
    assert calcular_ranking(respostas, regras)[0].id == "devops_sre"


def test_perfil_visual_favorece_frontend(regras):
    respostas = afinidades(1, A04=5, A01=4, A09=4)
    assert calcular_ranking(respostas, regras)[0].id == "frontend"


def test_aumentar_afinidade_relevante_aumenta_compatibilidade(regras):
    antes = por_id(calcular_ranking(afinidades(3, A04=2), regras), "frontend")
    depois = por_id(calcular_ranking(afinidades(3, A04=5), regras), "frontend")
    assert depois.compatibilidade > antes.compatibilidade


def test_objetivo_declarado_aumenta_a_compatibilidade(regras):
    sem = por_id(calcular_ranking(afinidades(3), regras), "mobile")
    com = por_id(calcular_ranking({**afinidades(3), "O08": 5}, regras), "mobile")
    assert com.compatibilidade > sem.compatibilidade


def test_conhecimento_alto_aumenta_a_compatibilidade(regras):
    base = {**afinidades(3), "O06": 3}
    sem = por_id(calcular_ranking({**base, "C14": 1, "C15": 1}, regras), "devops_sre")
    com = por_id(calcular_ranking({**base, "C14": 5, "C15": 5}, regras), "devops_sre")
    assert com.conhecimento > sem.conhecimento
    assert com.compatibilidade > sem.compatibilidade


def test_resultado_e_deterministico(regras):
    respostas = afinidades(3)
    primeiro = [r.id for r in calcular_ranking(respostas, regras)]
    segundo = [r.id for r in calcular_ranking(respostas, regras)]
    assert primeiro == segundo


# ---------------------------------------------------------------- penalidades (perfis conflitantes)

def test_penalidade_aplicada_quando_afinidade_central_e_baixa(regras):
    com = por_id(calcular_ranking(afinidades(3, A02=2), regras), "ciencia_dados")
    assert len(com.penalidades) == 1


def test_penalidade_nao_aplicada_acima_do_limite(regras):
    sem = por_id(calcular_ranking(afinidades(3, A02=3), regras), "ciencia_dados")
    assert sem.penalidades == []


def test_penalidade_reduz_a_nota_pelo_fator_da_base(regras):
    trilha = next(t for t in regras["trilhas"] if t["id"] == "ciencia_dados")
    fator = trilha["ajustes"][0]["fator"]
    com = por_id(calcular_ranking(afinidades(3, A02=2), regras), "ciencia_dados")
    regras_sem_ajuste = {**regras, "trilhas": [{**t, "ajustes": []} for t in regras["trilhas"]]}
    sem = por_id(calcular_ranking(afinidades(3, A02=2), regras_sem_ajuste), "ciencia_dados")
    assert com.compatibilidade == pytest.approx(sem.compatibilidade * fator, abs=0.1)


# ---------------------------------------------------------------- entradas inválidas

@pytest.mark.parametrize("nota", [0, 6, -1, 99, "5", None, True])
def test_nota_invalida_gera_erro(nota, regras):
    with pytest.raises(ValueError, match="Resposta inválida"):
        validar_respostas({"A01": nota}, regras)


@pytest.mark.parametrize("nota", [1, 2, 3, 4, 5])
def test_notas_validas_sao_aceitas(nota, regras):
    validar_respostas({"A01": nota}, regras)


def test_sem_respostas_nao_quebra_e_zera(regras):
    ranking = calcular_ranking({}, regras)
    assert len(ranking) == 10
    assert all(r.compatibilidade == 0 for r in ranking)
    assert all(r.afinidade is None and r.objetivo is None and r.conhecimento is None for r in ranking)


def test_respostas_parciais_renormalizam_os_pesos(regras):
    """Só afinidade respondida: o resultado não é diluído pelos componentes ausentes."""
    ranking = calcular_ranking(afinidades(5), regras)
    assert ranking[0].compatibilidade == 100


def test_ids_desconhecidos_sao_ignorados(regras):
    base = calcular_ranking(afinidades(3), regras)
    com_lixo = calcular_ranking({**afinidades(3), "X99": 5}, regras)
    assert [(r.id, r.compatibilidade) for r in base] == [(r.id, r.compatibilidade) for r in com_lixo]
