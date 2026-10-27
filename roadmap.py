"""Análise de lacunas (skill gap) e geração de roadmap (Fase 3).

Cruza a trilha escolhida com o conhecimento atual do usuário e indica o que falta
para o nível Júnior. Competências, importâncias, certificações e projetos vêm do
regras_carreiras.json; o nível mínimo vem de metodologia.nivel_dominio_minimo.

Uso rápido:  python roadmap.py
"""
from __future__ import annotations

from dataclasses import dataclass, field

from motor import top_n
from validar_base import carregar_regras


@dataclass
class Lacuna:
    """Competência Júnior em que o usuário ainda está abaixo do nível mínimo."""
    id: str
    nome: str
    nivel_atual: int
    nivel_necessario: int
    importancia: int
    prioridade: int          # importância x distância até o nível mínimo
    informado: bool          # False = usuário não respondeu (assumido nível 1)
    recurso: str


@dataclass
class Roadmap:
    trilha_id: str
    trilha_nome: str
    prontidao: float                      # 0-100: quão perto do nível Júnior
    lacunas: list[Lacuna] = field(default_factory=list)
    competencias_ok: list[str] = field(default_factory=list)
    fase_1_comece_por: list[Lacuna] = field(default_factory=list)
    fase_2_em_seguida: list[Lacuna] = field(default_factory=list)
    certificacoes: list[dict] = field(default_factory=list)
    projetos: list[str] = field(default_factory=list)
    recursos_gratuitos: list[str] = field(default_factory=list)


def _buscar_trilha(regras: dict, trilha_id: str) -> dict:
    for trilha in regras["trilhas"]:
        if trilha["id"] == trilha_id:
            return trilha
    raise ValueError(f"Trilha inexistente: {trilha_id}")


def analisar_gaps(trilha_id: str, respostas: dict[str, int], regras: dict | None = None) -> tuple[list[Lacuna], list[str], float]:
    """Retorna (lacunas ordenadas por prioridade, competências já atendidas, prontidão 0-100)."""
    regras = regras or carregar_regras()
    trilha = _buscar_trilha(regras, trilha_id)
    minimo = regras["escala"]["minimo"]
    dominio = regras["metodologia"]["nivel_dominio_minimo"]

    lacunas, atendidas = [], []
    pontos = total = 0.0
    for comp in trilha["competencias_junior"]:
        info = regras["competencias"][comp["id"]]
        informado = comp["id"] in respostas
        nivel = respostas.get(comp["id"], minimo)

        pontos += comp["importancia"] * (min(nivel, dominio) - minimo)
        total += comp["importancia"] * (dominio - minimo)

        if nivel >= dominio:
            atendidas.append(info["nome"])
        else:
            lacunas.append(Lacuna(
                id=comp["id"], nome=info["nome"], nivel_atual=nivel, nivel_necessario=dominio,
                importancia=comp["importancia"], prioridade=comp["importancia"] * (dominio - nivel),
                informado=informado, recurso=info["recurso"],
            ))

    # Mais prioritária primeiro; empate resolvido pela maior importância e depois pelo id.
    lacunas.sort(key=lambda l: (-l.prioridade, -l.importancia, l.id))
    prontidao = round(pontos / total * 100, 1) if total else 100.0
    return lacunas, atendidas, prontidao


def gerar_roadmap(trilha_id: str, respostas: dict[str, int], regras: dict | None = None) -> Roadmap:
    """Monta o plano: o que estudar primeiro, certificações e projetos de portfólio."""
    regras = regras or carregar_regras()
    trilha = _buscar_trilha(regras, trilha_id)
    lacunas, atendidas, prontidao = analisar_gaps(trilha_id, respostas, regras)

    # Fase 1: as lacunas de maior prioridade (metade, no mínimo 1); Fase 2: o restante.
    corte = (len(lacunas) + 1) // 2
    # Quanto menor a prontidão, menos projetos de uma vez: começa simples e evolui.
    qtd_projetos = 1 if prontidao < 40 else 2 if prontidao < 70 else len(trilha["projetos_portfolio"])

    return Roadmap(
        trilha_id=trilha["id"], trilha_nome=trilha["nome"], prontidao=prontidao,
        lacunas=lacunas, competencias_ok=atendidas,
        fase_1_comece_por=lacunas[:corte], fase_2_em_seguida=lacunas[corte:],
        certificacoes=trilha["certificacoes"],
        projetos=trilha["projetos_portfolio"][:qtd_projetos],
        recursos_gratuitos=trilha["recursos_gratuitos"],
    )


def roadmaps_top3(respostas: dict[str, int], regras: dict | None = None) -> list[Roadmap]:
    """Atalho: roadmap de cada uma das 3 trilhas mais compatíveis."""
    regras = regras or carregar_regras()
    return [gerar_roadmap(r.id, respostas, regras) for r in top_n(respostas, 3, regras)]


def formatar_roadmap(rm: Roadmap) -> str:
    """Texto simples do plano (a interface Streamlit poderá formatar de outro jeito)."""
    linhas = [f"Plano para {rm.trilha_nome} - prontidão para Júnior: {rm.prontidao:.0f}%"]

    def bloco(titulo: str, lacunas: list[Lacuna]) -> None:
        if not lacunas:
            return
        linhas.append(titulo)
        for l in lacunas:
            aviso = "" if l.informado else " (não informado)"
            linhas.append(f"  - {l.nome}: nível {l.nivel_atual} -> {l.nivel_necessario}{aviso}")
            linhas.append(f"      Estudar: {l.recurso}")

    bloco("1) Estude primeiro:", rm.fase_1_comece_por)
    bloco("2) Em seguida:", rm.fase_2_em_seguida)
    if not rm.lacunas:
        linhas.append("Você já atende a todas as competências Júnior desta trilha.")
    linhas.append("Certificações:")
    linhas += [f"  - {c['nome']}" + (" (obrigatória)" if c["obrigatoria"] else "") for c in rm.certificacoes]
    linhas.append("Projetos para o portfólio no GitHub:")
    linhas += [f"  - {p}" for p in rm.projetos]
    return "\n".join(linhas)


if __name__ == "__main__":
    exemplo = {
        "A01": 4, "A02": 2, "A03": 2, "A04": 1, "A05": 5, "A06": 3,
        "A07": 5, "A08": 2, "A09": 4, "A10": 1, "A11": 4, "A12": 2,
        "O06": 5, "O07": 4, "O01": 3,
        "C11": 4, "C14": 3, "C04": 4, "C01": 3,
    }
    for rm in roadmaps_top3(exemplo)[:1]:
        print(formatar_roadmap(rm))
