from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
import pandas as pd
import seaborn as sns

from cursor_cost_dashboard.palettes import CATEGORY_COLORS, CATEGORY_ORDER, COST_BINS, MODEL_COLORS, infer_provider


def _day_index_map(df: pd.DataFrame) -> tuple[list[str], dict[str, int]]:
    day_order = sorted(df["Day"].unique())
    return day_order, {day: idx for idx, day in enumerate(day_order)}


def _finalize_event_axis(ax: plt.Axes, day_order: list[str]) -> None:
    ax.set_title("Event Times by Day")
    ax.set_xlabel("Time of Day (JST)")
    ax.set_ylabel("Date")
    ax.set_xlim(0, 24)
    ax.set_xticks(range(0, 25, 2))
    ax.set_xticklabels([f"{hour:02d}:00" for hour in range(0, 25, 2)], rotation=30)
    ax.set_yticks(list(range(len(day_order))))
    ax.set_yticklabels(day_order)
    ax.grid(axis="x", color="#d0d0d0", linewidth=0.8)


def _sorted_model_order(models: pd.Series) -> list[str]:
    return sorted(models.dropna().unique().tolist(), key=lambda model: (infer_provider(model), model.casefold()))


def _sorted_group_order(df: pd.DataFrame) -> list[str]:
    return (
        df.loc[:, ["Provider", "Model", "MaxMode", "GroupLabel"]]
        .drop_duplicates()
        .sort_values(["Provider", "Model", "MaxMode"], kind="stable")
        ["GroupLabel"]
        .tolist()
    )


def _legend_handles(labels: list[str], color_map: dict[str, str]) -> list[Line2D]:
    return [
        Line2D(
            [0],
            [0],
            marker="o",
            linestyle="None",
            markerfacecolor=color_map[label],
            markeredgecolor=color_map[label],
            markersize=8,
            label=label,
        )
        for label in labels
    ]


def _high_load_reference_points(df: pd.DataFrame) -> pd.DataFrame:
    reference_rows: list[pd.DataFrame] = []
    for _, model_df in df.groupby("Model", observed=True, sort=False):
        q90 = model_df["Cost"].quantile(0.90)
        upper_tail = model_df.loc[model_df["Cost"] >= q90]
        reference_rows.append(
            pd.DataFrame(
                {
                    "Model": [model_df["Model"].iloc[0]],
                    "TotalTokens": [upper_tail["TotalTokens"].mean()],
                    "Cost": [upper_tail["Cost"].mean()],
                    "TotalTokensMillions": [upper_tail["TotalTokensMillions"].mean()],
                }
            )
        )
    return pd.concat(reference_rows, ignore_index=True)


def plot_cost_raster(df: pd.DataFrame, output_path: Path) -> None:
    plot_df = (
        df.loc[:, ["Date", "Cost"]]
        .assign(Cost=lambda x: pd.to_numeric(x["Cost"], errors="coerce"))
        .dropna(subset=["Date"])
        .pipe(_add_event_base)
        .assign(CostForCategory=lambda x: x["Cost"].fillna(0))
    )
    plot_df = plot_df.assign(
        Category=pd.Categorical(
            pd.cut(
                plot_df["CostForCategory"],
                bins=COST_BINS,
                labels=CATEGORY_ORDER,
                right=False,
            ),
            categories=CATEGORY_ORDER,
            ordered=True,
        )
    )
    day_order, day_to_index = _day_index_map(plot_df)
    plot_df = plot_df.assign(DayIndex=lambda x: x["Day"].map(day_to_index)).sort_values(
        ["Category", "Day", "TimeHour"],
        kind="stable",
    )

    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(12, max(3, len(day_order) * 0.8)))
    sns.scatterplot(
        data=plot_df,
        x="TimeHour",
        y="DayIndex",
        hue="Category",
        hue_order=CATEGORY_ORDER,
        palette=CATEGORY_COLORS,
        marker="|",
        s=700,
        linewidth=2,
        ax=ax,
    )
    _finalize_event_axis(ax, day_order)
    sns.move_legend(
        ax,
        "upper left",
        bbox_to_anchor=(1.02, 1),
        title="Cost per event",
        handles=_legend_handles(CATEGORY_ORDER, CATEGORY_COLORS),
    )
    fig.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def plot_model_budget_raster(df: pd.DataFrame, output_path: Path) -> None:
    plot_df = (
        df.loc[:, ["Date", "Model", "Max Mode"]]
        .assign(
            Model=lambda x: x["Model"].fillna("Unknown"),
            MaxMode=lambda x: x["Max Mode"].fillna("Unknown"),
        )
        .dropna(subset=["Date"])
        .pipe(_add_event_base)
        .assign(
            Provider=lambda x: x["Model"].map(infer_provider),
            GroupLabel=lambda x: x["Provider"] + " | " + x["Model"] + " | MaxMode=" + x["MaxMode"],
        )
    )
    day_order, day_to_index = _day_index_map(plot_df)
    group_order = _sorted_group_order(plot_df)
    color_map = {group: MODEL_COLORS.get(group.split(" | ")[1], "#6b7280") for group in group_order}
    plot_df = plot_df.assign(
        GroupLabel=pd.Categorical(plot_df["GroupLabel"], categories=group_order, ordered=True),
        DayIndex=lambda x: x["Day"].map(day_to_index),
    ).sort_values(["GroupLabel", "Day", "TimeHour"], kind="stable")

    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(13, max(3, len(day_order) * 0.8)))
    sns.scatterplot(
        data=plot_df,
        x="TimeHour",
        y="DayIndex",
        hue="GroupLabel",
        hue_order=group_order,
        palette=color_map,
        marker="|",
        s=700,
        linewidth=2,
        ax=ax,
    )
    _finalize_event_axis(ax, day_order)
    sns.move_legend(
        ax,
        "upper left",
        bbox_to_anchor=(1.02, 1),
        title="Model / Budget",
        handles=_legend_handles(group_order, color_map),
    )
    fig.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def plot_total_tokens_raster(df: pd.DataFrame, output_path: Path) -> None:
    plot_df = (
        df.loc[:, ["Date", "Total Tokens"]]
        .assign(TotalTokens=lambda x: pd.to_numeric(x["Total Tokens"], errors="coerce"))
        .dropna(subset=["Date", "TotalTokens"])
        .pipe(_add_event_base)
    )
    day_order, day_to_index = _day_index_map(plot_df)
    plot_df = plot_df.assign(DayIndex=lambda x: x["Day"].map(day_to_index))

    fig, ax = plt.subplots(figsize=(12, max(3, len(day_order) * 0.8)))
    scatter = ax.scatter(
        plot_df["TimeHour"],
        plot_df["DayIndex"],
        c=plot_df["TotalTokens"],
        cmap="Blues",
        norm=Normalize(vmin=plot_df["TotalTokens"].min(), vmax=plot_df["TotalTokens"].max()),
        marker="|",
        s=700,
        linewidths=2,
    )
    _finalize_event_axis(ax, day_order)
    fig.colorbar(scatter, ax=ax, label="Total Tokens")
    fig.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def plot_cost_tokens_scatter(df: pd.DataFrame, output_path: Path) -> None:
    plot_df = (
        df.loc[:, ["Total Tokens", "Cost", "Model"]]
        .assign(
            TotalTokens=lambda x: pd.to_numeric(x["Total Tokens"], errors="coerce"),
            Cost=lambda x: pd.to_numeric(x["Cost"], errors="coerce"),
            Model=lambda x: x["Model"].fillna("Unknown"),
        )
        .dropna(subset=["TotalTokens", "Cost", "Model"])
        .sort_values(["Model", "TotalTokens"])
    )
    model_order = _sorted_model_order(plot_df["Model"])
    palette = {model: MODEL_COLORS.get(model, "#6b7280") for model in model_order}

    sns.set_theme(style="whitegrid")
    plot_df = plot_df.assign(Model=pd.Categorical(plot_df["Model"], categories=model_order, ordered=True)).sort_values(
        ["Model", "TotalTokens"],
        kind="stable",
    )
    plot_df = plot_df.assign(TotalTokensMillions=lambda x: x["TotalTokens"] / 1_000_000)
    reference_df = _high_load_reference_points(plot_df)
    x_limits = (0, plot_df["TotalTokensMillions"].max() * 1.05)
    y_limits = (0, plot_df["Cost"].max() * 1.08)
    fig, ax = plt.subplots(figsize=(12.5, 7.5))
    sns.scatterplot(
        data=plot_df,
        x="TotalTokensMillions",
        y="Cost",
        hue="Model",
        hue_order=model_order,
        palette=palette,
        s=42,
        alpha=0.28,
        legend=False,
        ax=ax,
    )
    sns.scatterplot(
        data=reference_df,
        x="TotalTokensMillions",
        y="Cost",
        hue="Model",
        hue_order=model_order,
        palette=palette,
        s=170,
        alpha=1.0,
        linewidth=2.2,
        edgecolor="#111827",
        legend=False,
        zorder=5,
        ax=ax,
    )

    for model in model_order:
        model_df = plot_df.loc[plot_df["Model"] == model]
        if len(model_df) >= 2 and model_df["TotalTokens"].nunique() >= 2 and model_df["Cost"].nunique() >= 2:
            regression_order = 2 if len(model_df) >= 4 and model_df["TotalTokens"].nunique() >= 4 and model_df["Cost"].nunique() >= 4 else 1

            # Keep the extrapolated trend visible even where the model has no observations.
            sns.regplot(
                data=model_df,
                x="TotalTokensMillions",
                y="Cost",
                scatter=False,
                order=regression_order,
                ci=None,
                truncate=False,
                color=palette[model],
                line_kws={"linewidth": 2.2, "alpha": 0.95, "zorder": 4},
                ax=ax,
            )

            # Confidence bands are skipped for sparse models and limited to the observed range.
            if len(model_df) >= 8 and model_df["TotalTokens"].nunique() >= 5 and model_df["Cost"].nunique() >= 5:
                sns.regplot(
                    data=model_df,
                    x="TotalTokensMillions",
                    y="Cost",
                    scatter=False,
                    order=regression_order,
                    ci=90,
                    n_boot=500,
                    seed=0,
                    truncate=True,
                    color=palette[model],
                    line_kws={"linewidth": 1.6, "alpha": 0.0, "zorder": 3},
                    ax=ax,
                )
    fig.suptitle("Cost (USD) vs Total Tokens by Model", y=0.985, fontsize=16)
    ax.set_xlabel("Total Tokens (Millions)")
    ax.set_ylabel("Cost (USD)")
    ax.set_xlim(*x_limits)
    ax.set_ylim(*y_limits)
    legend_handles = _legend_handles(model_order, palette)
    fig.legend(legend_handles, [handle.get_label() for handle in legend_handles], loc="upper left", bbox_to_anchor=(1.01, 0.92), title="Model")
    fig.text(
        0.5,
        0.945,
        "Outlined markers show the mean of samples at or above each model's 90th-percentile cost.\nConfidence bands appear only when observations are sufficient; trend lines extend beyond the observed range.",
        ha="center",
        va="top",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.89))
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def _add_event_base(df: pd.DataFrame) -> pd.DataFrame:
    return df.assign(
        Day=lambda x: x["Date"].dt.strftime("%Y-%m-%d"),
        TimeHour=lambda x: (
            x["Date"].dt.hour
            + x["Date"].dt.minute / 60
            + x["Date"].dt.second / 3600
            + x["Date"].dt.microsecond / 3_600_000_000
        ),
    )
