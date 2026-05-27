from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from hec_hms_preprocess.pipeline import (
    PipelineConfig,
    build_output_path,
    find_rasters,
    run_pipeline,
)


class PipelineTests(unittest.TestCase):
    def test_find_rasters_supports_tif_and_tiff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.tif").write_text("fake")
            (root / "b.tiff").write_text("fake")
            (root / "c.txt").write_text("fake")
            self.assertEqual(len(find_rasters(root)), 2)

    def test_build_output_path(self) -> None:
        output = build_output_path(Path("rainfall.tif"), Path("out"), "_resampled", ".tif")
        self.assertEqual(output, Path("out/rainfall_resampled.tif"))

    def test_dry_run_builds_full_plan_without_gdal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_dir = root / "rasters"
            input_dir.mkdir()
            (input_dir / "rainfall.tif").write_text("fake")
            shapefile = root / "boundary.shp"
            shapefile.write_text("fake")

            result = run_pipeline(
                PipelineConfig(
                    input_dir=input_dir,
                    work_dir=root / "outputs",
                    shapefile=shapefile,
                    dry_run=True,
                )
            )

            self.assertEqual(result.summary["planned"], 3)
            self.assertEqual(result.summary["resample"], 1)
            self.assertEqual(result.summary["clip"], 1)
            self.assertEqual(result.summary["ascii"], 1)
            self.assertEqual(result.created_files, [])

    def test_clip_requires_shapefile_unless_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "rainfall.tif").write_text("fake")
            with self.assertRaises(ValueError):
                run_pipeline(PipelineConfig(input_dir=root, dry_run=True))

            result = run_pipeline(
                PipelineConfig(input_dir=root, dry_run=True, skip_clip=True)
            )
            self.assertEqual(result.summary["planned"], 2)


if __name__ == "__main__":
    unittest.main()
