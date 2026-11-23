"""Gera o painel e os indicadores do perfil em SVG, nas versões clara e escura.

Lê o painel.json e grava os arquivos em assets/. A Action
.github/workflows/painel.yml roda este script toda madrugada. Para rodar na mão:

    python scripts/gerar_painel.py

Com GITHUB_TOKEN no ambiente, busca as contribuições dos últimos 12 meses e
desenha as barras no painel. Sem token, o painel sai sem as barras.

No painel.json:
- sistema com status "no ar" ganha ponto ciano; qualquer outro status, lilás;
- KPI com "valor": null não aparece. Preencha o valor e o card surge.
"""

import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from xml.sax.saxutils import escape

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "assets"
BRASILIA = timezone(timedelta(hours=-3))  # sem horário de verão desde 2019

LARGURA = 880
X_ESQ, X_DIR, X_FIM = 84, 520, 840  # colunas do painel
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"

TEMAS = {
    "dark": {
        "card": "#110f17", "borda": "#2f2840", "linha": "#2a2238", "tile": "#12101a",
        "forte": "#ffffff", "texto": "#c9c2d8", "suave": "#8a80a0",
        "rosa": "#f472b6", "lilas": "#a78bfa", "ok": "#67e8f9", "barra": "#a78bfa",
    },
    "light": {
        "card": "#ffffff", "borda": "#e7dff0", "linha": "#eee8f4", "tile": "#fbf8fd",
        "forte": "#1b1226", "texto": "#3f3651", "suave": "#6e6585",
        "rosa": "#db2777", "lilas": "#7c3aed", "ok": "#0e7490", "barra": "#8b5cf6",
    },
}

# Ícones do menu lateral, preto nos dois temas, como no Painel VIP.
ICONES = [
    '<rect x="7" y="7" width="5" height="5" rx="1"/><rect x="14" y="7" width="5" height="5" rx="1"/>'
    '<rect x="7" y="14" width="5" height="5" rx="1"/><rect x="14" y="14" width="5" height="5" rx="1"/>',
    '<path d="M9 18v-5M13 18V8M17 18v-7"/>',
    '<path d="M8 8h10a1 1 0 0 1 1 1v6a1 1 0 0 1-1 1h-6l-3 3v-3H8a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1z"/>',
    '<path d="M14 6l-5 8h4l-1 6 5-9h-4z"/>',
    '<path d="M11 9l-4 4 4 4M15 9l4 4-4 4"/>',
]

ANIMACAO = (
    "<style>"
    ".pulso{transform-box:fill-box;transform-origin:center;animation:pulso 2.4s ease-out infinite}"
    "@keyframes pulso{from{transform:scale(1);opacity:.55}to{transform:scale(2.8);opacity:0}}"
    "@media (prefers-reduced-motion:reduce){.pulso{animation:none;opacity:0}}"
    "</style>"
)

CONSULTA = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { contributionCount } }
      }
    }
  }
}
"""


def num(valor):
    """Número curto para atributos SVG: 12.0 vira 12, 10.62 vira 10.6."""
    return f"{valor:.1f}".removesuffix(".0")


def milhar(valor):
    return f"{valor:,}".replace(",", ".")


def aspas(valor):
    return escape(valor, {'"': "&quot;"})


def texto(x, y, conteudo, tamanho, cor, *, mono=False, peso=400, ancora="start", espaco=0):
    extra = f' letter-spacing="{espaco}"' if espaco else ""
    return (
        f'<text x="{num(x)}" y="{num(y)}" font-family="{MONO if mono else SANS}" '
        f'font-size="{tamanho}" font-weight="{peso}" fill="{cor}" text-anchor="{ancora}"{extra}>'
        f"{escape(str(conteudo))}</text>"
    )


def svg(altura, rotulo, corpo):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{LARGURA}" height="{altura}" '
        f'viewBox="0 0 {LARGURA} {altura}" role="img" aria-label="{aspas(rotulo)}">'
        f"<title>{escape(rotulo)}</title>{corpo}</svg>\n"
    )


def kpis_visiveis(cfg):
    return [k for k in cfg["kpis"] if k.get("valor") not in (None, "")]


def cabe(conteudo, tamanho, espaco, mono=False):
    """O SVG não mede texto; esta estimativa avisa quando algo pode vazar."""
    if len(str(conteudo)) * tamanho * (0.62 if mono else 0.56) > espaco:
        print(f'aviso: "{conteudo}" pode não caber no painel', file=sys.stderr)


def conferir_textos(cfg):
    cabe(cfg["cargo"], 15, X_DIR - X_ESQ - 24)
    cabe(cfg["local"], 13, X_DIR - X_ESQ - 24)
    for sistema in cfg["sistemas"]:
        cabe(f'{sistema["nome"]}   {sistema["status"]}', 13, X_FIM - X_DIR - 18)
    kpis = kpis_visiveis(cfg)
    if kpis:
        espaco = (LARGURA - 12 * (len(kpis) - 1)) / len(kpis) - 32
        for kpi in kpis:
            cabe(kpi["rotulo"].upper(), 12, espaco, mono=True)
            cabe(kpi.get("detalhe", ""), 12, espaco)


def buscar_contribuicoes(usuario):
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("sem GITHUB_TOKEN: o painel sai sem as barras de contribuição", file=sys.stderr)
        return None
    pedido = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": CONSULTA, "variables": {"login": usuario}}).encode(),
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "gerar-painel",
        },
    )
    try:
        with urllib.request.urlopen(pedido, timeout=30) as resposta:
            dados = json.load(resposta)
        calendario = dados["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    except (OSError, ValueError, KeyError, TypeError) as erro:
        print(f"aviso: não consegui buscar as contribuições ({erro})", file=sys.stderr)
        return None
    semanas = [
        sum(dia["contributionCount"] for dia in semana["contributionDays"])
        for semana in calendario["weeks"]
    ][-52:]
    if not semanas:
        return None
    return {"total": calendario["totalContributions"], "semanas": semanas}


def menu_lateral():
    partes = []
    for i, icone in enumerate(ICONES):
        ativo = i == 0
        fundo = "#f472b6" if ativo else "#1d1a26"
        if ativo:
            tinta = 'fill="#1a0d16"'
        else:
            tinta = 'fill="none" stroke="#8a80a0" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"'
        partes.append(
            f'<g transform="translate(15 {20 + i * 38})">'
            f'<rect width="26" height="26" rx="7" fill="{fundo}"/><g {tinta}>{icone}</g></g>'
        )
    return "".join(partes)


def barras(t, contrib, topo):
    """Contribuições por semana. Devolve o SVG e a linha de base das barras."""
    semanas = contrib["semanas"]
    partes = [
        texto(X_ESQ, topo, f"CONTRIBUIÇÕES · ÚLTIMAS {len(semanas)} SEMANAS", 11, t["suave"],
              mono=True, peso=600, espaco=1.6),
        texto(X_FIM, topo, f'{milhar(contrib["total"])} em 12 meses', 13, t["forte"],
              peso=600, ancora="end"),
    ]
    base, teto, folga = topo + 56, 40, 4
    largura = (X_FIM - X_ESQ - folga * (len(semanas) - 1)) / len(semanas)
    maior = max(semanas) or 1
    for i, valor in enumerate(semanas):
        altura = max(2, teto * valor / maior)
        if i == len(semanas) - 1:
            cor = t["rosa"]  # semana atual
        elif valor:
            cor = t["barra"]
        else:
            cor = t["linha"]
        x = X_ESQ + i * (largura + folga)
        partes.append(
            f'<rect x="{num(x)}" y="{num(base - altura)}" width="{num(largura)}" '
            f'height="{num(altura)}" rx="2" fill="{cor}"/>'
        )
    return "".join(partes), base


def svg_painel(cfg, t, contrib, agora):
    sistemas = cfg["sistemas"]
    fim_texto = max(150, 76 + (len(sistemas) - 1) * 26)
    partes = [
        texto(X_ESQ, 46, cfg["selo"].upper(), 11, t["rosa"], mono=True, peso=600, espaco=1.6),
        texto(X_ESQ, 98, cfg["nome"], 46, t["forte"], peso=700),
        texto(X_ESQ, 128, cfg["cargo"], 15, t["texto"]),
        texto(X_ESQ, 150, cfg["local"], 13, t["suave"]),
        texto(X_DIR, 46, "SISTEMAS", 11, t["suave"], mono=True, peso=600, espaco=1.6),
    ]
    for i, sistema in enumerate(sistemas):
        y = 76 + i * 26
        cor = t["ok"] if sistema["status"] == "no ar" else t["lilas"]
        ponto = f'cx="{X_DIR + 5}" cy="{y - 4.5}" r="4" fill="{cor}"'
        partes += [
            f'<circle class="pulso" style="animation-delay:{i * 0.6:.1f}s" {ponto}/>',
            f"<circle {ponto}/>",
            texto(X_DIR + 18, y, sistema["nome"], 14, t["texto"]),
            texto(X_FIM, y, sistema["status"], 11.5, t["suave"], mono=True, ancora="end"),
        ]

    linha = fim_texto + 30
    if contrib:
        grafico, base = barras(t, contrib, topo=fim_texto + 38)
        partes.append(grafico)
        linha = base + 22
    altura = linha + 34
    partes += [
        f'<line x1="56" y1="{linha}" x2="{LARGURA - 1}" y2="{linha}" stroke="{t["linha"]}"/>',
        texto(X_ESQ, linha + 21, cfg["rodape"], 11.5, t["suave"], mono=True),
        texto(X_FIM, linha + 21, f"atualizado {agora:%d/%m/%Y} · {agora:%H:%M}", 11.5,
              t["suave"], mono=True, ancora="end"),
    ]

    corpo = (
        ANIMACAO
        + f'<defs><clipPath id="card"><rect width="{LARGURA}" height="{altura}" rx="14"/></clipPath></defs>'
        + f'<g clip-path="url(#card)"><rect width="{LARGURA}" height="{altura}" fill="{t["card"]}"/>'
        + f'<rect width="56" height="{altura}" fill="#000"/>{menu_lateral()}</g>'
        + f'<rect x=".5" y=".5" width="{LARGURA - 1}" height="{altura - 1}" rx="13.5" '
        + f'fill="none" stroke="{t["borda"]}"/>'
        + "".join(partes)
    )
    return svg(altura, f'{cfg["nome"]} · {cfg["cargo"]} · {cfg["local"]}', corpo)


def svg_kpis(cfg, t):
    kpis = kpis_visiveis(cfg)
    if not kpis:
        return None
    folga, altura = 12, 108
    largura = (LARGURA - folga * (len(kpis) - 1)) / len(kpis)
    partes = []
    for i, kpi in enumerate(kpis):
        x = i * (largura + folga)
        partes += [
            f'<rect x="{num(x + 0.5)}" y=".5" width="{num(largura - 1)}" height="{altura - 1}" '
            f'rx="10" fill="{t["tile"]}" stroke="{t["borda"]}"/>',
            texto(x + 16, 30, kpi["rotulo"].upper(), 10.5, t["suave"], mono=True, peso=600, espaco=1.2),
            texto(x + 16, 70, kpi["valor"], 30, t["forte"], peso=700),
            texto(x + 16, 92, kpi.get("detalhe", ""), 12, t["suave"]),
        ]
    rotulo = " · ".join(f'{kpi["valor"]} {kpi["rotulo"]}' for kpi in kpis)
    return svg(altura, rotulo, "".join(partes))


def salvar(nome, conteudo):
    (SAIDA / nome).write_text(conteudo, encoding="utf-8", newline="\n")
    print(f"ok  assets/{nome}")


def main():
    cfg = json.loads((RAIZ / "painel.json").read_text(encoding="utf-8"))
    conferir_textos(cfg)
    contrib = None
    if cfg.get("mostrar_contribuicoes"):
        contrib = buscar_contribuicoes(cfg["usuario_github"])
    agora = datetime.now(BRASILIA)
    SAIDA.mkdir(exist_ok=True)
    for tema, cores in TEMAS.items():
        salvar(f"painel-{tema}.svg", svg_painel(cfg, cores, contrib, agora))
        kpis = svg_kpis(cfg, cores)
        if kpis:
            salvar(f"kpis-{tema}.svg", kpis)


if __name__ == "__main__":
    main()
