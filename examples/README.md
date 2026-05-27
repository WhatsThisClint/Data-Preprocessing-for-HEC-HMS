# Example

This repository does not include large raster inputs. To run the pipeline, place TIFF grids in a folder and provide a basin/catchment shapefile.

```powershell
hec-hms-preprocess `
  --input-dir .\rasters `
  --shapefile .\boundary\basin.shp `
  --work-dir .\outputs `
  --pixel-size 0.0001
```

Preview the plan without requiring GDAL:

```powershell
hec-hms-preprocess --input-dir .\rasters --shapefile .\boundary\basin.shp --dry-run
```
