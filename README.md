# SOL CONTENT MACHINE

Generador automático de vídeos para 10 nichos. Funciona aunque el PC esté apagado.

## Cómo funciona

```
GitHub Actions (nube, gratis, 24/7)
    → genera scripts diarios → sol_queue.json
PC al encenderse (Task Scheduler)
    → descarga cola → genera voz + vídeo → E:\SOL_CONTENT\
```

## Setup inicial (solo una vez)

1. Cambia `GITHUB_USER` y `GITHUB_REPO` en `sol_pc_assembler.py`
2. El resto lo hace SOL automáticamente
