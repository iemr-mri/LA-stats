"""Mixed-effects analysis of longitudinal LA length, by age and sex.

For each length measure (max, min): a random-intercept linear mixed model with
categorical age x sex fixed effects over the Aging cohort, the likelihood-ratio
test for the age x sex interaction, estimated marginal means and pairwise age
contrasts per sex, plus residual diagnostics. Ends with a sensitivity refit that
pools in the healthy MI/AB Baseline scans. Run from the project root:

    .venv\\Scripts\\python.exe analysis\\length_mixed_effects.py
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data import NOMINAL_TIMEPOINTS, load_la_measurements, to_nominal_timepoints
from src.plotting import SEX_ORDER, plot_residual_diagnostics
from src.stats import (
    age_contrasts,
    estimated_marginal_means,
    fit_length_model,
    fixed_effects_table,
    interaction_lrt,
)

FIGURES_DIRECTORY = PROJECT_ROOT / "figs" / "length"

LENGTH_OUTCOMES = (
    ("max_length_mm", "LA length at maximum size"),
    ("min_length_mm", "LA length at minimum size"),
)

pd.set_option("display.width", 120)
pd.set_option("display.float_format", lambda value: f"{value:.4f}")


def report_outcome(measurements, value_column, label):
    """Fit, test and summarise one length outcome; save residual diagnostics."""
    print(f"\n{'=' * 70}\n{label}  ({value_column})\n{'=' * 70}")

    model = fit_length_model(measurements, value_column, reml=True)
    print("\nFixed effects (REML):")
    print(fixed_effects_table(model).to_string())
    print(f"\nRandom intercept variance (animal): {model.cov_re.iloc[0, 0]:.4f}")
    print(f"Residual variance:                  {model.scale:.4f}")

    interaction = interaction_lrt(measurements, value_column)
    print(
        f"\nAge x sex interaction (LRT): chi2({interaction['df']}) = "
        f"{interaction['statistic']:.3f}, p = {interaction['p_value']:.4f}"
    )

    print("\nEstimated marginal means (mm):")
    print(estimated_marginal_means(model, NOMINAL_TIMEPOINTS, SEX_ORDER).to_string(index=False))

    print("\nPairwise age contrasts within sex (Bonferroni-adjusted):")
    print(age_contrasts(model, NOMINAL_TIMEPOINTS, SEX_ORDER).to_string(index=False))

    _save_diagnostics(model, value_column, label)
    return model


def _save_diagnostics(model, value_column, label):
    """Save residuals-vs-fitted and Q-Q diagnostics for one model."""
    figure, (residuals_axes, quantile_axes) = plt.subplots(1, 2, figsize=(11, 4.5))
    plot_residual_diagnostics(residuals_axes, quantile_axes, model, label)
    figure.tight_layout()
    output_path = FIGURES_DIRECTORY / f"{value_column}_residual_diagnostics.svg"
    figure.savefig(output_path, format="svg", bbox_inches="tight")
    plt.close(figure)
    print(f"\nWrote {output_path}")


def report_sensitivity(value_column):
    """Refit the interaction LRT with the MI/AB Baseline scans pooled in."""
    pooled = to_nominal_timepoints(load_la_measurements(pool_baseline=True))
    interaction = interaction_lrt(pooled, value_column)
    print(
        f"  {value_column}: age x sex interaction chi2({interaction['df']}) = "
        f"{interaction['statistic']:.3f}, p = {interaction['p_value']:.4f}"
    )


def main():
    FIGURES_DIRECTORY.mkdir(parents=True, exist_ok=True)
    measurements = to_nominal_timepoints(load_la_measurements(pool_baseline=False))

    for value_column, label in LENGTH_OUTCOMES:
        report_outcome(measurements, value_column, label)

    print(f"\n{'=' * 70}\nSensitivity: MI/AB Baseline scans pooled into Aging\n{'=' * 70}")
    for value_column, _ in LENGTH_OUTCOMES:
        report_sensitivity(value_column)


if __name__ == "__main__":
    main()
