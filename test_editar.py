# -*- coding: utf-8 -*-
"""Editar meu status/bio: prova o PUT /users/{id} com sessão falsa.

Não toca na conta de verdade — o corpo enviado é o que importa aqui.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.service import VRChatService  # noqa: E402
from core.vrchat import VRChatClient  # noqa: E402

ME = {
    "id": "usr_eu",
    "displayName": "eu",
    "status": "active",
    "statusDescription": "bio antiga",
    "bio": "",
    "pronouns": "",
    "tags": [],
}


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
        self.chamadas = []

    def request(self, method, url, **kwargs):
        self.chamadas.append((method, url, kwargs.get("json")))
        if method == "PUT" and "/users/usr_eu" in url:
            corpo = dict(ME)
            corpo.update(kwargs.get("json") or {})
            return Resp(200, corpo)
        if "/users/usr_eu" in url:
            return Resp(200, ME)
        return Resp(404, {})


def main():
    sess = SessaoFalsa()
    cliente = VRChatClient()
    cliente.session = sess
    cliente.me = dict(ME)
    cliente.api_key = "chave"

    falhas = 0

    def check(nome, cond, detalhe=""):
        nonlocal falhas
        print(("OK  " if cond else "FALHA") + "  " + nome + (f"  [{detalhe}]" if detalhe else ""))
        if not cond:
            falhas += 1

    # 1) status
    novo = cliente.update_me(status="busy")
    metodo, url, corpo = sess.chamadas[-1]
    check("método e rota do PUT", metodo == "PUT" and url.endswith("/users/usr_eu"), f"{metodo} {url}")
    check("corpo só com status", corpo == {"status": "busy"}, json.dumps(corpo))
    check("me atualizado em memória", (novo or {}).get("status") == "busy", str((novo or {}).get("status")))

    # 2) bio
    cliente.update_me(status_description="bio nova")
    metodo, url, corpo = sess.chamadas[-1]
    check("corpo só com statusDescription", corpo == {"statusDescription": "bio nova"}, json.dumps(corpo))

    # 3) nada a mudar: não faz requisição
    antes = len(sess.chamadas)
    cliente.update_me()
    check("sem mudança não chama a API", len(sess.chamadas) == antes, str(len(sess.chamadas)))

    # 4) serviço devolve perfil pronto
    service = VRChatService(client=cliente)
    perfil = service.update_me(status="ask me")
    check("serviço devolve Profile", getattr(perfil, "name", "") == "eu", getattr(perfil, "name", "?"))
    check("status no perfil", getattr(perfil, "status", "") == "ask me", getattr(perfil, "status", "?"))

    print(f"\n{len(sess.chamadas)} requisições, {falhas} falha(s)")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
