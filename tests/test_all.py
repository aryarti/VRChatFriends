# -*- coding: utf-8 -*-
"""pytest entry point for the legacy check-scripts.

The project's tests are plain scripts: each one prints ``OK``/``FALHA`` lines and
exits with 1 on failure (see ``check()`` inside them). Instead of rewriting them,
this module runs each script as a subprocess and fails the pytest case when the
script exits non-zero.

Three groups, because not every script is safe to run unattended:

* ``SEGUROS``    - no network, no real session: run by default (``pytest``).
* ``COM_SESSAO`` - build a real ``Bridge()`` without isolating ``SESSION_FILE``, so
  they can overwrite the owner's ``session.json``: opt in with ``-m sessao_real``.
* ``REDE``       - hit the VRChat API with the real session: ``-m network``.

``test_qml_ui.py`` is intentionally absent: it is a screenshot helper that opens a
window and waits, not a test.
"""
from __future__ import annotations

import os
import subprocess
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON = sys.executable
LIMITE_SEGUNDOS = 420

SEGUROS = [
    "test_avisos.py",
    "test_favoritos.py",
    "test_instancias.py",
    "test_ocupacao.py",
    "test_ordenacao.py",
    "test_qml.py",
    "test_qml_v11.py",
    "test_qml_v12.py",
    "test_qml_v13.py",
]

COM_SESSAO = [
    "test_editar.py",
    "test_qml_checks.py",
    "test_qml_login.py",
    "test_qml_ocupacao.py",
    "test_qml_painel.py",
    "test_qml_widget.py",
]

REDE = [
    "test_qml_real.py",
]


def _rodar(script: str) -> None:
    caminho = os.path.join(RAIZ, script)
    if not os.path.exists(caminho):
        pytest.skip(f"{script} does not exist on this branch")

    ambiente = dict(os.environ)
    ambiente["PYTHONDONTWRITEBYTECODE"] = "1"
    # UI tests that need ListView delegates must run on the real platform
    ambiente.pop("QT_QPA_PLATFORM", None)

    processo = subprocess.run(
        [PYTHON, "-B", caminho],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        timeout=LIMITE_SEGUNDOS,
        env=ambiente,
    )
    saida = (processo.stdout or "") + (processo.stderr or "")
    if processo.returncode != 0:
        pytest.fail(
            f"{script} failed (exit {processo.returncode})\n{saida[-4000:]}",
            pytrace=False,
        )


@pytest.mark.parametrize("script", SEGUROS)
def test_safe_script(script):
    _rodar(script)


@pytest.mark.sessao_real
@pytest.mark.parametrize("script", COM_SESSAO)
def test_script_touching_the_real_session(script):
    _rodar(script)


@pytest.mark.network
@pytest.mark.sessao_real
@pytest.mark.parametrize("script", REDE)
def test_script_hitting_the_api(script):
    _rodar(script)
