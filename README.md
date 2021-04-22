HS-MVideoSumm
==============

Técnica de Sumarização Multivídeo: Human Strategies based Multi-video Summarization.

### Entrada
Nome do conjunto e nomes dos vídeos/textos a serem processados (sem extensão).

Textos de notícias relacionadas separados em subtópicos e organizados em arquivo JSON com campos: 
- content: texto do subtópico; 
- begin, end: tempos de início e fim do subtópico no formato HH:MM:SS.

Vídeos em formato MP4.

```
python3 main.py <video_set> <video1> <video2> [<video3> ...]
```

### Observação

Os limiares utilizados para detectar opinião a partir dos valores magnitude e score da Google Cloud Natural Language API foram definidos em janeiro/2020 considerando a base de vídeos https://github.com/tamires/base-de-videos
