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
| Formato | shards JSON `[{"story": "..."}, ...]` |
| Ubicación local | `data/TinyStoriesES_all_data/` (**no versionado**; ~65 MB) |

Filtros aplicados: español, longitud razonable, inclusión de palabras pedidas, baja repetición.

Muestra ilustrativa: [open_science/sample_stories.json](open_science/sample_stories.json).  
Métricas de generación: [open_science/corpus_generation_summary.json](open_science/corpus_generation_summary.json).

---

## 5. Adaptaciones para español

1. **Corpus sintético ES** en lugar de TinyStories inglés.
2. **Lista de vocabulario simple** (`data/vocab_es_simple.txt`) para condicionar prompts (sustantivos/verbos/adjetivos infantiles).
3. **Tokenizer SentencePiece custom** (no Llama-2 32k), porque el español se fragmenta peor con un vocab inglés grande y además infla embeddings.
4. **`character_coverage=0.9995`** en vocabs ≤1024: con coverage 1.0 y Unicode (tildes, ñ, signos), `required_chars` supera el vocab y falla el train de SentencePiece; se apoya en `byte_fallback`.
5. **CLI no interactiva** en `tinystories.py` (`--data_dir`, `--keep_tiny` / delete) para pipelines headless.
6. Inferencia final **sin cambios** a `run.c`: mismos binarios `.bin` + tokenizer `.bin` vía `-z`.

---

## 6. Modelos entrenados

### 6.1 TinyStories ES ~260K

- Arquitectura: igual a `stories260K` (`dim=64`, 5 layers, 8 heads, 4 kv heads, seq 512, vocab **512**).
- Train: 100 000 iters · ~36.5 min · VRAM peak ~2.8 GB.
- **Val loss final: 1.407** (train 1.401).
- Inferencia CPU: ~5–7k tok/s.
- Artefactos locales: `out_es_260k/` (**no versionado**).
- Resumen: [open_science/experiment_es_260k_SUMMARY.md](open_science/experiment_es_260k_SUMMARY.md).

### 6.2 TinyStories ES “15M” (efectivo ~7.2M)

- Arquitectura OG tipo `stories15M` (`dim=288`, 6 layers, 6 heads, seq 256) con vocab **4096** (no 32k).
- Por el vocab reducido, los parámetros efectivos son ~**7.2M**, no 15M.
- Train: 100 000 iters · ~85 min · VRAM peak ~4.6 GB.
- **Train loss 0.961 · val loss 3.231** → **overfitting claro**.
- Inferencia CPU: ~227 tok/s.
- Resumen: [open_science/experiment_es_15M_SUMMARY.md](open_science/experiment_es_15M_SUMMARY.md).

---

## 7. Comparación cualitativa (primera lectura)

| Modelo | Fortaleza | Debilidad observada |
|---|---|---|
| ES 260K | Español reconocible, barato, estable en loss | Frases cortas, repeticiones, lógica débil |
| ES ~7.2M | Más extensión y algo más de estructura | Overfit; rarezas semánticas (“atrapar un árbol”, colores inconsistentes) |
| EN 260K / 15M (referencia) | Más fluidez relativa | Dominio inglés; corpus original mucho más grande |

Con **100k** historias el 260K parece bien dimensionado; el modelo intermedio **necesita más datos** (u early stopping) para que el val loss acompañe al train.

---

## 8. Conclusiones preliminares

1. **La réplica a español es viable** end-to-end con Ollama + `llama2.c`, sin tocar la inferencia C.
2. **El cuello de botella actual es el volumen/calidad del corpus**, no la arquitectura en sí.
3. **Elegir generador por tradeoff calidad/velocidad importa**: el 7B ganó a modelos 3–4× más grandes.
4. **Tokenizer custom + coverage relajada** son adaptaciones necesarias para español con vocabs chicos.
5. **Más parámetros sin más datos empeora la generalización** (gap train/val del ~7.2M).
6. Para un objetivo tipo ESP32, el camino natural es: ampliar corpus → reentrenar el intermedio → cuantizar int8 (`runq`) → portar; PLE/offload a flash solo si se necesita más capacidad.

---

## 9. Limitaciones

- Evaluación de generadores y de los baby models es en gran parte **heurística / smoke test**, no benchmark humano ciego ni métricas tipo GPT-judge sistemático post-train.
- Corpus 100k ≪ escala típica TinyStories inglés (~2M historias en recetas de referencia).
- Los pesos y el corpus completo **no están en git** (tamaño); la reproducibilidad depende de regenerar o publicar en otro canal (HF/Zenodo).
- Un solo seed / un solo run por tamaño; no hay barrido de hiperparámetros.

---

## 10. Trabajo futuro sugerido

1. Ampliar corpus a 300–500k (mismo pipeline con resume).
2. Early stopping / checkpoint por mejor val loss en el modelo intermedio.
3. Export int8 y mediciones de calidad vs fp32.
4. Port ESP32-S3 (`runq` + flash mmap / PLE).
5. Publicar corpus + checkpoints en Hugging Face o Zenodo con DOI.

---

## 11. Política de qué va en el repositorio

Ver [open_science/README.md](open_science/README.md). En corto: **código, docs, métricas livianas, tokenizers chicos y muestras**; fuera de git: **corpus completo, pesos, logs crudos y entornos**.
