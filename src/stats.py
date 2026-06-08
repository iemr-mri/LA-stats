"""Mixed-effects models for longitudinal LA measurements.

One linear mixed model per outcome: categorical age x sex fixed effects with a
random intercept per animal, which absorbs the within-animal correlation of the
repeated MRI scans. Estimated marginal means and age contrasts are derived from
the fixed-effect estimates and their covariance. See
``analysis/length_mixed_effects.py`` for the run.
"""

import numpy as np
import pandas as pd
from patsy import dmatrix
from scipy import stats
import statsmodels.formula.api as smf

INTERACTION_FORMULA = "C(age_months) * C(gender)"
ADDITIVE_FORMULA = "C(age_months) + C(gender)"


def fit_length_model(measurements, value_column, reml=True):
    """Fit a random-intercept mixed model for one length outcome.

    Rows with a missing ``value_column`` are dropped (available-case). Returns
    the fitted statsmodels results object. Use ``reml=True`` for reporting
    estimates and ``reml=False`` (ML) when comparing fixed-effect structures.
    """
    usable = measurements.dropna(subset=[value_column]).copy()
    model = smf.mixedlm(
        f"{value_column} ~ {INTERACTION_FORMULA}",
        data=usable,
        groups=usable["animal_id"],
    )
    return model.fit(reml=reml)


def fixed_effects_table(fitted_model):
    """Return a tidy table of fixed-effect estimates, SEs, z, p and 95% CIs."""
    coefficients = fitted_model.fe_params
    names = coefficients.index
    confidence_interval = fitted_model.conf_int().loc[names]
    return pd.DataFrame(
        {
            "coefficient": coefficients,
            "standard_error": fitted_model.bse.loc[names],
            "z": fitted_model.tvalues.loc[names],
            "p_value": fitted_model.pvalues.loc[names],
            "ci_lower": confidence_interval[0],
            "ci_upper": confidence_interval[1],
        }
    )


def interaction_lrt(measurements, value_column):
    """Likelihood-ratio test for the age x sex interaction, using ML fits.

    Returns a dict with the chi-square statistic, degrees of freedom and
    p-value. Fixed-effect comparisons require ML, not REML.
    """
    usable = measurements.dropna(subset=[value_column]).copy()
    groups = usable["animal_id"]
    full = smf.mixedlm(
        f"{value_column} ~ {INTERACTION_FORMULA}", data=usable, groups=groups
    ).fit(reml=False)
    reduced = smf.mixedlm(
        f"{value_column} ~ {ADDITIVE_FORMULA}", data=usable, groups=groups
    ).fit(reml=False)

    statistic = 2 * (full.llf - reduced.llf)
    degrees_of_freedom = len(full.fe_params) - len(reduced.fe_params)
    p_value = stats.chi2.sf(statistic, degrees_of_freedom)
    return {"statistic": statistic, "df": degrees_of_freedom, "p_value": p_value}


def _aligned_design(fitted_model, timepoints, sexes):
    """Build a prediction grid and its fixed-effect design matrix.

    The grid spans every (timepoint, sex) cell so patsy infers the same
    categorical levels the model used; columns are aligned to the model's
    fixed-effect order.
    """
    grid = pd.DataFrame(
        [(age, sex) for sex in sexes for age in timepoints],
        columns=["age_months", "gender"],
    )
    design = dmatrix(INTERACTION_FORMULA, grid, return_type="dataframe")
    expected = fitted_model.fe_params.index
    missing = set(expected) - set(design.columns)
    if missing:
        raise ValueError(f"Design matrix missing expected columns: {missing}")
    return grid, design[expected]


def estimated_marginal_means(fitted_model, timepoints, sexes, confidence=0.95):
    """Model-based mean LA length per age x sex cell, with Wald CIs.

    The random intercept has mean zero, so the marginal mean of a cell is just
    its fixed-effect prediction; SEs come from the fixed-effect covariance.
    """
    grid, design = _aligned_design(fitted_model, timepoints, sexes)
    coefficients = fitted_model.fe_params.values
    fixed_covariance = fitted_model.cov_params().loc[
        fitted_model.fe_params.index, fitted_model.fe_params.index
    ].values

    means = design.values @ coefficients
    variances = np.einsum("ij,jk,ik->i", design.values, fixed_covariance, design.values)
    standard_errors = np.sqrt(variances)
    half_width = stats.norm.ppf(0.5 + confidence / 2)

    result = grid.copy()
    result["estimated_mean"] = means
    result["standard_error"] = standard_errors
    result["ci_lower"] = means - half_width * standard_errors
    result["ci_upper"] = means + half_width * standard_errors
    return result


def age_contrasts(fitted_model, timepoints, sexes, confidence=0.95):
    """Pairwise differences in mean length between timepoints, within each sex.

    Returns a table with each difference, its Wald SE/CI/p-value and a
    Bonferroni-adjusted p-value across all reported contrasts.
    """
    grid, design = _aligned_design(fitted_model, timepoints, sexes)
    coefficients = fitted_model.fe_params.values
    fixed_covariance = fitted_model.cov_params().loc[
        fitted_model.fe_params.index, fitted_model.fe_params.index
    ].values
    half_width = stats.norm.ppf(0.5 + confidence / 2)

    rows = []
    for sex in sexes:
        for earlier in range(len(timepoints)):
            for later in range(earlier + 1, len(timepoints)):
                earlier_row = (grid["gender"] == sex) & (grid["age_months"] == timepoints[earlier])
                later_row = (grid["gender"] == sex) & (grid["age_months"] == timepoints[later])
                contrast = design[later_row].values[0] - design[earlier_row].values[0]

                difference = contrast @ coefficients
                standard_error = np.sqrt(contrast @ fixed_covariance @ contrast)
                p_value = 2 * stats.norm.sf(abs(difference / standard_error))
                rows.append(
                    {
                        "gender": sex,
                        "from_age": timepoints[earlier],
                        "to_age": timepoints[later],
                        "difference": difference,
                        "standard_error": standard_error,
                        "ci_lower": difference - half_width * standard_error,
                        "ci_upper": difference + half_width * standard_error,
                        "p_value": p_value,
                    }
                )

    contrasts = pd.DataFrame(rows)
    contrasts["p_value_bonferroni"] = np.minimum(contrasts["p_value"] * len(contrasts), 1.0)
    return contrasts
