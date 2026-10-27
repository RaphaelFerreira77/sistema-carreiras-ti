"""Teste de fumaça da interface Streamlit (sem abrir navegador)."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

CAMINHO_APP = str(Path(__file__).resolve().parent.parent / "app.py")


def novo_app() -> AppTest:
    return AppTest.from_file(CAMINHO_APP, default_timeout=30).run()


def botao(at: AppTest, trecho: str):
    return next(b for b in at.button if trecho in b.label)


def test_primeira_tela_abre_sem_erro_e_bloqueia_avanco():
    at = novo_app()
    assert not at.exception
    assert botao(at, "Avançar").disabled


def test_avanco_liberado_apos_preencher_o_perfil():
    at = novo_app()
    at.text_input[0].set_value("Ana")
    for seletor in at.selectbox:
        seletor.select(seletor.options[0])
    at.run()
    assert not botao(at, "Avançar").disabled


def test_fluxo_completo_chega_aos_resultados():
    at = novo_app()
    at.text_input[0].set_value("Ana")
    for seletor in at.selectbox:
        seletor.select(seletor.options[0])
    at.run()
    botao(at, "Avançar").click().run()                    # afinidades
    for radio in at.radio:
        radio.set_value(4)
    at.run()
    botao(at, "Avançar").click().run()                    # conhecimentos (opcional)
    botao(at, "Avançar").click().run()                    # objetivos
    for radio in at.radio:
        radio.set_value(3)
    at.run()
    botao(at, "resultado").click().run()
    assert not at.exception
    assert len(at.metric) >= 3


def test_resultados_renderizam_com_respostas_parciais():
    at = novo_app()
    at.session_state.passo = 4
    at.session_state.perfil = {"nome": "Ana"}
    at.session_state.respostas = {"A01": 5, "A02": 5, "A03": 5, "O03": 5}
    at.run()
    assert not at.exception
