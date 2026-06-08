"""Longitudinal box plots of LA length across the nominal scan timepoints.

One figure per length measure (max, min), each over the Aging cohort and split
by sex (Male/Female as separate coloured boxes), binned to the nominal
9 / 16 / 24-month timepoints. Off-schedule 18-month scans are dropped by
:func:`to_nominal_timepoints`. Run from the project root:

    .venv\\Scripts\\python.exe analysis\\length_longitudinal.py
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data import NOMINAL_TIMEPOINTS, load_la_measurements, to_nominal_timepoints
from src.plotting import plot_length_by_sex

FIGURES_DIRECTORY = PROJECT_ROOT / "figs" / "length"

# (value column, figure title, output filename) per length measure.
LENGTH_FIGURES = (
    ("max_length_mm", "Longitudinal LA length at maximum size", "max_length_longitudinal.svg"),
    ("min_length_mm", "Longitudinal LA length at minimum size", "min_length_longitudinal.svg"),
)


def build_length_figure(measurements, value_column, title):
    """Return a single-panel figure of one length measure, split by sex."""
    figure, axes = plt.subplots(figsize=(7, 5))

    plot_length_by_sex(axes, measurements, value_column, NOMINAL_TIMEPOINTS)
    axes.set_ylabel("LA length (mm)")
    axes.set_title(title)
    axes.spines[["top", "right"]].set_visible(False)

    figure.tight_layout()
    return figure


def main():
    measurements = load_la_measurements(pool_baseline=False)
    timepoint_measurements = to_nominal_timepoints(measurements)
    FIGURES_DIRECTORY.mkdir(parents=True, exist_ok=True)

    for value_column, title, filename in LENGTH_FIGURES:
        figure = build_length_figure(timepoint_measurements, value_column, title)
        output_path = FIGURES_DIRECTORY / filename
        figure.savefig(output_path, format="svg", bbox_inches="tight")
        plt.close(figure)
        print(f"Wrote {output_path}")

    print(f"Scans plotted: {len(timepoint_measurements)} "
          f"(from {timepoint_measurements['animal_id'].nunique()} animals)")


if __name__ == "__main__":
    main()
