"""Reusable plot primitives for LA measurements, split by sex.

The core builder draws, for one measurement, a box plot per timepoint with
Male and Female shown as separate coloured boxes side by side. Each box is
annotated inside with ``n=<animals>`` so the (unbalanced) sample behind it is
always visible.
"""

import numpy as np
from scipy import stats

# Okabe-Ito colours: distinguishable in greyscale and for colour-blind readers.
SEX_COLORS = {"Female": "#0072B2", "Male": "#E69F00"}
SEX_ORDER = ("Female", "Male")

# Horizontal offset of each sex's box from its timepoint centre, and box width.
SEX_OFFSET = 0.2
BOX_WIDTH = 0.34

# Neutral colour for diagnostic scatter points.
POINT_COLOR = "#2c5f86"


def plot_length_by_sex(axes, measurements, value_column, timepoints):
    """Draw timepoint box plots of ``value_column``, grouped by sex.

    Parameters
    ----------
    axes : matplotlib.axes.Axes
        Target axes to draw onto.
    measurements : pandas.DataFrame
        Must contain ``animal_id``, ``gender``, ``age_months`` and
        ``value_column``.
    value_column : str
        Measurement to plot on the y-axis, e.g. ``"max_length_mm"``.
    timepoints : sequence of int
        Scan-age timepoints in months, in display order (left to right).
    """
    position_of_timepoint = {age: index + 1 for index, age in enumerate(timepoints)}
    offset_of_sex = {"Female": -SEX_OFFSET, "Male": +SEX_OFFSET}

    for sex in SEX_ORDER:
        of_sex = measurements[measurements["gender"] == sex]
        _draw_sex_boxes(
            axes,
            of_sex,
            value_column,
            timepoints,
            position_of_timepoint,
            offset_of_sex[sex],
            SEX_COLORS[sex],
        )

    axes.set_xticks(list(position_of_timepoint.values()))
    axes.set_xticklabels([f"{age} mo" for age in timepoints])
    axes.set_xlabel("Age at scan")
    _add_sex_legend(axes)


def _draw_sex_boxes(
    axes, of_sex, value_column, timepoints, position_of_timepoint, offset, color
):
    """Draw one sex's boxes across timepoints, each labelled with its n."""
    for age in timepoints:
        at_timepoint = of_sex[of_sex["age_months"] == age]
        values = at_timepoint[value_column].dropna()
        if values.empty:
            continue

        position = position_of_timepoint[age] + offset
        axes.boxplot(
            [values.to_numpy()],
            positions=[position],
            widths=BOX_WIDTH,
            showfliers=False,
            patch_artist=True,
            boxprops={"facecolor": color, "edgecolor": "black", "alpha": 0.65},
            medianprops={"color": "black"},
            whiskerprops={"color": "black"},
            capprops={"color": "black"},
        )

        animal_count = at_timepoint.loc[values.index, "animal_id"].nunique()
        first_quartile, third_quartile = np.percentile(values, [25, 75])
        axes.text(
            position,
            (first_quartile + third_quartile) / 2,
            f"n={animal_count}",
            ha="center",
            va="center",
            fontsize=8,
            color="black",
        )


def _add_sex_legend(axes):
    """Add a sex legend using proxy patches in the box colours."""
    from matplotlib.patches import Patch

    handles = [
        Patch(facecolor=SEX_COLORS[sex], edgecolor="black", alpha=0.65, label=sex)
        for sex in SEX_ORDER
    ]
    axes.legend(handles=handles, title="Sex", frameon=False)


def plot_residual_diagnostics(residuals_axes, quantile_axes, fitted_model, title):
    """Draw residuals-vs-fitted and a normal Q-Q plot for a fitted model.

    Checks the two mixed-model assumptions that matter here: homoscedasticity
    (no funnel in residuals-vs-fitted) and approximately normal residuals.
    """
    fitted_values = fitted_model.fittedvalues
    residuals = fitted_model.resid

    residuals_axes.scatter(fitted_values, residuals, s=12, alpha=0.6, color=POINT_COLOR)
    residuals_axes.axhline(0, color="grey", linewidth=0.8)
    residuals_axes.set_xlabel("Fitted value")
    residuals_axes.set_ylabel("Residual")
    residuals_axes.set_title(f"{title}: residuals vs fitted")

    stats.probplot(residuals, plot=quantile_axes)
    quantile_axes.set_title(f"{title}: normal Q-Q")

    for axes in (residuals_axes, quantile_axes):
        axes.spines[["top", "right"]].set_visible(False)
