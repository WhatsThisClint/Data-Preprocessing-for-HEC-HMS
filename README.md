# Data Preprocessing for HEC-HMS

This repository prepares gridded raster inputs for HEC-HMS workflows. The original notebook is preserved, and the processing logic has been moved into a reusable Python package and CLI.

The pipeline follows the original workflow:

1. Resample TIFF rasters to a target pixel size.
2. Clip rasters to a basin/catchment shapefile.
3. Export clipped rasters to Arc/Info ASCII Grid (`.asc`) files.

## Install

The package can be installed without GDAL for planning, testing, and dry runs:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

For real raster processing, install GDAL and its Python bindings. Depending on your system, this may be easiest through Conda/OSGeo4W, or:

```powershell
python -m pip install -e .[gdal]
```

## Usage

Preview a processing plan without running GDAL:

```powershell
hec-hms-preprocess `
  --input-dir .\rasters `
  --shapefile .\boundary\basin.shp `
  --work-dir .\outputs `
  --dry-run
```

Run the full pipeline:

```powershell
hec-hms-preprocess `
  --input-dir .\rasters `
  --shapefile .\boundary\basin.shp `
  --work-dir .\outputs `
  --pixel-size 0.0001 `
  --destination-nodata -9999
```

Useful options:

- `--target-srs EPSG:4326`: reproject outputs while resampling.
- `--resample-algorithm near`: use nearest-neighbor for categorical grids.
- `--skip-resample`: clip source TIFFs directly.
- `--skip-clip`: convert source or resampled TIFFs without a boundary mask.
- `--skip-ascii`: stop after GeoTIFF outputs.
- `--overwrite`: replace existing outputs.
- `--json`: print a machine-readable operation plan.

## Output Layout

By default, outputs are written under `outputs/`:

```text
outputs/
  resampled/
  clipped/
  ascii/
```

Generated outputs are ignored by Git.

## Development

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests
python -m compileall src tests
```

The tests use dry-run plans and do not require GDAL.

## Notes

- Confirm that raster and shapefile coordinate reference systems match, or pass `--target-srs`.
- Use `near` resampling for land-use or class rasters; use `bilinear` or `cubic` for continuous grids such as precipitation or elevation.
- The original notebook filename mentions `HEC-RMS`; it is retained as provenance, but the package and docs now target HEC-HMS preprocessing.

## DOI

https://doi.org/10.5281/zenodo.10959672
