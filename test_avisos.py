# -*- coding: utf-8 -*-
"""Aviso de "amigo entrou no jogo": transição, primeira carga, web, 10 min, resumo.

Sem rede e sem Qt. Uso: python -B test_avisos.py
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import Friend  # noqa: E402
from core import alerts  # noqa: E402

falhas = []


def check(nome, cond, extra=""):
    print(("OK   " if cond else "FALHA") + f"  {nome}" + (f"  [{extra}]" if extra else ""))
    if not cond:
        falhas.append(nome)


def amigo(uid, nome, platform="standalonewindows", location="wrld_a:1", world="Pug", avatar=""):
    return Friend(id=uid, name=nome, status="active", platform=platform,
                  location=location, world=world, avatar=avatar or None)


# ---------------------------------------------------------------- "no jogo"
check("mundo conta como no jogo", alerts.esta_no_jogo("standalonewindows", "wrld_a:1"))
check("menu do cliente conta", alerts.esta_no_jogo("android", "offline"))
check("web NÃO conta", not alerts.esta_no_jogo("web", "offline"))
check("web com location de mundo ainda não conta", not alerts.esta_no_jogo("web", "wrld_a:1"))
check("sem plataforma e sem mundo não conta", not alerts.esta_no_jogo("", "offline"))

# ---------------------------------------------------------------- primeira carga
foto = alerts.snapshot([amigo("u1", "Ana"), amigo("u2", "Bia", platform="web")])
check("foto traz quem está no jogo", foto["u1"]["no_jogo"] is True and foto["u2"]["no_jogo"] is False)
check("primeira carga não avisa", alerts.entradas_novas(None, foto) == [])

# ---------------------------------------------------------------- transições
antes = alerts.snapshot([
    amigo("u1", "Ana", platform="web", location="offline", world="na web"),
    amigo("u2", "Bia"),
    amigo("u3", "Caio", platform="web", location="offline", world="na web"),
])
depois = alerts.snapshot([
    amigo("u1", "Ana", platform="standalonewindows", location="offline", world="no menu"),
    amigo("u2", "Bia"),
    amigo("u3", "Caio", platform="web", location="offline", world="na web"),   # continua web
])
novos = alerts.entradas_novas(antes, depois)
check("quem saiu da web e abriu o cliente avisa", [d["name"] for d in novos] == ["Ana"],
      [d["name"] for d in novos])
check("quem já estava no jogo não avisa de novo",
      alerts.entradas_novas(depois, antes) == [], str(alerts.entradas_novas(depois, antes)))
check("quem continua na web não avisa", all(d["name"] != "Caio" for d in novos))

# amigo novo que aparece já no jogo também avisa (não estava na foto anterior)
depois2 = alerts.snapshot([amigo("u2", "Bia"), amigo("u9", "Duda")])
novos2 = alerts.entradas_novas(alerts.snapshot([amigo("u2", "Bia")]), depois2)
check("amigo que aparece direto no jogo avisa", [d["name"] for d in novos2] == ["Duda"],
      [d["name"] for d in novos2])

# ---------------------------------------------------------------- 10 minutos
agora = 10_000.0
ultimo = {"u1": agora - 60, "u2": agora - 700}
candidatos = [{"id": "u1", "name": "Ana"}, {"id": "u2", "name": "Bia"}]
filtrados = alerts.filtrar_intervalo(candidatos, ultimo, agora)
check("quem avisou faz 1 min fica de fora", [d["name"] for d in filtrados] == ["Bia"],
      [d["name"] for d in filtrados])
check("sem histórico todos passam",
      len(alerts.filtrar_intervalo(candidatos, {}, agora)) == 2)

# ---------------------------------------------------------------- agrupar
favoritos = {"u2": {"name": "Bia", "last_seen": 0}}
um = alerts.agrupar([{"id": "u1", "name": "Ana", "world": "Pug", "avatar": ""}], favoritos)
check("aviso individual carrega nome, mundo e a marca de favorito",
      len(um) == 1 and um[0]["name"] == "Ana" and um[0]["world"] == "Pug"
      and um[0]["favorito"] is False and um[0]["agregado"] == 0, str(um))
dois = alerts.agrupar([
    {"id": "u1", "name": "Ana", "world": "", "avatar": ""},
    {"id": "u2", "name": "Bia", "world": "", "avatar": ""},
], favoritos)
check("até 3 avisos saem separados", len(dois) == 2 and dois[1]["favorito"] is True, str(dois))

quatro = alerts.agrupar([
    {"id": f"u{i}", "name": n, "world": "", "avatar": ""}
    for i, n in enumerate(["Ana", "Bia", "Caio", "Duda"])
], favoritos)
check("mais de 3 vira UM aviso só", len(quatro) == 1, str(quatro))
check("resumo diz quantos entraram", quatro[0]["texto"] == "4 amigos entraram", str(quatro[0]))
check("resumo com favorito no meio sai em destaque", quatro[0]["favorito"] is True, str(quatro[0]))
quatro_fav = alerts.agrupar([
    {"id": "u1", "name": "Ana", "world": "", "avatar": ""},
    {"id": "u2", "name": "Bia", "world": "", "avatar": ""},
    {"id": "u3", "name": "Caio", "world": "", "avatar": ""},
    {"id": "u4", "name": "Duda", "world": "", "avatar": ""},
], favoritos)
check("resumo com favorito no meio fica em destaque", quatro_fav[0]["favorito"] is True)
check("lista vazia não gera aviso", alerts.agrupar([], favoritos) == [])

# ---------------------------------------------------------------- avatar
com_avatar = alerts.snapshot([amigo("u1", "Ana", avatar="/tmp/a.png")])
check("foto leva o caminho do avatar", com_avatar["u1"]["avatar"] == "/tmp/a.png")

print()
print("FALHAS:", falhas if falhas else "nenhuma")
sys.exit(1 if falhas else 0)
