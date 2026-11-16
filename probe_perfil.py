# -*- coding: utf-8 -*-
"""Só leitura: quais campos existem no amigo (lista) x perfil completo x meu usuário."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.service import VRChatService  # noqa: E402

svc = VRChatService()
print("sessao restaurada:", svc.restore())
amigos = svc.fetch_friends()
print("amigos online:", len(amigos))

if amigos:
    alvo = amigos[0]
    print("\n== campo extra na lista? bio:", getattr(alvo, "bio", "<nao existe>"))
    resp = svc.client._request("GET", f"/users/{alvo.id}", params=svc.client._params())
    print("GET /users/{id} ->", resp.status_code)
    if resp.ok:
        perfil = resp.json()
        campos = sorted(perfil.keys())
        print("campos:", ", ".join(campos))
        for c in ("displayName", "status", "statusDescription", "bio", "pronouns", "bioLinks",
                  "platform", "last_login", "date_joined", "tags", "isFriend", "iconUrl",
                  "currentAvatarImageUrl", "location"):
            if c in perfil:
                v = perfil[c]
                print(f"   {c} = {str(v)[:120]}")

me_resp = svc.client._request("GET", "/auth/user", params=svc.client._params())
print("\n== /auth/user ->", me_resp.status_code)
if me_resp.ok:
    me = me_resp.json()
    for c in ("displayName", "status", "statusDescription", "bio", "pronouns", "bioLinks",
              "platform", "last_login", "date_joined", "tags", "iconUrl"):
        if c in me:
            print(f"   {c} = {str(me[c])[:140]}")
