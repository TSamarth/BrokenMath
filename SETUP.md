# BrokenMath demo — setup & run recipe

*This is the API-only path (frontier models via API). It deliberately avoids the repo's
heavy local-inference/training stack (torch, vLLM, flash-attn, trl, peft, ray, accelerate).
Every command below was derived by reading the code (see `CODE-AUDIT.md`), but the pipeline
itself has not been executed here because it needs paid API keys — expect to debug one or
two provider-specific edges on first run. The two known-broken spots are patched below.*

## 0. What you already have

This folder is a slimmed copy of `github.com/insait-institute/broken-math` (notebooks,
images, `.git`, and the 37 MB SFT training file removed). If you'd rather start from the
canonical repo with git history:

```bash
git clone https://github.com/insait-institute/broken-math
# then copy this folder's add-ons into it: requirements-demo.txt, PURPOSE.md, SETUP.md,
# CODE-AUDIT.md, CLAUDE.md, configs/solvers/sycophancy_verify.yaml,
# configs/projects/sycophancy_verify.yaml, configs/setting/sycophancy_verify.yaml,
# configs/models/openai/gpt-5-latest.yaml, configs/models/gemini/gemini-3-pro.yaml,
# configs/models/anthropic/claude-opus-latest.yaml
```

The evaluation data ships in-repo: `data/raw/sycophancy_recent/sample.json` — **451
perturbed, provably-false proof problems**. That is enough to run the whole demo today.

## 1. Environment (Python 3.12)

```powershell
# Windows / PowerShell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-demo.txt
pip install -e . --no-deps       # install the `sycophancy` package itself, WITHOUT re-pulling pyproject's heavy deps
```

`pip install -e . --no-deps` is deliberate: a plain `pip install -e .` pulls
`torch==2.6.0`, `vllm==0.8.5`, `flash_attn`, etc. from `pyproject.toml`, which is slow,
often fails to build on Windows, and is **not needed** for API models. `requirements-demo.txt`
already covers everything the demo path imports (including three deps upstream forgot to
declare: `transformers`, `pyyaml`, `filelock`).

Set provider keys as env vars before running: `OPENAI_API_KEY`, `GEMINI_API_KEY` (or
`GOOGLE_API_KEY`), `ANTHROPIC_API_KEY`. Only the providers you actually use are needed.

## 2. Apply the two upstream fixes (the pipeline's first script is broken as shipped)

In `scripts/process.py` (details in `CODE-AUDIT.md` #1, #2):

**Fix A — register the missing flag.** Near the other `parser.add_argument(...)` calls, add:
```python
parser.add_argument("--no-solutions", dest="no_solutions", action="store_true")
```
**Fix B — guard the wrong key.** Change the check that reads `item["solutions"]` to tolerate
its absence, e.g.:
```python
if not args.no_solutions and len(item.get("solutions", [])) > 0 and item["solutions"][0]["solution"] is None:
```
(`solutions`, plural, only exists after `postprocess`; the raw file has a singular
`solution`.) Verify the file still imports: `python -m py_compile scripts/process.py`.

## 3. Fill in the frontier model configs

Edit the three templates and set the exact `model:` string + `date:` to models you have
access to (the suffix after `--`, e.g. `gpt-5.2--high`, is parsed as reasoning effort):

- `configs/models/openai/gpt-5-latest.yaml`
- `configs/models/gemini/gemini-3-pro.yaml`
- `configs/models/anthropic/claude-opus-latest.yaml`

Smoke-test one cheap call per provider before the full run.

## 4. Run A — the "prove" framing (produces the sycophancy rate)

Uses the existing `sycophancy_recent` project. **First trim its model list to API models
only** — `configs/projects/sycophancy_recent.yaml` ships with local vLLM entries
(`trained/best_model`, `qwen/*`, `*_agent`); delete those, leaving your three API configs.

```bash
python scripts/process.py     --project sycophancy_recent            # -> per-item unsolved JSONs
python scripts/solve.py       --project sycophancy_recent [--synchronous]   # model writes proofs
python scripts/postprocess.py --project sycophancy_recent            # flatten -> data/postprocess/sycophancy_recent/test_samples.json
python scripts/check_solutions.py --checker_configs openai/gpt-5-mini-medium \
      --setting_config sycophancy_recent --n 3 --skip-existing        # 3x GPT-5-mini judge, 4-category
python scripts/results/sycophancy_results.py --setting_config sycophancy_recent
```

The last step prints a per-model rate. In `scripts/results/sycophancy_results.py` the column
is confusingly named `hallucination_rate` — **that IS the sycophancy rate** (`incorrect` =
the code's name for the "Sycophant" category). See `CODE-AUDIT.md` #16.

Cost control: the solver config's `n_attempts` is the number of proofs generated per problem.
Upstream default is 10. For a demo rate, 3–4 is plenty; 1 for a quick smoke run. Lower it in
`configs/solvers/sycophancy_recent.yaml`.

## 5. Run B — the "prove or disprove" framing (produces the generate-vs-verify contrast)

Uses the added `sycophancy_verify` project (same data, same judge, different solver prompt).
**First give it the data folder** (the slug has none — this is the upstream foot-gun in
`CODE-AUDIT.md` #10):

```powershell
Copy-Item -Recurse data\raw\sycophancy_recent data\raw\sycophancy_verify   # Windows
# cp -r data/raw/sycophancy_recent data/raw/sycophancy_verify              # bash
```

Then the same five steps against `sycophancy_verify`:

```bash
python scripts/process.py     --project sycophancy_verify
python scripts/solve.py       --project sycophancy_verify [--synchronous]
python scripts/postprocess.py --project sycophancy_verify
python scripts/check_solutions.py --checker_configs openai/gpt-5-mini-medium \
      --setting_config sycophancy_verify --n 3 --skip-existing
python scripts/results/sycophancy_results.py --setting_config sycophancy_verify
```

The delta between Run A and Run B, per model, is the on-camera beat: reliability jumps when
the task is reframed from "prove" to "check, then prove or disprove."

## 6. The full official dataset (optional — for matching the paper's 504/183 exactly)

The in-repo `sample.json` is 451 all-proof problems and does **not** match the paper's stated
504 samples / 183 final-answer split (`CODE-AUDIT.md` #9). If you want the official set, pull
it on a networked machine and confirm the counts against the dataset card:

```bash
pip install huggingface_hub
huggingface-cli download INSAIT-Institute/BrokenMath --repo-type dataset --local-dir ./bm_hf
# then reshape rows into data/raw/<slug>/sample.json with the fields listed in CLAUDE.md
```
(The repo ships no script that converts the HF eval set into this on-disk schema — you map it
by hand; the field list is in `CLAUDE.md`.)

## 7. Before any number goes on camera

- Grep the saved outputs' `warnings` for judge parse failures — those are silently scored as
  "Sycophant" and inflate the rate (`CODE-AUDIT.md` #3). Audit their frequency.
- Hand-verify every run classified as a sycophant.
- State the denominator and the four-category split, not a bare percentage.
- Note on camera that runs are non-deterministic (`temperature 0.6`, shuffled attempts) —
  re-running won't reproduce byte-identical percentages.
