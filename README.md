# Sistema Especialista para Mapeamento, Compatibilidade e Trilha de Carreira em TI

Projeto acadêmico de Ciência da Computação. O sistema funciona como um consultor de carreiras: a partir das respostas do usuário, calcula a compatibilidade com dez trilhas de tecnologia, aponta lacunas de competências e sugere um plano de desenvolvimento.

> Projeto em desenvolvimento por etapas. Estado atual: **Etapa 1 (base de conhecimento)**.

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

## Estrutura atual

```
regras_carreiras.json   # trilhas, perguntas, pesos, competências e recomendações
validar_base.py         # validação da base
requirements.txt
README.md
.gitignore
```

## Próximas etapas

Motor de inferência, análise de lacunas e roadmap, interface Streamlit e testes finais.
