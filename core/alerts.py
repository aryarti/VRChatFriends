"""Quem ENTROU NO JOGO desde a última atualização -> aviso do próprio app.

Sem Qt e sem rede: recebe duas "fotos" da lista e devolve quem mudou. A interface
só desenha o que sair daqui.

Regra do aviso (fixada pelo usuario):
- só vale quem está NO JOGO. Quem está só na web (plataforma `web`) não interessa.
- quem está no cliente mas no menu (location "offline" com plataforma de cliente)
  conta como "no jogo": é o amigo aberto, pronto para receber convite.
- a primeira atualização depois de abrir/entrar nunca avisa (é a foto inicial).
- atualização que falhou não chega aqui (o bridge só chama no caminho de sucesso).
"""

INTERVALO_REPETICAO = 600   # 10 min: o mesmo amigo não avisa de novo antes disso
MAXIMO_INDIVIDUAIS = 3      # acima disso vira um aviso só ("N amigos entraram")

STATUS_DESCONHECIDO = ""


def esta_no_jogo(platform, location):
    """True quando o amigo está no cliente/jogo — False para web e para 'sumido'."""
    plat = (platform or "").strip().lower()
    loc = (location or "").strip().lower()
    if plat == "web":
        return False
    if loc.startswith("wrld_"):
        return True
    return bool(plat)   # cliente aberto (menu da plataforma), mesmo fora de mundo


def snapshot(friends):
    """{id: {"name", "no_jogo", "world", "avatar"}} — a foto usada na próxima comparação."""
    foto = {}
    for f in friends:
        foto[f.id] = {
            "name": f.name or "?",
            "no_jogo": esta_no_jogo(f.platform, f.location),
            "world": f.world or "",
            "avatar": f.avatar or "",
        }
    return foto


def entradas_novas(anterior, atual):
    """Quem passou de 'fora do jogo' para 'no jogo'.

    `anterior is None` = primeira carga: aprende a foto e não avisa ninguém.
    """
    if anterior is None:
        return []
    novos = []
    for uid, dados in (atual or {}).items():
        if not dados.get("no_jogo"):
            continue
        antes = anterior.get(uid)
        if antes is not None and antes.get("no_jogo"):
            continue      # já estava no jogo; não é entrada
        novos.append({
            "id": uid,
            "name": dados.get("name") or "?",
            "world": dados.get("world") or "",
            "avatar": dados.get("avatar") or "",
        })
    return sorted(novos, key=lambda d: d["name"].casefold())


def filtrar_intervalo(novos, ultimo_aviso, agora, intervalo=INTERVALO_REPETICAO):
    """Descarta quem já avisou faz menos de `intervalo` segundos."""
    return [d for d in novos if agora - (ultimo_aviso.get(d["id"]) or 0) >= intervalo]


def agrupar(novos, favoritos=None):
    """Até MAXIMO_INDIVIDUAIS avisos; acima disso, um resumo único.

    Cada aviso sai pronto para o QML: `favorito` decide a cor do cartão (accent
    para favorito, cinza padrão para o resto) e `agregado` marca o resumo.
    """
    favoritos = favoritos or {}
    if not novos:
        return []
    if len(novos) > MAXIMO_INDIVIDUAIS:
        return [{
            "id": "",
            "name": "",
            "world": "",
            "avatar": "",
            "favorito": any(d["id"] in favoritos for d in novos),
            "agregado": len(novos),
            "texto": f"{len(novos)} amigos entraram",
        }]
    return [{
        "id": d["id"],
        "name": d["name"],
        "world": d.get("world") or "",
        "avatar": d.get("avatar") or "",
        "favorito": d["id"] in favoritos,
        "agregado": 0,
        "texto": "",
    } for d in novos]
