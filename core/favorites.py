"""Favoritos locais. Ficam no settings.json — nenhuma requisição nova à API.

Regras (fixadas pelo usuario):
- favorito ONLINE fica fixado no topo (com a estrela e o contorno accent);
- favorito que NÃO veio na lista de online aparece depois dos online, apagado,
  com status "offline", avatar do cache e "visto há X";
- a ordenação por coluna vale dentro dos online; o bloco offline é sempre o
  último e ordenado por nome A->Z;
- nome e "visto por último" só são atualizados quando a atualização deu certo.

Nada aqui importa Qt: a ponte consome estas funções e o QML só desenha.
"""

import time

from .formatting import humanize_epoch
from .models import Friend
from .sorting import normalize, sort_friends

CHAVE = "favorites"        # settings[CHAVE] = {id: {"name": str, "last_seen": epoch}}

# não regrava o settings a cada atualização de 45 s só para mover o "visto há"
INTERVALO_VISTO = 300


def _limpar(bruto):
    """Sanitiza o que veio do settings.json (arquivo velho ou editado à mão)."""
    saida = {}
    if not isinstance(bruto, dict):
        return saida
    for uid, dados in bruto.items():
        if not isinstance(uid, str) or not uid:
            continue
        if not isinstance(dados, dict):
            dados = {}
        try:
            visto = float(dados.get("last_seen") or 0)
        except (TypeError, ValueError):
            visto = 0.0
        saida[uid] = {"name": str(dados.get("name") or "").strip(), "last_seen": visto}
    return saida


def carregar(settings):
    """Lê os favoritos do settings (sempre um dict id -> {"name", "last_seen"})."""
    return _limpar((settings or {}).get(CHAVE) or {})


def salvar(settings, favoritos):
    """Grava os favoritos no dict de settings (quem chama salva o arquivo)."""
    settings = settings if isinstance(settings, dict) else {}
    settings[CHAVE] = {
        uid: {"name": d.get("name") or "", "last_seen": d.get("last_seen") or 0}
        for uid, d in (favoritos or {}).items()
    }
    return settings


def alternar(favoritos, friend, agora=None):
    """Liga/desliga o favorito. Devolve (favoritos, virou_favorito)."""
    agora = time.time() if agora is None else agora
    saida = dict(favoritos or {})
    if friend.id in saida:
        del saida[friend.id]
        return saida, False
    saida[friend.id] = {"name": friend.name or "?", "last_seen": agora}
    return saida, True


def marcar_vistos(favoritos, online, agora=None):
    """Atualiza nome e "visto por último" de quem está online agora.

    Devolve (favoritos, mudou). Só deve ser chamado depois de atualização
    bem-sucedida — falha de rede não pode mexer no que está guardado.
    """
    agora = time.time() if agora is None else agora
    saida = dict(favoritos or {})
    mudou = False
    for amigo in online or []:
        dados = saida.get(amigo.id)
        if dados is None:
            continue
        nome = amigo.name or dados.get("name") or "?"
        visto = dados.get("last_seen") or 0.0
        if nome != dados.get("name") or agora - visto >= INTERVALO_VISTO:
            saida[amigo.id] = {"name": nome, "last_seen": agora}
            mudou = True
    return saida, mudou


def amigos_offline(favoritos, online_ids, avatar_de=None, agora=None):
    """Favoritos que não estão na lista de online, como Friend apagadinho.

    `avatar_de(id)` devolve o caminho do PNG em cache (sem rede) ou "".
    """
    agora = time.time() if agora is None else agora
    online_ids = online_ids or set()
    saida = []
    for uid, dados in (favoritos or {}).items():
        if uid in online_ids:
            continue
        amigo = Friend(
            id=uid,
            name=dados.get("name") or "?",
            status="offline",
            world="",
            location="",
            platform="",
            active=humanize_epoch(dados.get("last_seen") or 0, agora),
        )
        if avatar_de is not None:
            amigo.avatar = avatar_de(uid) or None
        saida.append(amigo)
    return sorted(saida, key=lambda f: (normalize(f.name), f.id or ""))


def montar_lista(online, offline, favoritos, coluna="status", direcao="asc"):
    """Favoritos online fixados no topo, resto dos online, e o bloco offline no fim.

    A ordenação da coluna escolhida vale dentro de cada bloco online; o bloco
    offline é sempre por nome A->Z (é o "visto há X", não tem status nem mundo).
    """
    favoritos = favoritos or {}
    fixos = [f for f in (online or []) if f.id in favoritos]
    resto = [f for f in (online or []) if f.id not in favoritos]
    caidos = sorted(offline or [], key=lambda f: (normalize(f.name), f.id or ""))
    return (
        sort_friends(fixos, coluna, direcao)
        + sort_friends(resto, coluna, direcao)
        + caidos
    )
