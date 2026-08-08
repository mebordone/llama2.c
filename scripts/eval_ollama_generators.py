#!/usr/bin/env python3
"""Evaluate Ollama text models for Spanish TinyStories generation (quality + speed + VRAM)."""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from exp_logger import ExperimentRun, sample_vram_mb  # noqa: E402

OLLAMA = "http://127.0.0.1:11434"
DEFAULT_MODELS = [
    "qwen3.6:27b",
    "qwen3.5:27b",
    "mistral-small3.2:24b",
    "gpt-oss:20b",
    "qwen3.5:9b",
    "llama3.1:8b",
    "mistral-nemo:latest",
    "qwen2.5:7b-instruct",
    "gemma3:4b",
    "phi4-mini:latest",
]

PROMPTS = [
    {
        "id": "p01",
        "words": ["decorar", "trueno", "antiguo"],
        "features": ["diálogo", "final triste"],
    },
    {
        "id": "p02",
        "words": ["compartir", "pelota", "rojo"],
        "features": ["diálogo", "moraleja"],
    },
    {
        "id": "p03",
        "words": ["buscar", "tesoro", "valiente"],
        "features": ["aventura"],
    },
    {
        "id": "p04",
        "words": ["ayudar", "abuela", "amable"],
        "features": ["diálogo"],
    },
    {
        "id": "p05",
        "words": ["volar", "mariposa", "brillante"],
        "features": ["giro inesperado"],
    },
    {
        "id": "p06",
        "words": ["cocinar", "sopa", "caliente"],
        "features": ["diálogo", "final feliz"],
    },
    {
        "id": "p07",
        "words": ["nadar", "río", "pequeño"],
        "features": ["moraleja"],
    },
    {
        "id": "p08",
        "words": ["dibujar", "estrella", "dorado"],
        "features": ["diálogo"],
    },
    {
        "id": "p09",
        "words": ["proteger", "gato", "asustado"],
        "features": ["conflicto"],
    },
    {
        "id": "p10",
        "words": ["plantar", "semilla", "verde"],
        "features": ["final feliz"],
    },
    {
        "id": "p11",
        "words": ["perdón", "hermano", "triste"],
        "features": ["diálogo", "moraleja"],
    },
    {
        "id": "p12",
        "words": ["explorar", "bosque", "oscuro"],
        "features": ["aventura", "giro inesperado"],
    },
]

ENGLISH_HINTS = re.compile(
    r"\b(the|and|was|were|said|once upon|little|girl|boy|they|with|that|this|have|from)\b",
    re.I,
)
SPANISH_CHARS = re.compile(r"[áéíóúñüÁÉÍÓÚÑÜ¿¡]")
COMMON_ES = re.compile(
    r"\b(el|la|los|las|un|una|de|que|y|en|a|es|se|no|hay|era|había|muy|con|para|por|como|más|pero|su|al|lo|le|sí|también|cuando|porque|después|entonces|dijo|niño|niña|mamá|papá)\b",
    re.I,
)


def build_prompt(spec: Dict[str, Any]) -> str:
    words = ", ".join(spec["words"])
    feats = ", ".join(spec["features"])
    return (
        "Escribe un cuento corto (2 a 4 párrafos) en español muy simple, "
        "con palabras que entienda un niño de 3 o 4 años. "
        f"Debes usar estas palabras: {words}. "
        f"El cuento debe incluir: {feats}. "
        "Solo responde con el cuento, sin título ni explicaciones. "
        "No uses inglés."
    )


def generate(model: str, prompt: str, options: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    t0 = time.perf_counter()
    first_token_t = None
    text_parts: List[str] = []
    eval_count = 0
    eval_duration = 0
    prompt_eval_count = 0
    with requests.post(
        f"{OLLAMA}/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": True,
            "think": False,  # disable reasoning models dumping into empty response
            "options": options,
        },
        stream=True,
        timeout=600,
    ) as r:
        r.raise_for_status()
        for line in r.iter_lines(decode_unicode=True):
            if not line:
                continue
            obj = json.loads(line)
            chunk = obj.get("response") or ""
            if chunk and first_token_t is None:
                first_token_t = time.perf_counter()
            text_parts.append(chunk)
            if obj.get("done"):
                eval_count = int(obj.get("eval_count") or 0)
                eval_duration = int(obj.get("eval_duration") or 0)
                prompt_eval_count = int(obj.get("prompt_eval_count") or 0)
    t1 = time.perf_counter()
    text = "".join(text_parts).strip()
    wall = t1 - t0
    tok_s = (eval_count / (eval_duration / 1e9)) if eval_duration > 0 else (
        eval_count / wall if wall > 0 else 0.0
    )
    return text, {
        "wall_sec": wall,
        "ttft_sec": (first_token_t - t0) if first_token_t else None,
        "eval_count": eval_count,
        "prompt_eval_count": prompt_eval_count,
        "tok_s": tok_s,
    }


def quality_score(text: str, words: List[str]) -> Dict[str, float]:
    if not text or len(text) < 40:
        return {
            "Q": 0.0,
            "spanish": 0.0,
            "length": 0.0,
            "words_hit": 0.0,
            "repetition": 0.0,
            "english_pen": 1.0,
        }
    low = text.lower()
    es_hits = len(COMMON_ES.findall(text))
    en_hits = len(ENGLISH_HINTS.findall(text))
    has_special = 1.0 if SPANISH_CHARS.search(text) else 0.5
    spanish = min(1.0, (es_hits / 12.0) * 0.7 + has_special * 0.3)
    english_pen = min(1.0, en_hits / 8.0)
    spanish = max(0.0, spanish - 0.5 * english_pen)

    nchars = len(text)
    # ideal ~250-900 chars for 2-4 short paragraphs
    if 200 <= nchars <= 1200:
        length = 1.0
    elif 100 <= nchars < 200 or 1200 < nchars <= 2000:
        length = 0.6
    else:
        length = 0.2

    hits = sum(1 for w in words if w.lower() in low)
    words_hit = hits / max(1, len(words))

    # repetition: repeated 5-grams
    toks = re.findall(r"\w+", low)
    rep = 0.0
    if len(toks) >= 20:
        grams = [" ".join(toks[i : i + 5]) for i in range(len(toks) - 4)]
        if grams:
            rep = 1.0 - (len(set(grams)) / len(grams))
    repetition = max(0.0, 1.0 - rep)

    Q = 0.35 * spanish + 0.20 * length + 0.30 * words_hit + 0.15 * repetition
    return {
        "Q": Q,
        "spanish": spanish,
        "length": length,
        "words_hit": words_hit,
        "repetition": repetition,
        "english_pen": english_pen,
    }


def list_installed() -> Dict[str, Dict[str, Any]]:
    r = requests.get(f"{OLLAMA}/api/tags", timeout=30)
    r.raise_for_status()
    return {m["name"]: m for m in r.json().get("models", [])}


def safe_name(model: str) -> str:
    return model.replace("/", "_").replace(":", "_")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", type=str, default=None)
    ap.add_argument("--models", nargs="*", default=None)
    ap.add_argument("--warmup", action="store_true", default=True)
    ap.add_argument("--temperature", type=float, default=0.8)
    ap.add_argument("--num-predict", type=int, default=400)
    ap.add_argument("--q-min", type=float, default=0.55)
    args = ap.parse_args()

    installed = list_installed()
    models = args.models or DEFAULT_MODELS
    models = [m for m in models if m in installed]
    missing = [m for m in (args.models or DEFAULT_MODELS) if m not in installed]
    if not models:
        raise SystemExit("No candidate models installed")

    config = {
        "stage": "eval_generators",
        "models": models,
        "missing_models": missing,
        "temperature": args.temperature,
        "num_predict": args.num_predict,
        "q_min": args.q_min,
        "n_prompts": len(PROMPTS),
        "score": "0.55*Q + 0.45*S_norm",
    }
    run = ExperimentRun(run_id=args.run_id, config=config)
    samples_root = ROOT / "data" / "eval_generators"
    samples_root.mkdir(parents=True, exist_ok=True)

    options = {
        "temperature": args.temperature,
        "num_predict": args.num_predict,
        "num_gpu": 99,  # use GPU layers aggressively
    }

    per_model: List[Dict[str, Any]] = []

    for model in models:
        print(f"\n=== Evaluating {model} ===", flush=True)
        mdir = samples_root / safe_name(model)
        mdir.mkdir(parents=True, exist_ok=True)
        vrams: List[float] = []
        rows = []
        # warmup
        try:
            generate(model, "Di hola en español en una frase.", {**options, "num_predict": 32})
        except Exception as e:
            print(f"warmup failed: {e}", flush=True)

        for spec in PROMPTS:
            prompt = build_prompt(spec)
            v0 = sample_vram_mb()
            try:
                text, timing = generate(model, prompt, options)
                err = None
            except Exception as e:
                text, timing, err = "", {"wall_sec": None, "tok_s": 0, "ttft_sec": None, "eval_count": 0}, str(e)
            v1 = sample_vram_mb()
            vrams.append(max(v0["memory_used_mb"], v1["memory_used_mb"]))
            q = quality_score(text, spec["words"])
            row = {
                "model": model,
                "prompt_id": spec["id"],
                "words": ",".join(spec["words"]),
                "error": err,
                **q,
                **{k: timing.get(k) for k in ("wall_sec", "tok_s", "ttft_sec", "eval_count")},
                "vram_used_mb": v1["memory_used_mb"],
            }
            rows.append(row)
            run.append_jsonl("eval_generators/per_prompt.jsonl", row)
            (mdir / f"{spec['id']}.txt").write_text(text + "\n", encoding="utf-8")
            print(
                f"  {spec['id']}: Q={q['Q']:.3f} wall={timing.get('wall_sec')} tok/s={timing.get('tok_s'):.1f}"
                if timing.get("wall_sec") is not None
                else f"  {spec['id']}: FAILED {err}",
                flush=True,
            )

        ok = [r for r in rows if r.get("wall_sec")]
        Q = sum(r["Q"] for r in ok) / len(ok) if ok else 0.0
        sec = sum(r["wall_sec"] for r in ok) / len(ok) if ok else float("inf")
        tok_s = sum(r["tok_s"] for r in ok) / len(ok) if ok else 0.0
        size_b = installed.get(model, {}).get("size") or 0
        summary = {
            "model": model,
            "Q": Q,
            "sec_per_story": sec,
            "tok_s": tok_s,
            "eta_100k_h": (sec * 100000) / 3600 if sec < float("inf") else None,
            "vram_peak_mb": max(vrams) if vrams else 0.0,
            "vram_avg_mb": sum(vrams) / len(vrams) if vrams else 0.0,
            "size_gb": size_b / 1e9,
            "n_ok": len(ok),
            "n_fail": len(rows) - len(ok),
        }
        per_model.append(summary)
        run.append_jsonl("eval_generators/per_model.jsonl", summary)

    # scoring
    speeds = [1.0 / m["sec_per_story"] for m in per_model if m["sec_per_story"] and m["sec_per_story"] < float("inf")]
    max_s = max(speeds) if speeds else 1.0
    for m in per_model:
        if m["sec_per_story"] and m["sec_per_story"] < float("inf"):
            s_norm = (1.0 / m["sec_per_story"]) / max_s
        else:
            s_norm = 0.0
        m["S_norm"] = s_norm
        eligible = m["Q"] >= args.q_min
        m["eligible"] = eligible
        m["score"] = (0.55 * m["Q"] + 0.45 * s_norm) if eligible else -1.0

    ranked = sorted(per_model, key=lambda x: (x["score"], x["S_norm"]), reverse=True)
    winner = ranked[0]["model"] if ranked and ranked[0]["score"] >= 0 else None
    if winner is None:
        # fallback: best Q among all
        winner = max(per_model, key=lambda x: x["Q"])["model"]
        print(f"WARNING: no model passed Q>={args.q_min}; falling back to best Q: {winner}")

    run.write_csv(
        "eval_generators/report.csv",
        ranked,
        fieldnames=[
            "model",
            "Q",
            "sec_per_story",
            "tok_s",
            "S_norm",
            "score",
            "eligible",
            "eta_100k_h",
            "vram_peak_mb",
            "vram_avg_mb",
            "size_gb",
            "n_ok",
            "n_fail",
        ],
    )

    lines = [
        "# Eval generadores TinyStories ES",
        "",
        f"Run: `{run.run_id}`",
        f"Winner: **{winner}**",
        "",
        "| model | Q | sec/hist | tok/s | S_norm | score | eligible | ETA 100k (h) | VRAM peak MB | size GB |",
        "|---|---:|---:|---:|---:|---:|---|---:|---:|---:|",
    ]
    for m in ranked:
        lines.append(
            f"| {m['model']} | {m['Q']:.3f} | {m['sec_per_story']:.2f} | {m['tok_s']:.1f} | "
            f"{m['S_norm']:.3f} | {m['score']:.3f} | {m['eligible']} | "
            f"{(m['eta_100k_h'] or 0):.1f} | {m['vram_peak_mb']:.0f} | {m['size_gb']:.1f} |"
        )
    report = "\n".join(lines) + "\n"
    run.write_text("eval_generators/report.md", report)
    (samples_root / "report.md").write_text(report, encoding="utf-8")
    (samples_root / "winner.txt").write_text(winner + "\n", encoding="utf-8")
    run.write_text("eval_generators/winner.txt", winner + "\n")
    run.write_json("eval_generators/ranking.json", ranked)
    print("\n" + report)
    print(f"Winner: {winner}")
    print(f"Artifacts: {run.root}")


if __name__ == "__main__":
    main()
