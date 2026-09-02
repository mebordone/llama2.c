# TinyStories ES 260K — run `20260805_125324`

- GPU: NVIDIA GeForce RTX 3090 (24576.0 MB)
- Host: mebordone-PC
- Git: `350e04fe35433e6d2941dce5a1f53308f87058eb`

## Eval generadores

# Eval generadores TinyStories ES

Run: `20260805_125324`
Winner: **qwen2.5:7b-instruct**

| model | Q | sec/hist | tok/s | S_norm | score | eligible | ETA 100k (h) | VRAM peak MB | size GB |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|
| qwen2.5:7b-instruct | 0.983 | 1.21 | 130.8 | 1.000 | 0.991 | True | 33.7 | 19768 | 4.7 |
| phi4-mini:latest | 0.958 | 1.37 | 195.4 | 0.884 | 0.925 | True | 38.1 | 4400 | 2.5 |
| qwen3.5:9b | 0.983 | 1.86 | 105.8 | 0.651 | 0.834 | True | 51.7 | 22281 | 6.6 |
| llama3.1:8b | 0.983 | 1.86 | 125.7 | 0.651 | 0.834 | True | 51.7 | 10201 | 4.9 |
| gemma3:4b | 1.000 | 1.99 | 154.8 | 0.608 | 0.824 | True | 55.4 | 17701 | 3.3 |
| mistral-nemo:latest | 0.945 | 2.83 | 91.0 | 0.428 | 0.713 | True | 78.6 | 13221 | 7.1 |
| mistral-small3.2:24b | 0.975 | 3.79 | 48.6 | 0.320 | 0.680 | True | 105.2 | 20975 | 15.2 |
| qwen3.5:27b | 0.992 | 4.92 | 38.6 | 0.246 | 0.656 | True | 136.7 | 20119 | 17.4 |
| qwen3.6:27b | 0.975 | 4.55 | 39.0 | 0.267 | 0.656 | True | 126.3 | 20111 | 17.4 |
| gpt-oss:20b | 0.233 | 3.24 | 145.3 | 0.374 | -1.000 | False | 90.0 | 14506 | 13.8 |


## Corpus

- Modelo: `qwen2.5:7b-instruct`
- Aceptadas: 100000
- Rechazadas: 358
- Accept rate: 0.9964426995625617
- Historias/h: 2835.085711783326
- Elapsed s: 126980.28793406487

## Vocab / pretok

- vocab_size: 512
- tokenizer_model: data/tok512.model
- tokenizer_bin: data/tok512.bin
- tokenizer_bin_bytes: 6255
- n_bin_shards: 20
- total_tokens: 32026456
- avg_seqlen: 320.26455999999996
- bin_bytes: {'data00.bin': 3209808, 'data01.bin': 3219808, 'data02.bin': 3195566, 'data03.bin': 3212824, 'data04.bin': 3185384, 'data05.bin': 3191000, 'data06.bin': 3202368, 'data07.bin': 3204456, 'data08.bin': 3199098, 'data09.bin': 3207706, 'data10.bin': 3188036, 'data11.bin': 3200318, 'data12.bin': 3207110, 'data13.bin': 3204766, 'data14.bin': 3223756, 'data15.bin': 3180986, 'data16.bin': 3222222, 'data17.bin': 3189254, 'data18.bin': 3206562, 'data19.bin': 3201884}
- timings: train_vocab_sec=3
pretokenize_sec=3


## Train

- returncode: 0
- elapsed_sec: 2190.5449039936066
- peak_vram_mb_observed: 2803.0
- stdout_log: /media/mebordone/Datos/programando_ando/llama2.c/experiments/20260805_125324/train/stdout.log

## Infer

### cmd_default.txt
```
./run out_es_260k/model.bin -z data/tok512.bin -t 1.0 -p 0.9 -n 150

```

### cmd_t0.txt
```
./run out_es_260k/model.bin -z data/tok512.bin -t 0.0 -n 200 -i "Había una vez"

```

### cmd_t08.txt
```
./run out_es_260k/model.bin -z data/tok512.bin -t 0.8 -n 200 -i "Un día, un niño"

```

### metrics.json
```
[
  {
    "file": "out_t0.txt",
    "tok_s": 5102.564103,
    "preview": "Había una vez un niño llamado Juanito. Juanito tenía un amigo muy especial que le gustaba mucho. Un día, su mamá le dijo: \"Juanito, vamos a jugar con tu casa\". Juanito se sentó en el suelo y empezó a correr por el camino.\n\nJuanito se sentó en el suelo y empezó a correr por el camino. De repente, vio que el cielo estaba muy bonito. Juanito se acercó a la casa y le dijo: \"No te preocupes, Juanito. Te ayudaré a correr\". Juanito asintió conachieved tok/s: 5102.564103\n\n"
  },
  {
    "file": "out_t08.txt",
    "tok_s": 6218.75,
    "preview": "Un día, un niño llamado Carlos quería ver las flores. En la tierrita, vio un robot grande y colorido. Era muy amable y le había dejado algo bonito.\n\nCarlos decidió que quería jugar con sus muñecas en la plaza. Decidió ayudar a su abuelo y fue a despertar más hasta que volvieron a ver sus mejores amigos.\n\nCarlos se sintió mejor y les dijo: \"Estamos ayudando a sus amigos por venir cosas frescas\". Carlos se dio cuenta de queachieved tok/s: 6218.750000\n\n"
  },
  {
    "file": "out_default.txt",
    "tok_s": 6772.727273,
    "preview": "Un día, en una ciudad bonita, vivía una niña llamada María. María solía tocar cosas por el parque para jugar con él porque quería saber cómo ella tenía que regresar a la puerta de su propia plaza.\n\nUn día, María volvió a estar tranquila, pero agradeció a María saludar a Juan. María estaba muy orgullosa de su mamáachieved tok/s: 6772.727273\n\n"
  }
]

```

### out_default.txt
```
Un día, en una ciudad bonita, vivía una niña llamada María. María solía tocar cosas por el parque para jugar con él porque quería saber cómo ella tenía que regresar a la puerta de su propia plaza.

Un día, María volvió a estar tranquila, pero agradeció a María saludar a Juan. María estaba muy orgullosa de su mamáachieved tok/s: 6772.727273


```

### out_t0.txt
```
Había una vez un niño llamado Juanito. Juanito tenía un amigo muy especial que le gustaba mucho. Un día, su mamá le dijo: "Juanito, vamos a jugar con tu casa". Juanito se sentó en el suelo y empezó a correr por el camino.

Juanito se sentó en el suelo y empezó a correr por el camino. De repente, vio que el cielo estaba muy bonito. Juanito se acercó a la casa y le dijo: "No te preocupes, Juanito. Te ayudaré a correr". Juanito asintió conachieved tok/s: 5102.564103


```

### out_t08.txt
```
Un día, un niño llamado Carlos quería ver las flores. En la tierrita, vio un robot grande y colorido. Era muy amable y le había dejado algo bonito.

Carlos decidió que quería jugar con sus muñecas en la plaza. Decidió ayudar a su abuelo y fue a despertar más hasta que volvieron a ver sus mejores amigos.

Carlos se sintió mejor y les dijo: "Estamos ayudando a sus amigos por venir cosas frescas". Carlos se dio cuenta de queachieved tok/s: 6218.750000


```

### time_t0.txt
```
wall_sec=0.04 rss_kb=3456

```

### time_t08.txt
```
wall_sec=0.03 rss_kb=3456

```


## Highlights

- Generador Ollama: `qwen2.5:7b-instruct` (ganador calidad/velocidad)
- Corpus: 100000 historias ES, 20 shards
- Tokenizer: vocab 512, `character_coverage=0.9995` (necesario por Unicode; byte_fallback)
- Train: 100000 iters, val loss final **1.4071**, wall ~2191s (~36.5 min), VRAM peak ~2803 MB
- Infer CPU `./run out_es_260k/model.bin -z data/tok512.bin` → ~5k–6.7k tok/s

### Comando de inferencia

```bash
./run out_es_260k/model.bin -z data/tok512.bin -i "Había una vez"
```

