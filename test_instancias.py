# -*- coding: utf-8 -*-
"""Tipo de instância a partir do `location` — tabela oficial do VRChat.

Fonte: vrchat.community, guia de instâncias.
    Público        (sem marcador)
    Friends+       ~hidden(<userId>)
    Friends        ~friends(<userId>)
    Invite         ~private(<userId>)
    Invite+        ~private(<userId>)~canRequestInvite
    Grupo          ~group(<groupId>)~groupAccessType(public|plus|members)

Sem rede. Uso: python -B test_instancias.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.formatting import describe_location, is_public_location  # noqa: E402

falhas = []


def check(nome, cond, extra=""):
    print(("OK   " if cond else "FALHA") + f"  {nome}" + (f"  [{extra}]" if extra else ""))
    if not cond:
        falhas.append(nome)


def tipo(instance):
    world, tag = describe_location("wrld_4432ea9b-729c-46e3-8eaf-846aa0a37fdd:" + instance)
    return tag, world


# ---------------------------------------------------------------- tabela oficial
casos = [
    ("12345", "público", "Público"),
    ("12345~region(us)", "público · US", "Público com região"),
    ("12345~hidden(usr_c1644b5b)~region(eu)", "amigos+ · EU", "Friends+ (~hidden)"),
    ("12345~friends(usr_c1644b5b)", "amigos", "Friends (~friends)"),
    ("12345~friends(usr_c1644b5b)~region(jp)", "amigos · JP", "Friends com região"),
    ("12345~private(usr_c1644b5b)", "privado", "Invite (~private)"),
    ("12345~private(usr_c1644b5b)~canRequestInvite", "privado · convite", "Invite+"),
    ("12345~group(grp_1234)~groupAccessType(public)", "grupo", "Grupo público"),
    ("12345~group(grp_1234)~groupAccessType(plus)", "grupo", "Grupo+"),
    ("12345~group(grp_1234)~groupAccessType(members)", "grupo", "Grupo (membros)"),
    ("12345~hidden(usr_x)~nonce(27e8414a-59a0-4f3d-af1f-f27557eb49a2)",
     "amigos+", "Friends+ com nonce"),
]

for instance, esperado, nome in casos:
    tag, world = tipo(instance)
    check(f"{nome}: '{esperado}'", tag == esperado, f"veio '{tag}'")
    check(f"{nome}: id do mundo", world.startswith("wrld_4432ea9b"), str(world))

# o caso que motivou o conserto: amigos em Friends+ apareciam como "amigos"
tag_friends_plus, _ = tipo("12345~hidden(usr_c1644b5b)~region(us)")
check("Friends+ NÃO é rotulado só como amigos", "amigos+" in tag_friends_plus, tag_friends_plus)
tag_friends, _ = tipo("12345~friends(usr_c1644b5b)")
check("Friends NÃO ganha '+'", tag_friends == "amigos", tag_friends)

# ---------------------------------------------------------------- fora de mundo
for location, platform, esperado, nome in [
    ("offline", "web", "na web", "online na web"),
    ("offline", "standalonewindows", "no menu", "online no menu"),
    ("offline", "android", "no menu", "online no menu (Quest)"),
    ("traveling", "", "viajando", "viajando entre mundos"),
    ("private", "", "mundo privado", "localização oculta"),
    ("", "", "desconhecido", "sem location"),
]:
    _, tag = describe_location(location, platform)
    check(f"{nome}: '{esperado}'", tag == esperado, f"veio '{tag}'")

# ---------------------------------------------------------------- instância pública
check("público é público", is_public_location("wrld_x:1234~region(us)"))
check("Friends+ não é público", not is_public_location("wrld_x:1234~hidden(usr_1)"))
check("Friends não é público", not is_public_location("wrld_x:1234~friends(usr_1)"))
check("Invite não é público", not is_public_location("wrld_x:1234~private(usr_1)"))
check("Grupo não é público", not is_public_location("wrld_x:1234~group(grp_1)"))

# ---------------------------------------------------------------- caminho real (service)
from core.service import VRChatService  # noqa: E402


class ClienteFalso:
    me = {"id": "usr_eu", "displayName": "aryaah"}

    def fetch_online_friends(self):
        return [
            {"id": "u1", "displayName": "Ana", "status": "active",
             "platform": "standalonewindows", "location": "wrld_a:1234~hidden(usr_1)~region(us)",
             "iconUrl": ""},
            {"id": "u2", "displayName": "Bia", "status": "active",
             "platform": "standalonewindows", "location": "wrld_a:1234~friends(usr_1)~region(us)",
             "iconUrl": ""},
            {"id": "u3", "displayName": "Caio", "status": "active",
             "platform": "standalonewindows", "location": "wrld_a:1234~region(eu)",
             "iconUrl": ""},
        ]

    def world_name(self, wid):
        return "The Black Cat"

    def instance_occupancy(self, *a, **k):
        return (5, 16)

    def flush_world_cache(self):
        pass

    def avatar_path(self, *a, **k):
        return None


svc = VRChatService(client=ClienteFalso())
por_nome = {a.name: a for a in svc.fetch_friends()}
check("Friends+ na lista: 'The Black Cat · amigos+ · US'",
      por_nome["Ana"].world == "The Black Cat · amigos+ · US", por_nome["Ana"].world)
check("Friends na lista: 'The Black Cat · amigos · US'",
      por_nome["Bia"].world == "The Black Cat · amigos · US", por_nome["Bia"].world)
check("público na lista: 'The Black Cat · público · EU'",
      por_nome["Caio"].world == "The Black Cat · público · EU", por_nome["Caio"].world)


print()
print("FALHAS:", falhas if falhas else "nenhuma")
sys.exit(1 if falhas else 0)
