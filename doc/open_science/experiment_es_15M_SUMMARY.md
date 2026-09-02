# TinyStories ES 260K — run `20260807_190503`

- GPU: NVIDIA GeForce RTX 3090 (24576.0 MB)
- Host: mebordone-PC
- Git: `350e04fe35433e6d2941dce5a1f53308f87058eb`

## Vocab / pretok

- vocab_size: 4096
- tokenizer_model: data/tok4096.model
- tokenizer_bin: data/tok4096.bin
- tokenizer_bin_bytes: 55577
- n_bin_shards: 20
- total_tokens: 15440163
- avg_seqlen: 154.40163
- bin_bytes: {'data00.bin': 1547768, 'data01.bin': 1554994, 'data02.bin': 1534162, 'data03.bin': 1549252, 'data04.bin': 1533800, 'data05.bin': 1540750, 'data06.bin': 1541854, 'data07.bin': 1545466, 'data08.bin': 1542070, 'data09.bin': 1546264, 'data10.bin': 1538052, 'data11.bin': 1541202, 'data12.bin': 1545478, 'data13.bin': 1546350, 'data14.bin': 1557292, 'data15.bin': 1531906, 'data16.bin': 1556692, 'data17.bin': 1541192, 'data18.bin': 1543500, 'data19.bin': 1542282}
- timings: train_vocab_sec=3
pretokenize_sec=2


## Train

- returncode: 0
- elapsed_sec: 5097.629076719284
- peak_vram_mb_observed: 4591.0
- stdout_log: /media/mebordone/Datos/programando_ando/llama2.c/experiments/20260807_190503/train/stdout.log

## Infer

### cmd_t0.txt
```
CMD: ./run out_es_15M/model.bin -z data/tok4096.bin -t 0.0 -n 200 -i "Había una vez"

```

### cmd_t08.txt
```
CMD: ./run out_es_15M/model.bin -z data/tok4096.bin -t 0.8 -n 200 -i "Un día"

```

### metrics.json
```
[
  {
    "file": "out_t0.txt",
    "tok_s": 226.648352
  },
  {
    "file": "out_t08.txt",
    "tok_s": 227.474151
  },
  {
    "file": "out_default.txt",
    "tok_s": 228.527607
  }
]

```

### out_default.txt
```
Un día, en un pequeño pueblo, vivía un perro llamado Pipo. Pipo tenía un amigo muy especial, un búhito rojo que le gustaba mucho. El búhito era amarillo y tenían plumas verdes brillantes.

Pipo decía: "Sol, ven a jugar conmigo". Pero su mejor amiga era una coneja llamada Clara. Clara era una lunita muy ligera, más que Pipo.

En el pueblo había un lugar donde nadie podía dormir bien y hacer frío. Un día, Clara le dijo a Pipo: "Vamos a traerte tu cobijita". Pipo se alegró mucho. Así, juntas la compartieron y soltaron una bonita cobijita.

En la pradera de Clara, su cobijita se veía como un dragón.achieved tok/s: 228.527607


```

### out_t0.txt
```
Había una vez un niño llamado Carlos. Carlos tenía un amigo llamado Pedro. Un día, Carlos y Pedro decidieron ir al parque para jugar. En el parque había muchos niños jugando. Carlos vio un gran árbol y dijo: "¡Vamos a ver si podemos atrapar un árbol!" Pedro asintió con la cabeza y los dos se acercaron al árbol.

Carlos tomó la mano de Pedro y juntos subieron al árbol. El árbol era muy alto, pero Carlos no se atrevía. "No puedo atrapar al árbol", dijo Carlos. Pedro rió y le dijo: "Yo te ayudaré a atraparlo". Juntos, con sus manos pequeñas, llevaron el árbol hasta un árbol.

Carlos y Pedro se sentaron en el pasto y disfrutaron de su juego. "Gracias por ayudarme", dijo Carlos. "Eres mi mejor amigo", respondió Pedro.achieved tok/s: 226.648352


```

### out_t08.txt
```
Un día, en un jardín muy bonito, vivía un niño llamado Juan. Juan era muy paciente y le gustaba mucho ayudar a su mamá.

Una mañana, Juan decidió que quería cosechar las flores del jardín. Le dijo a su mamá: "Mamá, quiero hacer una casa para mis muñecos".

Su mamá sonrió y le dijo: "Juan, primero debes recoger la flores. Eres paciente y paciente".

Juan fue al jardín y vio una flor hermosa en un arbol grande. Con cuidado, tomó las flores.

Las flores se vieron más bonitas que nunca. Juan sonrió muy contento.

Moraleja: Si queremos hacer algo, debemos ser pacientes y seguir las reglas para ayudar, sin dejarnos de trabajar.achieved tok/s: 227.474151


```


## Highlights (ES 15M)

- Corpus reutilizado: 100k historias ES
- Tokenizer custom **4096** (`data/tok4096.bin`)
- Arch OG: dim=288, layers=6, heads=6, seq=256
- Params ~7.2M (vocab menor que Llama2-32k del stories15M inglés)
- Train wall ~5098s (~85 min), VRAM peak ~4591 MB
- Final: train loss **0.961**, val loss **3.231** (overfit; dataset chico vs capacidad)
- Infer CPU ~227 tok/s

### Comando

```bash
./run out_es_15M/model.bin -z data/tok4096.bin -i "Había una vez"
```
