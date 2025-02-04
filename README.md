# napari-cell-gater

[![License BSD-3](https://img.shields.io/pypi/l/napari-cell-gater.svg?color=green)](https://github.com/melonora/napari-cell-gater/raw/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/napari-cell-gater.svg?color=green)](https://pypi.org/project/napari-cell-gater)
[![Python Version](https://img.shields.io/pypi/pyversions/napari-cell-gater.svg?color=green)](https://python.org)
[![tests](https://github.com/melonora/napari-cell-gater/workflows/tests/badge.svg)](https://github.com/melonora/napari-cell-gater/actions)
[![codecov](https://codecov.io/gh/melonora/napari-cell-gater/branch/main/graph/badge.svg)](https://codecov.io/gh/melonora/napari-cell-gater)
[![napari hub](https://img.shields.io/endpoint?url=https://api.napari-hub.org/shields/napari-cell-gater)](https://napari-hub.org/plugins/napari-cell-gater)

A plugin to perform cell marker gating for multiplexed immunofluorescent imaging

![Screenshot 2024-06-17 at 19 34 17](https://github.com/melonora/napari-cell-gater/assets/30318135/f469c380-ef53-42d6-a136-ebcae723e987)

----------------------------------

# Installation

### Step 1. 
Install napari (see https://napari.org/stable/tutorials/fundamentals/installation)

### Step 2.
Install `napari-cell-gater` via [pip]:

    pip install git+https://github.com/josenimo/napari-cell-gater.git

# How to use
## Step 0: Open plugin
- Open napari by executing `napari` in the command line
- Open plugin with name `load_sample_data (Multiplex imaging cell gating)`
- Menu should be displayed on napari user interface

## Step 1: Stage files
Users will select the necesary directories: images, masks, and quantification directories.
### Assumptions for inputs:  
- Files are inside directories, single files are not supported.
- The naming of files must match, for example the image for sample 1, should be "1.ome.tif" or "1.tif"; the mask file "1.tif"; and the quantification file "1.csv".  
- All images, masks, and quantification files should be inside their respective folders.
- Any extra files in those folders can make code fail.  

### Example 1: Staging for single files.
![Screenshot 2025-02-04 at 12 53 43](https://github.com/user-attachments/assets/2afaab0a-0159-46a8-a71e-81aefdcb136f)

### Example 2: Staging for many files.
![Screenshot 2025-02-04 at 13 05 34](https://github.com/user-attachments/assets/dce335e0-c288-424a-ad2b-809edaba72d3)

## Step 2: Select directories in napari plugin
![Screenshot 2025-02-04 at 13 07 36](https://github.com/user-attachments/assets/531700de-6e09-4aaf-93b2-3695ba5611cc)

- Click `Load quantifications dir` and select in the popup the folder with quantification matrices
- Click `Load image dir` and select in the popup the folder with images
- Click `Load mask dir` and select in the popup the folder with segmentation masks
- Optional `Load channel map` can be used to define specific channels, its usage is explain later.

## Step 3: Select lowerbound and upperbound channels

- The two dropdown menus will show all measured features (acquired from the column names from the quantification matrices).
- The `lowerbound` defines the first feature to threshold, and the `upperbound` the last feature to threshold. Theoretically, you could choose all features. I suggest you pick the ones you need for phenotyping.
- If you plan to save gates file, and reload the file in another instance, you must pick the same lowerbound and upperbound features.
- The `Remove markers with prefix (default: DNA,DAPI)` field will let you ignore any channel with any prefix provided, for many prefixes you must separate with a comma `,`. 

## Step 4: Validate and proceed to sample and marker selection

- Press `Validate input` button, it will check files to ensure concordance between files.
- Assumptions are:
- Quantification matrix should have the same number of rows as the maximum segmentation CellID
- Segmentation mask and multiplexed image should have the same x,y dimensions

## Step 5: Sample and marker selection

4. Select a sample, and a marker from dropdown menus. 3 layers will load:   
        (a.) the reference channel (default: first channel, changeable by dropdown menu)   
        (b.) the segmentation mask (for large images this might be a problem)  
        (c.) the channel_to_be_gated  
A scatter plot (default: x-axis=channel_to_be_gated intensity, y-axis=Area) (y-axis can be changed by dropdown)      
Underneath the scatterplot a slider will appear, the position of the slider will show up as a vertical line in the scatter plot.
The scatter plot can also be changed to a hexbin plot, which really helps with dense clusters of cells.
Plotting the data in log10 space is also possible by dropdown. Most of the times it helps. Gates would still be saved in linear space.

6. Adjust the contrast with the Napari layer menu (top left)
7. Drag the slider to what they think is correct
8. Click "Plot Points" to plot points on top of positive cells.
9. Repeat steps 5 and 6 until satisfied.
10. Click "Save Gate" to save the gate for the current marker and sample. Go to step 4 and repeat.

## Contributing

Contributions are very welcome. Tests can be run with [tox], please ensure
the coverage at least stays the same before you submit a pull request.

## License

Distributed under the terms of the [BSD-3] license,
"napari-cell-gater" is free and open source software

## Issues

If you encounter any problems, please [file an issue] along with a detailed description.

[napari]: https://github.com/napari/napari
[Cookiecutter]: https://github.com/audreyr/cookiecutter
[@napari]: https://github.com/napari
[MIT]: http://opensource.org/licenses/MIT
[BSD-3]: http://opensource.org/licenses/BSD-3-Clause
[GNU GPL v3.0]: http://www.gnu.org/licenses/gpl-3.0.txt
[GNU LGPL v3.0]: http://www.gnu.org/licenses/lgpl-3.0.txt
[Apache Software License 2.0]: http://www.apache.org/licenses/LICENSE-2.0
[Mozilla Public License 2.0]: https://www.mozilla.org/media/MPL/2.0/index.txt
[cookiecutter-napari-plugin]: https://github.com/napari/cookiecutter-napari-plugin

[napari]: https://github.com/napari/napari
[tox]: https://tox.readthedocs.io/en/latest/
[pip]: https://pypi.org/project/pip/
[PyPI]: https://pypi.org/
