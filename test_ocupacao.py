# -*- coding: utf-8 -*-
"""Ocupação de instância pública + rótulo de quem está online fora de mundo.

Roda com sessão falsa (sem credenciais): prova qual endpoint foi chamado, que a
consulta é UMA por instância (amigos no mesmo mundo dividem) e que instância
fechada não inventa número.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.service import VRChatService  # noqa: E402
from core.vrchat import VRChatClient  # noqa: E402

FRIENDS = [
    # mesma instância pública, dois amigos
    {"id": "usr_1", "displayName": "Ana", "status": "active", "platform": "standalonewindows",
     "location": "wrld_a:1234~region(us)", "last_activity": "2026-11-14T21:00:00Z",
     "iconUrl": ""},
    {"id": "usr_2", "displayName": "Bia", "status": "active", "platform": "standalonewindows",
     "location": "wrld_a:1234~region(us)", "last_activity": "2026-11-14T21:00:00Z",
     "iconUrl": ""},
    # instância privada: sem consulta
    {"id": "usr_3", "displayName": "Caio", "status": "join me", "platform": "standalonewindows",
     "location": "wrld_b:999~private(usr_x)~region(eu)", "last_activity": "2026-11-14T21:00:00Z",
     "iconUrl": ""},
    # instância de grupo: API responde 200 mas com userCount 0 (medido na conta real)
    {"id": "usr_6", "displayName": "Fabio Grupo", "status": "active",
     "platform": "standalonewindows",
     "location": "wrld_c:90508~group(grp_0a2230f4-99f0-4d0e-9a4f-1111aaaa2222)~region(us)",
     "last_activity": "2026-11-14T21:00:00Z", "iconUrl": ""},
    # online, fora de mundo: na web e no menu
    {"id": "usr_4", "displayName": "Duda", "status": "active", "platform": "web",
     "location": "offline", "last_activity": "2026-11-14T21:00:00Z", "iconUrl": ""},
    {"id": "usr_5", "displayName": "Edu", "status": "active", "platform": "android",
     "location": "offline", "last_activity": "2026-11-14T21:00:00Z", "iconUrl": ""},
]


class Resp:
    def __init__(self, status, payload):
        self.status_code = status
        self._payload = payload
        self.headers = {}

    @property
    def ok(self):
        return 200 <= self.status_code < 300

    def json(self):
        return self._payload

    def raise_for_status(self):
        if not self.ok:
            raise RuntimeError(f"HTTP {self.status_code}")


class SessaoFalsa:
    headers = {}
    cookies = {}

    def __init__(self):
        self.urls = []

    def request(self, method, url, **kwargs):
        self.urls.append(url)
        if "/auth/user/friends" in url:
            return Resp(200, FRIENDS)
        if "/worlds/wrld_a/1234" in url:
            return Resp(200, {"userCount": 17, "capacity": 32, "type": "public"})
        if "/worlds/wrld_c/90508" in url:
            # caso real: instância de grupo responde 200 com userCount 0
            return Resp(200, {"userCount": 0, "n_users": 0, "capacity": 80, "type": "public"})
        if url.endswith("/worlds/wrld_c"):
            return Resp(200, {"name": "Cruzeiro Brasil"})
        if "/worlds/wrld_b/" in url:
            return Resp(403, {})          # instância fechada
        if url.endswith("/worlds/wrld_a"):
            return Resp(200, {"name": "The Great Pug"})
        if url.endswith("/worlds/wrld_b"):
            return Resp(200, {"name": "Mundo Fechado"})
        return Resp(404, {})


def main():
    sess = SessaoFalsa()
    cliente = VRChatClient()
    cliente.session = sess
    cliente.api_key = "chave_falsa"
    service = VRChatService(client=cliente)

    amigos = service.fetch_friends()
    por_nome = {a.name: a for a in amigos}

    falhas = 0

    def check(nome, cond, detalhe=""):
        nonlocal falhas
        print(("OK  " if cond else "FALHA") + "  " + nome + (f"  [{detalhe}]" if detalhe else ""))
        if not cond:
            falhas += 1

    ana = por_nome["Ana"]
    bia = por_nome["Bia"]
    caio = por_nome["Caio"]
    duda = por_nome["Duda"]
    edu = por_nome["Edu"]
    fabio = por_nome["Fabio Grupo"]

    check("ocupação na instância pública (17/32)",
          ana.occupants == 17 and ana.capacity == 32,
          f"{ana.occupants}/{ana.capacity}")
    check("rótulo de ocupação", ana.occupants_label == "17/32", ana.occupants_label)
    check("amigo no mesmo mundo tem o mesmo número", bia.occupants == 17, str(bia.occupants))
    check("instância privada não mostra número", caio.occupants is None, str(caio.occupants))
    # instância pública com região legítima mostra "The Great Pug · US"
    check("world do público é o nome do mundo",
          ana.world.startswith("The Great Pug"), ana.world)
    check("sufixo só de região (não é restrição)",
          "privado" not in ana.world and "amigos" not in ana.world, ana.world)
    check("world do privado com sufixo", "privado" in caio.world, caio.world)

    check("instância de grupo: userCount 0 vira piso '1+/80'",
          fabio.occupants_label == "1+/80", fabio.occupants_label)
    check("capacidade lida mesmo sem contagem", fabio.capacity == 80, str(fabio.capacity))

    check("online fora de mundo na web", duda.world == "na web", duda.world)
    check("online fora de mundo no menu", edu.world == "no menu", edu.world)

    consultas = [u for u in sess.urls if "/worlds/wrld_a/1234" in u]
    check("uma consulta por instância (não por amigo)", len(consultas) == 1, str(len(consultas)))
    privadas = [u for u in sess.urls if "/worlds/wrld_b/" in u]
    check("não consulta instância privada", not privadas, str(privadas))

    d = ana.as_dict()
    check("as_dict leva ocupação", d.get("occupants") == 17 and d.get("occupants_label") == "17/32",
          str(d.get("occupants_label")))

    print(f"\n{len(amigos)} amigos, {len(sess.urls)} requisições")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
