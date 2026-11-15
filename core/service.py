"""Fachada que as duas UIs usam. Toda regra de dados vive aqui, nunca na interface.

Fluxo tipico (igual em Tkinter e QML):

    svc = VRChatService()
    if not svc.restore():            # mostra login
        ...
    amigos = svc.fetch_friends()     # list[Friend] ja ordenado
    icones = svc.fetch_avatars(amigos, size=20)   # dict[id, caminho]
"""

from .formatting import (
    describe_location,
    instance_ids,
    format_date,
    format_last_login,
    humanize_delta,
    languages_from_tags,
    trust_from_tags,
)
from .models import Friend, Profile, sort_friends
from .paths import REFRESH_SECONDS  # reexportado: a UI agenda o refresh com isto
from .vrchat import VRChatClient

__all__ = ["VRChatService", "ApiError", "Friend", "Profile", "REFRESH_SECONDS"]

# teto de instancias consultadas por refresh: cada uma custa 1 requisicao e a API
# derruba quem faz rajada (429). Amigos no mesmo mundo dividem a mesma consulta.
MAX_INSTANCIAS = 12


class ApiError(Exception):
    """Falha de rede/API ja traduzida: a UI so mostra a mensagem."""


class VRChatService:
    def __init__(self, client=None):
        self.client = client or VRChatClient()
        self._profiles = {}   # id -> Profile (o perfil completo custa 1 requisicao)
        self._me_completo = None   # objeto cru de /users/{meu id}

    # ---------- sessao ----------
    def restore(self):
        return self.client.restore_session()

    @property
    def display_name(self):
        return (self.client.me or {}).get("displayName", "") or ""

    @property
    def pending_types(self):
        return list(self.client.pending_types)

    def login(self, username, password):
        return self.client.login(username, password)

    def verify(self, code, method="emailOtp"):
        return self.client.verify_2fa(code, method)

    # ---------- dados ----------
    def fetch_friends(self):
        """Uma lista, uma requisicao por pagina, + 1 por mundo novo (cache).

        Levanta PermissionError se a sessao caiu e ApiError para o resto;
        a UI nao precisa conhecer `requests`.
        """
        try:
            raw = self.client.fetch_online_friends()
        except PermissionError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ApiError(str(exc)) from exc

        # 1) quem esta em qual instancia: 1 consulta por instancia (amigos no mesmo
        #    mundo dividem) e o numero de amigos nossos vira piso quando a API omite.
        por_instancia = {}   # (world, instance) -> {"n": amigos, "privada": bool}
        for f in raw:
            loc = f.get("location") or ""
            chave = instance_ids(loc)
            if not (chave[0] and chave[1]):
                continue
            registro = por_instancia.setdefault(chave, {"n": 0, "privada": False})
            registro["n"] += 1
            if "~private" in loc.lower():
                registro["privada"] = True

        # privada nao responde nada util (403): nem consulta
        abertas = [c for c, d in por_instancia.items() if not d["privada"]]
        info = {}
        for chave in abertas[:MAX_INSTANCIAS]:
            info[chave] = self.client.instance_occupancy(*chave)

        rows = []
        for f in raw:
            loc = f.get("location") or ""
            plat = f.get("platform") or ""
            wid, tag = describe_location(loc, plat)
            world = self.client.world_name(wid) if wid else tag
            if wid and tag and tag != "público":
                world = f"{world} · {tag}" if world else tag

            chave = instance_ids(loc)
            dados = info.get(chave) or (None, None)
            presentes = por_instancia.get(chave, {}).get("n", 0)

            rows.append(
                Friend(
                    id=f.get("id") or "",
                    name=f.get("displayName") or f.get("username") or "?",
                    status=f.get("status") or "active",
                    world=world or tag or "—",
                    platform=plat,
                    location=loc,
                    active=humanize_delta(f.get("last_activity")),
                    icon_url=f.get("iconUrl") or f.get("currentAvatarImageUrl") or "",
                    occupants=dados[0],
                    capacity=dados[1],
                    presentes=presentes,
                )
            )
        self.client.flush_world_cache()
        return sort_friends(rows)

    # ---------- perfil ----------
    def fetch_profile(self, friend, size=96, force=False):
        """Perfil completo do amigo: 1 requisicao, cacheada por id.

        A lista de amigos vem reduzida (sem statusDescription/pronouns/datas),
        por isso a busca sob demanda — e so quando o popup abre.
        """
        if not force and friend.id in self._profiles:
            return self._profiles[friend.id]
        try:
            raw = self.client.get_user(friend.id)
        except PermissionError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ApiError(str(exc)) from exc
        perfil = self._montar_perfil(raw, size=size, world=friend.world)
        self._profiles[friend.id] = perfil
        return perfil

    def update_me(self, status=None, status_description=None):
        """Muda meu status/bio no VRChat e devolve o perfil novo."""
        try:
            self.client.update_me(status=status, status_description=status_description)
        except PermissionError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ApiError(str(exc)) from exc
        self._me_completo = None
        return self.my_profile(force=True)

    def my_profile(self, size=96, force=False):
        """Eu mesmo, com dado ATUAL (1 requisicao, cacheada ate salvar algo).

        Antes isto usava `client.me` (o retrato de /auth/user no login): status e
        mensagem ficavam velhos, e o painel abria vazio mesmo com o perfil preenchido.
        `/users/{id}` devolve o mesmo objeto com os campos frescos.
        """
        uid = (self.client.me or {}).get("id")
        if force or self._me_completo is None:
            if uid:
                try:
                    self._me_completo = self.client.get_user(uid) or {}
                except Exception:          # noqa: BLE001 - perfil e opcional
                    self._me_completo = dict(self.client.me or {})
            else:
                self._me_completo = dict(self.client.me or {})
        return self._montar_perfil(self._me_completo, size=size, sou_eu=True)

    def _montar_perfil(self, raw, size=96, world="", sou_eu=False):
        icon = raw.get("iconUrl") or ""
        uid = raw.get("id") or ""
        avatar = None
        if icon and uid:
            avatar = self.client.avatar_path(icon, uid, size=size)
        loc = raw.get("location") or ""
        return Profile(
            id=uid,
            name=raw.get("displayName") or raw.get("username") or "?",
            status=raw.get("status") or "active",
            status_description=(raw.get("statusDescription") or "").strip(),
            pronouns=(raw.get("pronouns") or "").strip(),
            platform=raw.get("platform") or raw.get("last_platform") or "",
            world=world or describe_location(loc)[1],
            location=loc,
            joined=format_date(raw.get("date_joined") or ""),
            last_login=format_last_login(raw.get("last_login") or ""),
            languages=languages_from_tags(raw.get("tags")),
            trust=trust_from_tags(raw.get("tags")),
            note=(raw.get("note") or "").strip(),
            avatar=avatar,
            icon_url=icon,
            profile_url=f"https://vrchat.com/home/user/{uid}" if uid else "",
            is_friend=bool(raw.get("isFriend", True)) and not sou_eu,
        )

    def fetch_avatars(self, friends, size=20):
        """Baixa o que faltar e devolve {id: caminho}. Nunca levanta excecao."""
        out = {}
        for f in friends:
            if not f.icon_url:
                continue
            caminho = self.client.avatar_path(f.icon_url, f.id, size=size)
            if caminho:
                f.avatar = caminho
                out[f.id] = caminho
        return out
