# Sistema Especialista para Mapeamento, Compatibilidade e Trilha de Carreira em TI

Projeto acadêmico de Ciência da Computação. O sistema funciona como um consultor de carreiras: a partir das respostas do usuário, calcula a compatibilidade com dez trilhas de tecnologia, aponta lacunas de competências e sugere um plano de desenvolvimento.

> Projeto em desenvolvimento por etapas. Estado atual: **Fase 5 (testes de robustez)**.

## Trilhas contempladas

Back-end, Front-end/UX, Ciência de Dados, Engenharia de Dados, Cibersegurança, DevOps/SRE, Arquitetura Cloud, Desenvolvimento Mobile, Quality Assurance (QA) e Product Management.

## Tecnologias

Python 3.10+, Streamlit, JSON (base de conhecimento externa), pandas, plotly, pytest, Git/GitHub.

## Instalação (Windows / PyCharm)

1. Abra a pasta do projeto no PyCharm e ative o ambiente virtual `.venv`.
2. No terminal do PyCharm, instale as dependências:

```
pip install -r requirements.txt
```

## Validação da base de conhecimento

```
python validar_base.py
```

O script confere se o JSON carrega, se há as dez trilhas e se todas as referências (perguntas, competências, pesos) são consistentes.

## Motor de inferência

```
python motor.py
```

Compatibilidade = afinidade (60%) + objetivo (25%) + conhecimento (15%), com pesos lidos do JSON; ajustes justificados aplicam penalidades a perfis conflitantes e empates parciais são sinalizados.

## Testes

```
pytest
```

Cobrem a validação da base, o motor (cálculo, penalidades, entradas inválidas), gaps e roadmap, casos limite (perfis ambíguos, empates parciais, justificativas) e um teste de fumaça da interface.

## Interface web

```
streamlit run app.py
```

Wizard em etapas (perfil, afinidades, conhecimentos, objetivos) seguido do resultado: Top 3, gráficos de radar e barras, tabela de componentes, lacunas e plano de ação por trilha.

## Lacunas e roadmap

```
python roadmap.py
```

Compara o nível do usuário em cada competência Júnior da trilha com o mínimo definido no JSON, ordena as lacunas por prioridade (importância x distância) e sugere o que estudar, certificações e projetos de portfólio.

## Estrutura atual

```
regras_carreiras.json   # trilhas, perguntas, pesos, competências e recomendações
validar_base.py         # validação da base
motor.py                # motor de inferência (pontuação ponderada e ranking)
roadmap.py              # análise de lacunas e roadmap personalizado
requirements.txt
README.md
.gitignore
```

## Status

Todas as fases do enunciado (1 a 5) foram implementadas.
