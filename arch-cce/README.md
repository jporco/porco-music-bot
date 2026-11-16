# Porco Music Bot no Arch-CCE

Código da instalação do CCE, que usa `~/porco-music-bot` como pasta de execução. Os controles do Spotify Connect usam a interface MPRIS do `spotifyd` pelo barramento de sessão. O motor do Porco usa mpv, PulseAudio e o mixer ALSA do CCE.

No SSH, carregue `source ~/porco-music-bot/funcoes.sh` e consulte `porco-help`.

- `play [busca]` procura no YouTube. A fila recebe até cinco faixas por busca, com a primeira disponível antes das demais.
- `mais [busca]` acrescenta até duas faixas. A fila comporta até 30 aguardando.
- `play` sem argumentos retoma a reprodução. `pause`, `proximo`, `proxima` e `anterior` atuam no player selecionado.
- `fila` mostra a faixa atual, a fila do Porco e o andamento das buscas.

A instalação do CCE usa `tools/yt-dlp` (versão 2026.10.26) e `tools/deno`. Obtenha os executáveis nas distribuições oficiais do [yt-dlp](https://github.com/yt-dlp/yt-dlp/releases) e do [Deno](https://github.com/denoland/deno/releases). Os serviços de usuário, o roteamento de áudio e os dados persistentes pertencem à instalação em execução.
