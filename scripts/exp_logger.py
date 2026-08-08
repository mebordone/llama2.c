"""Experiment logging helpers for TinyStories ES pipeline."""
from __future__ import annotations

import csv
import json
import os
import platform
import socket
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENTS_DIR = ROOT / "experiments"


def new_run_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def gpu_info() -> Dict[str, Any]:
    info: Dict[str, Any] = {"gpus": []}
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=index,name,memory.total,memory.used,memory.free,utilization.gpu,driver_version",
                "--format=csv,noheader,nounits",
            ],
            text=True,
        )
        for line in out.strip().splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 7:
                info["gpus"].append(
                    {
                        "index": int(parts[0]),
                        "name": parts[1],
                        "memory_total_mb": float(parts[2]),
                        "memory_used_mb": float(parts[3]),
                        "memory_free_mb": float(parts[4]),
                        "utilization_gpu": float(parts[5]),
                        "driver_version": parts[6],
                    }
                )
    except Exception as e:
        info["error"] = str(e)
    return info


def git_commit() -> Optional[str]:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except Exception:
        return None


class ExperimentRun:
    def __init__(self, run_id: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        self.run_id = run_id or new_run_id()
        self.root = EXPERIMENTS_DIR / self.run_id
        for sub in (
            "eval_generators",
            "corpus",
            "vocab_pretok",
            "train",
            "infer",
        ):
            (self.root / sub).mkdir(parents=True, exist_ok=True)

        meta = {
            "run_id": self.run_id,
            "created_at": datetime.now().isoformat(),
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "python": platform.python_version(),
            "cwd": str(ROOT),
            "git_commit": git_commit(),
            "gpu": gpu_info(),
        }
        self.write_json("meta.json", meta)
        if config is not None:
            self.write_json("config.json", config)
        # pointer to latest run
        (EXPERIMENTS_DIR / "LATEST").write_text(self.run_id + "\n")

    def path(self, *parts: str) -> Path:
        return self.root.joinpath(*parts)

    def write_json(self, rel: str, obj: Any) -> Path:
        p = self.path(rel)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")
        return p

    def append_jsonl(self, rel: str, row: Dict[str, Any]) -> None:
        p = self.path(rel)
        p.parent.mkdir(parents=True, exist_ok=True)
        row = dict(row)
        row.setdefault("ts", time.time())
        row.setdefault("iso", datetime.now().isoformat())
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def write_csv(self, rel: str, rows: List[Dict[str, Any]], fieldnames: Optional[Iterable[str]] = None) -> Path:
        p = self.path(rel)
        p.parent.mkdir(parents=True, exist_ok=True)
        if not rows:
            p.write_text("")
            return p
        fields = list(fieldnames) if fieldnames else list(rows[0].keys())
        with p.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow(r)
        return p

    def write_text(self, rel: str, text: str) -> Path:
        p = self.path(rel)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        return p


def load_latest_run() -> Optional[ExperimentRun]:
    latest = EXPERIMENTS_DIR / "LATEST"
    if not latest.exists():
        return None
    run_id = latest.read_text().strip()
    run = ExperimentRun.__new__(ExperimentRun)
    run.run_id = run_id
    run.root = EXPERIMENTS_DIR / run_id
    return run


def sample_vram_mb() -> Dict[str, float]:
    g = gpu_info().get("gpus") or []
    if not g:
        return {"memory_used_mb": 0.0, "memory_total_mb": 0.0, "utilization_gpu": 0.0}
    x = g[0]
    return {
        "memory_used_mb": x["memory_used_mb"],
        "memory_total_mb": x["memory_total_mb"],
        "utilization_gpu": x["utilization_gpu"],
    }
