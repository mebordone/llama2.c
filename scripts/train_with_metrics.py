#!/usr/bin/env python3
"""Launch train.py while logging loss lines and GPU memory to experiments/."""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from exp_logger import ExperimentRun, load_latest_run, sample_vram_mb  # noqa: E402

LOSS_RE = re.compile(
    r"^(?P<iter>\d+)\s*\|\s*loss\s+(?P<loss>[0-9.eE+-]+)",
    re.I,
)
# eval lines: "step 2000: train loss 1.234, val loss 1.345"
STEP_RE = re.compile(
    r"step\s+(?P<iter>\d+):\s*train loss\s+(?P<train>[0-9.eE+-]+),\s*val loss\s+(?P<val>[0-9.eE+-]+)",
    re.I,
)
VAL_RE = re.compile(
    r"val loss",
    re.I,
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", type=str, default=None)
    ap.add_argument("--poll-sec", type=float, default=10.0)
    ap.add_argument("train_args", nargs=argparse.REMAINDER, help="args after -- passed to train.py")
    args = ap.parse_args()
    train_args = args.train_args
    if train_args and train_args[0] == "--":
        train_args = train_args[1:]

    run = ExperimentRun(run_id=args.run_id) if args.run_id else (load_latest_run() or ExperimentRun())
    run.write_json(
        "train/launch.json",
        {"cmd": [sys.executable, "train.py", *train_args], "cwd": str(ROOT)},
    )

    env = os.environ.copy()
    env.setdefault("CUDA_VISIBLE_DEVICES", "0")

    cmd = [sys.executable, "-u", str(ROOT / "train.py"), *train_args]
    print("Running:", " ".join(cmd), flush=True)
    proc = subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    stop = threading.Event()

    def poll_vram():
        while not stop.wait(args.poll_sec):
            v = sample_vram_mb()
            run.append_jsonl(
                "train/vram.jsonl",
                {"memory_used_mb": v["memory_used_mb"], "utilization_gpu": v["utilization_gpu"]},
            )

    th = threading.Thread(target=poll_vram, daemon=True)
    th.start()
    t0 = time.time()
    log_path = run.path("train/stdout.log")
    peak_vram = 0.0
    with log_path.open("w", encoding="utf-8") as logf:
        assert proc.stdout is not None
        for line in proc.stdout:
            logf.write(line)
            logf.flush()
            print(line, end="", flush=True)
            m = LOSS_RE.search(line.strip())
            s = STEP_RE.search(line)
            if s:
                v = sample_vram_mb()
                peak_vram = max(peak_vram, v["memory_used_mb"])
                run.append_jsonl(
                    "train/metrics.jsonl",
                    {
                        "iter": int(s.group("iter")),
                        "train_loss": float(s.group("train")),
                        "val_loss": float(s.group("val")),
                        "is_eval": True,
                        "line": line.strip(),
                        "vram_used_mb": v["memory_used_mb"],
                        "elapsed_sec": time.time() - t0,
                    },
                )
            elif m:
                v = sample_vram_mb()
                peak_vram = max(peak_vram, v["memory_used_mb"])
                run.append_jsonl(
                    "train/metrics.jsonl",
                    {
                        "iter": int(m.group("iter")),
                        "loss": float(m.group("loss")),
                        "is_eval": False,
                        "line": line.strip(),
                        "vram_used_mb": v["memory_used_mb"],
                        "elapsed_sec": time.time() - t0,
                    },
                )
    rc = proc.wait()
    stop.set()
    summary = {
        "returncode": rc,
        "elapsed_sec": time.time() - t0,
        "peak_vram_mb_observed": peak_vram,
        "stdout_log": str(log_path),
    }
    run.write_json("train/summary.json", summary)
    if rc != 0:
        raise SystemExit(rc)


if __name__ == "__main__":
    main()
