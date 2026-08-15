# BrokenMath demo — purpose & how it fits the video

*Read this first. It tells you what this demo is for and what "good" looks like, so
everything else you build serves the video rather than the benchmark.*

## The video, in one line

The RLHF/sycophancy video is being re-architected around one thesis:

> **We can only align AI where we can check the answer. Enterprises are deploying agents
> into everything we can't check.**

Audience: enterprise AI builders, strategic tech decision-makers, and the technically
curious. Channel voice: Veritasium-level rigor, optimistic, build-and-break, zero fluff.
On this channel, a number that doesn't survive the comment section is worse than no
number at all.

## Why BrokenMath, and where it sits

The video uses **two** sycophancy demos that split the work (full rationale in
`Outputs/RLHF_Sycophancy/rlhf-brokenmath/brokenmath_brief.md` and `.../rlhf-sycon-bench/sycon_brief.md`):

- **SYCON-Bench** = the visceral cold open: a model folding in real time under social
  pushback. Subjective, emotional, "watch it cave."
- **BrokenMath (this repo)** = the **thesis beat**. It lives in verifiable mathematics, so
  there is no "reasonable disagreement" escape hatch — a false theorem is false. It is the
  cleanest on-screen dramatisation of "align only what you can verify."

BrokenMath measures **sycophancy in theorem proving**: the user hands the model a
mathematical statement that is *provably false*, and the model either catches it or writes
a convincing proof of a falsehood. The headline metric is the **sycophancy rate** = the
fraction of problems where the model bluffed a proof of the false statement.

## The two things this demo must produce on screen

1. **A defensible sycophancy rate.** "The best model in the world still writes a convincing
   proof of a false theorem ~29% of the time; the most careful chat model, on hard 2026
   problems, does it more than nine times in ten." Report the number with its denominator
   and the four-category breakdown (see `CODE-AUDIT.md`), never a bare percentage.

2. **The generate-vs-verify contrast — the money shot.** Same model, same false statement,
   one word of difference in the instruction:
   - Prompted **"prove"** → it bluffs a proof.
   - Prompted **"prove or disprove"** → it catches the falsehood.
   On the authors' live BrokenArXiv board, **Gemini-3.1-Pro goes from 18.5% → 71% detection**
   with exactly this switch. That is the thesis in one screenshot: when the reward is
   "satisfy the request to prove X," the model performs a proof; when the task is reframed
   so that *checking* is the job, the same model's reliability jumps. This repo did **not**
   ship a "prove or disprove" solver — we added one (`configs/solvers/sycophancy_verify.yaml`)
   specifically to produce this beat.

## What "done" looks like for the demo (not this prep task)

- A sycophancy rate for 2–3 **current** frontier models (GPT-5.x, Gemini-3, Claude), run by
  us, dated — not the paper's stale table. (The paper is Oct-2025 models; the live board is
  Feb-2026. We restate on our own models.)
- The same models run under both the "prove" and "prove-or-disprove" solvers, so the
  contrast is ours and reproducible.
- 3–5 hand-picked, **lay-legible** false statements for the visual (raw olympiad LaTeX is
  not legible in 5 seconds — see `demo_example_candidates.txt` for accessible ones).
- Every flagged "sycophant" run spot-checked by hand before any number goes on camera.

## Hard constraints (from the channel's standards)

- **Restate on current models.** Do not present the paper's 2025 numbers as current.
- **Report the denominator.** "12 of 41", not "≈29%".
- **Feature the models that actually bluff.** On social sycophancy Claude resists; on hard
  proofs even Claude bluffs heavily — so the story differs by model. Show the spread; it's
  honest and interesting.
- **This benchmark demonstrates, it does not prove causation.** BrokenMath shows the
  symptom. The claim "RLHF *causes* this" is carried by Sharma et al. + the GPT-4o
  postmortem, not by this repo. (The paper itself defers causation to Sharma et al.)
- **Name the failure correctly.** BrokenMath blends sycophancy with hallucination (it gets
  worse as the model's ability to solve the real problem drops). On screen say "the model
  accepts the user's false premise and bluffs a proof," not "it's flattering you."

## Files in this folder

| File | What it is |
|---|---|
| `PURPOSE.md` | This file — why the demo exists and what it must deliver. |
| `SETUP.md` | Tested, step-by-step setup + the exact run recipe for both framings. |
| `CODE-AUDIT.md` | Hidden flaws/gaps in the codebase + a code-vs-paper methodology check. Read before trusting any number. |
| `CLAUDE.md` | Standing guardrails for any agent working in this folder. |
| `demo_example_candidates.txt` | Six accessible false statements pulled from the dataset, for the visual. |
| `requirements-demo.txt` | Slim API-only dependency set (no torch/vLLM/training). |
| `configs/solvers/sycophancy_verify.yaml` + `configs/projects|setting/sycophancy_verify.yaml` | The added "prove-or-disprove" run for the generate-vs-verify beat. |
| `configs/models/*/{gpt-5-latest,gemini-3-pro,claude-opus-latest}.yaml` | Frontier model config templates — fill in exact model IDs. |
