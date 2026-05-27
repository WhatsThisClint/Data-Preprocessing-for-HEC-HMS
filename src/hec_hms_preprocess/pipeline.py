"""Reusable raster preprocessing pipeline for HEC-HMS gridded inputs."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Literal

RasterStep = Literal["resample", "clip", "ascii"]


class GdalUnavailable(RuntimeError):
    """Raised when a raster operation needs GDAL but it is not installed."""


@dataclass(frozen=True)
class PipelineConfig:
    """Configuration for the raster preprocessing workflow."""

    input_dir: Path | str
    work_dir: Path | str = "outputs"
    shapefile: Path | str | None = None
    pixel_size: float | None = 0.0001
    resample_algorithm: str = "bilinear"
    source_nodata: float | None = None
    destination_nodata: float = -9999.0
    target_srs: str | None = None
    output_prefix: str = ""
    overwrite: bool = False
    dry_run: bool = False
    skip_resample: bool = False
    skip_clip: bool = False
    skip_ascii: bool = False
    patterns: tuple[str, ...] = ("*.tif", "*.tiff")

    def __post_init__(self) -> None:
        object.__setattr__(self, "input_dir", Path(self.input_dir))
        object.__setattr__(self, "work_dir", Path(self.work_dir))
        if self.shapefile is not None:
            object.__setattr__(self, "shapefile", Path(self.shapefile))
        if self.pixel_size is not None and self.pixel_size <= 0:
            raise ValueError("pixel_size must be greater than zero")

    @property
    def resampled_dir(self) -> Path:
        return self.work_dir / "resampled"

    @property
    def clipped_dir(self) -> Path:
        return self.work_dir / "clipped"

    @property
    def ascii_dir(self) -> Path:
        return self.work_dir / "ascii"


@dataclass
class PlannedOperation:
    step: RasterStep
    source: Path
    destination: Path


@dataclass
class PipelineResult:
    """Pipeline outputs and operation summary."""

    operations: list[PlannedOperation] = field(default_factory=list)
    created_files: list[Path] = field(default_factory=list)
    skipped_files: list[Path] = field(default_factory=list)

    @property
    def summary(self) -> dict[str, int]:
        counts = {"planned": len(self.operations), "created": len(self.created_files), "skipped": len(self.skipped_files)}
        for step in ("resample", "clip", "ascii"):
            counts[step] = sum(1 for operation in self.operations if operation.step == step)
        return counts


def run_pipeline(config: PipelineConfig) -> PipelineResult:
    """Run the full raster preprocessing pipeline."""

    validate_config(config)
    result = PipelineResult()
    raster_paths = find_rasters(config.input_dir, config.patterns)
    if not raster_paths:
        raise ValueError(f"No raster files found in {config.input_dir}")

    current_paths = raster_paths
    if not config.skip_resample:
        current_paths = _resample_many(current_paths, config, result)
    if not config.skip_clip:
        current_paths = _clip_many(current_paths, config, result)
    if not config.skip_ascii:
        _ascii_many(current_paths, config, result)

    return result


def validate_config(config: PipelineConfig) -> None:
    """Validate filesystem settings before building a processing plan."""

    if not config.input_dir.exists():
        raise FileNotFoundError(f"Input directory does not exist: {config.input_dir}")
    if not config.input_dir.is_dir():
        raise NotADirectoryError(f"Input path is not a directory: {config.input_dir}")
    if not config.skip_clip and config.shapefile is None:
        raise ValueError("A shapefile is required unless --skip-clip is used")
    if config.shapefile is not None and not config.shapefile.exists():
        raise FileNotFoundError(f"Clip shapefile does not exist: {config.shapefile}")


def find_rasters(input_dir: Path | str, patterns: Iterable[str] = ("*.tif", "*.tiff")) -> list[Path]:
    """Find raster files matching one or more glob patterns."""

    root = Path(input_dir)
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(root.glob(pattern))
    return sorted({path.resolve() for path in paths if path.is_file()})


def build_output_path(source: Path, destination_dir: Path, suffix: str, extension: str) -> Path:
    """Build a deterministic output path for a pipeline step."""

    return destination_dir / f"{source.stem}{suffix}{extension}"


def resample_raster(source: Path, destination: Path, config: PipelineConfig) -> None:
    """Resample a raster with GDAL Warp."""

    gdal = _import_gdal()
    options = {
        "xRes": config.pixel_size,
        "yRes": config.pixel_size,
        "resampleAlg": config.resample_algorithm,
        "dstNodata": config.destination_nodata,
        "multithread": True,
        "format": "GTiff",
        "creationOptions": ["COMPRESS=LZW", "TILED=YES"],
    }
    if config.source_nodata is not None:
        options["srcNodata"] = config.source_nodata
    if config.target_srs:
        options["dstSRS"] = config.target_srs
    _run_warp(gdal, source, destination, options)


def clip_raster(source: Path, destination: Path, config: PipelineConfig) -> None:
    """Clip a raster to the configured shapefile boundary."""

    if config.shapefile is None:
        raise ValueError("shapefile is required for clipping")
    gdal = _import_gdal()
    options = {
        "cutlineDSName": str(config.shapefile),
        "cropToCutline": True,
        "dstNodata": config.destination_nodata,
        "multithread": True,
        "format": "GTiff",
        "creationOptions": ["COMPRESS=LZW", "TILED=YES"],
    }
    _run_warp(gdal, source, destination, options)


def raster_to_ascii(source: Path, destination: Path, config: PipelineConfig) -> None:
    """Convert a raster to Arc/Info ASCII Grid for HEC-HMS ingestion."""

    gdal = _import_gdal()
    destination.parent.mkdir(parents=True, exist_ok=True)
    translate_options = gdal.TranslateOptions(
        format="AAIGrid",
        noData=config.destination_nodata,
    )
    output = gdal.Translate(str(destination), str(source), options=translate_options)
    if output is None:
        raise RuntimeError(f"GDAL Translate failed for {source}")
    output = None


def _resample_many(paths: list[Path], config: PipelineConfig, result: PipelineResult) -> list[Path]:
    outputs = []
    for source in paths:
        destination = build_output_path(
            source,
            config.resampled_dir,
            "_resampled",
            ".tif",
        )
        result.operations.append(PlannedOperation("resample", source, destination))
        _maybe_run(source, destination, config, result, resample_raster)
        outputs.append(destination)
    return outputs


def _clip_many(paths: list[Path], config: PipelineConfig, result: PipelineResult) -> list[Path]:
    outputs = []
    for source in paths:
        destination = build_output_path(
            source,
            config.clipped_dir,
            "_clipped",
            ".tif",
        )
        result.operations.append(PlannedOperation("clip", source, destination))
        _maybe_run(source, destination, config, result, clip_raster)
        outputs.append(destination)
    return outputs


def _ascii_many(paths: list[Path], config: PipelineConfig, result: PipelineResult) -> list[Path]:
    outputs = []
    for source in paths:
        destination = build_output_path(source, config.ascii_dir, "", ".asc")
        result.operations.append(PlannedOperation("ascii", source, destination))
        _maybe_run(source, destination, config, result, raster_to_ascii)
        outputs.append(destination)
    return outputs


def _maybe_run(source: Path, destination: Path, config: PipelineConfig, result: PipelineResult, func) -> None:
    if destination.exists() and not config.overwrite:
        result.skipped_files.append(destination)
        return
    if config.dry_run:
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    func(source, destination, config)
    result.created_files.append(destination)


def _run_warp(gdal, source: Path, destination: Path, options: dict) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    warp_options = gdal.WarpOptions(**options)
    output = gdal.Warp(str(destination), str(source), options=warp_options)
    if output is None:
        raise RuntimeError(f"GDAL Warp failed for {source}")
    output = None


def _import_gdal():
    try:
        from osgeo import gdal
    except ImportError as exc:
        raise GdalUnavailable(
            "GDAL is required for raster processing. Install system GDAL and "
            "the Python bindings, or try `python -m pip install -e .[gdal]`."
        ) from exc
    if hasattr(gdal, "UseExceptions"):
        gdal.UseExceptions()
    return gdal
