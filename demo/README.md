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
```

Luego elegí la interfaz:

| Script | Cuándo usarlo |
|---|---|
| `./demo.sh` | **Portable** — solo bash; anda en cualquier lado |
| `./demo-ui.sh` | **Demo linda** — requiere `whiptail` (recomendado en la netbook) |

```bash
./demo.sh      # base
./demo-ui.sh   # menús whiptail, menos fricción
```

Requisitos comunes: `gcc` o `cc`, `make`, `bash`.
Para `demo-ui.sh` además: `whiptail` (`apt install whiptail`).

No uses el binario `run` compilado en Ubuntu moderno: suele fallar por versión de glibc. Compilá siempre en la netbook.

## Uso (`demo-ui.sh`)

1. Elegí modelo (ES/EN × chico/grande) — **sin** avisos ni confirmaciones extra
2. Al azar, ejemplo, o escribí **cómo empieza el cuento**
3. Al final: tiempo y tok/s (150 tokens máx., igual que `demo.sh`)
4. Después de cada cuento elegí:
   - otro con la misma configuración (opción predeterminada)
   - cambiar solamente el inicio
   - cambiar modelo / empezar de nuevo
   - salir

Cancelar al elegir el inicio vuelve al selector de modelos; no cierra el demo.

## Modelos incluidos

| Archivo | Origen |
|---|---|
| `models/en_260k.bin` + `_tok` | Karpathy stories260K |
| `models/es_260k.bin` + `_tok` | TinyStories ES 260K (este trabajo) |
| `models/en_15M.bin` + `_tok` | Karpathy stories15M |
| `models/es_15M.bin` + `_tok` | TinyStories ES ~7.2M (este trabajo) |

## Notas

- En la netbook del demo, `demo-ui.sh` es la experiencia pensada para público.
- Los pesos `.bin` no van a git (ver `.gitignore`); sí el script y el código fuente.
