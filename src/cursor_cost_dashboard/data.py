from pathlib import Path

import pandas as pd


def load_usage_data(csv_path: Path, timezone: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    return df.assign(Date=lambda x: pd.to_datetime(x["Date"], utc=True).dt.tz_convert(timezone))


def add_day_time_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.assign(
        Day=lambda x: x["Date"].dt.strftime("%Y-%m-%d"),
        TimeHour=lambda x: (
            x["Date"].dt.hour
            + x["Date"].dt.minute / 60
            + x["Date"].dt.second / 3600
            + x["Date"].dt.microsecond / 3_600_000_000
        ),
    )
