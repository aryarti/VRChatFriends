"""Ordenacao da lista de amigos. Python puro: a ponte QML e a UI Tkinter usam igual.

Regras (fixadas pelo usuario na v1.1):

- Colunas clicaveis: Amigo, Status, Mundo. Primeiro clique = crescente, segundo =
  decrescente; a seta existe so na coluna ativa.
- Status crescente: Join Me, Online, Ask Me, Busy; status desconhecido no fim.
- Mundo crescente: publico, grupo, amigos/convite, privado, web/menu/outras
  plataformas; dentro do mesmo tipo, nome do mundo e depois nome do amigo.
- Desempate SEMPRE por nome A->Z (sem acento, sem caixa) e ele NAO inverte com a
  direcao; ultimo criterio e o ID.

Como o desempate nao inverte, a ordenacao e feita em duas passadas com o sort
estavel do Python: primeiro nome+ID (ordem que fica de base), depois a chave da
coluna. Assim `reverse=True` inverte apenas a coluna, nunca o desempate.
"""

import unicodedata

from .formatting import is_public_location

COLUMNS = ("name", "status", "world")
DIRECTIONS = ("asc", "desc")
DEFAULT_COLUMN = "status"
DEFAULT_DIRECTION = "asc"

# ordem pedida: Join Me -> Online -> Ask Me -> Busy (desconhecido depois de tudo)
STATUS_RANK = {"join me": 0, "active": 1, "ask me": 2, "busy": 3}
STATUS_UNKNOWN = 4

# tipos de instancia, do mais aberto para o mais fechado
WORLD_PUBLIC = 0    # sem marca de restricao
WORLD_GROUP = 1     # ~group(...)
WORLD_FRIENDS = 2   # ~friends / ~hidden / canrequestinvite  (amigos, amigos+, convite)
WORLD_PRIVATE = 3   # ~private(...)
WORLD_OUTSIDE = 4   # web, menu, viajando, desconhecido

_MARCAS_AMIGOS = ("~friends", "~hidden", "canrequestinvite")


def normalize(text):
    """'Ágata' -> 'agata': sem acento e sem caixa, para comparar nomes."""
    decomposto = unicodedata.normalize("NFKD", text or "")
    sem_acento = "".join(c for c in decomposto if not unicodedata.combining(c))
    return sem_acento.casefold().strip()


def normalize_choice(column, direction):
    """(coluna, direcao) validos — o settings.json pode estar velho ou torto."""
    col = column if column in COLUMNS else DEFAULT_COLUMN
    dir_ = direction if direction in DIRECTIONS else DEFAULT_DIRECTION
    return col, dir_


def status_rank(friend):
    return STATUS_RANK.get((friend.status or "").strip().lower(), STATUS_UNKNOWN)


def world_rank(friend):
    """Tipo da instancia onde o amigo esta (ver constantes WORLD_*)."""
    loc = (friend.location or "").strip().lower()
    if not loc:
        return WORLD_OUTSIDE
    if not loc.startswith("wrld_"):
        # fora de mundo: 'offline' (web/menu), 'private', 'traveling'
        return WORLD_PRIVATE if loc == "private" else WORLD_OUTSIDE
    if is_public_location(loc):
        return WORLD_PUBLIC
    if "~group" in loc:
        return WORLD_GROUP
    if any(marca in loc for marca in _MARCAS_AMIGOS):
        return WORLD_FRIENDS
    if "~private" in loc:
        return WORLD_PRIVATE
    return WORLD_OUTSIDE


def world_name(friend):
    """'Furry Hangout · público · JP' -> 'Furry Hangout' (o sufixo e rotulo, nao nome)."""
    return (friend.world or "").split(" · ")[0]


def _name_key(friend):
    return normalize(friend.name)


def _status_key(friend):
    return status_rank(friend)


def _world_key(friend):
    return (world_rank(friend), normalize(world_name(friend)))


_KEYS = {"name": _name_key, "status": _status_key, "world": _world_key}


def sort_friends(friends, column=DEFAULT_COLUMN, direction=DEFAULT_DIRECTION):
    """Devolve uma lista nova ordenada pela coluna/direcao pedidas."""
    col, dir_ = normalize_choice(column, direction)
    # 1a passada: desempate fixo (nome A->Z, depois ID) — nunca invertido
    base = sorted(friends, key=lambda f: (normalize(f.name), f.id or ""))
    # 2a passada: so a coluna; o sort estavel preserva o desempate dentro dos empates
    return sorted(base, key=_KEYS[col], reverse=(dir_ == "desc"))
