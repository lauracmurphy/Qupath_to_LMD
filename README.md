# QuPath to Leica LMD Converter (Tube Cap Edition)

This is a modified version of the [Qupath_to_LMD](https://github.com/CosciaLab/Qupath_to_LMD) tool, tailored specifically for workflows that utilise tube collectors instead of standard well plates. It was created in the IGC AIR.

This streamlist link for this modified version is [here](https://igc-qupath-to-lmd.streamlit.app/)

## What This Does
This application takes `.geojson` polygon annotations generated in QuPath and converts them into the `.xml` format required by the Leica LMD7 microscope software for automated laser microdissection. 

**Custom Feature:** The original version of this app strictly maps samples to 96-well or 384-well plate grids. This modified fork adds native support for **Tube Cap Collectors** (e.g., 0.5ml, 1.5ml, and 8-strip tubes). It maps samples directly to Caps A, B, C, D, and E to match the Leica LMD software's expected tube targets.

## How to Use
1. **Upload:** Drop your `.geojson` file (exported from QuPath) into Step 1. Ensure it contains at least 3 calibration points.
2. **Select Target:** In Step 2, select **Tubes** as your collection method and specify the number of caps available.
3. **Map & Process:** Assign your QuPath sample classes to the corresponding caps, and click **Process files** in Step 3.
4. **Download:** You will receive a `.zip` file containing the `.xml` file for the microscope, a tracking `.csv`, and a Quality Control image.

## Attribution and License
This project is a modified fork of the original [Qupath_to_LMD](https://github.com/CosciaLab/Qupath_to_LMD) repository, originally developed by the **CosciaLab** as part of the openDVP framework. 

All credit for the core conversion engine (via `py-lmd`), the spatial data processing, and the foundation of the Streamlit UI goes to the original authors. 

In accordance with the original licensing, this modified version remains open-source and is distributed under the **GNU General Public License v3.0 (GPL-3.0)**. Please see the `LICENSE` file for full terms and conditions.
