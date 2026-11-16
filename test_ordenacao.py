# -*- coding: utf-8 -*-
"""Testes da v1.1: ordenação por coluna, limite de 32 do status e as defesas
do cliente HTTP (retry de conexão morta e 429).

Sem rede, sem Qt. Uso: python test_ordenacao.py  (python -B)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests  # noqa: E402

import core.vrchat as vrc  # noqa: E402
from core import Friend  # noqa: E402
from core.formatting import STATUS_DESCRIPTION_MAX  # noqa: E402
from core.sorting import normalize, sort_friends  # noqa: E402

falhas = []


def check(nome, cond, extra=""):
    print(("OK   " if cond else "FALHA") + f"  {nome}" + (f"  [{extra}]" if extra else ""))
    if not cond:
        falhas.append(nome)


def nomes(lista):
    return [f.name for f in lista]


# ---------------------------------------------------------------- normalização
check("normalize tira acento e caixa", normalize("Ágata") == "agata", normalize("Ágata"))
check("normalize mantém símbolos do nick", normalize("Duda_Teste") == "duda_teste")
check("normalize ignora espaço nas pontas", normalize("  zeca ") == "zeca")

# ---------------------------------------------------------------- status
amigos = [
    Friend(id="1", name="Zeca", status="busy"),
    Friend(id="2", name="ana", status="join me"),
    Friend(id="3", name="Bruno", status="active"),
    Friend(id="4", name="Caio", status="ask me"),
    Friend(id="5", name="Duda", status="offline"),      # desconhecido
    Friend(id="6", name="Ágata", status="active"),
]
asc = sort_friends(amigos, "status", "asc")
check("status asc: Join Me -> Online -> Ask Me -> Busy",
      [f.status for f in asc] == ["join me", "active", "active", "ask me", "busy", "offline"],
      [f.status for f in asc])
check("status asc: desconhecido no fim", asc[-1].name == "Duda", asc[-1].name)
check("status asc: desempate por nome sem acento",
      nomes(asc)[1:3] == ["Ágata", "Bruno"], nomes(asc)[1:3])

desc = sort_friends(amigos, "status", "desc")
check("status desc: inverte a coluna (desconhecido vai para o começo)",
      [f.status for f in desc] == ["offline", "busy", "ask me", "active", "active", "join me"],
      [f.status for f in desc])
check("status desc: desempate NÃO inverte",
      nomes(desc)[3:5] == ["Ágata", "Bruno"], nomes(desc)[3:5])

# ---------------------------------------------------------------- nome
por_nome = sort_friends(amigos, "name", "asc")
check("nome asc: A->Z sem acento/caixa",
      nomes(por_nome) == ["Ágata", "ana", "Bruno", "Caio", "Duda", "Zeca"],
      nomes(por_nome))
por_nome_desc = sort_friends(amigos, "name", "desc")
check("nome desc: Z->A", nomes(por_nome_desc) == ["Zeca", "Duda", "Caio", "Bruno", "ana", "Ágata"],
      nomes(por_nome_desc))

mesmo_nome = [
    Friend(id="usr_b", name="Igual", status="active"),
    Friend(id="usr_a", name="igual", status="busy"),
    Friend(id="usr_c", name="IGUAL", status="active"),
]
check("nome igual: último critério é o ID",
      [f.id for f in sort_friends(mesmo_nome, "name", "desc")] == ["usr_a", "usr_b", "usr_c"],
      [f.id for f in sort_friends(mesmo_nome, "name", "desc")])

# ---------------------------------------------------------------- mundo
mundos = [
    Friend(id="1", name="A", location="wrld_priv:1~private(usr_x)"),
    Friend(id="2", name="B", location="wrld_group:1~group(grp_1)"),
    Friend(id="3", name="C", location="wrld_pub:1"),
    Friend(id="4", name="D", location="offline", platform="web"),
    Friend(id="5", name="E", location="wrld_friends:1~friends(usr_x)"),
    Friend(id="6", name="F", location="wrld_inv:1~private(usr_x)~canrequestinvite"),
    Friend(id="7", name="G", location="wrld_hidden:1~hidden(usr_x)"),
    Friend(id="8", name="H", location="offline", platform="standalonewindows"),
]
ordem_mundo = sort_friends(mundos, "world", "asc")
tipos = [f.location for f in ordem_mundo]
check("mundo asc: público, grupo, amigos/convite, privado, fora",
      tipos[0] == "wrld_pub:1" and tipos[1] == "wrld_group:1~group(grp_1)"
      and set(tipos[2:5]) == {"wrld_friends:1~friends(usr_x)",
                              "wrld_inv:1~private(usr_x)~canrequestinvite",
                              "wrld_hidden:1~hidden(usr_x)"}
      and tipos[5] == "wrld_priv:1~private(usr_x)"
      and tipos[6:] == ["offline", "offline"],
      tipos)

# mesmo tipo: nome do mundo e depois nome do amigo
por_mundo = [
    Friend(id="1", name="Bruno", world="Zeta · público", location="wrld_z:1"),
    Friend(id="2", name="Ana", world="Alfa · público", location="wrld_a:1"),
    Friend(id="3", name="Zeca", world="Beta · público", location="wrld_b:1"),
    Friend(id="4", name="Caio", world="Alfa · público", location="wrld_a:2"),
]
mm = sort_friends(por_mundo, "world", "asc")
check("mundo: dentro do tipo ordena por nome do mundo, depois amigo",
      nomes(mm) == ["Ana", "Caio", "Zeca", "Bruno"], nomes(mm))
mm_desc = sort_friends(por_mundo, "world", "desc")
check("mundo desc: nome do mundo inverte, amigo dentro do mundo não",
      nomes(mm_desc) == ["Bruno", "Zeca", "Ana", "Caio"], nomes(mm_desc))

# ---------------------------------------------------------------- settings torto
from core.sorting import normalize_choice  # noqa: E402

check("coluna inválida cai no padrão Status",
      normalize_choice("bogus", "desc") == ("status", "desc"))
check("direção inválida cai em crescente",
      normalize_choice("world", "sideways") == ("world", "asc"))
check("padrão ao abrir é Status ▲", normalize_choice(None, None) == ("status", "asc"))

# ---------------------------------------------------------------- 32 caracteres
check("limite do status é 32", STATUS_DESCRIPTION_MAX == 32, str(STATUS_DESCRIPTION_MAX))


class Resposta:
    status_code = 200
    ok = True
    headers = {}

    def json(self):
        return {"id": "usr_1", "displayName": "aryaah"}

    def raise_for_status(self):
        pass


cliente = vrc.VRChatClient()
cliente.me = {"id": "usr_1", "displayName": "aryaah"}
capturado = {}
cliente._request = lambda metodo, caminho, **kw: (capturado.update(kw), Resposta())[1]
cliente.update_me(status_description="x" * 40)
enviado = capturado["json"]["statusDescription"]
check("status cortado em 32 antes do PUT", len(enviado) == 32, f"{len(enviado)}: {enviado}")
cliente.update_me(status_description="   oi   ")
check("status perde espaço nas pontas", capturado["json"]["statusDescription"] == "oi",
      repr(capturado["json"]["statusDescription"]))
cliente.update_me(status="busy")
check("só status não manda statusDescription",
      "statusDescription" not in capturado["json"], str(capturado["json"]))

# ---------------------------------------------------------------- retry de conexão
class SessaoFalsa:
    """Imita o requests.Session: N primeiras chamadas morrem com Timeout."""

    def __init__(self, falhas=0, codigo=200):
        self.headers = {}
        self.cookies = requests.cookies.RequestsCookieJar()
        self.falhas = falhas
        self.codigo = codigo
        self.chamadas = 0

    def request(self, *a, **k):
        self.chamadas += 1
        if self.chamadas <= self.falhas:
            raise requests.Timeout("keep-alive morto")
        r = Resposta()
        r.status_code = self.codigo
        return r

    def close(self):
        pass


c2 = vrc.VRChatClient()
suave = SessaoFalsa(falhas=1)
c2.session = suave
recicladas = []


def reciclar():
    recicladas.append(True)
    c2.session = SessaoFalsa(falhas=0)   # conexão nova


c2._recycle_session = reciclar
resp = c2._request("GET", "/auth/user")
check("conexão morta: repete numa conexão nova", resp.status_code == 200 and len(recicladas) == 1,
      f"{resp.status_code} reciclagens={len(recicladas)}")
check("conexão morta: gastou 2 chamadas", c2.session.chamadas == 1 and suave.chamadas == 1,
      f"{suave.chamadas}+{c2.session.chamadas}")

c3 = vrc.VRChatClient()
c3.session = SessaoFalsa(falhas=99)
c3._recycle_session = lambda: None
try:
    c3._request("GET", "/auth/user")
    estourou = False
except requests.Timeout:
    estourou = True
check("sem conexão até o fim: levanta o erro (vira 'sem conexão' na tela)", estourou)

# ---------------------------------------------------------------- 429
dormir = []
vrc.time.sleep = lambda s: dormir.append(s)

c4 = vrc.VRChatClient()
c4.session = SessaoFalsa(falhas=0, codigo=429)
r429 = c4._request("GET", "/auth/user")
check("429 na última tentativa volta como resposta (não vira exceção)",
      r429.status_code == 429)
check("429 espera entre 2 e 8 s", all(2 <= s <= vrc.ESPERA_LIMITE_MAX for s in dormir),
      str(dormir))
check("429 tentou 3 vezes", c4.session.chamadas == 3, str(c4.session.chamadas))

cabecalho = vrc.espera_limite(type("R", (), {"headers": {"X-RateLimit-Reset": "9999999999"}})())
check("X-RateLimit-Reset gigante é limitado ao teto", cabecalho == vrc.ESPERA_LIMITE_MAX,
      str(cabecalho))
sem_cabecalho = vrc.espera_limite(type("R", (), {"headers": {}})())
check("sem X-RateLimit-Reset: espera 3 s", sem_cabecalho == 3.0, str(sem_cabecalho))

# ---------------------------------------------------------------- sessão em disco
import json  # noqa: E402
import tempfile  # noqa: E402

tmp = tempfile.mkdtemp(prefix="vrc_sess_")
vrc.SESSION_FILE = os.path.join(tmp, "session.json")

c5 = vrc.VRChatClient()
c5.session = SessaoFalsa()        # cookiejar vazio (ninguém logado)
c5.api_key = "x"
check("sem cookie não grava (não apaga a sessão boa)",
      c5.persist_session_if_changed() is False and not os.path.exists(vrc.SESSION_FILE))

c5.session.cookies.set("auth", "abc")
check("grava quando o cookie aparece", c5.persist_session_if_changed() is True
      and os.path.exists(vrc.SESSION_FILE))
with open(vrc.SESSION_FILE, encoding="utf-8") as fh:
    gravado = json.load(fh)
check("cookie foi para o arquivo", gravado["cookies"].get("auth") == "abc", str(gravado))
check("segunda chamada não regrava", c5.persist_session_if_changed() is False)


print()
print("FALHAS:", falhas if falhas else "nenhuma")
sys.exit(1 if falhas else 0)
