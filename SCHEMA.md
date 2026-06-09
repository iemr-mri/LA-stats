# AGORA_LA database schema

SQLite database: `C:\Users\heskalde\Databases\AGORA-db\AGORA_LA.db`

Two tables in a one-to-many relationship: one `subjects` row per animal,
many `la_mri` rows per animal (repeated/longitudinal MRI measurements).
Join on `animal_id`.

## Table: `subjects` (156 rows)

One row per animal.

| Column      | Type    | Null? | Notes |
|-------------|---------|-------|-------|
| `animal_id` | TEXT    | PK    | Primary key. |
| `gender`    | TEXT    | NOT NULL | Values: `Female` (100), `Male` (56). |
| `cohort`    | TEXT    | NOT NULL | e.g. `AG-24 Cohort 10`. 24 distinct cohorts. Encodes model + age group + batch. |
| `model`     | TEXT    | NOT NULL | Disease model: `Aging` (140), `MI` (9), `AB` (7). |
| `age_group` | INTEGER | NOT NULL | Nominal age group in months: `24` (100), `9` (40), `16` (16). |

## Table: `la_mri` (269 rows)

One row per MRI session. Left-atrium size measurements from the 4-chamber view.

| Column              | Type    | Null?     | Notes |
|---------------------|---------|-----------|-------|
| `mri_id`            | INTEGER | PK (autoincrement) | |
| `animal_id`         | TEXT    | NOT NULL  | FK → `subjects.animal_id`. |
| `age_months`        | INTEGER | NOT NULL  | Actual age at scan. Range 9–24. |
| `max_volume_ul`     | REAL    | 2 nulls   | LA volume at maximum size, microlitres. Range 107–944. |
| `min_volume_ul`     | REAL    | 2 nulls   | LA volume at minimum size, microlitres. Range 24–915. |
| `stroke_volume_ul`  | REAL    | 2 nulls   | max − min volume, microlitres. Range 20–222. |
| `ejection_fraction` | REAL    | 2 nulls   | LA ejection fraction (%). Range 3.07–77.57. |
| `max_length_mm`     | REAL    | 2 nulls   | LA length at maximum size. Range 2.27–6.98. |
| `min_length_mm`     | REAL    | 3 nulls   | LA length at minimum size. Range 1.42–6.39. |
| `op_week`           | TEXT    | 258 nulls | Operation-relative timing. Populated only for operated models (MI/AB); NULL for Aging. Only value present is `Baseline` (pre-op), on all 11 MI/AB scans. |

### Models and the `op_week` / Baseline scans

- **Aging** (140 animals, 258 scans): the longitudinal cohort. `op_week` NULL.
- **MI / AB** (operated models): each animal has exactly **one** scan, and every
  one is `op_week = Baseline`, i.e. **pre-operative**. There are no post-op
  scans. Because they are pre-op, these are healthy LA measurements.

### Analysis decision: pool Baseline scans into the healthy population

Current focus is the Aging cohort. The pre-op MI/AB Baseline scans are treated
as healthy observations and **pooled into the Aging population by `age_months`**
(age at scan), not analysed as a disease model:

- +8 animals into the age-9 group (MI baselines)
- +3 animals into the age-24 group (1 MI + 2 AB baselines)

All are single-scan. Keep `model`/`op_week` available so these can be excluded
for a sensitivity check if needed.

### Repeated-measures structure (Aging cohort)

`animal_id` repeats across `la_mri` for Aging animals — longitudinal data, not
independent samples. Per-animal MRI counts (Aging):

- 49 animals with 1 MRI
- 64 animals with 2 MRIs
- 27 animals with 3 MRIs

Analyses comparing groups must account for within-animal correlation
(paired tests / mixed-effects models, not tests that assume independence).
Pooled-in Baseline animals contribute a single scan each.

## Data-quality notes

Status of known issues (raw → fixed):

- **Volume units** — *converted in DB.* The three volume columns were originally
  in millilitres (`*_volume_ml`); they were multiplied by 1000 and renamed to
  microlitres (`*_volume_ul`) for more natural magnitudes at LA scale. Stroke
  volume equals max − min in all but 14 rows, where source-level rounding leaves
  a small discrepancy (pre-existing, unchanged by the conversion).
- **`gender`** — *fixed in DB.* One row (`AGORA112.M1`) had `Male\r` (trailing
  carriage return), distinct from `Male`; corrected via UPDATE. As a safeguard
  against any future recurrence, the loader still normalises whitespace
  (`df['gender'] = df['gender'].str.strip()`).
- **`op_week`** — *typo fixed in DB.* 258 of 269 rows are NULL; the only
  non-null value is now `Baseline` (11 rows). Still effectively unusable as a
  variable — verify before relying on it.

Still open — handle on load / verify before analysis:

- **`ejection_fraction`**: minimum of 3.07% is physiologically low — check
  for outliers / measurement errors before analysis.
- **NULL measurements**: ~2–3 rows have NULL measurement values; decide on
  drop vs. impute per analysis.

## Notes

- All `la_mri.animal_id` values exist in `subjects` (referential integrity holds).
- Volumes in microlitres (µl), lengths in millimetres (mm), EF as a percentage.
