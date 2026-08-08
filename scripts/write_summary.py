#!/usr/bin/env python3
"""Write experiments/<run_id>/SUMMARY.md from available stage artifacts."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_json(p: Path):
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def main():
    run_id = sys.argv[1] if len(sys.argv) > 1 else (ROOT / "experiments" / "LATEST").read_text().strip()
    root = ROOT / "experiments" / run_id
    lines = [f"# TinyStories ES 260K — run `{run_id}`", ""]
    meta = load_json(root / "meta.json")
    if meta:
        gpus = (meta.get("gpu") or {}).get("gpus") or []
        if gpus:
            lines.append(f"- GPU: {gpus[0].get('name')} ({gpus[0].get('memory_total_mb')} MB)")
        lines.append(f"- Host: {meta.get('hostname')}")
        lines.append(f"- Git: `{meta.get('git_commit')}`")
        lines.append("")

    report = root / "eval_generators" / "report.md"
    if report.exists():
        lines.append("## Eval generadores")
        lines.append("")
        lines.append(report.read_text(encoding="utf-8"))
        lines.append("")

    corp = load_json(root / "corpus" / "summary.json")
    if corp:
        lines.append("## Corpus")
        lines.append("")
        lines.append(f"- Modelo: `{corp.get('model')}`")
        lines.append(f"- Aceptadas: {corp.get('accepted')}")
        lines.append(f"- Rechazadas: {corp.get('rejected')}")
        lines.append(f"- Accept rate: {corp.get('accept_rate')}")
        lines.append(f"- Historias/h: {corp.get('stories_per_hour')}")
        lines.append(f"- Elapsed s: {corp.get('elapsed_sec')}")
        lines.append("")

    vocab = load_json(root / "vocab_pretok" / "summary.json")
    if vocab:
        lines.append("## Vocab / pretok")
        lines.append("")
        for k, v in vocab.items():
            lines.append(f"- {k}: {v}")
        lines.append("")

    train = load_json(root / "train" / "summary.json")
    if train:
        lines.append("## Train")
        lines.append("")
        for k, v in train.items():
            lines.append(f"- {k}: {v}")
        lines.append("")

    infer = root / "infer"
    if infer.exists():
        lines.append("## Infer")
        lines.append("")
        for p in sorted(infer.glob("*")):
            if p.suffix in {".txt", ".md", ".json"}:
                lines.append(f"### {p.name}")
                lines.append("```")
                lines.append(p.read_text(encoding="utf-8")[:4000])
                lines.append("```")
                lines.append("")

    out = root / "SUMMARY.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
