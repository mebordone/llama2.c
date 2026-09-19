# TinyStories Demo (netbook)

Paquete autocontenido para probar **4 modelos** TinyStories (inglés/español × chico/grande) en una netbook con poco RAM (antiX / Atom, etc.).

Todo corre **offline** en CPU con `run.c` (llama2.c).

## Preparar en la PC de desarrollo

Desde la raíz del repo `llama2.c` (con los modelos ya entrenados/descargados):

```bash
./demo/prepare_pack.sh
```

Eso copia los `.bin` a `demo/models/`, embebe `run.c` y deja listo el directorio `demo/`.

Opcional — tarball para USB:

```bash
tar czf tinystories-demo.tar.gz demo/
```

## En la netbook

```bash
cd demo
make          # compila ./run contra la glibc local (importante)
./demo.sh
```

Requisitos: `gcc` o `cc`, `make`, `bash`.

No uses el binario `run` compilado en Ubuntu moderno: suele fallar por versión de glibc. Compilá siempre en la netbook.

## Uso

1. Elegí idioma (Español / English)
2. Elegí tamaño (Chico ~260K más rápido · Grande ~15M más lento)
3. Al azar, o escribí **cómo empieza el cuento**
4. Al final: tiempo y tok/s del experimento

## Modelos incluidos

| Archivo | Origen |
|---|---|
| `models/en_260k.bin` + `_tok` | Karpathy stories260K |
| `models/es_260k.bin` + `_tok` | TinyStories ES 260K (este trabajo) |
| `models/en_15M.bin` + `_tok` | Karpathy stories15M |
| `models/es_15M.bin` + `_tok` | TinyStories ES ~7.2M (este trabajo) |

## Notas

- El modelo **grande** en un Atom N455 / 1 GB RAM puede ir lento; el chico es el default del demo.
- Los pesos `.bin` no van a git (ver `.gitignore`); sí el script y el código fuente.
