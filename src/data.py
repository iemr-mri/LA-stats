"""Load and clean left-atrium MRI measurements from the AGORA database.

Every analysis starts from :func:`load_la_measurements`, so the load-time
decisions documented in ``SCHEMA.md`` (whitespace cleanup, optional pooling of
the pre-op MI/AB Baseline scans into the Aging population) live in one place.
"""

import sqlite3
from pathlib import Path

import pandas as pd

DATABASE_PATH = Path(r"C:\Users\heskalde\Databases\AGORA-db\AGORA_LA.db")

# Scan-age timepoints the longitudinal study targets, in months.
NOMINAL_TIMEPOINTS = (9, 16, 24)

# Off-schedule scan ages excluded when binning to nominal timepoints. The five
# 18-month Aging scans are dropped for the longitudinal length analysis.
OFF_SCHEDULE_AGE_MONTHS = (18,)

_MEASUREMENT_QUERY = """
    SELECT
        l.mri_id,
        l.animal_id,
        l.age_months,
        l.max_volume_ul,
        l.min_volume_ul,
        l.stroke_volume_ul,
        l.ejection_fraction,
        l.max_length_mm,
        l.min_length_mm,
        l.op_week,
        s.gender,
        s.cohort,
        s.model,
        s.age_group
    FROM la_mri AS l
    JOIN subjects AS s ON s.animal_id = l.animal_id
"""


def load_la_measurements(database_path=DATABASE_PATH, pool_baseline=False):
    """Return one cleaned, analysis-ready row per MRI session.

    Parameters
    ----------
    database_path : Path or str
        Location of the AGORA_LA SQLite file.
    pool_baseline : bool
        When ``False`` (default) only the Aging cohort is returned -- the pure
        longitudinal population. When ``True`` the single-scan pre-op MI/AB
        Baseline sessions are pooled in as healthy observations, keyed by their
        ``age_months`` (see ``SCHEMA.md``). The ``model`` and ``op_week``
        columns are retained either way so pooled rows can be filtered out for a
        sensitivity check.

    Raises
    ------
    FileNotFoundError
        If ``database_path`` does not exist.
    """
    database_path = Path(database_path)
    if not database_path.exists():
        raise FileNotFoundError(f"AGORA database not found at {database_path}")

    connection = sqlite3.connect(database_path)
    try:
        measurements = pd.read_sql_query(_MEASUREMENT_QUERY, connection)
    finally:
        connection.close()

    # Safeguard against the historical 'Male\r' issue (see SCHEMA.md).
    measurements["gender"] = measurements["gender"].str.strip()

    if pool_baseline:
        keep_model = measurements["model"].isin(["Aging", "MI", "AB"])
    else:
        keep_model = measurements["model"] == "Aging"
    measurements = measurements[keep_model].reset_index(drop=True)

    return measurements


def to_nominal_timepoints(measurements, timepoints=NOMINAL_TIMEPOINTS):
    """Filter to the nominal scan-age timepoints, dropping off-schedule scans.

    Keeps only rows whose ``age_months`` is one of ``timepoints`` and adds a
    categorical ``timepoint`` column ordered as given. The five 18-month scans
    fall away here because 18 is not a nominal timepoint.
    """
    on_schedule = measurements["age_months"].isin(timepoints)
    binned = measurements[on_schedule].copy()
    binned["timepoint"] = pd.Categorical(
        binned["age_months"], categories=list(timepoints), ordered=True
    )
    return binned.reset_index(drop=True)
