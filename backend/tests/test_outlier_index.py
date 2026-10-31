"""Regression tests for row-aligned z-score outlier masks."""

import importlib.util
import unittest
from pathlib import Path

import pandas as pd

spec = importlib.util.spec_from_file_location(
    "validators", Path(__file__).resolve().parents[1] / "data_ingestion" / "validators.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class OutlierIndexTests(unittest.TestCase):
    def test_missing_rows_keep_original_labels(self):
        df = pd.DataFrame({"price": [1.0, None, 1.0, 10.0]}, index=["a", "b", "c", "d"])
        valid, mask = module.DataValidator.check_outliers(df, "price", method="zscore", threshold=1.0)
        self.assertFalse(valid)
        pd.testing.assert_series_equal(mask, pd.Series([False, False, False, True], index=df.index, name="price"))
        self.assertEqual(df.loc[mask].index.tolist(), ["d"])

    def test_duplicate_labels_preserved(self):
        df = pd.DataFrame({"price": [1.0, None, 1.0, 10.0]}, index=[4, 4, 7, 7])
        _, mask = module.DataValidator.check_outliers(df, "price", method="zscore", threshold=1.0)
        self.assertEqual(mask.tolist(), [False, False, False, True])
        self.assertTrue(mask.index.equals(df.index))

    def test_all_missing_rows_return_full_false_mask(self):
        df = pd.DataFrame({"price": [float("nan"), float("nan")]}, index=[8, 9])
        valid, mask = module.DataValidator.check_outliers(df, "price", method="zscore")
        self.assertTrue(valid)
        self.assertEqual(mask.tolist(), [False, False])
        self.assertTrue(mask.index.equals(df.index))

    def test_constant_values_and_missing_row_are_not_outliers(self):
        df = pd.DataFrame({"price": [2.0, None, 2.0]}, index=[5, 6, 7])
        valid, mask = module.DataValidator.check_outliers(df, "price", method="zscore")
        self.assertTrue(valid)
        self.assertEqual(mask.tolist(), [False, False, False])
        self.assertTrue(mask.index.equals(df.index))


if __name__ == "__main__":
    unittest.main()
