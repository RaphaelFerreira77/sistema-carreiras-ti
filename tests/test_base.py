"""Testes da base de conhecimento e do validador."""
import json

import pytest

from validar_base import carregar_regras, validar


def test_base_atual_e_valida(regras):
    assert validar(regras) == []


def test_base_tem_dez_trilhas(regras):
    assert len(regras["trilhas"]) == 10


def test_json_inexistente_gera_erro_claro(tmp_path):
    with pytest.raises(FileNotFoundError):
        carregar_regras(tmp_path / "nao_existe.json")


def test_json_malformado_gera_erro_claro(tmp_path):
    arquivo = tmp_path / "ruim.json"
    arquivo.write_text("{ isto nao e json", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON inválido"):
        carregar_regras(arquivo)


def test_json_valido_carrega(tmp_path):
    arquivo = tmp_path / "ok.json"
    arquivo.write_text(json.dumps({"a": 1}), encoding="utf-8")
    assert carregar_regras(arquivo) == {"a": 1}


def test_detecta_pergunta_de_afinidade_inexistente(regras):
    regras["trilhas"][0]["pesos_afinidade"]["A99"] = 1
    assert any("A99" in e for e in validar(regras))


def test_detecta_peso_invalido(regras):
    regras["trilhas"][0]["pesos_afinidade"]["A01"] = 0
    assert any("peso inválido" in e for e in validar(regras))


def test_detecta_competencia_inexistente(regras):
    regras["trilhas"][0]["competencias_junior"].append({"id": "C99", "importancia": 1})
    assert any("C99" in e for e in validar(regras))


def test_detecta_pesos_globais_que_nao_somam_um(regras):
    regras["metodologia"]["pesos_globais"]["afinidade"] = 0.9
    assert any("somar 1.0" in e for e in validar(regras))


def test_detecta_trilha_removida(regras):
    regras["trilhas"].pop()
    assert any("10 trilhas" in e for e in validar(regras))


def test_detecta_ajuste_sem_justificativa(regras):
    trilha = next(t for t in regras["trilhas"] if t["ajustes"])
    trilha["ajustes"][0]["justificativa"] = ""
    assert any("sem justificativa" in e for e in validar(regras))
