import argparse
from pathlib import Path

from rich import print

from cursor_cost_dashboard.config import DEFAULT_OUTPUT_DIR, DEFAULT_TIMEZONE
from cursor_cost_dashboard.data import load_usage_data
from cursor_cost_dashboard.plots import (
    plot_cost_15min_raster,
    plot_cost_raster,
    plot_cost_tokens_scatter,
    plot_model_budget_raster,
    plot_total_tokens_raster,
)

PLOT_BUILDERS = {
    "cost-raster": ("event_raster.png", plot_cost_raster),
    "cost-15min-raster": ("event_raster_cost_15min.png", plot_cost_15min_raster),
    "model-budget-raster": ("event_raster_model_budget.png", plot_model_budget_raster),
    "total-tokens-raster": ("event_raster_total_tokens.png", plot_total_tokens_raster),
    "cost-tokens-scatter": ("cost_tokens_model_scatter.png", plot_cost_tokens_scatter),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate reusable Cursor cost dashboard plots")
    parser.add_argument("--csv", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--plot",
        choices=["all", *PLOT_BUILDERS.keys()],
        default="all",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    df = load_usage_data(args.csv, timezone=DEFAULT_TIMEZONE)

    selected = PLOT_BUILDERS.items() if args.plot == "all" else [(args.plot, PLOT_BUILDERS[args.plot])]
    for plot_name, (filename, builder) in selected:
        output_path = args.output_dir / filename
        builder(df.copy(), output_path)
        print(f"[green]Generated[/green] {plot_name}: {output_path}")


if __name__ == "__main__":
    main()
