# VRChat Friends

App leve para ver **quais amigos estão online no VRChat**, sem manter o site aberto no navegador.

## Como abrir

- Atalho **VRChat Friends** na Área de Trabalho, ou
- `abrir.vbs`, na pasta do projeto (abre sem janela de console)

## Primeiro uso

1. Digite usuário (ou e-mail) e senha do VRChat.
2. **Código de verificação:** o app lê do servidor qual método sua conta usa e mostra o campo certo:
   - **código do e-mail** (email OTP) → o VRChat envia o código para o e-mail da conta assim que o login é feito,
     igual ao site. Se não chegar em ~1 min, use **Reenviar código** (espera de 25 s entre pedidos).
   - **app autenticador** (TOTP) → código de 6 dígitos do autenticador.
   - **código de recuperação** → um dos códigos de backup.
   Se a conta tiver mais de um método, aparece um seletor no canto direito.
3. A senha é usada **uma única vez** para criar a sessão. Só o cookie de sessão
   fica salvo em `%LOCALAPPDATA%\VRChatFriends\session.json` — a senha não é gravada.
4. Nas próximas vezes o app entra direto. Se a sessão expirar, ele volta pra tela de login.

Endpoints usados (um por método, sem tentativa às cegas):

| Método | Endpoint |
|---|---|
| `emailOtp` | `POST /auth/twofactorauth/emailotp/verify` |
| `totp` | `POST /auth/twofactorauth/totp/verify` |
| `otp` (recuperação) | `POST /auth/twofactorauth/otp/verify` |

O endpoint é escolhido pelo que vem em `requiresTwoFactorAuth` na resposta do login —
tentar os três com o mesmo código queimaria as tentativas do código.

## O que ele faz

- Atualiza sozinho a cada 45 s (`GET /auth/user/friends?offline=false`); depois de uma
  falha tenta de novo em 15 s e volta ao ritmo normal quando dá certo
- Mostra nome, status (Online / Join Me / Ask Me / Busy), mundo e tipo de instância
  (público, Friends · amigos, Friends+ · amigos+, Invite · privado, Invite+ · privado+convite,
  Grupo e região)
- Bolinha de status **cheia** = abriu o cliente/jogo; **vazada** (só o anel) = está
  online apenas na **web**, sem cliente aberto
- Nomes de mundo são guardados em cache (`worlds.json`), então não custa requisição repetida
- **Somente leitura**: não entra em mundo, não manda convite, não envia mensagem

## Controles

| Ação | Como |
|---|---|
| Atualizar agora | botão ⟳ |
| Ordenar | clique em **AMIGO**, **STATUS** ou **MUNDO** (1º clique ▲, 2º ▼) |
| Favoritar / desfavoritar | clique na **estrela** da linha ou do cartão |
| Minimizar para a bandeja | botão ▁ ou fechar a janela (✕) |
| Reabrir | clique no ícone da bandeja |
| Sair de vez | botão direito no ícone da bandeja → Sair |
| Abrir/fechar o widget | botão **widget** no rodapé; o **✕** do próprio widget fecha |
| Copiar nome do mundo | duplo clique na linha |
| Copiar link `vrchat://` | botão direito na linha |

### Ordem das colunas

A coluna e a direção ficam salvas em `settings.json`; ao abrir, a lista vem em **Status ▲**.

- **Status ▲** — Join Me, Online, Ask Me, Busy; status desconhecido no fim.
- **Mundo ▲** — público, grupo, amigos/convite, privado, web/menu/outras plataformas;
  dentro do mesmo tipo, pelo nome do mundo.
- **Amigo ▲** — nome A→Z.
- Desempate sempre por nome A→Z (sem acento e sem diferenciar maiúsculas) e ele **não**
  inverte com a direção; o último critério é o ID. A regra vive em `core/sorting.py`,
  sem importar Qt — a seta ▲/▼ é só desenho, no QML.

A seleção acompanha o amigo (por ID), então reordenar ou atualizar não joga a marca em
outra pessoa.

## Meu status

- A mensagem de status é limitada a **32 caracteres** — é o teto da API do VRChat
  (33 devolve erro). O campo mostra o contador `n/32` e o cliente corta antes de enviar.

## Favoritos

- **Estrela** em cada linha e no cartão do amigo. Clicar liga/desliga; fica salvo em
  `settings.json` (`favorites`: id, nome de exibição e a última vez que o app o viu online).
- Favorito **online** fica fixado no topo, com o contorno na cor de destaque. A
  ordenação escolhida vale dentro do bloco dos favoritos e dentro do resto.
- Favorito que **não está online** aparece no fim da lista, apagado, com status
  `Offline`, avatar do cache e `visto há X`. Nada de requisição nova: esse bloco é
  montado com o que o app já tem em disco (nome, avatar em cache e a última vez visto).
- A estrela é lida do `settings.json` a cada atualização: favorito salvo continua na
  lista depois de fechar e abrir o app, e gravar outra coisa (ordem, posição do widget)
  não apaga a estrela.
- O bloco offline só é recalculado quando a atualização termina bem. Se ela falhar, a
  lista fica como estava e o rodapé avisa `desatualizado`.
- Contadores (janela, painel e widget) contam **só quem está online**.

## Avisos de "amigo entrou"

Quando um amigo entra no jogo depois de uma atualização automática, aparece um aviso
do próprio app (não é notificação do Windows): janela sem moldura, sempre no topo e
sem roubar o foco, empilhada no canto inferior direito da área útil do **monitor
principal** — mesmo com a janela do app aberta no monitor secundário.

- Avisa só quem está **no jogo**: quem ficou online apenas na web não gera aviso.
- A primeira atualização depois de abrir o app nunca avisa; atualização que falhou não conta.
- Cada amigo avisa no máximo uma vez a cada 10 minutos.
- Até 3 cartões empilhados; se mais gente entrar de uma vez, sai um resumo
  ("4 amigos entraram").
- Favorito aparece **na cor de destaque**; os demais no cinza padrão.
- O cartão some sozinho em ~5 s (pausa com o mouse em cima) e o clique abre o perfil
  do amigo.
- Liga/desliga em **menu da bandeja → Avisos de amigo entrou** (salvo no `settings.json`).
  Com o meu status em **Busy**, os avisos ficam quietos.

Em VR ou em jogo de tela cheia exclusiva o aviso pode não aparecer: nesses modos o
sistema costuma ficar com a janela exclusiva do jogo.

## Consumo medido

- RAM: ~66 MB (contra ~500 MB+ de um Firefox com o site do VRChat aberto)
- CPU parado: ~0,5% de um núcleo

## Estrutura

```
app_qml.py             ponto de entrada usado pelo .exe
abrir.vbs              lançador sem console
core/                  o "cérebro" — nenhum import de Qt aqui
    vrchat.py          único módulo que fala HTTP (sessão, retentativas, cache)
    service.py         fachada que a interface chama
    models.py          Friend / Profile
    formatting.py      valores da API -> textos da tela (PT-BR)
    sorting.py         ordenação das colunas
    favorites.py       favoritos locais (settings.json)
    alerts.py          detecção de "amigo entrou"
    store.py           JSON, configuração e log em disco
    paths.py           caminhos, constantes e APP_VERSION
ui_qml/                interface (PySide6 / Qt Quick)
    main.py            ponte entre o Qt e o core
    qml/               Main.qml, Theme.qml, Toast.qml, Widget.qml e components/
assets/                ícone e fonte Inter (com OFL.txt)
docs/                  prints do README (dados fictícios)
tests/test_all.py      roda os scripts de teste pelo pytest
test_*.py              testes (executados pelo pytest)
screenshots.py         gera os prints de docs/
make_icon.py           reconstrói assets/icon.ico
requirements*.txt      dependências (QML e dev)
VRChatFriends.spec     empacotamento PyInstaller
versao_exe.txt         metadados de versão do .exe
build_qml.bat          build do executável
verificar_exe.ps1      confere metadados e consumo do .exe gerado
instalar.bat           cria o .venv e instala as dependências
%LOCALAPPDATA%\VRChatFriends\
    session.json       cookie de sessão (+ apiKey)
    settings.json      janela, ordem das colunas, widget, favoritos e avisos
    worlds.json        cache de nomes de mundo
    avatars/           avatares em cache (PNG redondo)
    app.log            log (quando roda sem console)
```

## Notas

- Não está no startup do Windows (o startup enxuto foi uma escolha sua). Se quiser,
  copie o atalho para `shell:startup`.
- **Uma cópia por vez**: abrir o app de novo mostra um aviso e você continua usando o
  que já está aberto, pelo ícone da bandeja. Duas janelas ao mesmo tempo brigavam pelo
  mesmo `settings.json` (a mais velha apagava os favoritos da outra).
- A API do VRChat é não-oficial. O app faz só leitura, no mesmo volume de requisições
  que o site oficial faz, mas ainda assim é uso de API não documentado — vale saber.
- Se aparecer "falha ao atualizar", o rodapé diz o motivo (sem conexão, sem resposta do
  VRChat, limite de requisições, servidor instável). O app tenta de novo sozinho em 15 s.
  Conexão morta por tempo parado é reconectada na hora, sem precisar clicar duas vezes.
- Se ele pedir login de novo, a sessão expirou: entre novamente. Se persistir, apague
  `session.json`.
- Para reconstruir o ícone: `.venv\Scripts\python.exe make_icon.py`
