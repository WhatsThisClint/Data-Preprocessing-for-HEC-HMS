# HEC-HMS Raster Preprocessing Workflow

The pipeline prepares gridded raster data for HEC-HMS by running three repeatable stages.

## 1. Resample

Input TIFF rasters are resampled to a target pixel size using GDAL Warp. The default pixel size matches the original notebook: `0.0001`.

## 2. Clip

Resampled rasters are clipped to a basin or catchment boundary shapefile. The output is cropped to the cutline and receives a consistent NoData value.

## 3. Export ASCII Grid

Clipped rasters are translated to Arc/Info ASCII Grid (`.asc`) files using GDAL Translate. This format is commonly accepted by HEC tools for gridded inputs.

## Recommended Checks

- Confirm the raster CRS and shapefile CRS match, or pass `--target-srs`.
- Use `--dry-run` first to verify filenames and output folders.
- Keep generated `outputs/` out of Git.
- Spot-check a few output grids in QGIS before importing into HEC-HMS.
