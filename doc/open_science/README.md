# Artefactos de ciencia abierta (TinyStories ES)

Este directorio concentra **evidencia liviana y versionable** del experimento preliminar. El informe narrativo está en [`../informe_tinystories_es.md`](../informe_tinystories_es.md).

## Qué sí está aquí (recomendado en el repo)

| Archivo | Contenido |
|---|---|
| `eval_generators_report.md` | Tabla de ranking Ollama (calidad/velocidad/VRAM) |
| `eval_generators_ranking.json` | Ranking machine-readable |
| `eval_generators_winner.txt` | Modelo elegido: `qwen2.5:7b-instruct` |
| `run_es_260k_eval_config.json` | Config de la eval (temp, prompts, score) |
| `corpus_generation_summary.json` | Tiempo, accept rate, ritmo de las 100k historias |
| `sample_stories.json` | 5 cuentos de muestra del corpus |
| `vocab_pretok_512_summary.json` | Stats pretok vocab 512 |
| `vocab_pretok_4096_summary.json` | Stats pretok vocab 4096 |
| `train_es_260k_launch.json` | argv exacto del train 260K |
| `train_es_15M_launch.json` | argv exacto del train ~7.2M |
| `run_es_260k_meta.json` | Host/GPU/Python/git del run |
| `run_es_15M_config.json` | Config declarativa del run 15M |
| `experiment_es_260k_SUMMARY.md` | Resumen del train/infer ~260K |
| `experiment_es_15M_SUMMARY.md` | Resumen del train/infer ~7.2M |

También en el repo (fuera de esta carpeta): scripts, `tinystories.py` adaptado, `data/vocab_es_simple.txt`, `data/tok512.bin`, `data/tok4096.bin`, docs cortas de modelos.

## Qué no va en git (y por qué)

| Artefacto | Motivo |
|---|---|
| `data/TinyStoriesES_all_data/` (~65 MB, 100k JSON) | Corpus regenerable; mejor HF/Zenodo |
| `out_es_260k/`, `out_es_15M/` (pesos) | Binarios grandes; publicar como release/HF |
| `experiments/` completo (logs, JSONL crudos) | Ruido + tamaño; bastan los SUMMARY publicados |
| `.venv/`, `run`/`runq` | Entorno/build local |

## Cómo reproducir (alto nivel)

```bash
# 1) Eval generadores (opcional si ya hay winner)
.venv/bin/python scripts/eval_ollama_generators.py

# 2) Corpus
.venv/bin/python scripts/generate_tinystories_es.py --target 100000

# 3) Vocab + pretok (ej. 512)
.venv/bin/python tinystories.py train_vocab --vocab_size=512 --data_dir=data/TinyStoriesES_all_data
.venv/bin/python tinystories.py pretokenize --vocab_size=512 --data_dir=data/TinyStoriesES_all_data
.venv/bin/python tokenizer.py --tokenizer-model=data/tok512.model

# 4) Train + métricas (ver doc/tinystories_es_260k.md o tinystories_es_15M.md)
.venv/bin/python scripts/train_with_metrics.py -- --out_dir=out_es_260k ...

# 5) Infer
make run
./run out_es_260k/model.bin -z data/tok512.bin -i "Había una vez"
```

## Licencia / atribución

- Código base: licencia del upstream `llama2.c` (Karpathy).
- Idea de dominio: TinyStories (Eldan & Li).
- Corpus sintético: generado localmente con Ollama / `qwen2.5:7b-instruct` (respetar términos del modelo al redistribuir texto).
