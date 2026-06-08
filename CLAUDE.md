## Project
Analysis of size measurements of the left atrium in rats, volume and length at maximum and minimum
LA size (as determined by 4-chamber view).

Loading, statistical analysis and figure exports.

## Analysis conventions
- Always split analyses by sex (Male/Female) — every figure and statistical
  comparison is reported separately for, or grouped by, sex.

## Stack
- Python 3.10 (venv at `.venv/`; activate with `.venv\Scripts\activate`)

Installed packages (pinned to what's in the venv):
- numpy 2.2.6
- pandas 2.3.3
- matplotlib 3.10.9
- scipy 1.15.3
- statsmodels 0.14.6

## Structure
AGORA SQLite database:
`C:\Users\heskalde\Databases\AGORA-db\AGORA_LA.db`
Schema, value ranges and data-quality notes: `SCHEMA.md`

Figures (in SVG-format):
`figs/`

## Git
- The user handles ALL git operations (staging, commits, branches, push).
  Do not run `git add`/`commit`/`push`/branch commands or offer to commit;
  read-only git inspection (`status`, `diff`, `log`) is fine.

## Don't
- Don't use `# type: ignore` without a comment explaining why.
- Don't catch bare `Exception` — catch specific exceptions.

## Keeping docs in sync
After any structural change (new file, renamed file, split/merged module, added public function), 
update `README.md`.