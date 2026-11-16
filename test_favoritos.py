# -*- coding: utf-8 -*-
"""Favoritos locais: settings, nome/visto, fixados no topo e bloco offline.

Sem rede e sem Qt. Uso: python -B test_favoritos.py
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import Friend  # noqa: E402
from core import favorites  # noqa: E402
import core.paths as paths_mod  # noqa: E402

falhas = []


def check(nome, cond, extra=""):
    print(("OK   " if cond else "FALHA") + f"  {nome}" + (f"  [{extra}]" if extra else ""))
    if not cond:
        falhas.append(nome)


def amigo(uid, nome, status="active", world="Pug", location="wrld_a:1"):
    return Friend(id=uid, name=nome, status=status, world=world, location=location)


# ---------------------------------------------------------------- carregar/salvar
torto = {"favorites": {
    "u1": {"name": "Ana", "last_seen": "123.5"},
    "u2": "lixo",
    "": {"name": "sem id"},
    "u3": {"name": 7, "last_seen": None},
}}
limpos = favorites.carregar(torto)
check("sanitiza o settings", set(limpos) == {"u1", "u2", "u3"}, str(sorted(limpos)))
check("converte last_seen para número", limpos["u1"]["last_seen"] == 123.5, str(limpos["u1"]))
check("entrada torta vira nome vazio e visto 0",
      limpos["u2"] == {"name": "", "last_seen": 0.0}, str(limpos["u2"]))
check("nome numérico vira texto", limpos["u3"]["name"] == "7", str(limpos["u3"]))
check("settings sem a chave devolve vazio", favorites.carregar({}) == {})

s = favorites.salvar({}, {"u1": {"name": "Ana", "last_seen": 10.0}})
check("salvar cria a chave certa", s["favorites"]["u1"]["name"] == "Ana", str(s))

# ---------------------------------------------------------------- estrela
fav = {}
fav, virou = favorites.alternar(fav, amigo("u1", "Ana"), agora=500.0)
check("favoritar guarda id, nome e hora", virou and fav["u1"]["name"] == "Ana"
      and fav["u1"]["last_seen"] == 500.0, str(fav))
fav, virou = favorites.alternar(fav, amigo("u1", "Ana"), agora=900.0)
check("desfavoritar remove", virou is False and fav == {}, str(fav))

# ---------------------------------------------------------------- visto/nome
favoritos = {
    "u1": {"name": "Ana", "last_seen": 0.0},          # nunca visto
    "u2": {"name": "nome velho", "last_seen": 0.0},   # nome mudou
    "u3": {"name": "Caio", "last_seen": 9_990.0},     # visto agora há pouco
}
online = [amigo("u1", "Ana"), amigo("u2", "Bia"), amigo("u3", "Caio")]
atualizados, mudou = favorites.marcar_vistos(favoritos, online, agora=10_000.0)
check("marca visto/nome de quem está online", mudou is True)
check("nome do favorito acompanha o online", atualizados["u2"]["name"] == "Bia")
check("visto do recém-visto não é reescrito", atualizados["u3"]["last_seen"] == 9_990.0,
      str(atualizados["u3"]))
check("quem não está online não é tocado",
      favorites.marcar_vistos(favoritos, [], agora=10_000.0)[1] is False)

# ---------------------------------------------------------------- bloco offline
favoritos = {
    "u1": {"name": "Ana", "last_seen": 10_000.0 - 7200},   # 2 h
    "u2": {"name": "Bia", "last_seen": 0},                 # sem dado
}
avatar_de = lambda uid: "/cache/%s.png" % uid  # noqa: E731
off = favorites.amigos_offline(favoritos, {"u1"}, avatar_de=avatar_de, agora=10_000.0)
check("só entra quem não está online", [f.id for f in off] == ["u2"], [f.id for f in off])
check("status é offline", off[0].status == "offline")
check("avatar vem do cache", off[0].avatar == "/cache/u2.png", str(off[0].avatar))
check("sem dado de visto -> texto vazio", off[0].active == "", repr(off[0].active))

off2 = favorites.amigos_offline(
    {"u1": {"name": "Ana", "last_seen": 10_000.0 - 7200},
     "u2": {"name": "Zeca", "last_seen": 10_000.0 - 60}},
    set(), avatar_de=None, agora=10_000.0)
check("offline é ordenado por nome", [f.name for f in off2] == ["Ana", "Zeca"], [f.name for f in off2])
check("visto há 2 h", off2[0].active == "2 h", off2[0].active)
check("visto agora", off2[1].active == "agora", off2[1].active)

# ---------------------------------------------------------------- ordem da lista
online = [
    amigo("u1", "Ana", status="active", world="Pug"),
    amigo("u2", "Bia", status="busy", world="Pug"),
    amigo("u3", "Caio", status="join me", world="Pug"),
    amigo("u4", "Duda", status="active", world="Pug"),
]
favoritos = {"u2": {"name": "Bia", "last_seen": 0}, "u4": {"name": "Duda", "last_seen": 0}}
offline = favorites.amigos_offline(
    {"u9": {"name": "Zeca", "last_seen": 0},
     "u8": {"name": "Abel", "last_seen": 0}}, set())
lista = favorites.montar_lista(online, offline, favoritos, "status", "asc")
check("favoritos online no topo, depois o resto, offline no fim",
      [f.name for f in lista] == ["Duda", "Bia", "Caio", "Ana", "Abel", "Zeca"],
      [f.name for f in lista])

lista_coluna = favorites.montar_lista(online, [], favoritos, "name", "desc")
check("a coluna escolhida ordena DENTRO de cada bloco (favoritos e resto)",
      [f.name for f in lista_coluna] == ["Duda", "Bia", "Caio", "Ana"],
      [f.name for f in lista_coluna])

sem_fav = favorites.montar_lista(online, offline, {}, "status", "asc")
check("sem favoritos é a ordem normal + offline no fim",
      [f.name for f in sem_fav] == ["Caio", "Ana", "Duda", "Bia", "Abel", "Zeca"],
      [f.name for f in sem_fav])

check("favorito offline fica depois de todo mundo",
      favorites.montar_lista(online, offline, favoritos, "name", "asc")[-2:] == offline,
      str([f.name for f in favorites.montar_lista(online, offline, favoritos, "name", "asc")][-2:]))

# ---------------------------------------------------------------- avatar do cache
tmp = tempfile.mkdtemp(prefix="vrc_fav_")
paths_mod.AVATARS_DIR = tmp
check("cache vazio devolve ''", paths_mod.avatar_cache_path("u1", 56) == "")
open(os.path.join(tmp, "u1-56.png"), "wb").close()
check("cache existente devolve o caminho",
      paths_mod.avatar_cache_path("u1", 56).endswith("u1-56.png"),
      paths_mod.avatar_cache_path("u1", 56))
check("tamanho diferente não existe", paths_mod.avatar_cache_path("u1", 20) == "")
check("sem id devolve ''", paths_mod.avatar_cache_path("", 56) == "")

print()
print("FALHAS:", falhas if falhas else "nenhuma")
sys.exit(1 if falhas else 0)
