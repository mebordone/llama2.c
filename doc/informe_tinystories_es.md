# Informe preliminar: TinyStories en español con llama2.c

**Estado:** experimentación preliminar / ciencia abierta  
**Fecha de los runs:** agosto 2026  
**Hardware:** NVIDIA GeForce RTX 3090 (24 GB) · host `mebordone-PC`  
**Código base:** fork de [karpathy/llama2.c](https://github.com/karpathy/llama2.c) → [mebordone/llama2.c](https://github.com/mebordone/llama2.c)  
**Evidencia empaquetada:** [doc/open_science/](open_science/)

---

## 1. Motivación y pregunta

¿Se puede replicar la idea de TinyStories (cuentos sintéticos simples + modelo muy chico) en **español**, manteniendo el stack mínimo de `llama2.c` (`train.py` + `./run`), y obtener generación medianamente coherente?

Objetivo de largo plazo (todavía no implementado en este informe): desplegar un ejecutor + modelo en un **ESP32**.

---

## 2. Qué se hizo (pipeline)

```text
Eval Ollama (calidad/velocidad/VRAM)
        ↓
Corpus ES sintético (100k cuentos)
        ↓
Tokenizer custom + pretokenize
        ↓
Train PyTorch (CUDA) + métricas
        ↓
Inferencia CPU con ./run (sin cambios de GPU en inferencia)
```

Scripts añadidos (reproducibles desde el repo):

| Script | Rol |
|---|---|
| `scripts/eval_ollama_generators.py` | Benchmark de generadores Ollama |
| `scripts/generate_tinystories_es.py` | Generación de corpus con filtros y resume |
| `scripts/exp_logger.py` | Runs bajo `experiments/<run_id>/` |
| `scripts/train_with_metrics.py` | Wrapper de `train.py` + loss/VRAM |
| `scripts/write_summary.py` | `SUMMARY.md` por run |

Adaptaciones en `tinystories.py`: `--data_dir`, modo no interactivo, y `character_coverage` relajado para vocabularios chicos con Unicode.

---

## 3. Experimentación preliminar de generadores Ollama

Se evaluaron modelos **ya instalados** en Ollama con prompts fijos de cuentos infantiles en español. El score combinó calidad y velocidad:

\[
\text{score} = 0.55 \cdot Q + 0.45 \cdot S_{\text{norm}}
\]

con descarte si \(Q < 0.55\).

### 3.1 Ranking (resumen)

Fuente completa: [open_science/eval_generators_report.md](open_science/eval_generators_report.md).

| Modelo | Q | seg/historia | tok/s | score | ETA 100k (h) | VRAM peak (MB) |
|---|---:|---:|---:|---:|---:|---:|
| **qwen2.5:7b-instruct** | 0.983 | 1.21 | 130.8 | **0.991** | 33.7 | 19768 |
| phi4-mini:latest | 0.958 | 1.37 | 195.4 | 0.925 | 38.1 | 4400 |
| qwen3.5:9b | 0.983 | 1.86 | 105.8 | 0.834 | 51.7 | 22281 |
| llama3.1:8b | 0.983 | 1.86 | 125.7 | 0.834 | 51.7 | 10201 |
| gemma3:4b | 1.000 | 1.99 | 154.8 | 0.824 | 55.4 | 17701 |
| mistral-nemo:latest | 0.945 | 2.83 | 91.0 | 0.713 | 78.6 | 13221 |
| mistral-small3.2:24b | 0.975 | 3.79 | 48.6 | 0.680 | 105.2 | 20975 |
| qwen3.5:27b | 0.992 | 4.92 | 38.6 | 0.656 | 136.7 | 20119 |
| qwen3.6:27b | 0.975 | 4.55 | 39.0 | 0.656 | 126.3 | 20111 |
| gpt-oss:20b | 0.233 | 3.24 | 145.3 | descartado | 90.0 | 14506 |

**Ganador:** `qwen2.5:7b-instruct`.

### 3.2 Conclusión de la selección

El modelo más grande **no** fue el óptimo para generar el corpus. Con calidad casi empatada entre varios instruct, la velocidad dominó el ranking. Los 24–27B mejoran poco la calidad percibida y multiplican el tiempo/VRAM.

Nota operativa: en modelos “reasoning” hizo falta desactivar thinking (`think: false`) para no contaminar la respuesta vacía en streaming.

---

## 4. Corpus de entrenamiento

| Campo | Valor |
|---|---|
| Generador | `qwen2.5:7b-instruct` |
| Historias aceptadas | 100 000 (+6 residuales en disco → 100 006) |
| Intentos / rechazos | 100 357 / 358 (accept rate ≈ 99.6 %) |
| Tiempo de generación | ≈ **35.3 h** (126 980 s) |
| Ritmo | ≈ 2835 historias/h |
| Throughput medio | ≈ 140 tok/s |
| Longitud media | ≈ 110 palabras / ≈ 621 caracteres |
| Formato | shards JSON `[{"story": "..."}, ...]` · `shard_size=5000` |
| Seed generación | **42** |
| Ubicación local | `data/TinyStoriesES_all_data/` (**no versionado**; ~65 MB) |

Filtros aplicados: español, longitud razonable, inclusión de palabras pedidas, baja repetición.  
API Ollama: `stream=True`, `think=False`, `temperature=0.9`, `num_predict=450`, `num_gpu=99`, concurrency 2.

Muestra ilustrativa: [open_science/sample_stories.json](open_science/sample_stories.json).  
Métricas de generación: [open_science/corpus_generation_summary.json](open_science/corpus_generation_summary.json).

---

## 5. Adaptaciones para español

1. **Corpus sintético ES** en lugar de TinyStories inglés.
2. **Lista de vocabulario simple** (`data/vocab_es_simple.txt`, ~1231 entradas) para condicionar prompts (sustantivos/verbos/adjetivos infantiles).
3. **Tokenizer SentencePiece custom** (no Llama-2 32k): mejor cobertura del español y embeddings mucho más chicos.
4. **CLI no interactiva** en `tinystories.py` (`--data_dir`, `--keep_tiny` / `--delete_tiny`, `--character_coverage`) para pipelines headless.
5. Inferencia final **sin cambios** a `run.c`: mismos binarios `.bin` + tokenizer `.bin` vía `-z`.

---

## 6. Tokenizer SentencePiece (detalle)

Entrenado con `sentencepiece.SentencePieceTrainer` desde `tinystories.py train_vocab`, sobre texto concatenado de hasta **10 shards** del corpus ES (`data/tiny.txt`).

### 6.1 Hiperparámetros SentencePiece

| Parámetro | Valor |
|---|---|
| Librería | `sentencepiece` (entorno del run: **0.2.2**; `requirements.txt` del upstream lista 0.1.99) |
| `model_type` | **`bpe`** |
| `input_format` | `text` |
| `byte_fallback` | `True` |
| `split_digits` | `True` |
| `allow_whitespace_only_pieces` | `True` |
| `normalization_rule_name` | `identity` (sin NFKC / sin reordenar Unicode) |
| `unk_surface` | espacio + U+2077 (igual que upstream) |
| `self_test_sample_size` | `0` |
| Shards usados para vocab | 10 (eficiencia; no el corpus entero) |

### 6.2 Variantes usadas en este trabajo

| Artefacto | `vocab_size` | `character_coverage` | Modelo destino | Tokens pretok (aprox.) | Avg seq len |
|---|---:|---:|---|---:|---:|
| `data/tok512.model` → `tok512.bin` | 512 | **0.9995** (auto si vocab ≤1024 y coverage pedida ≥1.0) | ES ~260K | 32 026 456 | 320.3 |
| `data/tok4096.model` → `tok4096.bin` | 4096 | **0.9995** (fijado en el run 15M) | ES ~7.2M | 15 440 163 | 154.4 |

**Por qué bajar coverage:** con vocab 512 y `character_coverage=1.0`, el conjunto de caracteres Unicode del español (tildes, ñ, signos, etc.) + meta-pieces supera el tamaño del vocab y SentencePiece falla (`Vocabulary size is smaller than required_chars`). Con `0.9995` + `byte_fallback`, los caracteres raros se representan por bytes.

**Export a formato `run.c`:**

```bash
python tokenizer.py --tokenizer-model=data/tok512.model   # → data/tok512.bin
python tokenizer.py --tokenizer-model=data/tok4096.model  # → data/tok4096.bin
```

Resúmenes machine-readable: [vocab_pretok_512_summary.json](open_science/vocab_pretok_512_summary.json), [vocab_pretok_4096_summary.json](open_science/vocab_pretok_4096_summary.json).

**Split train/val del pretok (upstream):** shard `data00.bin` = validación; el resto = train (`PretokDataset`, seed de RNG **42**).

---

## 7. Modelos entrenados

### 7.1 TinyStories ES ~260K

| Campo | Valor |
|---|---|
| Run id | `20260805_125324` |
| Arquitectura | `dim=64`, `n_layers=5`, `n_heads=8`, `n_kv_heads=4`, `multiple_of=4`, `max_seq_len=512` |
| Vocab | custom **512** |
| Optim | lr `1e-3`, dropout `0.05`, wd `0.01`, β2 `0.99`, warmup 1000, batch 128 |
| Iters | 100 000 · wall ~36.5 min · VRAM peak ~2.8 GB |
| Loss final | train **1.401** · val **1.407** |
| Infer CPU | ~5–7k tok/s |
| Out | `out_es_260k/` (**no versionado**) |

Launch exacto: [open_science/train_es_260k_launch.json](open_science/train_es_260k_launch.json) · resumen: [experiment_es_260k_SUMMARY.md](open_science/experiment_es_260k_SUMMARY.md).

### 7.2 TinyStories ES “15M” (efectivo ~7.2M)

| Campo | Valor |
|---|---|
| Run id | `20260807_190503` |
| Arquitectura | `dim=288`, `n_layers=6`, `n_heads=6`, `n_kv_heads=6`, `multiple_of=32`, `max_seq_len=256` |
| Vocab | custom **4096** (por eso ~7.2M params, no 15M del EN con Llama-32k) |
| Optim | lr `5e-4`, dropout `0.0`, wd `0.1`, β2 `0.95`, warmup 1000, batch 128 |
| Iters | 100 000 · wall ~85 min · VRAM peak ~4.6 GB |
| Loss final | train **0.961** · val **3.231** → **overfit** |
| Infer CPU | ~227 tok/s |
| Out | `out_es_15M/` (**no versionado**) |

Launch exacto: [open_science/train_es_15M_launch.json](open_science/train_es_15M_launch.json) · resumen: [experiment_es_15M_SUMMARY.md](open_science/experiment_es_15M_SUMMARY.md).

---

## 8. Comparación cualitativa (primera lectura)

| Modelo | Fortaleza | Debilidad observada |
|---|---|---|
| ES 260K | Español reconocible, barato, estable en loss | Frases cortas, repeticiones, lógica débil |
| ES ~7.2M | Más extensión y algo más de estructura | Overfit; rarezas semánticas (“atrapar un árbol”, colores inconsistentes) |
| EN 260K / 15M (referencia) | Más fluidez relativa | Dominio inglés; corpus original mucho más grande |

Con **100k** historias el 260K parece bien dimensionado; el modelo intermedio **necesita más datos** (u early stopping) para que el val loss acompañe al train.

---

## 9. Conclusiones preliminares

1. **La réplica a español es viable** end-to-end con Ollama + `llama2.c`, sin tocar la inferencia C.
2. **El cuello de botella actual es el volumen/calidad del corpus**, no la arquitectura en sí.
3. **Elegir generador por tradeoff calidad/velocidad importa**: el 7B ganó a modelos 3–4× más grandes.
4. **Tokenizer BPE custom + coverage 0.9995 + byte_fallback** son adaptaciones necesarias para español con vocabs chicos.
5. **Más parámetros sin más datos empeora la generalización** (gap train/val del ~7.2M).
6. Para un objetivo tipo ESP32, el camino natural es: ampliar corpus → reentrenar el intermedio → cuantizar int8 (`runq`) → portar; PLE/offload a flash solo si se necesita más capacidad.

---

## 10. Limitaciones

- Evaluación de generadores y de los baby models es en gran parte **heurística / smoke test**, no benchmark humano ciego ni métricas tipo GPT-judge sistemático post-train.
- Corpus 100k ≪ escala típica TinyStories inglés (~2M historias en recetas de referencia).
- Los pesos y el corpus completo **no están en git** (tamaño); la reproducibilidad depende de regenerar o publicar en otro canal (HF/Zenodo).
- Un solo seed de generación de corpus (`42`) / un solo run de train por tamaño; no hay barrido de hiperparámetros.
- El commit git registrado en `meta.json` del run 260K es el upstream `350e04f…` (antes de pushear el pipeline ES); el código de scripts vive en el fork actual.

---

## 11. Reproducibilidad

### 11.1 Entorno de los runs

| Componente | Valor observado |
|---|---|
| Host | `mebordone-PC` |
| OS | Linux 6.8.x · glibc 2.39 · x86_64 |
| GPU | NVIDIA GeForce RTX 3090 24 GB |
| Driver (meta del run) | 580.159.03 |
| Python | 3.12.3 (venv local `.venv`) |
| PyTorch | 2.6.0+cu124 (CUDA 12.4) |
| sentencepiece | 0.2.2 |
| Ollama | 0.30.8 (API local; GPU) |
| Generador corpus | `qwen2.5:7b-instruct` |
| Inferencia baby model | `./run` CPU (sin CUDA en `run.c`) |

Meta del run 260K: [open_science/run_es_260k_meta.json](open_science/run_es_260k_meta.json).

### 11.2 Semillas y defaults del pipeline de corpus

| Parámetro | Default usado |
|---|---|
| `--seed` (generate) | **42** |
| `--n` | 100000 |
| `--shard-size` | 5000 |
| `--concurrency` | 2 |
| `--temperature` | 0.9 |
| `--num-predict` | 450 |
| `--vocab` | `data/vocab_es_simple.txt` |
| Ollama `think` | `false` |
| Ollama `num_gpu` | 99 (forzar GPU) |

Eval de generadores: `temperature=0.8`, `num_predict=400`, `n_prompts=12`, `q_min=0.55`, score `0.55*Q + 0.45*S_norm` → [run_es_260k_eval_config.json](open_science/run_es_260k_eval_config.json).

### 11.3 Comandos de reproducción (checklist)

```bash
# 0) entorno
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
# (en esta máquina también: torch cu124 / sentencepiece actual)

# 1) eval generadores → winner
.venv/bin/python scripts/eval_ollama_generators.py

# 2) corpus (resume-friendly)
.venv/bin/python scripts/generate_tinystories_es.py \
  --model qwen2.5:7b-instruct --n 100000 --seed 42

# 3a) vocab 512 + pretok + export (modelo 260K)
.venv/bin/python tinystories.py train_vocab --vocab_size=512 \
  --data_dir=data/TinyStoriesES_all_data --character_coverage=0.9995
.venv/bin/python tinystories.py pretokenize --vocab_size=512 \
  --data_dir=data/TinyStoriesES_all_data
.venv/bin/python tokenizer.py --tokenizer-model=data/tok512.model

# 3b) vocab 4096 + pretok + export (modelo intermedio)
.venv/bin/python tinystories.py train_vocab --vocab_size=4096 \
  --data_dir=data/TinyStoriesES_all_data --character_coverage=0.9995
.venv/bin/python tinystories.py pretokenize --vocab_size=4096 \
  --data_dir=data/TinyStoriesES_all_data
.venv/bin/python tokenizer.py --tokenizer-model=data/tok4096.model

# 4) train (ver launch JSON publicados; ejemplo 260K)
.venv/bin/python scripts/train_with_metrics.py -- --out_dir=out_es_260k \
  --batch_size=128 --max_seq_len=512 --gradient_accumulation_steps=1 \
  --vocab_source=custom --vocab_size=512 \
  --dim=64 --n_layers=5 --n_heads=8 --n_kv_heads=4 --multiple_of=4 \
  --learning_rate=1e-3 --dropout=0.05 --weight_decay=0.01 \
  --max_iters=100000 --beta2=0.99 --warmup_iters=1000 \
  --eval_interval=2000 --eval_iters=100 --compile=True --device=cuda

# 5) inferencia
make run
./run out_es_260k/model.bin -z data/tok512.bin -t 0.8 -n 200 -i "Había una vez"
./run out_es_15M/model.bin  -z data/tok4096.bin -t 0.8 -n 200 -i "Había una vez"
```

### 11.4 Artefactos versionados vs locales

| Versionado en git | Solo local / publicar aparte |
|---|---|
| Scripts, informe, `doc/open_science/*` | Corpus `data/TinyStoriesES_all_data/` |
| `data/vocab_es_simple.txt` | Pesos `out_es_260k/`, `out_es_15M/` |
| `data/tok512.bin`, `data/tok4096.bin` | Logs crudos `experiments/**` (JSONL/stdout) |
| Launch/config/SUMMARY publicados | `.model`/`.vocab` SentencePiece (regenerables) |

---

## 12. Trabajo futuro sugerido

1. Ampliar corpus a 300–500k (mismo pipeline con resume).
2. Early stopping / checkpoint por mejor val loss en el modelo intermedio.
3. Export int8 y mediciones de calidad vs fp32.
4. Port ESP32-S3 (`runq` + flash mmap / PLE).
5. Publicar corpus + checkpoints en Hugging Face o Zenodo con DOI.
6. Fijar un `environment.yml` / lock de pip con las versiones exactas del run (torch cu124, sentencepiece, ollama).

---

## 13. Política de qué va en el repositorio

Ver [open_science/README.md](open_science/README.md). En corto: **código, docs, métricas livianas, configs de launch, tokenizers `.bin` chicos y muestras**; fuera de git: **corpus completo, pesos, logs crudos y entornos**.
