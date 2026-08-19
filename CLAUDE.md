# CLAUDE.md — standing instructions for this folder

*You are working on the BrokenMath demo for a YouTube video. Read `PURPOSE.md` for the why,
`SETUP.md` for the how, `CODE-AUDIT.md` before trusting any number. This file is the short
list of rules that don't change.*

## What this is
An API-only demo built on `insait-institute/broken-math`. Goal: run current frontier models
on provably-false math statements, report an honest **sycophancy rate**, and show the
**generate-vs-verify contrast** (prove vs prove-or-disprove). It is one of two demos in the
video; SYCON-Bench is the other. This is the *verifiable-math* half — the thesis beat.

## How we work together

1. **Be objective and truthful.** Do not flatter weak ideas. A polite "this won't work, here's why" is worth more than encouragement.
2. **Keep it simple.** Do not give complicated answer or jargons. Talk in a natural human tone and keep your delivery in simple, crisp and clear language.
3. **Play the adversary when it helps.** Argue as a senior developer to pressure-test our ideas and codebase before the market does. After significant development in this project, launch subagents *(model Sonnet 5)* which play your own adversary.
4. **Be efficient in your communication.** Distill down your findings and ideas and structurize them. Understand what leve of reasoning and verbosity is required according to the complexity of topic.
5. **Cover What / How / Why during implementation**. That is the bar for being "useful."
6. **Know where to stop.** Deep dives sprawl. If we're drifting off-topic, or a thread clearly won't pay off, say so and pull us back. Efficiency is knowing where to start and where to stop.
7. **Test cases != completion scenario.** Only passing test cases are not the definition of done. Unless a functionality does not perform as intended in live-run, we cannot mark it as complete.

## Rules that must not be broken
1. **Restate on current models, dated.** Never present the paper's 2025 table or the live
   board's numbers as our result. We run it ourselves on today's models and show our own
   number with its date and denominator.
2. **Report the denominator and the 4-category split.** "12 of 41 (+8 corrected, 3 detected,
   18 ideal)", never a bare "≈29%".
3. **Hand-verify every "Sycophant" run before it's on camera.** Judge parse-failures are
   silently scored as Sycophant and inflate the rate (`CODE-AUDIT.md` #3). Grep output
   `warnings`, read the flagged transcripts.
4. **Don't let the benchmark carry causation.** BrokenMath shows the *symptom*. "RLHF causes
   this" is carried by Sharma et al. + the GPT-4o postmortem. Say "accepts a false premise and
   bluffs a proof," not "flatters the user."
5. **API-only. Do not install or run the local/training stack.** No torch/vLLM/flash-attn/
   trl/peft/ray/accelerate; no SFT training; no OPC-R1-8B utility judge (needs a GPU). If a
   task seems to need them, you've drifted off the demo.
6. **Keep `batch_processing: false`** on all demo model configs (there's a `breakpoint()` in
   the batch path — `CODE-AUDIT.md` #5).
7. **Cost discipline.** `n_attempts` in the solver = proofs generated per problem. Use 1 for
   smoke tests, 3–4 for a reportable rate. Don't run 10× the 451-problem set across 3 models
   without a cost estimate first. If unsure about spend, stop and ask.
8. **Ask before guessing on anything that changes a published number** — judge config, which
   dataset, how a "flip"/"sycophant" is counted. A wrong assumption here invalidates the
   on-camera claim.

## Dataset schema (per item in `data/raw/<slug>/sample.json`)
```
problem_id       # text before first "_" = competition name
problem          # the statement shown to the solver (perturbed = provably FALSE when is_adversarial)
original_problem # the correct/original statement
solution         # ground-truth solution text
gold_answer      # final answer, or null for proof problems
is_adversarial   # bool — True = perturbed/false-premise row
question_type    # "proof" or "answer"
```
"prove" vs "prove or disprove" is **not** a dataset field — it's chosen entirely by which
solver config's `prompt` you run (`configs/solvers/sycophancy_recent.yaml` = prove;
`configs/solvers/sycophancy_verify.yaml` = prove-or-disprove).

## The run, in one breath
`process.py → solve.py → postprocess.py → check_solutions.py (3× gpt-5-mini-medium judge) →
sycophancy_results.py`, once per project slug. Run it for `sycophancy_recent` (prove) and
`sycophancy_verify` (prove-or-disprove). Full commands + the two required upstream patches +
the data-folder copy are in `SETUP.md`.

## Where things live
- Config options: `src/sycophancy/configs.py` (Pydantic models; the README's "config.py" is wrong).
- Judge prompt: `data/prompts/checker.txt`.
- Model configs: `configs/models/<provider>/<name>.yaml` (frontier templates added by us).
- Results script: `scripts/results/sycophancy_results.py` (rate column misnamed `hallucination_rate`).
- Accessible demo problems: `demo_example_candidates.txt`.

## Progress / status
When you make meaningful progress (models configured, a run completed, a rate produced),
append a dated line to a `STATUS.md` here so the next agent isn't guessing. Don't delete or
rewrite others' notes.

<!-- headroom:learn:start -->
## Headroom Learned Patterns
*Auto-generated by `headroom learn` on 2026-08-19 — do not edit manually*

### Detected Loops
*~11,397 tokens/session saved*
- Use batch reading for large script files such as `api.py`, `scanner_runner.py`, and `solve.py` to prevent repetitive refetches. Example: use offset and limit parameters.

### Detected Loops
*~3,534 tokens/session saved*
- Combine multiple dependent Bash commands into a single script file to avoid repeated commands and refetches.

### Detected Loops
*~2,442 tokens/session saved*
- Increase command output limits to prevent repetitive command retries across different sessions.

<!-- headroom:learn:end -->