# TinyStories ES (~260K)

Modelo baby Llama 2 entrenado en cuentos sintéticos en español, misma receta que `stories260K`.

## Inferencia

```bash
./run out_es_260k/model.bin -z data/tok512.bin
./run out_es_260k/model.bin -z data/tok512.bin -t 0.8 -n 256 -i "Había una vez"
```

Requiere el binario `run` (`make run`) y el tokenizer custom `data/tok512.bin` (vocab 512).

## Pipeline (resumen)

1. Eval de generadores Ollama → `data/eval_generators/winner.txt`
2. Corpus ES → `data/TinyStoriesES_all_data/*.json`
3. `python tinystories.py train_vocab --vocab_size=512 --data_dir=data/TinyStoriesES_all_data`
4. `python tinystories.py pretokenize --vocab_size=512 --data_dir=data/TinyStoriesES_all_data`
5. `python tokenizer.py --tokenizer-model=data/tok512.model`
6. Entrenamiento (GPU):

```bash
.venv/bin/python scripts/train_with_metrics.py -- --out_dir=out_es_260k \
  --batch_size=128 --max_seq_len=512 --gradient_accumulation_steps=1 \
  --vocab_source=custom --vocab_size=512 \
  --dim=64 --n_layers=5 --n_heads=8 --n_kv_heads=4 --multiple_of=4 \
  --learning_rate=1e-3 --dropout=0.05 --weight_decay=0.01 \
  --max_iters=100000 --beta2=0.99 --warmup_iters=1000 \
  --eval_interval=2000 --eval_iters=100 --compile=True
```

Métricas y artefactos: `experiments/<run_id>/` (ver `SUMMARY.md`).

## Scripts

- `scripts/eval_ollama_generators.py` — calidad / velocidad / VRAM
- `scripts/generate_tinystories_es.py` — corpus sintético vía Ollama
- `scripts/exp_logger.py` — logging de experimentos
- `scripts/train_with_metrics.py` — train + métricas
- `scripts/write_summary.py` — resumen final

## Estado del entrenamiento (run 20260805_125324)

- Corpus: 100k cuentos con `qwen2.5:7b-instruct`
- Val loss final: ~1.407
- Artefactos: `out_es_260k/model.bin`, `data/tok512.bin`
- Métricas: `experiments/20260805_125324/SUMMARY.md`

Nota: `train_vocab` usó `character_coverage=0.9995` (con vocab 512 y Unicode del corpus ES, coverage=1.0 falla).
