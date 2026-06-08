# LA-stats

Loading, statistical analysis and figure exports for left-atrium (LA) size
measurements in rats — volume and length at maximum and minimum size, from the
4-chamber MRI view.

## Layout

```
src/        Reusable modules
  data.py       DB load + cleaning; one analysis-ready DataFrame per scan
  plotting.py   Plot primitives (box plots by sex; residual diagnostics)
  stats.py      Mixed-effects models, marginal means, age contrasts
analysis/   Thin orchestration scripts, one per analysis
  length_longitudinal.py    Box plots of LA length across timepoints, by sex
  length_mixed_effects.py   Mixed model of LA length by age and sex
figs/       Exported figures (SVG), one subfolder per measure group
  length/       LA length figures
SCHEMA.md   Database schema, value ranges, data-quality notes
```

The design rule: every analysis starts from `src.data.load_la_measurements`,
so load-time decisions (whitespace cleanup, optional pooling of pre-op MI/AB
Baseline scans) live in exactly one place.

## Setup

```
.venv\Scripts\activate
```

Database location and schema: see `SCHEMA.md`.

## Analyses

### Longitudinal LA length

`analysis/length_longitudinal.py` →
`figs/length/max_length_longitudinal.svg`, `figs/length/min_length_longitudinal.svg`

One figure per length measure (max, min) over the Aging cohort, binned to the
nominal 9 / 16 / 24-month scan timepoints. Within each figure, Male and Female
are shown as separate coloured boxes, each labelled inside with `n=<animals>`.
Off-schedule 18-month scans (n=5) are dropped; Baseline MI/AB scans are
excluded (toggle `pool_baseline` in `load_la_measurements` to include them).

```
.venv\Scripts\python.exe analysis\length_longitudinal.py
```

### Longitudinal LA length — mixed-effects model

`analysis/length_mixed_effects.py` →
`figs/length/{max,min}_length_mm_residual_diagnostics.svg`

Per length measure, a random-intercept linear mixed model
(`length ~ C(age_months) * C(gender)`, random intercept per `animal_id`) over
the same 9/16/24-month Aging data. The random intercept absorbs the
within-animal correlation of repeated scans. Reports fixed effects, the
likelihood-ratio test for the age×sex interaction, estimated marginal means and
Bonferroni-adjusted pairwise age contrasts per sex, with residual diagnostics
and a `pool_baseline=True` sensitivity refit. Inference uses Wald z-tests
(normal approximation — small-sample p-values run slightly optimistic).

```
.venv\Scripts\python.exe analysis\length_mixed_effects.py
```
