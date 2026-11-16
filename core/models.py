"""Modelos de dados que as duas UIs consomem. Sem dependencia de toolkit."""

from dataclasses import dataclass, field

from .formatting import STATUS_LABELS, STATUS_ORDER


@dataclass
class Friend:
    """Um amigo online, como a lista precisa dele."""

    id: str
    name: str
    status: str = "active"
    world: str = "—"
    platform: str = ""
    location: str = ""
    active: str = ""
    avatar: str | None = None  # caminho do PNG redondo em disco
    icon_url: str = ""         # iconUrl da API (origem do avatar)
    # quantas pessoas na instancia. `occupants` = numero que a API informou;
    # `presentes` = quantos amigos NOSSOS estao la (piso honesto quando a API
    # devolve userCount=0 em instancia de grupo, que e o caso comum)
    occupants: int | None = None
    capacity: int | None = None
    presentes: int = 0

    @property
    def occupants_label(self):
        """'17/32', '8' ou '1+/80' — vazio quando nao ha o que mostrar.

        O '+' existe porque a API devolve userCount=0 para instancias de grupo mesmo
        com gente dentro (ver ESTADO). Mostrar "1" seco seria afirmar um numero que
        nao sabemos; "1+" diz "pelo menos os nossos".
        """
        if self.occupants:
            num = str(self.occupants)
        elif self.presentes:
            num = f"{self.presentes}+"
        else:
            return ""
        return f"{num}/{self.capacity}" if self.capacity else num

    @property
    def status_label(self):
        return STATUS_LABELS.get(self.status, self.status)

    @property
    def clock(self):
        """('Online', 'Furry Hangout · público · JP') — o que a linha mostra."""
        return self.status_label, self.world or "—"

    @property
    def on_web(self):
        """Logado só no site, sem cliente aberto.

        É o que a linha desenha como bolinha VAZADA (anel) em vez de cheia: o
        preenchimento diz "está num cliente/jogo", o anel diz "só na web".
        """
        return (self.platform or "").strip().lower() == "web"

    def as_dict(self):
        """Para quem prefere dict (QML, JSON, log)."""
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "status_label": self.status_label,
            "world": self.world,
            "platform": self.platform,
            "web": self.on_web,
            "location": self.location,
            "active": self.active,
            "avatar": self.avatar,
            "icon_url": self.icon_url,
            "occupants": self.occupants,
            "capacity": self.capacity,
            "presentes": self.presentes,
            "occupants_label": self.occupants_label,
        }


def sort_friends(friends):
    """join me -> ask me -> active -> busy, depois nome (case-insensitive)."""
    return sorted(
        friends,
        key=lambda f: (STATUS_ORDER.get(f.status, 4), f.name.lower()),
    )


@dataclass
class Profile:
    """Perfil de um usuario (amigo ou eu). So o que a API entrega de verdade.

    A API nao devolve mais `bio`/`bioLinks` — o campo sumiu do objeto de usuario.
    O que existe: statusDescription, pronouns, datas, tags (idiomas + confianca)
    e a nota privada que VOCE escreveu sobre aquele amigo.
    """

    id: str = ""
    name: str = ""
    status: str = "active"
    status_description: str = ""
    pronouns: str = ""
    platform: str = ""
    world: str = ""
    location: str = ""
    joined: str = ""
    last_login: str = ""
    languages: list[str] = field(default_factory=list)
    trust: str = ""
    note: str = ""
    avatar: str | None = None
    icon_url: str = ""
    profile_url: str = ""
    is_friend: bool = True

    @property
    def status_label(self):
        return STATUS_LABELS.get(self.status, self.status)

    @property
    def languages_text(self):
        return ", ".join(self.languages) if self.languages else ""

    def as_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "status_label": self.status_label,
            "status_description": self.status_description,
            "pronouns": self.pronouns,
            "platform": self.platform,
            "world": self.world,
            "location": self.location,
            "joined": self.joined,
            "last_login": self.last_login,
            "languages": list(self.languages),
            "languages_text": self.languages_text,
            "trust": self.trust,
            "note": self.note,
            "avatar": self.avatar,
            "icon_url": self.icon_url,
            "profile_url": self.profile_url,
            "is_friend": self.is_friend,
        }


@dataclass
class Session:
    """Estado de sessao que a UI precisa saber (sem carregar o client inteiro)."""

    logged_in: bool = False
    display_name: str = ""
    pending_2fa_types: list[str] = field(default_factory=list)
    login_hint: str = ""
