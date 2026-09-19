#!/usr/bin/env bash
# TinyStories interactive demo — EN/ES × small/large models
set -euo pipefail

DEMO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DEMO_DIR"

STEPS=150
TEMP=0.8
TOPP=0.9

LANG_UI="es"   # ui language for menus (follows model language choice)
MODEL_KEY=""
MODEL_LABEL=""
MODEL_BIN=""
TOK_BIN=""
START_TEXT=""

die() { echo "ERROR: $*" >&2; exit 1; }

need_files() {
  [[ -x "./run" || -f "./run" ]] || die "No está ./run. En esta carpeta ejecutá: make"
  [[ -f "$MODEL_BIN" ]] || die "Falta modelo: $MODEL_BIN (corré ./prepare_pack.sh en la PC)"
  [[ -f "$TOK_BIN" ]] || die "Falta tokenizer: $TOK_BIN"
}

t() {
  # bilingual short string: t "es text" "en text"
  if [[ "$LANG_UI" == "en" ]]; then
    printf '%s' "$2"
  else
    printf '%s' "$1"
  fi
}

banner() {
  clear 2>/dev/null || true
  cat <<EOF
========================================
  TinyStories Demo · EN / ES
  $(t "Modelos chicos que inventan cuentos" "Tiny models that invent stories")
  $(t "Offline · CPU · sin internet" "Offline · CPU · no internet")
========================================
EOF
}

help_experiment() {
  cat <<EOF

$(t "Sobre el experimento" "About the experiment")
----------------------------------------
$(t "TinyStories muestra que, con cuentos simples, un modelo muy chico puede generar texto coherente en ese dominio." "TinyStories shows that, with simple stories, a very small model can generate coherent text in that domain.")

$(t "Este demo incluye:" "This demo includes:")
  · EN 260K / EN 15M — Karpathy (llama2.c), inglés
  · ES 260K / ES ~7M — réplica en español (corpus sintético + train local)

$(t "El modelo chico es más rápido (ideal en netbooks)." "The small model is faster (ideal on netbooks).")
$(t "El grande puede tardar más y, en español, se entrenó con menos datos que el inglés." "The large one can be slower; the Spanish one was trained with less data than English.")

$(t "Tras cada cuento verás tiempo y velocidad (tok/s)." "After each story you will see time and speed (tok/s).")

EOF
  read -r -p "$(t "Enter para volver... " "Press Enter to return... ")" _
}

ask_lang() {
  echo
  echo "$(t "¿En qué idioma?" "Which language?")"
  echo "  1) Español"
  echo "  2) English"
  read -r -p "[1]: " ans
  ans="${ans:-1}"
  case "$ans" in
    2) LANG_UI="en" ;;
    *) LANG_UI="es" ;;
  esac
}

ask_size() {
  echo
  echo "$(t "¿Qué tamaño de modelo?" "Which model size?")"
  echo "  1) $(t "Chico  (~260K) — más rápido" "Small (~260K) — faster")"
  echo "  2) $(t "Grande (~15M)  — más lento" "Large (~15M)  — slower")"
  read -r -p "[1]: " ans
  ans="${ans:-1}"
  local size="260k"
  if [[ "$ans" == "2" ]]; then
    echo
    echo "$(t "Aviso: en una netbook vieja puede tardar bastante." "Note: on an old netbook this may take a while.")"
    read -r -p "$(t "¿Seguir? [s/N]: " "Continue? [y/N]: ")" conf
    conf="${conf:-n}"
    if [[ ! "$conf" =~ ^[sSyY]$ ]]; then
      size="260k"
    else
      size="15M"
    fi
  fi

  if [[ "$LANG_UI" == "es" ]]; then
    if [[ "$size" == "260k" ]]; then
      MODEL_KEY="es_260k"
      MODEL_LABEL="TinyStories ES ~260K"
      MODEL_BIN="models/es_260k.bin"
      TOK_BIN="models/es_260k_tok.bin"
    else
      MODEL_KEY="es_15M"
      MODEL_LABEL="TinyStories ES ~7.2M (arch 15M)"
      MODEL_BIN="models/es_15M.bin"
      TOK_BIN="models/es_15M_tok.bin"
    fi
  else
    if [[ "$size" == "260k" ]]; then
      MODEL_KEY="en_260k"
      MODEL_LABEL="TinyStories EN ~260K"
      MODEL_BIN="models/en_260k.bin"
      TOK_BIN="models/en_260k_tok.bin"
    else
      MODEL_KEY="en_15M"
      MODEL_LABEL="TinyStories EN ~15M"
      MODEL_BIN="models/en_15M.bin"
      TOK_BIN="models/en_15M_tok.bin"
    fi
  fi
}

ask_start() {
  START_TEXT=""
  echo
  echo "$(t "¿Cómo querés el cuento?" "How should the story start?")"
  echo "  1) $(t "Al azar (el modelo inventa desde cero)" "Random (model invents from scratch)")"
  echo "  2) $(t "Yo elijo cómo empieza" "I choose how it starts")"
  read -r -p "[1]: " ans
  ans="${ans:-1}"
  if [[ "$ans" == "2" ]]; then
    echo
    if [[ "$LANG_UI" == "es" ]]; then
      echo "¿Cómo empieza el cuento?"
      echo "(ej. Había una vez una niña en el bosque)"
    else
      echo "How does the story start?"
      echo "(e.g. Once upon a time there was a little girl)"
    fi
    read -r -p "> " START_TEXT
    # empty -> treat as random
    START_TEXT="$(printf '%s' "$START_TEXT" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  fi
}

run_story() {
  need_files
  echo
  echo "$(t "Generando con:" "Generating with:") $MODEL_LABEL"
  if [[ -n "$START_TEXT" ]]; then
    echo "$(t "Inicio:" "Start:") \"$START_TEXT\""
  else
    echo "$(t "Inicio: (al azar)" "Start: (random)")"
  fi
  echo "----------------------------------------"

  local stderr_file
  stderr_file="$(mktemp)"
  local t0 t1 wall_ms tok_s=""
  t0="$(date +%s%N 2>/dev/null || date +%s)"

  set +e
  if [[ -n "$START_TEXT" ]]; then
    ./run "$MODEL_BIN" -z "$TOK_BIN" -t "$TEMP" -p "$TOPP" -n "$STEPS" -i "$START_TEXT" \
      2>"$stderr_file"
  else
    ./run "$MODEL_BIN" -z "$TOK_BIN" -t "$TEMP" -p "$TOPP" -n "$STEPS" \
      2>"$stderr_file"
  fi
  local rc=$?
  set -e

  t1="$(date +%s%N 2>/dev/null || date +%s)"
  # wall seconds (support %N or whole seconds)
  if [[ "${#t0}" -gt 12 ]]; then
    wall_ms=$(( (t1 - t0) / 1000000 ))
  else
    wall_ms=$(( (t1 - t0) * 1000 ))
  fi
  local wall_s
  wall_s="$(awk -v ms="$wall_ms" 'BEGIN { printf "%.2f", ms/1000 }')"

  tok_s="$(grep -oE 'achieved tok/s: [0-9.]+' "$stderr_file" 2>/dev/null | tail -1 | awk '{print $3}')"
  # also show any other stderr errors
  if [[ "$rc" -ne 0 ]]; then
    echo
    echo "$(t "Falló la inferencia (código $rc)." "Inference failed (code $rc).")"
    cat "$stderr_file" >&2 || true
  fi
  rm -f "$stderr_file"

  echo "----------------------------------------"
  echo
  echo "$(t "-- Datos del demo --" "-- Demo stats --")"
  echo "$(t "Modelo:" "Model:") $MODEL_LABEL"
  if [[ -n "$START_TEXT" ]]; then
    echo "$(t "Inicio:" "Start:") \"$START_TEXT\""
  else
    echo "$(t "Inicio: (al azar)" "Start: (random)")"
  fi
  echo "$(t "Pasos (máx. tokens):" "Steps (max tokens):") $STEPS"
  echo "$(t "Tiempo:" "Time:") ${wall_s} s"
  if [[ -n "$tok_s" ]]; then
    echo "$(t "Velocidad:" "Speed:") ${tok_s} tok/s"
  else
    echo "$(t "Velocidad:" "Speed:") $(t "(no disponible)" "(n/a)")"
  fi
  echo "$(t "Hardware: CPU local · sin internet" "Hardware: local CPU · no internet")"
  echo
}

menu_loop() {
  while true; do
    banner
    ask_lang
    ask_size
    ask_start
    run_story

    while true; do
      echo "$(t "Enter = otro cuento (mismas opciones) · M = menú · H = ayuda · Q = salir" "Enter = another story (same options) · M = menu · H = help · Q = quit")"
      read -r -p "> " next
      next="$(printf '%s' "${next:-}" | tr '[:lower:]' '[:upper:]')"
      case "$next" in
        Q) echo "$(t "Chau." "Bye.")"; exit 0 ;;
        H) help_experiment; ;;
        M) break ;;
        "") run_story ;;
        *) run_story ;;
      esac
    done
  done
}

# Non-interactive smoke: DEMO_SMOKE=1 ./demo.sh
if [[ "${DEMO_SMOKE:-}" == "1" ]]; then
  LANG_UI="es"
  MODEL_KEY="es_260k"
  MODEL_LABEL="TinyStories ES ~260K"
  MODEL_BIN="models/es_260k.bin"
  TOK_BIN="models/es_260k_tok.bin"
  START_TEXT="${DEMO_SMOKE_START:-Había una vez}"
  STEPS="${DEMO_SMOKE_STEPS:-80}"
  run_story
  exit 0
fi

menu_loop
