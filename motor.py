"""Motor de inferência por pontuação ponderada (Etapa 2).

Lê a base de conhecimento (regras_carreiras.json) e calcula a compatibilidade
percentual do usuário com cada trilha. Nenhuma regra ou peso está no código:
tudo vem do JSON.

Respostas esperadas: dicionário {id_da_pergunta: nota}, com notas inteiras de 1 a 5.
  - "A01".."A12": afinidade
  - "O01".."O10": objetivo de carreira
  - "C01".."C24": nível de conhecimento atual na competência

Uso rápido:  python motor.py
"""
from __future__ import annotations

from dataclasses import dataclass, field

from validar_base import carregar_regras


@dataclass
class ResultadoTrilha:
    """Resultado do cálculo para uma trilha."""
    id: str
    nome: str
    compatibilidade: float            # 0-100, já com ajustes aplicados
    afinidade: float | None           # 0-100 (None = sem respostas)
    objetivo: float | None
    conhecimento: float | None
    penalidades: list[str] = field(default_factory=list)   # justificativas dos ajustes aplicados
    justificativas: list[str] = field(default_factory=list)
    empate_parcial: bool = False      # diferença menor que a tolerância para uma vizinha do ranking


def _normalizar(media: float, minimo: int, maximo: int) -> float:
    """Converte a média ponderada da escala (ex.: 1-5) para 0-100."""
    return (media - minimo) / (maximo - minimo) * 100


def _media_ponderada(itens: list[tuple[float, float]]) -> float | None:
    """Média de (nota, peso). Retorna None se não houver itens."""
    peso_total = sum(peso for _, peso in itens)
    if not itens or peso_total == 0:
        return None
    return sum(nota * peso for nota, peso in itens) / peso_total


def validar_respostas(respostas: dict[str, int], regras: dict) -> None:
    """Garante que todas as notas informadas estão dentro da escala da base."""
    minimo, maximo = regras["escala"]["minimo"], regras["escala"]["maximo"]
    for pergunta, nota in respostas.items():
        if isinstance(nota, bool) or not isinstance(nota, (int, float)) or not minimo <= nota <= maximo:
            raise ValueError(f"Resposta inválida em {pergunta}: {nota!r} (esperado {minimo} a {maximo})")


def _calcular_trilha(trilha: dict, respostas: dict[str, int], regras: dict) -> ResultadoTrilha:
    minimo, maximo = regras["escala"]["minimo"], regras["escala"]["maximo"]
    pesos_globais = regras["metodologia"]["pesos_globais"]
    textos = {p["id"]: p["texto"] for p in regras["perguntas_afinidade"]}

    # 1) Afinidade: cada resposta multiplica o peso da regra correspondente.
    itens = [(respostas[pid], peso) for pid, peso in trilha["pesos_afinidade"].items() if pid in respostas]
    media = _media_ponderada(itens)
    afinidade = None if media is None else _normalizar(media, minimo, maximo)

    # 2) Objetivo: uma pergunta direta por trilha.
    id_objetivo = trilha["pergunta_objetivo"]["id"]
    objetivo = _normalizar(respostas[id_objetivo], minimo, maximo) if id_objetivo in respostas else None

    # 3) Conhecimento: média das competências Júnior da trilha, ponderada pela importância.
    itens = [(respostas[c["id"]], c["importancia"]) for c in trilha["competencias_junior"] if c["id"] in respostas]
    media = _media_ponderada(itens)
    conhecimento = None if media is None else _normalizar(media, minimo, maximo)

    # Soma ponderada; se um componente não foi respondido, os pesos dos demais são renormalizados.
    componentes = {"afinidade": afinidade, "objetivo": objetivo, "conhecimento": conhecimento}
    presentes = {nome: valor for nome, valor in componentes.items() if valor is not None}
    soma_pesos = sum(pesos_globais[nome] for nome in presentes)
    compat = sum(valor * pesos_globais[nome] for nome, valor in presentes.items()) / soma_pesos if soma_pesos else 0.0

    # 4) Penalidades lógicas para perfis conflitantes (definidas e justificadas no JSON).
    penalidades = []
    for ajuste in trilha["ajustes"]:
        nota = respostas.get(ajuste["pergunta"])
        if nota is not None and nota <= ajuste["valor_maximo"]:
            compat *= ajuste["fator"]
            penalidades.append(ajuste["justificativa"])

    # Justificativas: perguntas de afinidade que mais contribuíram + objetivo.
    justificativas = []
    contribuicoes = sorted(
        ((respostas[pid] - minimo) * peso, pid) for pid, peso in trilha["pesos_afinidade"].items() if pid in respostas
    )[::-1]
    for pontos, pid in contribuicoes[:2]:
        if pontos > 0:
            justificativas.append(f"Afinidade ({respostas[pid]}/{maximo}): {textos[pid]}")
    if objetivo is not None and objetivo >= 75:
        justificativas.append("Você declarou interesse alto em atuar nesta área.")
    if conhecimento is not None and conhecimento >= 50:
        justificativas.append("Você já possui base relevante nas competências esperadas para Júnior.")

    return ResultadoTrilha(
        id=trilha["id"], nome=trilha["nome"], compatibilidade=round(compat, 1),
        afinidade=None if afinidade is None else round(afinidade, 1),
        objetivo=None if objetivo is None else round(objetivo, 1),
        conhecimento=None if conhecimento is None else round(conhecimento, 1),
        penalidades=penalidades, justificativas=justificativas,
    )


def calcular_ranking(respostas: dict[str, int], regras: dict | None = None) -> list[ResultadoTrilha]:
    """Calcula a compatibilidade com todas as trilhas, da maior para a menor.

    Desempate: objetivo declarado e, depois, afinidade. Trilhas separadas por menos
    que a tolerância da base são marcadas com `empate_parcial`.
    """
    regras = regras or carregar_regras()
    validar_respostas(respostas, regras)

    resultados = [_calcular_trilha(t, respostas, regras) for t in regras["trilhas"]]
    resultados.sort(key=lambda r: (-r.compatibilidade, -(r.objetivo or 0), -(r.afinidade or 0), r.nome))

    tolerancia = regras["metodologia"]["tolerancia_empate_pontos_percentuais"]
    for atual, proximo in zip(resultados, resultados[1:]):
        if atual.compatibilidade - proximo.compatibilidade < tolerancia:
            atual.empate_parcial = proximo.empate_parcial = True
    return resultados


def top_n(respostas: dict[str, int], n: int = 3, regras: dict | None = None) -> list[ResultadoTrilha]:
    """Atalho para o Top N (o enunciado pede Top 3)."""
    return calcular_ranking(respostas, regras)[:n]


if __name__ == "__main__":
    # Demonstração: perfil inclinado para infraestrutura e automação.
    exemplo = {
        "A01": 4, "A02": 2, "A03": 2, "A04": 1, "A05": 5, "A06": 3,
        "A07": 5, "A08": 2, "A09": 4, "A10": 1, "A11": 4, "A12": 2,
        "O06": 5, "O07": 4, "O01": 3,
        "C11": 4, "C14": 3, "C04": 4, "C01": 3,
    }
    for posicao, r in enumerate(top_n(exemplo), start=1):
        marca = " (empate parcial)" if r.empate_parcial else ""
        print(f"{posicao}º {r.nome} - {r.compatibilidade:.0f}%{marca}")
        for texto in r.justificativas + r.penalidades:
            print(f"     - {texto}")
