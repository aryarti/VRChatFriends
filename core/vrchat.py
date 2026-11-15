"""Cliente HTTP da API do VRChat. Somente leitura: nenhum endpoint de escrita
(nao entra em mundo, nao convida, nao manda mensagem)."""

import base64
import os
import sys
import time
import urllib.parse

import requests

from .formatting import TYPE_ENDPOINTS
from .paths import API, AVATARS_DIR, SESSION_FILE, UA, WORLD_CACHE
from .store import load_json, save_json


class VRChatClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": UA, "Accept": "application/json"})
        self.api_key = None
        self.me = None
        self.pending_types = []
        self._pending_2fa = False
        self.worlds = load_json(WORLD_CACHE, {})
        self._worlds_dirty = False
        # ocupacao de instancia muda rapido: cache curto, so em memoria
        self._instances = {}   # "wrld_x:123" -> (ts, (occupants, capacity))

    # -- infra
    def _params(self, extra=None):
        p = {}
        if self.api_key:
            p["apiKey"] = self.api_key
        if extra:
            p.update(extra)
        return p

    def _request(self, method, path, **kwargs):
        kwargs.setdefault("timeout", 20)
        resp = None
        for _attempt in range(3):
            resp = self.session.request(method, API + path, **kwargs)
            if resp.status_code == 429:
                wait = int(resp.headers.get("X-RateLimit-Reset") or 5)
                time.sleep(max(2, min(wait, 20)))
                continue
            return resp
        return resp

    def load_config(self):
        try:
            resp = self.session.get(API + "/config", timeout=15)
            if resp.ok:
                self.api_key = resp.json().get("clientApiKey")
        except Exception:
            pass

    # -- sessao
    def restore_session(self):
        data = load_json(SESSION_FILE, None)
        if not data or not data.get("cookies"):
            return False
        self.session.cookies.update(data["cookies"])
        if data.get("api_key"):
            self.api_key = data["api_key"]
        try:
            me = self.current_user()
        except Exception:
            return False
        return bool(me)

    def persist_session(self):
        save_json(
            SESSION_FILE,
            {
                "cookies": requests.utils.dict_from_cookiejar(self.session.cookies),
                "api_key": self.api_key,
            },
        )

    def login(self, username, password):
        """Retorna (ok, precisa_2fa, mensagem)."""
        if not self.api_key:
            self.load_config()
        token = f"{urllib.parse.quote(username, safe='')}:{urllib.parse.quote(password, safe='')}"
        self.session.headers["Authorization"] = "Basic " + base64.b64encode(token.encode()).decode()
        try:
            resp = self._request("GET", "/auth/user", params=self._params())
        except requests.RequestException as exc:
            return False, False, f"Sem conexao com a API do VRChat.\n{exc}"

        self.session.headers.pop("Authorization", None)

        if resp.status_code == 401:
            return False, False, "Usuario ou senha incorretos."
        if resp.status_code == 429:
            return False, False, "Muitas tentativas de login. Espere alguns minutos."
        if not resp.ok:
            return False, False, f"Falha no login (HTTP {resp.status_code})."

        body = resp.json()
        types = body.get("requiresTwoFactorAuth")
        if types:
            self._pending_2fa = True
            self.pending_types = [t for t in types if isinstance(t, str)] or ["emailOtp"]
            return True, True, ",".join(self.pending_types)
        self.me = body
        self.persist_session()
        return True, False, "ok"

    def verify_2fa(self, code, method="emailOtp"):
        code = "".join(code.split())
        if not code:
            return False, "Digite o codigo que chegou."
        path = TYPE_ENDPOINTS.get(method, TYPE_ENDPOINTS["emailOtp"])
        try:
            resp = self._request("POST", path, params=self._params(), json={"code": code})
        except requests.RequestException as exc:
            return False, f"Sem conexao com a API.\n{exc}"

        if resp.status_code == 429:
            return False, "Muitas tentativas. Espere alguns minutos."

        verified = False
        message = ""
        try:
            data = resp.json()
            verified = bool(data.get("verified"))
            err = data.get("error")
            if isinstance(err, dict):
                message = err.get("message", "") or ""
        except Exception:
            pass
        if not verified and "twoFactorAuth" in self.session.cookies:
            verified = True

        if not verified:
            if message:
                return False, message
            if method == "emailOtp":
                return False, "Codigo incorreto ou expirado. Use “Reenviar codigo” para pedir outro."
            return False, "Codigo invalido."

        me = self.current_user()
        if not me:
            time.sleep(1)
            me = self.current_user()
        if not me:
            return False, "Codigo aceito, mas a sessao nao abriu (401). Tente entrar de novo."
        self.me = me
        self._pending_2fa = False
        self.persist_session()
        return True, "ok"

    def current_user(self):
        resp = self._request("GET", "/auth/user", params=self._params())
        if resp.status_code == 401:
            return None
        resp.raise_for_status()
        self.me = resp.json()
        return self.me

    # -- dados
    def fetch_online_friends(self):
        friends, offset, page = [], 0, 100
        while True:
            resp = self._request(
                "GET",
                "/auth/user/friends",
                params=self._params({"offline": "false", "n": page, "offset": offset}),
            )
            if resp.status_code == 401:
                raise PermissionError("sessao expirada")
            resp.raise_for_status()
            batch = resp.json() or []
            friends.extend(batch)
            if len(batch) < page or offset > 1000:
                break
            offset += page
        return friends

    def get_user(self, user_id):
        """Perfil completo de um usuario. 401 -> PermissionError (sessao caiu)."""
        resp = self._request("GET", f"/users/{user_id}", params=self._params())
        if resp.status_code == 401:
            raise PermissionError("sessao expirada")
        resp.raise_for_status()
        return resp.json() or {}

    def world_name(self, world_id):
        if not world_id:
            return ""
        if world_id in self.worlds:
            return self.worlds[world_id]
        try:
            resp = self._request("GET", f"/worlds/{world_id}", params=self._params())
            if resp.ok:
                name = resp.json().get("name") or ""
                if name:
                    self.worlds[world_id] = name
                    self._worlds_dirty = True
                return name
        except Exception:
            pass
        self.worlds[world_id] = ""  # evita repetir a chamada
        self._worlds_dirty = True
        return ""

    def instance_occupancy(self, world_id, instance_id, ttl=60):
        """Quantas pessoas na instancia: (occupants, capacity) ou None.

        `GET /worlds/{worldId}/{instanceId}` responde `occupants` (e `capacity` quando
        o mundo define). Instancia privada/fechada devolve erro: nesse caso None, e a
        UI simplesmente nao mostra numero — nunca inventa zero.
        """
        if not world_id or not instance_id:
            return None
        chave = f"{world_id}:{instance_id}"
        agora = time.time()
        guardado = self._instances.get(chave)
        if guardado and agora - guardado[0] < ttl:
            return guardado[1]
        try:
            resp = self._request(
                "GET", f"/worlds/{world_id}/{instance_id}", params=self._params()
            )
            if not resp.ok:
                return None
            dados = resp.json() or {}
            # a resposta moderna usa `userCount` (e `n_users`, legado); `occupants`
            # não existe mais — ler só ele foi o motivo de nunca aparecer número.
            occ = dados.get("userCount")
            if occ is None:
                occ = dados.get("n_users")
            if occ is None:
                return None
            valor = (int(occ), dados.get("capacity"))
            self._instances[chave] = (agora, valor)
            return valor
        except Exception:
            return None

    def update_me(self, status=None, status_description=None):
        """PUT /users/{id}: muda meu status e/ou minha bio. Devolve o usuario novo.

        A API exige o id do proprio usuario; `self.me` ja veio no login.
        """
        uid = (self.me or {}).get("id")
        if not uid:
            raise RuntimeError("sem usuario logado")
        corpo = {}
        if status is not None:
            corpo["status"] = status
        if status_description is not None:
            corpo["statusDescription"] = status_description
        if not corpo:
            return self.me
        resp = self._request("PUT", f"/users/{uid}", params=self._params(), json=corpo)
        if resp.status_code == 401:
            raise PermissionError("sessao expirada")
        resp.raise_for_status()
        novo = resp.json() or {}
        if novo:
            self.me = {**(self.me or {}), **novo}
        return self.me

    def flush_world_cache(self):
        if self._worlds_dirty:
            save_json(WORLD_CACHE, self.worlds)
            self._worlds_dirty = False

    # -- avatares (icone de perfil do amigo, herdado do VRChat)
    def avatar_path(self, url, user_id, size=20):
        """Baixa o icone do amigo e recorta em circulo. 1 download por amigo/size.

        A API devolve `iconUrl` (a mesma imagem de `currentAvatarImageUrl`), 256x256 PNG,
        servida sem cookie. O recorte roda no worker, nunca na thread da interface.
        """
        if not url or not user_id:
            return None
        dest = os.path.join(AVATARS_DIR, f"{user_id}-{size}.png")
        if os.path.exists(dest):
            return dest
        tmp = dest + ".tmp"
        try:
            from io import BytesIO

            from PIL import Image, ImageDraw

            resp = self.session.get(url, timeout=10)
            if not resp.ok:
                return None
            img = Image.open(BytesIO(resp.content)).convert("RGBA")
            lado = min(img.size)
            left, top = (img.width - lado) // 2, (img.height - lado) // 2
            img = img.crop((left, top, left + lado, top + lado))
            grande = img.resize((size * 4, size * 4), Image.LANCZOS)
            mask = Image.new("L", grande.size, 0)
            ImageDraw.Draw(mask).ellipse((0, 0, grande.size[0] - 1, grande.size[1] - 1), fill=255)
            out = Image.new("RGBA", grande.size, (0, 0, 0, 0))
            out.paste(grande, (0, 0), mask)
            out = out.resize((size, size), Image.LANCZOS)
            os.makedirs(AVATARS_DIR, exist_ok=True)
            out.save(tmp, format="PNG")
            os.replace(tmp, dest)
            return dest
        except Exception as exc:  # noqa: BLE001
            print(f"[aviso] avatar de {user_id}: {exc}", file=sys.stderr)
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except Exception:
                pass
            return None
