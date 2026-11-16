# -*- coding: utf-8 -*-
"""So leitura: quais campos de imagem a API devolve para amigos online."""
import json, os, sys
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vrchat_friends as m

data = m.load_json(m.SESSION_FILE, None) or {}
print("tem sessao salva:", bool(data.get("cookies")))

s = requests.Session()
s.headers.update({"User-Agent": m.UA, "Accept": "application/json"})
s.cookies.update(data.get("cookies") or {})
api_key = data.get("api_key")

params = {"offline": "false", "n": 100}
if api_key:
    params["apiKey"] = api_key
r = s.get(m.API + "/auth/user/friends", params=params, timeout=20)
print("HTTP", r.status_code)
if not r.ok:
    print(r.text[:300]); sys.exit()

friends = r.json()
print("amigos online:", len(friends))
if friends:
    print("\ncampos do objeto:", ", ".join(sorted(friends[0].keys())))
campos_img = [k for k in (friends[0].keys() if friends else []) if "mage" in k or "Icon" in k or "Pic" in k]
print("\ncampos de imagem:", campos_img)
for f in friends[:5]:
    print("\n--", f.get("displayName"), f.get("status"))
    for k in campos_img:
        print(f"   {k} = {f.get(k)}")
    for k in ("profilePicOverrideThumbnail", "profilePicOverride", "currentAvatarThumbnailImageUrl",
              "currentAvatarImageUrl", "userIcon", "fallbackAvatar"):
        if k in f:
            print(f"   [{k}] {str(f.get(k))[:120]}")
