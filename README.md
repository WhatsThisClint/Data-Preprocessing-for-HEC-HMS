# Data Preprocessing for HEC-HMS Input

This repository contains a Jupyter notebook script that automates the preprocessing of a large dataset of TIFF files for use in the HEC-RMS (Hydrologic Engineering Center's River Analysis System) software.

## Overview

The script performs the following tasks:

1. **Resampling TIFF files**: The script iterates through all TIFF files in the `input_folder` directory and resamples them to a desired pixel size (in this case, 0.0001). The resampled TIFF files are saved in the `output_folder` directory with a "_resampled" suffix.

2. **Extracting data using a shapefile**: The script then iterates through the resampled TIFF files in the `output_folder` directory and extracts the data using a specified shapefile (`shapefile_path`). The extracted data is saved in the `extracted` folder with an "_extracted" suffix.

3. **Converting TIFF to ASCII**: Finally, the script converts the extracted TIFF files in the `extracted` folder to the ASCII format and saves them in the `ascii` folder with a ".asc" extension.

This preprocessing step is essential for preparing the data to be used as input for the HEC-RMS software, which requires the data to be in a specific format. By automating these tasks, the script helps to streamline the data preparation process and ensures that the input data is properly formatted for use in HEC-RMS.

## Usage

1. Ensure you have the following dependencies installed:
   - Python
   - GDAL (Geospatial Data Abstraction Library)

2. Update the following variables in the script to match your specific setup:
   - `input_folder`: The directory containing the TIFF files to be processed.
   - `output_folder`: The directory where the resampled TIFF files will be saved.
   - `shapefile_path`: The file path to the shapefile used for data extraction.

3. Run the Jupyter notebook script to execute the data preprocessing steps.

## Compatibility

This script has been tested and verified to work with HEC-RMS. While the core preprocessing logic should be transferable to HEC-RAS as well, you may need to make some adjustments to accommodate any differences in data format requirements between the two systems.

## Contribution

If you have any suggestions, improvements, or bug fixes, feel free to submit a pull request. I'm always happy to collaborate and enhance the functionality of this script.

## License

This project is licensed under the [MIT License](LICENSE).
