"""Valida a base de conhecimento (regras_carreiras.json) da Etapa 1.

Execute com o botão Run do PyCharm ou com:  python validar_base.py
"""
import json
import sys
from pathlib import Path

CAMINHO_JSON = Path(__file__).parent / "regras_carreiras.json"

TRILHAS_ESPERADAS = {
    "backend",
    "frontend",
    "ciencia_dados",
    "engenharia_dados",
    "ciberseguranca",
    "devops_sre",
    "arquitetura_cloud",
    "mobile",
    "qa",
    "product_management",
}


def carregar_regras(caminho: Path = CAMINHO_JSON) -> dict:
    """Carrega o JSON, com mensagens de erro claras."""
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
    try:
        with open(caminho, encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except json.JSONDecodeError as erro:
        raise ValueError(f"JSON inválido (linha {erro.lineno}, coluna {erro.colno}): {erro.msg}") from erro


def validar(regras: dict) -> list[str]:
    """Retorna a lista de problemas encontrados (lista vazia = base válida)."""
    erros = []

    for chave in ("escala", "metodologia", "etapas", "campos_perfil",
                  "perguntas_afinidade", "competencias", "trilhas"):
        if chave not in regras:
            erros.append(f"Chave obrigatória ausente: '{chave}'")
    if erros:
        return erros

    # Pesos globais
    pesos_globais = regras["metodologia"].get("pesos_globais", {})
    if set(pesos_globais) != {"afinidade", "objetivo", "conhecimento"}:
        erros.append("pesos_globais deve conter afinidade, objetivo e conhecimento")
    elif abs(sum(pesos_globais.values()) - 1.0) > 1e-9:
        erros.append(f"pesos_globais deve somar 1.0 (soma atual: {sum(pesos_globais.values())})")

    ids_afinidade = {p["id"] for p in regras["perguntas_afinidade"]}
    ids_competencias = set(regras["competencias"])

    # Dez trilhas
    ids_trilhas = [t.get("id") for t in regras["trilhas"]]
    if len(regras["trilhas"]) != 10:
        erros.append(f"Esperadas 10 trilhas, encontradas {len(regras['trilhas'])}")
    if len(ids_trilhas) != len(set(ids_trilhas)):
        erros.append("Há ids de trilha repetidos")
    faltando = TRILHAS_ESPERADAS - set(ids_trilhas)
    if faltando:
        erros.append(f"Trilhas ausentes: {sorted(faltando)}")

    ids_objetivo = []
    for trilha in regras["trilhas"]:
        tid = trilha.get("id", "?")
        for campo in ("nome", "descricao", "pergunta_objetivo", "pesos_afinidade",
                      "competencias_junior", "ajustes", "recursos_gratuitos",
                      "certificacoes", "projetos_portfolio"):
            if campo not in trilha:
                erros.append(f"[{tid}] campo ausente: '{campo}'")
        if "pesos_afinidade" not in trilha or "competencias_junior" not in trilha:
            continue

        ids_objetivo.append(trilha["pergunta_objetivo"]["id"])

        for pid, peso in trilha["pesos_afinidade"].items():
            if pid not in ids_afinidade:
                erros.append(f"[{tid}] pergunta de afinidade inexistente: {pid}")
            if not isinstance(peso, (int, float)) or peso <= 0:
                erros.append(f"[{tid}] peso inválido em {pid}: {peso}")

        for comp in trilha["competencias_junior"]:
            if comp["id"] not in ids_competencias:
                erros.append(f"[{tid}] competência inexistente: {comp['id']}")
            if comp.get("importancia", 0) <= 0:
                erros.append(f"[{tid}] importância inválida em {comp['id']}")

        for ajuste in trilha["ajustes"]:
            if ajuste.get("pergunta") not in ids_afinidade:
                erros.append(f"[{tid}] ajuste com pergunta inexistente")
            if not 0 < ajuste.get("fator", 0) <= 1:
                erros.append(f"[{tid}] fator de ajuste deve estar entre 0 e 1")
            if not ajuste.get("justificativa"):
                erros.append(f"[{tid}] ajuste sem justificativa")

    if len(ids_objetivo) != len(set(ids_objetivo)):
        erros.append("Há perguntas de objetivo repetidas")

    return erros


def main() -> int:
    try:
        regras = carregar_regras()
    except (FileNotFoundError, ValueError) as erro:
        print(f"ERRO: {erro}")
        return 1

    erros = validar(regras)
    if erros:
        print("Base de conhecimento INVÁLIDA:")
        for erro in erros:
            print(f"  - {erro}")
        return 1

    print("Base de conhecimento válida.")
    print(f"  Trilhas: {len(regras['trilhas'])}")
    print(f"  Perguntas de afinidade: {len(regras['perguntas_afinidade'])}")
    print(f"  Competências no catálogo: {len(regras['competencias'])}")
    print("  Resumo por trilha:")
    for trilha in regras["trilhas"]:
        print(f"    - {trilha['nome']}: {len(trilha['competencias_junior'])} competências Júnior")
    return 0


if __name__ == "__main__":
    sys.exit(main())
