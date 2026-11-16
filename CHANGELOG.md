# Changelog

Todas as mudanças importantes do VRChat Friends. O formato segue
[Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e a versão vem de
`core/paths.py` (`APP_VERSION`).

## [1.1.0] — 2026-11-16

### Adicionado
- **Favoritos locais**: estrela na linha e no cartão do amigo, salva em `settings.json`
  (id, nome de exibição e a última vez que o app viu a pessoa online).
- Favorito que sai do ar continua na lista, apagado no fim, com avatar do cache e
  "visto há X" — sem nenhuma requisição nova ao VRChat.
- **Aviso de "amigo entrou no jogo"**: cartão próprio do app, sem roubar foco, até 3
  empilhados (mais que isso vira resumo), 10 min de intervalo por amigo e silêncio quando
  o seu status é Busy.
- Ordenação clicável por **AMIGO**, **STATUS** ou **MUNDO** (1º clique ▲, 2º ▼), com a
  coluna e a direção salvas entre sessões.
- Bolinha de status **vazada** para quem está online só na web, sem cliente aberto.
- Widget flutuante: resumo compacto dos amigos online, com atualizar e fechar.

### Corrigido
- A estrela não se perde mais: gravar outra configuração (ordem, posição do widget)
  não apaga os favoritos.
- Só uma cópia do app roda por vez — duas janelas brigavam pelo mesmo `settings.json`.
- O aviso de "amigo entrou" passa a nascer no canto inferior direito do **monitor
  principal**, mesmo com a janela do app no monitor secundário.
- O **✕** do widget fecha o widget de verdade (o clique era capturado pela área de
  arrastar, que também engolia o botão de atualizar).
- Desfavoritar o último favorito offline tira a linha dele da lista na hora.

### Alterado
- Versão do app: `1.1.0` no rodapé da janela e nos metadados do `.exe`.
- Instância de grupo que devolve `userCount: 0` mostra o piso (`1+/80`) em vez de esconder
  o número.

## [1.0.0] — 2026-11-15

### Adicionado
- Primeira versão com interface em Qt Quick (QML): lista dos amigos online com status,
  mundo, tipo de instância e ocupação.
- Login com usuário e senha, verificação em duas etapas (e-mail, app autenticador ou
  código de recuperação) e sessão lembrada entre aberturas.
- Ícone na bandeja, fechar para a bandeja e "sempre no topo".
- Painel com o seu próprio perfil e edição do status e da mensagem (32 caracteres, o
  limite da API).
- Cache de nomes de mundo (`worlds.json`) e de avatares, para não repetir requisição.
- Aplicativo somente leitura: não entra em mundo, não manda convite, não envia mensagem.

[1.1.0]: https://github.com/aryarti/VRChatFriends/releases/tag/v1.1.0
