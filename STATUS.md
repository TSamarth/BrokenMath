# STATUS — dated progress log

Append a dated line when you make meaningful progress (models configured, run
completed, rate produced) so the next agent isn't guessing. Don't delete or
rewrite others' notes.

---

## 2026-08-16 — remote Ollama/vLLM support + HF dataset provenance (branch `feat/remote-local-models-and-data`)

Two changes, both reviewed clean (Sonnet 5 subagents, final whole-branch review passed). git initialized this session; baseline `83fbe9b`.

- **Remote local models (Task 1, commits `e9cd3b5`, `4e6fd0b`).** The existing
  `vllm_server` API path in `src/sycophancy/api.py` now reads `base_url`/`api_key`
  per-model from the model YAML, falling back to the old `http://localhost:8000/v1`
  / `token-abc123` defaults. This is the OpenAI-compatible HTTP path (no torch/vllm
  import) — so a **remote** Ollama or vLLM host works with zero local inference stack,
  staying within the API-only rule. Template: `configs/models/local/qwen3-4b-remote.yaml`
  (shows both vLLM `:8000/v1` and Ollama `:11434/v1`). Self-check:
  `tests/test_vllm_server_base_url.py`. All local model configs and the local entries
  in `configs/projects/sycophancy_recent.yaml` were **retained** (not deleted).

- **Dataset provenance (Task 2, commit `aa951ec`).** FINDING: the shipped
  `data/raw/sycophancy_recent/sample.json` (451 rows, all adversarial proof, gold null)
  is **content-identical** to HF `INSAIT-Institute/BrokenMath`'s `benchmark` split
  (`data/test-00000-of-00001.parquet`) — verified field-by-field, 0 mismatches. So the
  old CODE-AUDIT #9 / SETUP §6 "in-repo ≠ paper, pull HF to fix" claim was stale and is
  now corrected: 451 = the adversarial-proof subset; the paper's 504/183 is its fuller
  set, not what this demo evaluates. `scripts/fetch_dataset.py --slug <s> [--write]`
  reproduces/verifies it (verify-only by default; `--write` seeds a slug's data folder).
  `data/raw/sycophancy_verify/` seeded via the script. Deps `huggingface_hub`+`pyarrow`
  added to `requirements-demo.txt` (light; no heavy stack).

- **Env:** demo venv created at `.venv` (Python 3.12, `requirements-demo.txt` +
  `pip install -e . --no-deps`), so the pipeline is now importable/runnable locally.
  Pipeline itself still not run end-to-end (needs paid API keys).
