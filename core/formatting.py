"""Traducao de dados da API para texto de tela. Sem Tk, sem QML."""

import time
from datetime import datetime, timezone

# rotulos de status sao os oficiais do VRChat (nao traduzir)
STATUS_LABELS = {
    "active": "Online",
    "join me": "Join Me",
    "ask me": "Ask Me",
    "busy": "Busy",
    "offline": "Offline",
}

# ordem da lista: quem chama primeiro
STATUS_ORDER = {"join me": 0, "ask me": 1, "active": 2, "busy": 3}

# a API recusa statusDescription maior que isto (HTTP 400). O corte e feito no
# cliente e no QML: limitar so na tela deixaria passar texto colado.
STATUS_DESCRIPTION_MAX = 32

PLATFORM_LABELS = {
    "standalonewindows": "PC",
    "android": "Quest",
    "ios": "iOS",
    "web": "Web",
}

METHOD_LABELS = {
    "emailOtp": "código do email",
    "totp": "app autenticador",
    "otp": "código de recuperação",
}

TYPE_ENDPOINTS = {
    "emailOtp": "/auth/twofactorauth/emailotp/verify",
    "totp": "/auth/twofactorauth/totp/verify",
    "otp": "/auth/twofactorauth/otp/verify",
}

HINT_CREDS = (
    "A senha é usada uma única vez para criar a sessão; só o cookie\n"
    "de sessão fica salvo nesta máquina."
)
HINT_EMAIL = (
    "Enviamos 6 dígitos para o e-mail da conta. Sem código em ~1 min,\n"
    "confira o spam ou use “Reenviar”."
)
HINT_TOTP = "Digite o código de 6 dígitos do seu app autenticador."
HINT_OTP = "Digite um dos seus códigos de recuperação do VRChat."


LANGUAGES = {
    "language_eng": "Inglês", "language_por": "Português", "language_spa": "Espanhol",
    "language_jpn": "Japonês", "language_fra": "Francês", "language_deu": "Alemão",
    "language_ita": "Italiano", "language_kor": "Coreano", "language_rus": "Russo",
    "language_zho": "Chinês", "language_ara": "Árabe", "language_hin": "Hindi",
    "language_nld": "Holandês", "language_pol": "Polonês", "language_swe": "Sueco",
    "language_tha": "Tailandês", "language_tur": "Turco", "language_ukr": "Ucraniano",
    "language_vie": "Vietnamita",
}

# do mais alto para o mais baixo: o primeiro que aparecer nas tags vence
TRUST_ORDER = [
    ("system_trust_veteran", "Veteran"),
    ("system_trust_trusted", "Trusted"),
    ("system_trust_known", "Known"),
    ("system_trust_intermediate", "Intermediate"),
    ("system_trust_basic", "Basic"),
]


PLATFORM_LABELS = {
    "web": "Site",
    "standalonewindows": "PC",
    "android": "Quest",
    "ios": "iOS",
    "linux": "Linux",
}


def platform_label(code):
    return PLATFORM_LABELS.get((code or "").lower(), (code or "").capitalize())


def languages_from_tags(tags):
    return [LANGUAGES[t] for t in (tags or []) if t in LANGUAGES]


def trust_from_tags(tags):
    tags = tags or []
    for chave, rotulo in TRUST_ORDER:
        if chave in tags:
            return rotulo
    return ""


def format_date(iso):
    """'2023-08-22' -> '22/08/2023'."""
    if not iso:
        return ""
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).strftime("%d/%m/%Y")
    except Exception:
        return iso[:10]


def format_last_login(iso):
    """'hoje 20:31' / 'ontem 22:10' / '14/11/2026'."""
    if not iso:
        return ""
    try:
        ts = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone()
    except Exception:
        return ""
    hoje = datetime.now().astimezone().date()
    delta = (hoje - ts.date()).days
    if delta == 0:
        return f"hoje {ts.strftime('%H:%M')}"
    if delta == 1:
        return f"ontem {ts.strftime('%H:%M')}"
    return ts.strftime("%d/%m/%Y")


def hint_for(method):
    return {"totp": HINT_TOTP, "otp": HINT_OTP}.get(method, HINT_EMAIL)


def _delta_legivel(segundos):
    """Segundos -> 'agora' / '12 min' / '3 h' / '2 d'."""
    if segundos < 90:
        return "agora"
    minutos = segundos / 60
    if minutos < 60:
        return f"{int(minutos)} min"
    horas = minutos / 60
    if horas < 24:
        return f"{int(horas)} h"
    return f"{int(horas / 24)} d"


def humanize_delta(iso_ts):
    """'ha 12 min' a partir de um timestamp ISO da API."""
    if not iso_ts:
        return ""
    try:
        ts = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
    except Exception:
        return ""
    delta = (datetime.now(timezone.utc) - ts).total_seconds()
    return _delta_legivel(delta)


def humanize_epoch(ts, agora=None):
    """Mesmo texto do humanize_delta, mas a partir de um epoch (favoritos guardam assim)."""
    if not ts:
        return ""
    try:
        ts = float(ts)
    except (TypeError, ValueError):
        return ""
    agora = time.time() if agora is None else float(agora)
    return _delta_legivel(max(0.0, agora - ts))


# "offline" aqui NAO quer dizer desconectado: a lista so mostra quem esta online.
# Significa "logado, mas fora de um mundo" — de onde ele esta: site, ou o app aberto
# no menu. "fora do jogo" era confuso (o usuario esta no jogo/app, so nao numa instancia).
OFFLINE_LABELS = {
    "web": "na web",
    "standalonewindows": "no menu",
    "android": "no menu",
    "ios": "no menu",
}


def offline_label(platform=""):
    """Rotulo curto para quem esta online mas fora de um mundo."""
    return OFFLINE_LABELS.get((platform or "").lower(), "fora do mundo")


def instance_ids(location):
    """(world_id, instance_id) de 'wrld_x:12345~region(us)~...' — (None, None) fora disso."""
    if not location or not location.startswith("wrld_"):
        return None, None
    world_id, _, resto = location.partition(":")
    instance_id = resto.split("~")[0]
    return world_id, instance_id or None


# marcas que tornam a instancia fechada (mesmo com region/regiao junto)
RESTRICOES = ("~private", "~friends", "~hidden", "~group", "canrequestinvite")


def is_public_location(location):
    """Instancia publica = location de mundo SEM marca de restricao.

    Nao da para decidir pelo rotulo: uma instancia publica com regiao vira
    "público · US" no describe_location e uma publica sem nada vira "público".
    Por isso a checagem e sobre as marcas no proprio location.
    """
    if not location or not location.startswith("wrld_"):
        return False
    low = location.lower()
    return not any(marca in low for marca in RESTRICOES)


def describe_location(location, platform=""):
    """Traduz 'wrld_x:123~region(us)~private(...)' em (world_id, sufixo legivel)."""
    if not location:
        return None, "desconhecido"
    if not location.startswith("wrld_"):
        if location == "offline":
            return None, offline_label(platform)
        mapping = {
            "private": "mundo privado",
            "traveling": "viajando",
        }
        return None, mapping.get(location, location)

    world_id, _, instance = location.partition(":")
    tags = []
    low = instance.lower()
    # Tabela oficial (vrchat.community, guia de instâncias):
    #   ~hidden(<id>)  -> Friends+      ~friends(<id>) -> Friends
    #   ~private(<id>) -> Invite        + canRequestInvite -> Invite+
    #   ~group(<id>)   -> Group         (+ groupAccessType public/plus/members)
    # Os dois primeiros estavam TROCADOS aqui: quem estava numa instância Friends+
    # (que traz ~hidden) aparecia como "amigos".
    if "~private(" in low or "~private" == low:
        tags.append("privado")
    elif "~hidden(" in low:
        tags.append("amigos+")   # Friends+ = amigos de amigos podem entrar
    elif "~friends(" in low:
        tags.append("amigos")    # Friends = só amigos
    elif "~group(" in low:
        tags.append("grupo")
    else:
        # sem marcador = instância pública. Antes, quando havia região, o rótulo
        # saía só "US" e o "público" sumia da lista.
        tags.append("público")
    if "canrequestinvite" in low:
        tags.append("convite")
    for region in ("us", "eu", "jp"):
        if f"region({region})" in low:
            tags.append(region.upper())
            break
    return world_id, " · ".join(tags) if tags else "público"
