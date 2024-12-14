
# Dashboard futebol com LLM

Projeto como parte do Assessment de Desenvolvimento de Data-Driven Apps com Python, essa aplicação consome os dados da API do StatsBomb e disponibiliza ao usuário interagir com esses dados de maneira dinâmica, incluindo: sumarização/narração de partida com LLM, análise do perfil do jogador com LLM, visão geral da partida e mapa de passes dos jogadores.




## Acessando a aplicação

Você pode acessar a aplicação clicando neste [link](https://dashboard-futebol-llm.streamlit.app)

## Linguagens, Frameworks e Ferramentas usadas

![Python](https://img.shields.io/badge/Python-3.11.9-blue?style=for-the-badge&logo=python&logoColor=yellow) ![LangChain](https://img.shields.io/badge/LangChain-0.3.11-green?style=for-the-badge&logo=langchain&logoColor=green) ![Streamlit](https://img.shields.io/badge/streamlit-1.41.0-red?style=for-the-badge&logo=streamlit&logoColor=red) ![Mplsoccer](https://img.shields.io/badge/mplsoccer-1.4.0-green?style=for-the-badge) ![Gemini](https://img.shields.io/badge/gemini-1.5--flash-%234796E3?style=for-the-badge&logo=googlegemini&logoColor=%234796E3)

## Rodando localmente

Clone o projeto

```
  git clone https://github.com/Leticia-Infnet/leticia_abreu_DR3_AT_parte1.git
```

Entre no diretório do projeto

```
  cd leticia_abreu_DR3_AT_parte1
```

Instale as dependências

```
  pip install -r requirements.txt
```

Crie um arquivo .env contendo sua chave da API do Gemini, no formato abaixo:

GEMINI_API_KEY = SUA_API_KEY

Rode o projeto

```
  streamlit run main.py
```


