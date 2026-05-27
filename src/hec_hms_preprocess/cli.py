"""Command-line interface for HEC-HMS raster preprocessing."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .pipeline import GdalUnavailable, PipelineConfig, run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hec-hms-preprocess",
        description="Resample, clip, and convert raster grids for HEC-HMS.",
    )
    parser.add_argument("--input-dir", required=True, type=Path, help="Folder containing TIFF rasters.")
    parser.add_argument("--work-dir", default=Path("outputs"), type=Path, help="Output workspace.")
    parser.add_argument("--shapefile", type=Path, help="Boundary shapefile for clipping.")
    parser.add_argument("--pixel-size", default=0.0001, type=float, help="Output pixel size for resampling.")
    parser.add_argument("--resample-algorithm", default="bilinear", help="GDAL resampling algorithm.")
    parser.add_argument("--source-nodata", type=float, help="Input NoData value.")
    parser.add_argument("--destination-nodata", default=-9999.0, type=float, help="Output NoData value.")
    parser.add_argument("--target-srs", help="Optional GDAL target CRS, such as EPSG:4326.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing outputs.")
    parser.add_argument("--dry-run", action="store_true", help="Print the processing plan without running GDAL.")
    parser.add_argument("--skip-resample", action="store_true", help="Use input TIFFs directly.")
    parser.add_argument("--skip-clip", action="store_true", help="Skip shapefile clipping.")
    parser.add_argument("--skip-ascii", action="store_true", help="Skip ASCII-grid export.")
    parser.add_argument("--json", action="store_true", help="Print summary as JSON.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    config = PipelineConfig(
        input_dir=args.input_dir,
        work_dir=args.work_dir,
        shapefile=args.shapefile,
        pixel_size=args.pixel_size,
        resample_algorithm=args.resample_algorithm,
        source_nodata=args.source_nodata,
        destination_nodata=args.destination_nodata,
        target_srs=args.target_srs,
        overwrite=args.overwrite,
        dry_run=args.dry_run,
        skip_resample=args.skip_resample,
        skip_clip=args.skip_clip,
        skip_ascii=args.skip_ascii,
    )

    try:
        result = run_pipeline(config)
    except GdalUnavailable as exc:
        parser.exit(2, f"{exc}\n")

    if args.json:
        print(
            json.dumps(
                {
                    "summary": result.summary,
                    "operations": [
                        {
                            "step": operation.step,
                            "source": str(operation.source),
                            "destination": str(operation.destination),
                        }
                        for operation in result.operations
                    ],
                },
                indent=2,
            )
        )
    else:
        print("Pipeline plan:")
        for operation in result.operations:
            print(f"- {operation.step}: {operation.source} -> {operation.destination}")
        print(f"Summary: {result.summary}")

    return 0
