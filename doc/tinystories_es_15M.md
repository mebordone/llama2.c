# TinyStories ES (~15M)

Baby Llama 2 entrenado en el corpus español sintético (`data/TinyStoriesES_all_data`), arquitectura OG tipo `stories15M` de Karpathy, tokenizer custom 4096.

Informe preliminar (ciencia abierta): [informe_tinystories_es.md](informe_tinystories_es.md) · artefactos: [open_science/](open_science/).

## Inferencia

```bash
./run out_es_15M/model.bin -z data/tok4096.bin
./run out_es_15M/model.bin -z data/tok4096.bin -t 0.8 -n 256 -i "Había una vez"
```

## Arquitectura / train

- `dim=288`, `n_layers=6`, `n_heads=6`, `n_kv_heads=6`, `max_seq_len=256`
- `vocab_source=custom`, `vocab_size=4096`
- `max_iters=100000`, `lr=5e-4`, batch 128
- Parámetros efectivos ~7.2M (vocab 4096; el 15M inglés usa vocab Llama2 32k)

## Artefactos

- `out_es_15M/model.bin`, `out_es_15M/ckpt.pt`
- `data/tok4096.model`, `data/tok4096.bin`, `data/tok4096/*.bin`
- Métricas: `experiments/<run_id>/SUMMARY.md` (p. ej. `20260807_190503`)

## Nota

Con 100k historias el train loss baja mucho más que el val (overfitting). Aun así genera español coherente en smoke tests. Más datos o early stopping mejorarían el val loss.
