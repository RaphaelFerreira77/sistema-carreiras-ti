"""Fixtures compartilhadas pelos testes."""
import copy

import pytest

from validar_base import carregar_regras


@pytest.fixture(scope="session")
def regras_originais() -> dict:
    return carregar_regras()


@pytest.fixture
def regras(regras_originais) -> dict:
    """Cópia isolada: cada teste pode alterar a base sem afetar os outros."""
    return copy.deepcopy(regras_originais)


def afinidades(valor: int = 3, **excecoes: int) -> dict[str, int]:
    """Respostas A01..A12 com um valor padrão e exceções (ex.: afinidades(3, A01=5))."""
    respostas = {f"A{i:02d}": valor for i in range(1, 13)}
    respostas.update(excecoes)
    return respostas
