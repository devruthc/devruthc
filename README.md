<!-- O painel, os indicadores e a cobrinha são gerados pela Action "painel" toda madrugada.
     Para mudar textos e números, edite o painel.json (não os SVGs). -->

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/painel-dark.svg">
  <img src="assets/painel-light.svg" width="100%" alt="Ruth, Analista de Dados e Desenvolvedora Python na VIP Promotora, em Florianópolis. Sistemas: Dashboard de Vendas, Huggy Sync, Formalização e Central de Monitoramento.">
</picture>

<p align="center">
  <a href="https://www.linkedin.com/in/ruthcavalcante"><img src="https://img.shields.io/badge/LinkedIn-ruthcavalcante-F472B6?style=flat-square" alt="LinkedIn"></a>
</p>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/kpis-dark.svg">
  <img src="assets/kpis-light.svg" width="100%" alt="Indicadores do perfil.">
</picture>

## atividade

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/cobrinha-dark.svg">
  <img src="assets/cobrinha-light.svg" width="100%" alt="Cobrinha percorrendo o gráfico de contribuições.">
</picture>

## módulos carregados

| camada | módulos |
|---|---|
| **dados** | `python 3.13` `pandas` `numpy` `sql` `postgresql 17` `power bi` |
| **backend** | `django 6` `django rest framework` `jwt` `gunicorn` |
| **assíncrono** | `celery` `celery beat` `redis` |
| **integrações** | `huggy api` `google sheets api` `rest` |
| **interface** | `chart.js` `bootstrap` `tailwind` `html` `css` `javascript` |
| **qualidade** | `docker` `github actions` `ruff` `pytest` `git` |

## projetos

| projeto | status | stack | o que entrega |
|---|---|---|---|
| **Dashboard de Vendas** | ![privado](https://img.shields.io/badge/privado-7C3AED?style=flat-square) | Django · Celery · Redis · PostgreSQL | indicadores comerciais por sala, coordenador e corretor, atualizados toda madrugada |
| **Huggy Sync** | ![privado](https://img.shields.io/badge/privado-7C3AED?style=flat-square) | Django · PostgreSQL · Docker | atendimentos da Huggy sincronizados por API |
| **Dashboard de Formalização** | ![privado](https://img.shields.io/badge/privado-7C3AED?style=flat-square) | Django · Python | esteira de formalização, com versão mobile |
| **Central de Monitoramento** | ![privado](https://img.shields.io/badge/privado-7C3AED?style=flat-square) | Django · Python | rotinas e processos automatizados |
| [**Biblioteca de Identidade Visual**](https://github.com/devruthc/biblioteca-identidade-visual-vip-) | ![aberto](https://img.shields.io/badge/aberto-0E7490?style=flat-square) | CSS | componentes e estilos com a cara da empresa |
| [**disparos.py**](https://github.com/devruthc/disparos.py) | ![aberto](https://img.shields.io/badge/aberto-0E7490?style=flat-square) | Python | automação de disparos de mensagens |

<details>
<summary><b>como este painel se atualiza sozinho</b></summary>
<br>

Toda madrugada, às 03:00, uma GitHub Action:

1. busca minhas contribuições na API GraphQL do GitHub;
2. roda o [`gerar_painel.py`](scripts/gerar_painel.py), que lê o [`painel.json`](painel.json) e desenha o painel e os indicadores em SVG, nas versões clara e escura;
3. gera a cobrinha com o [Platane/snk](https://github.com/Platane/snk);
4. faz o commit só quando algo mudou.

</details>

<p align="center"><sub>feito com carinho e Python</sub></p>
