#!/usr/bin/env bash
# Assemble a self-contained demo/ pack: models + tokenizers + run.c
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEMO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODELS="$DEMO/models"

die() { echo "ERROR: $*" >&2; exit 1; }

need() {
  local path="$1"
  local label="$2"
  [[ -f "$path" ]] || die "faltá $label: $path"
}

echo "==> TinyStories demo pack"
echo "    repo: $ROOT"
echo "    demo: $DEMO"

need "$ROOT/run.c" "run.c"
need "$ROOT/stories260K/stories260K.bin" "EN 260K model"
need "$ROOT/stories260K/tok512.bin" "EN 260K tokenizer"
need "$ROOT/out_es_260k/model.bin" "ES 260K model"
need "$ROOT/data/tok512.bin" "ES 260K tokenizer"
need "$ROOT/stories15M.bin" "EN 15M model"
need "$ROOT/tokenizer.bin" "EN 15M tokenizer"
need "$ROOT/out_es_15M/model.bin" "ES 15M model"
need "$ROOT/data/tok4096.bin" "ES 15M tokenizer"

mkdir -p "$MODELS"

copy() {
  local src="$1" dst="$2"
  echo "  $src -> $dst"
  cp -f "$src" "$dst"
}

echo "==> Copiando modelos y tokenizers"
copy "$ROOT/stories260K/stories260K.bin" "$MODELS/en_260k.bin"
copy "$ROOT/stories260K/tok512.bin"      "$MODELS/en_260k_tok.bin"
copy "$ROOT/out_es_260k/model.bin"       "$MODELS/es_260k.bin"
copy "$ROOT/data/tok512.bin"             "$MODELS/es_260k_tok.bin"
copy "$ROOT/stories15M.bin"              "$MODELS/en_15M.bin"
copy "$ROOT/tokenizer.bin"               "$MODELS/en_15M_tok.bin"
copy "$ROOT/out_es_15M/model.bin"        "$MODELS/es_15M.bin"
copy "$ROOT/data/tok4096.bin"            "$MODELS/es_15M_tok.bin"

echo "==> Embebiendo run.c"
cp -f "$ROOT/run.c" "$DEMO/run.c"

chmod +x "$DEMO/demo.sh" "$DEMO/prepare_pack.sh" 2>/dev/null || true

echo "==> Listo. Contenido de models/:"
ls -lh "$MODELS"/*.bin

cat <<EOF

Siguiente:
  cd demo && make && ./demo.sh

Para la netbook:
  tar czf tinystories-demo.tar.gz -C "$(dirname "$DEMO")" "$(basename "$DEMO")"
  # copiá el .tar.gz, allá: tar xzf ... && cd demo && make && ./demo.sh
EOF
