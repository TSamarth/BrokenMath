# BrokenMath codebase audit — hidden flaws & code-vs-paper check

*Audit of `github.com/insait-institute/broken-math` as cloned 2026-08-15. Read this before
trusting any number the pipeline prints. Nothing here was run against a live API; findings
are from reading the code. Line numbers are against the upstream files in this package.*

## TL;DR — the four things that can corrupt an on-camera number

1. **Judge parse-failures are silently scored as "Sycophant" (inflates the rate).** A judge
   response that is truncated, empty (API retries exhausted → `""`), or phrased off-template
   falls through to `"incorrect"` = Sycophant, with only a `logger.warning`. No re-query on
   parse failure. → Grep output `warnings` and hand-check flagged runs before quoting a rate.
   (#3)
2. **The first pipeline script is broken as shipped** (`scripts/process.py`) — a missing
   `--no-solutions` arg and a wrong `item["solutions"]` key. Two-line fix in `SETUP.md §2`. (#1, #2)
3. **The in-repo dataset is the HF `benchmark` split, not the paper's fuller 504/183 figure.**
   Shipped `sample.json` = 451 all-proof rows, verified content-identical to HF
   `INSAIT-Institute/BrokenMath`'s `benchmark` split via `scripts/fetch_dataset.py`. The
   paper's "504 samples / 183 final-answer" is a larger, separate figure this split does not
   cover — don't conflate the two. (#9)
4. **The generate-vs-verify contrast isn't in the repo** — no "prove or disprove" solver
   exists upstream. We added one (`configs/solvers/sycophancy_verify.yaml`). (Part 2, mitigation row)

Non-determinism is inherent (temperature 0.6 + shuffled attempts); re-running won't
reproduce byte-identical percentages. Say so on camera. (#15)

---

## Part 1 — Hidden flaws / gaps

### Major
- **#1 `scripts/process.py` won't run as shipped.** `args.no_solutions` is referenced but the
  `--no-solutions` flag is never registered → `AttributeError` on the first item. Blocks the
  whole pipeline. Fix in `SETUP.md §2`.
- **#2 `scripts/process.py` reads the wrong schema.** The raw file has a singular `solution`
  field; the code indexes `item["solutions"]` (plural) → `KeyError` every row. Guard with
  `.get("solutions", [])`.
- **#3 Judge parse-failures coerced one-directionally to "Sycophant".** `parser.py::extract_judgement`
  (~L669) returns `"incorrect"` for anything not matching `correct|detected|corrected|incorrect`,
  and `api.py::run_query_with_retry` returns `{"output": ""}` on total failure
  (`throw_error_on_failure=False`). Empty/truncated/refused judge calls → counted as the model
  proving the false theorem. No retry loop in `scanner_runner.py:130-141`. **Highest-risk item
  for an honest number.**
- **#4 Nested retry can stall ~50 min then corrupt a query.** Outer `run_query_with_retry`
  (`max_retries=10`, 60 s sleeps) wraps an inner 5-retry loop; a persistently failing request
  hangs a long time, then downgrades to `""` (→ #3). Lower retries/sleeps in model configs for
  a live demo, or watch logs.
- **#5 FIXED — `src/sycophancy/api.py` had a bare `breakpoint()` in `retrieve_batch()`.**
  Correction to the original finding: it was not reachable via plain `batch_processing: true`
  (that path uses `openai_batch_processing()` / `anthropic_batch_processing()`, which never
  called `retrieve_batch()`). It only fired via `scripts/retrieve_batches.py --batch_id`
  (the async resume path, `solve.py:105`). Removed; `retrieve_batch()` also had a latent
  `UnboundLocalError` if the first `client.batches.retrieve()` call raised — fixed alongside.
  Regression test: `tests/test_retrieve_batch.py`. `batch_processing: true` is now safe for
  `api: openai` / `api: anthropic` configs.

### Moderate
- **#6 No tie-break for a 3-way judge split.** With 4 categories and `--n 3`, a 1-1-1 split has
  no majority; `Counter(...).most_common(1)` breaks ties by completion order of
  `as_completed()` → network-timing dependent, so the "winning" category can change between
  reprocesses. Rare but real ("why did it move 0.1pp").
- **#7 `scripts/results/utility_results.py:56` type bug** (Utility metric only — off the demo
  path): stores a string into a column later `.mean()`'d. Flag only if someone runs Utility.
- **#8 `utility_results.py:97-103` copy/paste bug** mislabels the sycophancy judge as "OPC R1 8B"
  in Utility tables. Labels only; values unaffected. Off-path.
- **#9 In-repo dataset is HF's `benchmark` split, which is smaller than the paper's headline
  count.** `data/raw/sycophancy_recent/sample.json` = 451 rows, 100% proof, 100% adversarial —
  verified content-identical to HF `INSAIT-Institute/BrokenMath`'s `benchmark` split
  (`scripts/fetch_dataset.py` reproduces + diffs it field-by-field, 0 mismatches). Paper's
  fuller "504 samples, 183 final-answer" figure is a separate, larger set not covered by this
  split. Nuance only, not a bug — just don't quote "504/183" as our own number.
- **#10 `sycophancy_hint` project points at a non-existent raw folder.** Default
  `raw_base_folder = data/raw/{slug}` and there's no `data/raw/sycophancy_hint/`. Our
  `sycophancy_verify` project hits the same foot-gun by design — fix by copying the data folder
  (see `SETUP.md §5`).

### Minor
- **#11 No configs for current frontier models** — none past GPT-5 / Gemini-2.5 / Claude-4 /
  Grok-4. We added three templates (`SETUP.md §3`).
- **#12 `api.py:20` unconditionally imports `transformers`** (module scope), which is not in
  `pyproject.toml` and vanishes once the ML stack is stripped → add it explicitly (done in
  `requirements-demo.txt`).
- **#13 Gemini is routed via the OpenAI-compatibility endpoint**, not the native `google-genai`
  SDK (`api.py:217-220` flips `api="google"` → `"openai"`). Confirm reasoning/thinking params
  pass through that shim for Gemini-3.
- **#14 `claude-4-sonnet.yaml` sets `concurrent_requests: 1`** — Claude will be much slower than
  other providers in a multi-hundred-problem run unless bumped (our template sets 8).
- **#15 Non-determinism is inherent** — `temperature 0.6`, `allow_shuffle: true`. State it on
  camera.
- **#16 `sycophancy_results.py` names the sycophancy rate `hallucination_rate`.** Correct number,
  confusing name — don't read it literally on camera.
- **#17 Hardcoded judge label** `judge == 'GPT-5-mini (medium)'` (`sycophancy_results.py:119`)
  must exactly match the judge config's `human_readable_id`, or the table silently comes back
  empty. Don't rename the judge config.
- **#18 `configs.py::load_config` swallows config errors** — a typo'd YAML key silently degrades
  to a plain dict instead of failing loudly. Confirm new/edited YAML loads as the expected type
  when debugging.

---

## Part 2 — Does the code match the paper?

| Paper claim | In the code? |
|---|---|
| 504 samples, 2025 comps, perturbed+expert-refined, 183 final-answer | **Not this split** — shipped file is HF's 451-row `benchmark` split (all proof, no final-answer), verified identical via `scripts/fetch_dataset.py`. Paper's fuller 504/183 figure is a separate set. (#9) |
| 4 categories: Ideal / Corrected / Detected / Sycophant | **Yes.** `data/prompts/checker.txt` maps them to `\boxed{correct|detected|corrected|incorrect}`; parsed in `parser.py::extract_judgement`. |
| Sycophancy rate = fraction Sycophant | **Yes.** `sycophancy_results.py:73,79` (`incorrect` == Sycophant; named `hallucination_rate`). |
| Judge = 3× GPT-5-mini (medium) majority, independent of evaluated models | **Yes.** `check_solutions.py --checker_configs openai/gpt-5-mini-medium --n 3`; `gpt-5-mini--medium` → effort parsed from `--` suffix. The "95% vs 250 human labels" figure is a paper claim, not re-derived by any script. Caveat: no 3-way tie-break (#6). |
| Utility judged by OPC-R1-8B | **Yes, config exists** (`configs/models/opc/opc_r1_8b.yaml`, `api: vllm_sync` = local GPU). Off the demo path; has bugs #7/#8. |
| ρ=−0.62; sycophancy ↑ with difficulty; worse on proofs | **Not in scripts** — notebook-level analysis (`notebooks/extraction.ipynb`) over precomputed CSVs. Treat as paper-only unless you open the notebook. |
| Mitigation: "verify-first" prompt | **Partial.** `configs/solvers/sycophancy_hint.yaml` adds an "identify if unprovable" line — functionally verify-first, but **no literal "prove or disprove" eval solver ships.** We added `sycophancy_verify.yaml` for the exact generate-vs-verify beat. The literal phrase only appears in `data_collection/gather_data.py` for building *training* data. |
| Best-of-n / self-consistency | **Yes** (`best_of_n.py`, `configs/solvers/sycophancy_best_of_n.yaml`). Off demo path. |
| SFT on ~13k curated examples | **Yes** (`scripts/train/*`, `prepare_training_data.py`; raw pre-filter set = 14,959 rows). Needs GPUs; off demo path. |

**Bottom line:** the core measurement (4-category judge → % Sycophant, 3× GPT-5-mini majority)
faithfully implements the paper. The gaps that matter for us are operational, not conceptual:
the shipped dataset differs from the paper's, the first script is broken, judge parse-failures
bias the rate upward, and the generate-vs-verify solver had to be added.
