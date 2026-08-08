#!/usr/bin/env python3
"""Generate Spanish TinyStories corpus via Ollama (GPU), with resume + metrics."""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from exp_logger import ExperimentRun, load_latest_run, sample_vram_mb  # noqa: E402

OLLAMA = "http://127.0.0.1:11434"
ENGLISH_HINTS = re.compile(
    r"\b(the|and|was|were|said|once upon|little|girl|boy|they|with|that|this|have|from)\b",
    re.I,
)


def load_vocab(path: Path) -> Dict[str, List[str]]:
    out = {"NOUN": [], "VERB": [], "ADJ": []}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        t, w = line.split(None, 1)
        if t in out:
            out[t].append(w.strip())
    return out


def build_prompt(noun: str, verb: str, adj: str, features: List[str]) -> str:
    feats = ", ".join(features)
    return (
        "Escribe un cuento corto (2 a 4 párrafos) en español muy simple, "
        "con palabras que entienda un niño de 3 o 4 años. "
        f"Debes incluir estas palabras: verbo «{verb}», sustantivo «{noun}», adjetivo «{adj}». "
        f"El cuento debe tener: {feats}. "
        "Empieza de forma natural (por ejemplo «Había una vez» o «Un día»). "
        "Solo escribe el cuento, sin título ni notas. No uses inglés."
    )


FEATURES_POOL = [
    ["diálogo"],
    ["moraleja"],
    ["final feliz"],
    ["diálogo", "moraleja"],
    ["giro inesperado"],
    ["diálogo", "final feliz"],
    ["amistad"],
    ["diálogo", "amistad"],
]


def generate_one(model: str, prompt: str, options: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    t0 = time.perf_counter()
    text_parts: List[str] = []
    eval_count = 0
    eval_duration = 0
    with requests.post(
        f"{OLLAMA}/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": True,
            "think": False,
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
            text_parts.append(obj.get("response") or "")
            if obj.get("done"):
                eval_count = int(obj.get("eval_count") or 0)
                eval_duration = int(obj.get("eval_duration") or 0)
    text = "".join(text_parts).strip()
    wall = time.perf_counter() - t0
    tok_s = (eval_count / (eval_duration / 1e9)) if eval_duration > 0 else (
        eval_count / wall if wall > 0 else 0.0
    )
    return text, {"wall_sec": wall, "eval_count": eval_count, "tok_s": tok_s}


def accept_story(text: str, words: List[str]) -> Tuple[bool, str]:
    if not text or len(text) < 120:
        return False, "too_short"
    if len(text) > 2500:
        return False, "too_long"
    if len(ENGLISH_HINTS.findall(text)) >= 6:
        return False, "english"
    low = text.lower()
    hits = sum(1 for w in words if w.lower() in low)
    if hits < 1:
        return False, "missing_words"
    return True, "ok"


def read_winner() -> str:
    p = ROOT / "data" / "eval_generators" / "winner.txt"
    if not p.exists():
        raise SystemExit("winner.txt not found; run eval first")
    return p.read_text(encoding="utf-8").strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", type=str, default=None)
    ap.add_argument("--model", type=str, default=None)
    ap.add_argument("--n", type=int, default=100000)
    ap.add_argument("--shard-size", type=int, default=5000)
    ap.add_argument("--concurrency", type=int, default=2)
    ap.add_argument("--out-dir", type=str, default="data/TinyStoriesES_all_data")
    ap.add_argument("--vocab", type=str, default="data/vocab_es_simple.txt")
    ap.add_argument("--temperature", type=float, default=0.9)
    ap.add_argument("--num-predict", type=int, default=450)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--log-every", type=int, default=50)
    args = ap.parse_args()

    model = args.model or read_winner()
    out_dir = ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    state_path = out_dir / "generation_state.json"
    vocab = load_vocab(ROOT / args.vocab)
    rng = random.Random(args.seed)

    run = None
    if args.run_id:
        run = ExperimentRun(run_id=args.run_id)
    else:
        run = load_latest_run() or ExperimentRun()

    options = {"temperature": args.temperature, "num_predict": args.num_predict, "num_gpu": 99}

    # resume
    accepted = 0
    attempted = 0
    rejected = 0
    retries = 0
    shard_idx = 0
    shard_buf: List[Dict[str, str]] = []
    if state_path.exists():
        st = json.loads(state_path.read_text(encoding="utf-8"))
        accepted = st.get("accepted", 0)
        attempted = st.get("attempted", 0)
        rejected = st.get("rejected", 0)
        retries = st.get("retries", 0)
        shard_idx = st.get("shard_idx", 0)
        shard_path = out_dir / f"data{shard_idx:02d}.json"
        if shard_path.exists():
            shard_buf = json.loads(shard_path.read_text(encoding="utf-8"))
            # sync accepted with persisted stories if needed
            persisted = sum(
                len(json.loads(p.read_text(encoding="utf-8")))
                for p in out_dir.glob("data*.json")
            )
            if persisted > 0:
                accepted = persisted
                shard_idx = accepted // args.shard_size
                rem = accepted % args.shard_size
                if rem == 0 and accepted > 0:
                    # last shard is full; start a new empty buffer
                    shard_buf = []
                else:
                    cur = out_dir / f"data{shard_idx:02d}.json"
                    shard_buf = json.loads(cur.read_text(encoding="utf-8")) if cur.exists() else []
        print(f"Resuming: accepted={accepted} attempted={attempted} shard={shard_idx} buf={len(shard_buf)}", flush=True)

    def save_state():
        state_path.write_text(
            json.dumps(
                {
                    "accepted": accepted,
                    "attempted": attempted,
                    "rejected": rejected,
                    "retries": retries,
                    "shard_idx": shard_idx,
                    "model": model,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    def flush_shard(force: bool = False):
        nonlocal shard_idx, shard_buf
        if not shard_buf:
            return
        # Persist periodically (not every story) to balance durability vs I/O
        if (not force) and (len(shard_buf) % 50 != 0) and (len(shard_buf) < args.shard_size):
            return
        path = out_dir / f"data{shard_idx:02d}.json"
        path.write_text(json.dumps(shard_buf, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if len(shard_buf) >= args.shard_size:
            shard_idx += 1
            shard_buf = []

    t_start = time.time()
    wall_sum = 0.0
    tok_sum = 0.0
    n_timing = 0

    def one_job(i: int) -> Dict[str, Any]:
        noun = rng.choice(vocab["NOUN"])
        verb = rng.choice(vocab["VERB"])
        adj = rng.choice(vocab["ADJ"])
        feats = rng.choice(FEATURES_POOL)
        prompt = build_prompt(noun, verb, adj, feats)
        words = [noun, verb, adj]
        last_err = None
        for attempt in range(3):
            try:
                text, timing = generate_one(model, prompt, options)
                ok, reason = accept_story(text, words)
                return {
                    "ok": ok,
                    "reason": reason,
                    "story": text,
                    "words": words,
                    "features": feats,
                    "timing": timing,
                    "attempts": attempt + 1,
                    "error": None,
                }
            except Exception as e:
                last_err = str(e)
                time.sleep(1.0 + attempt)
        return {
            "ok": False,
            "reason": "error",
            "story": "",
            "words": words,
            "features": feats,
            "timing": {},
            "attempts": 3,
            "error": last_err,
        }

    # sequential-ish with small pool: submit jobs until accepted == n
    # Use index only for logging; RNG in main thread for reproducibility of prompts
    print(f"Generating {args.n} stories with model={model} concurrency={args.concurrency}", flush=True)

    # Pre-generate prompt specs in main thread for resume-friendly counting
    # Actually for resume we continue from accepted count with new random draws
    inflight = {}
    next_job = accepted  # conceptual

    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        def submit_new():
            nonlocal next_job
            # build prompt in main thread with rng
            noun = rng.choice(vocab["NOUN"])
            verb = rng.choice(vocab["VERB"])
            adj = rng.choice(vocab["ADJ"])
            feats = rng.choice(FEATURES_POOL)
            prompt = build_prompt(noun, verb, adj, feats)
            words = [noun, verb, adj]

            def work(prompt=prompt, words=words, feats=feats):
                last_err = None
                for attempt in range(3):
                    try:
                        text, timing = generate_one(model, prompt, options)
                        ok, reason = accept_story(text, words)
                        return {
                            "ok": ok,
                            "reason": reason,
                            "story": text,
                            "words": words,
                            "features": feats,
                            "timing": timing,
                            "attempts": attempt + 1,
                            "error": None,
                        }
                    except Exception as e:
                        last_err = str(e)
                        time.sleep(1.0 + attempt)
                return {
                    "ok": False,
                    "reason": "error",
                    "story": "",
                    "words": words,
                    "features": feats,
                    "timing": {},
                    "attempts": 3,
                    "error": last_err,
                }

            fut = ex.submit(work)
            inflight[fut] = True
            next_job += 1

        target_inflight = args.concurrency
        while accepted < args.n:
            while len(inflight) < target_inflight and accepted + len(inflight) < args.n + args.concurrency * 2:
                submit_new()
            if not inflight:
                break
            for fut in as_completed(list(inflight.keys()), timeout=None):
                inflight.pop(fut, None)
                res = fut.result()
                attempted += 1
                if res["attempts"] > 1:
                    retries += res["attempts"] - 1
                timing = res.get("timing") or {}
                if timing.get("wall_sec"):
                    wall_sum += timing["wall_sec"]
                    tok_sum += timing.get("tok_s") or 0
                    n_timing += 1
                if res["ok"]:
                    shard_buf.append({"story": res["story"]})
                    accepted += 1
                    flush_shard(False)
                else:
                    rejected += 1
                    # if filter reject, still counts as attempt; optionally retry by submitting more
                if accepted % args.log_every == 0 or attempted % args.log_every == 0:
                    elapsed = time.time() - t_start
                    rate = accepted / elapsed * 3600 if elapsed > 0 else 0
                    vram = sample_vram_mb()
                    row = {
                        "accepted": accepted,
                        "attempted": attempted,
                        "rejected": rejected,
                        "retries": retries,
                        "stories_per_hour": rate,
                        "avg_wall_sec": wall_sum / n_timing if n_timing else None,
                        "avg_tok_s": tok_sum / n_timing if n_timing else None,
                        "vram_used_mb": vram["memory_used_mb"],
                        "elapsed_sec": elapsed,
                        "model": model,
                    }
                    run.append_jsonl("corpus/metrics.jsonl", row)
                    save_state()
                    print(
                        f"accepted={accepted}/{args.n} rejected={rejected} rate={rate:.1f}/h "
                        f"vram={vram['memory_used_mb']:.0f}MB",
                        flush=True,
                    )
                break  # back to refill pool

    flush_shard(force=True)
    save_state()
    elapsed = time.time() - t_start
    # final stats
    shard_files = sorted(out_dir.glob("data*.json"))
    sizes = {p.name: p.stat().st_size for p in shard_files}
    summary = {
        "model": model,
        "accepted": accepted,
        "attempted": attempted,
        "rejected": rejected,
        "retries": retries,
        "elapsed_sec": elapsed,
        "stories_per_hour": accepted / elapsed * 3600 if elapsed else 0,
        "avg_wall_sec": wall_sum / n_timing if n_timing else None,
        "avg_tok_s": tok_sum / n_timing if n_timing else None,
        "n_shards": len(shard_files),
        "shard_bytes": sizes,
        "accept_rate": accepted / attempted if attempted else 0,
    }
    run.write_json("corpus/summary.json", summary)
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
