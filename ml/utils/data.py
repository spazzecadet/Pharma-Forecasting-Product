from __future__ import annotations

import os
import pandas as pd


def load_sample_series(brand_id: str = "BRAND_A", value_col: str = "trx") -> pd.Series:
	"""Load sample weekly demand series for a brand from data/sample/fact_demand.csv."""
	root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
	path = os.path.join(root, "data", "sample", "fact_demand.csv")
	df = pd.read_csv(path, parse_dates=["date"])
	df = df[df["brand_id"] == brand_id].sort_values("date")
	return df[value_col].reset_index(drop=True)

