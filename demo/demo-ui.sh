#!/usr/bin/env bash
# TinyStories demo — whiptail UI (netbook-friendly). Portable fallback: ./demo.sh
set -euo pipefail

DEMO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DEMO_DIR"

STEPS=150
TEMP=0.8
TOPP=0.9

LANG_UI="es"
MODEL_KEY=""
MODEL_LABEL=""
MODEL_BIN=""
TOK_BIN=""
START_TEXT=""

die() { echo "ERROR: $*" >&2; exit 1; }

if ! command -v whiptail >/dev/null 2>&1; then
  echo "Este script necesita whiptail." >&2
  echo "Instalalo (apt install whiptail) o usá la versión portable: ./demo.sh" >&2
  exit 1
fi

need_files() {
  [[ -x "./run" || -f "./run" ]] || die "No está ./run. En esta carpeta ejecutá: make"
  [[ -f "$MODEL_BIN" ]] || die "Falta modelo: $MODEL_BIN (corré ./prepare_pack.sh en la PC)"
  [[ -f "$TOK_BIN" ]] || die "Falta tokenizer: $TOK_BIN"
}

wt() {
  # Run whiptail; on Cancel (exit 1) return 1 without aborting set -e callers that check $?
  set +e
  whiptail "$@"
  local rc=$?
  set -e
  return "$rc"
}

welcome() {
  wt --title "TinyStories Demo" --msgbox \
    "Modelos chicos que inventan cuentos.\n\n4 modelos · EN / ES · offline · CPU\nSin internet.\n\nEnter para empezar." \
    12 50 || true
}

show_about() {
  wt --title "Sobre el experimento" --msgbox \
    "TinyStories: con cuentos simples, un modelo muy chico puede generar texto coherente.\n\n\
EN 260K / EN 15M — Karpathy (llama2.c)\n\
ES 260K / ES ~7M — réplica en español (100k cuentos sintéticos)\n\n\
Tras cada cuento verás tiempo y velocidad (tok/s).\n\n\
Versión portable sin whiptail: ./demo.sh" \
    18 60 || true
}

pick_model() {
  local choice
  set +e
  choice=$(whiptail --title "Elegí el modelo" --default-item "es_260k" --menu \
    "Idioma y tamaño (sin confirmaciones extra):" 16 60 5 \
    "es_260k" "Español · Chico (~260K)" \
    "es_15M"  "Español · Grande (~7M)" \
    "en_260k" "English · Small (~260K)" \
    "en_15M"  "English · Large (~15M)" \
    "about"   "Sobre el experimento" \
    3>&1 1>&2 2>&3)
  local rc=$?
  set -e
  [[ "$rc" -eq 0 ]] || return 1

  if [[ "$choice" == "about" ]]; then
    show_about
    pick_model
    return $?
  fi

  MODEL_KEY="$choice"
  case "$MODEL_KEY" in
    es_260k)
      LANG_UI="es"
      MODEL_LABEL="TinyStories ES ~260K"
      MODEL_BIN="models/es_260k.bin"
      TOK_BIN="models/es_260k_tok.bin"
      ;;
    es_15M)
      LANG_UI="es"
      MODEL_LABEL="TinyStories ES ~7.2M (arch 15M)"
      MODEL_BIN="models/es_15M.bin"
      TOK_BIN="models/es_15M_tok.bin"
      ;;
    en_260k)
      LANG_UI="en"
      MODEL_LABEL="TinyStories EN ~260K"
      MODEL_BIN="models/en_260k.bin"
      TOK_BIN="models/en_260k_tok.bin"
      ;;
    en_15M)
      LANG_UI="en"
      MODEL_LABEL="TinyStories EN ~15M"
      MODEL_BIN="models/en_15M.bin"
      TOK_BIN="models/en_15M_tok.bin"
      ;;
    *) die "Modelo desconocido: $MODEL_KEY" ;;
  esac
  return 0
}

pick_start() {
  START_TEXT=""
  local mode
  set +e
  if [[ "$LANG_UI" == "es" ]]; then
    mode=$(whiptail --title "Cómo empieza el cuento" --default-item "random" --menu \
      "Elegí una opción:" 14 55 3 \
      "random"  "Al azar" \
      "example" "Elegir un ejemplo" \
      "custom"  "Escribir cómo empieza" \
      3>&1 1>&2 2>&3)
  else
    mode=$(whiptail --title "How the story starts" --default-item "random" --menu \
      "Choose one:" 14 55 3 \
      "random"  "Random" \
      "example" "Pick an example" \
      "custom"  "Type how it starts" \
      3>&1 1>&2 2>&3)
  fi
  local rc=$?
  set -e
  [[ "$rc" -eq 0 ]] || return 1

  case "$mode" in
    random)
      START_TEXT=""
      ;;
    example)
      local ex
      set +e
      if [[ "$LANG_UI" == "es" ]]; then
        ex=$(whiptail --title "Ejemplos de inicio" --radiolist \
          "Elegí un inicio (espacio para marcar):" 16 70 4 \
          "1" "Había una vez una niña en el bosque" ON \
          "2" "Un día, un niño encontró una llave dorada" OFF \
          "3" "En un pueblo pequeño vivía un gato curioso" OFF \
          "4" "La abuela preparaba una sopa caliente" OFF \
          3>&1 1>&2 2>&3)
      else
        ex=$(whiptail --title "Example openings" --radiolist \
          "Pick a start (space to select):" 16 70 4 \
          "1" "Once upon a time there was a little girl" ON \
          "2" "One day a boy found a golden key" OFF \
          "3" "In a small town lived a curious cat" OFF \
          "4" "Grandma was making a warm soup" OFF \
          3>&1 1>&2 2>&3)
      fi
      rc=$?
      set -e
      [[ "$rc" -eq 0 ]] || return 1
      case "$ex" in
        1) START_TEXT="$([[ "$LANG_UI" == "es" ]] && echo "Había una vez una niña en el bosque" || echo "Once upon a time there was a little girl")" ;;
        2) START_TEXT="$([[ "$LANG_UI" == "es" ]] && echo "Un día, un niño encontró una llave dorada" || echo "One day a boy found a golden key")" ;;
        3) START_TEXT="$([[ "$LANG_UI" == "es" ]] && echo "En un pueblo pequeño vivía un gato curioso" || echo "In a small town lived a curious cat")" ;;
        4) START_TEXT="$([[ "$LANG_UI" == "es" ]] && echo "La abuela preparaba una sopa caliente" || echo "Grandma was making a warm soup")" ;;
        *) START_TEXT="" ;;
      esac
      ;;
    custom)
      local typed
      set +e
      if [[ "$LANG_UI" == "es" ]]; then
        typed=$(whiptail --title "Cómo empieza el cuento" --inputbox \
          "Escribí el inicio (vacío = al azar):" 10 60 \
          "Había una vez" \
          3>&1 1>&2 2>&3)
      else
        typed=$(whiptail --title "How the story starts" --inputbox \
          "Type the opening (empty = random):" 10 60 \
          "Once upon a time" \
          3>&1 1>&2 2>&3)
      fi
      rc=$?
      set -e
      [[ "$rc" -eq 0 ]] || return 1
      START_TEXT="$(printf '%s' "$typed" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
      ;;
  esac
  return 0
}

run_story() {
  need_files
  clear 2>/dev/null || true
  echo "========================================"
  echo "  $MODEL_LABEL"
  if [[ -n "$START_TEXT" ]]; then
    echo "  Inicio: \"$START_TEXT\""
  else
    echo "  Inicio: (al azar)"
  fi
  echo "  Generando… ($STEPS tokens máx.)"
  echo "========================================"
  echo

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
  if [[ "${#t0}" -gt 12 ]]; then
    wall_ms=$(( (t1 - t0) / 1000000 ))
  else
    wall_ms=$(( (t1 - t0) * 1000 ))
  fi
  local wall_s
  wall_s="$(awk -v ms="$wall_ms" 'BEGIN { printf "%.2f", ms/1000 }')"
  tok_s="$(grep -oE 'achieved tok/s: [0-9.]+' "$stderr_file" 2>/dev/null | tail -1 | awk '{print $3}')"

  if [[ "$rc" -ne 0 ]]; then
    local error_text
    error_text="$(cat "$stderr_file" 2>/dev/null || true)"
    rm -f "$stderr_file"
    wt --title "No se pudo generar" --msgbox \
      "La inferencia falló (código $rc).\n\n${error_text:0:500}\n\nVolverás al menú de modelos." \
      16 65 || true
    return 1
  fi
  rm -f "$stderr_file"

  echo
  echo "----------------------------------------"
  read -r -p "Enter para ver las métricas… " _

  local start_line speed_line
  if [[ -n "$START_TEXT" ]]; then
    start_line="Inicio: \"$START_TEXT\""
  else
    start_line="Inicio: (al azar)"
  fi
  if [[ -n "$tok_s" ]]; then
    speed_line="Velocidad: ${tok_s} tok/s"
  else
    speed_line="Velocidad: (no disponible)"
  fi

  wt --title "Datos del demo" --msgbox \
    "Modelo: $MODEL_LABEL\n\
$start_line\n\
Pasos (máx. tokens): $STEPS\n\
Tiempo: ${wall_s} s\n\
$speed_line\n\
Hardware: CPU local · sin internet" \
    14 60 || true
}

pick_next_action() {
  local action
  set +e
  if [[ "$LANG_UI" == "es" ]]; then
    action=$(whiptail --title "¿Qué querés hacer?" --default-item "same" --menu \
      "Elegí el siguiente paso:" 15 62 4 \
      "same"  "Otro cuento con la misma configuración" \
      "start" "Cambiar cómo empieza" \
      "model" "Cambiar modelo / empezar de nuevo" \
      "exit"  "Salir" \
      3>&1 1>&2 2>&3)
  else
    action=$(whiptail --title "What next?" --default-item "same" --menu \
      "Choose the next step:" 15 62 4 \
      "same"  "Another story with the same settings" \
      "start" "Change how the story starts" \
      "model" "Change model / start over" \
      "exit"  "Quit" \
      3>&1 1>&2 2>&3)
  fi
  local rc=$?
  set -e
  if [[ "$rc" -ne 0 ]]; then
    printf '%s' "exit"
  else
    printf '%s' "$action"
  fi
}

main() {
  local state="model"
  local action

  welcome
  while true; do
    case "$state" in
      model)
        if pick_model; then
          state="start"
        else
          echo "Chau."
          exit 0
        fi
        ;;
      start)
        if pick_start; then
          state="run"
        else
          # Cancelar vuelve al selector anterior en lugar de cerrar el demo.
          state="model"
        fi
        ;;
      run)
        if ! run_story; then
          state="model"
          continue
        fi
        action="$(pick_next_action)"
        case "$action" in
          same)  state="run" ;;
          start) state="start" ;;
          model) state="model" ;;
          exit)
            echo "Chau."
            exit 0
            ;;
          *) state="model" ;;
        esac
        ;;
    esac
  done
}

main
