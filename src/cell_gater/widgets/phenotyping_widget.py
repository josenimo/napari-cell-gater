from __future__ import annotations

import sys
from itertools import product


import numpy as np
import pandas as pd
from dask_image.imread import imread
from loguru import logger
from matplotlib.backends.backend_qt5agg import (
    FigureCanvas,
)
from matplotlib.figure import Figure
from matplotlib.widgets import Slider
from napari import Viewer
from napari.layers import Image, Points
from napari.utils.history import (
    get_open_history,
)
from qtpy.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QWidget,
)

from cell_gater.model.data_model import DataModel
from cell_gater.utils.misc import napari_notification

logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss.SS}</green> | <level>{level}</level> | {message}")

class PhenotypingWidget(QWidget):
    """Widget for a scatter plot with markers on the x axis and any dtype column on the y axis."""

    def __init__(self, model: DataModel, viewer: Viewer) -> None:
        super().__init__()

        self.setLayout(QGridLayout())
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)

        self._model = model
        self._viewer = viewer

        self._current_sample = None
        self._image = None
        self._mask = None

        # 1. Dropdown for selecting the sample
        selection_label = QLabel("Select sample:")
        self.sample_selection_dropdown = QComboBox()
        self.sample_selection_dropdown.addItems(sorted(self.model.samples, key=self.natural_sort_key))
        self.sample_selection_dropdown.currentTextChanged.connect(self._on_sample_changed)

        # 2. Button for loading the gates dataframe
        self.load_gates_button = QPushButton("Load existing gates")
        self.load_gates_button.clicked.connect(self.load_gates_dataframe)

        # 3. Button for loading processed quantification dataframe
        self.load_quantification_button = QPushButton("Load quantification")
        self.load_quantification_button.clicked.connect(self.load_quantification_dataframe)

        # 4. Button for loading the scimap phenotyping dataframe
        self.load_phenotyping_button = QPushButton("Load phenotyping")
        self.load_phenotyping_button.clicked.connect(self.load_phenotyping_dataframe)

        # self.layout().addWidget(object, int row, int column, int rowSpan = 1, int columnSpan = 1)
        self.layout().addWidget(selection_label, 0, 0)
        self.layout().addWidget(self.sample_selection_dropdown, 0, 1)

        # we have to do this because initially the dropdowns did not change texts yet so these variables are still None.
        self.model.active_sample = self.sample_selection_dropdown.currentText()
        self._read_marker_image()
        self._read_mask_image()
        self._load_labels()
        self._load_image()
        self.load_ref_channel()

        # Initialize gates dataframe
        sample_marker_combinations = list(product(self.model.regionprops_df["sample_id"].unique(), self.model.markers_image_indices.keys()))
        self.model.gates = pd.DataFrame(sample_marker_combinations, columns=["sample_id", "marker_id"])
        self.model.gates["gate_value"] = float(0)

        # plot points button
        plot_points_button = QPushButton("Plot Points")
        plot_points_button.clicked.connect(self.plot_points)
        self.layout().addWidget(plot_points_button, 6,0,1,1)

    #################################################################
    ########################### FUNCTIONS ###########################
    #################################################################

    def load_quantification_dataframe(self):
        """Load quantification dataframe from csv."""
        file_path, _ = self._file_dialog()
        if file_path:
            self.model.regionprops_df = pd.read_csv(file_path)

        logger.debug(f"Quantification dataframe from {file_path} loaded.")
        logger.debug(f"Shape: {self.model.regionprops_df.shape}")
        napari_notification(f"Quantification dataframe loaded from: {file_path}")

    def load_phenotyping_dataframe(self):
        """Load phenotyping dataframe from csv."""
        file_path, _ = self._file_dialog()
        if file_path:
            self.model.phenotyping_df = pd.read_csv(file_path)

        logger.debug(f"Phenotyping dataframe from {file_path} loaded.")
        logger.debug(f"Shape: {self.model.phenotyping_df.shape}")
        napari_notification(f"Phenotyping dataframe loaded from: {file_path}")


    ###################
    ### PLOT POINTS ###
    ###################

    # TODO dynamic plotting of points on top of created polygons

    def plot_points(self, ref_gate=False):
        """Plot positive cells in Napari."""
        df = self.model.regionprops_df
        df = df[df["sample_id"] == self.model.active_sample]

        for layer in self.viewer.layers:
            if isinstance(layer, Points):
                layer.visible = False

        logger.info("Plotting points in Napari.")
        logger.debug(f"sample: {self.model.active_sample}")
        logger.debug(f"marker: {self.model.active_marker}")
        logger.debug(f"current_gate: {self.model.current_gate}")

        if ref_gate:
            ref_gate_value = self.access_gate()
            self.viewer.add_points(
                df[df[self.model.active_marker] > ref_gate_value][["Y_centroid", "X_centroid"]],
                name=f"Gate: {round(ref_gate_value)} | {self.model.active_sample}:{self.model.active_marker}",
                face_color="yellow", edge_color="black", size=12, opacity=0.6)
        else:
            self.viewer.add_points(
                df[df[self.model.active_marker] > self.model.current_gate][["Y_centroid", "X_centroid"]],
                name=f"Gate: {round(self.model.current_gate)} | {self.model.active_sample}:{self.model.active_marker}",
                face_color="yellow", edge_color="black", size=12, opacity=0.6)

    ####################################
    ### GATES DATAFRAME INPUT OUTPUT ###
    ####################################

    def load_gates_dataframe(self):
        """Load gates dataframe from csv."""
        file_path, _ = self._file_dialog()
        if file_path:
            self.model.gates = pd.read_csv(file_path)

        self.model.gates["sample_id"] = self.model.gates["sample_id"].astype(str)
        assert "sample_id" in self.model.gates.columns, "sample_id column not found in gates dataframe."
        assert "marker_id" in self.model.gates.columns, "marker_id column not found in gates dataframe."
        assert "gate_value" in self.model.gates.columns, "gate_value column not found in gates dataframe."
        assert set(self.model.gates["sample_id"].unique()) == set(self.model.regionprops_df["sample_id"].unique()), "Samples do not match."
        assert set(self.model.gates["marker_id"].unique()) == set(self.model.markers_image_indices.keys()), "Markers don't match, pick the same quantification files."

        self.csv_path = file_path
        logger.debug(f"Gates dataframe from {file_path} loaded and checked.")
        logger.debug(f"self.access_gate(): {self.access_gate()}")
        self.scatter_canvas.fixed_vertical_line()
        self.plot_points(ref_gate=True)
        napari_notification(f"Gates dataframe loaded from: {file_path}")

    def select_save_directory(self):
        """Select the directory where the gates CSV file will be saved."""
        if self.csv_path:
            logger.debug(f"Save directory already selected: {self.csv_path}")
            napari_notification(f"Save directory already selected: {self.csv_path}")
        else:
            fileName, _ = QFileDialog.getSaveFileName(self, "Save gates in csv", "", "CSV Files (*.csv);;All Files (*)", options=QFileDialog.Options())
            if fileName:
                self.csv_path = fileName
                logger.debug(f"Save directory selected: {self.csv_path}")
                napari_notification(f"Save directory selected: {self.csv_path}")

    def save_gates_dataframe(self):
        """Save gates dataframe to csv."""
        if not self.csv_path:
            self.select_save_directory()

        if self.csv_path:
            self.model.gates.to_csv(self.csv_path, index=False)
            logger.debug(f"Gates dataframe saved to {self.csv_path}")
            napari_notification(f"File saved to: {self.csv_path}")

    def save_gate(self):
        """Save the current gate value to the gates dataframe."""
        if self.model.current_gate == 0:
            napari_notification("Gate not saved, please select a gate value.")
            return
        if self.access_gate() == self.model.current_gate:
            napari_notification("No changes detected.")
            return
        if self.access_gate() != self.model.current_gate:
            napari_notification(f"Old gate {round(self.access_gate(), 2)} overwritten to {round(self.model.current_gate, 2)}")

        self.model.gates.loc[
            (self.model.gates["sample_id"] == self.model.active_sample) &
            (self.model.gates["marker_id"] == self.model.active_marker),
            "gate_value"] = self.model.current_gate

        assert self.access_gate() == self.model.current_gate
        self.save_gates_dataframe()
        self.scatter_canvas.fixed_vertical_line()
        logger.debug(f"Gate saved: {self.model.current_gate}")

    def access_gate(self):
        """Access the current gate value."""
        assert self.model.active_sample is not None
        assert self.model.active_marker is not None
        gate_value = self.model.gates.loc[
            (self.model.gates["sample_id"] == self.model.active_sample) &
            (self.model.gates["marker_id"] == self.model.active_marker),
            "gate_value"].values[0]
        assert isinstance(gate_value, float)
        return gate_value

    ##########################
    ###### LOADING DATA ######
    ##########################

    def _read_marker_image(self):
        """Read the marker image for the selected marker."""
        image_path = self.model.sample_image_mapping[self.model.active_sample]
        self._image = imread(image_path)

    def _read_mask_image(self):
        """Read the mask image for the selected sample."""
        mask_path = self.model.sample_mask_mapping[self.model.active_sample]
        self._mask = imread(mask_path)

    def load_ref_channel(self):
        """Load the reference channel."""
        for layer in self.viewer.layers:
            if isinstance(layer, Image) and "REF:" in layer.name:
                self.viewer.layers.remove(layer)
        self.viewer.add_image(
            self._image[self.model.markers_image_indices[self.model.active_ref_marker]],
            name="REF:" + self.model.active_ref_marker + "_" + self.model.active_sample,
            blending="additive", visible=True, colormap="magenta")

    def _load_labels(self):
        """Load the labels into the napari viewer."""
        self.viewer.add_labels(self._mask, name="mask_" + self.model.active_sample, visible=False, opacity=0.4)

    def _load_image(self):
        """Load the image into the napari viewer."""
        marker_index = self.model.markers_image_indices[self.model.active_marker]
        self.viewer.add_image(self._image[marker_index], name=self.model.active_marker + "_" + self.model.active_sample, blending="additive", colormap="green")

    def _on_sample_changed(self):
        """Set active sample, load mask, image, and ref."""
        self.model.active_sample = self.sample_selection_dropdown.currentText()
        self._clear_layers()
        self._read_marker_image()
        self._read_mask_image()
        self.load_ref_channel()
        self._load_labels()
        self._load_image()
        self.update_plot()
        self.update_slider()
        if self.access_gate() > 0.0:
            self.scatter_canvas.fixed_vertical_line()
            self.plot_points(ref_gate=True)

    def _on_marker_changed(self):
        """Set active marker, load only new marker image."""
        self.model.active_marker = self.marker_selection_dropdown.currentText()
        for layer in list(self.viewer.layers):
            if isinstance(layer, Image) and "REF:" not in layer.name:  # noqa: SIM114
                self.viewer.layers.remove(layer)
            elif isinstance(layer, Points):
                self.viewer.layers.remove(layer)
        self._read_marker_image()
        self._load_image()
        self.update_plot()
        self.update_slider()
        if self.access_gate() > 0.0:
            self.scatter_canvas.fixed_vertical_line()
            self.plot_points(ref_gate=True)

    def _clear_layers(self) -> None:
        """Remove all layers upon changing sample."""
        self.viewer.layers.select_all()
        self.viewer.layers.remove_selected()

    def _on_y_axis_changed(self):
        """Set active y-axis and update the scatter plot."""
        self.model.active_y_axis = self.choose_y_axis_dropdown.currentText()
        self.update_plot()

    def _file_dialog(self):
        """Open dialog for a user to select a file."""
        dlg = QFileDialog()
        hist = get_open_history()
        dlg.setHistory(hist)
        options = QFileDialog.Options()
        return dlg.getOpenFileName(
            self,
            "Select file",
            hist[0],
            "CSV Files (*.csv)",
            options=options,
        )

    def natural_sort_key(self, s):
        """Key function for natural sorting."""
        import re
        return [int(text) if text.isdigit() else text.lower() for text in re.split(r"(\d+)", s)]

    @property
    def model(self) -> DataModel:
        """The dataclass model that stores information required for cell_gating."""
        return self._model
    @model.setter
    def model(self, model: DataModel) -> None:
        self._model = model

    @property
    def viewer(self) -> Viewer:
        """The napari Viewer."""
        return self._viewer
    @viewer.setter
    def viewer(self, viewer: Viewer) -> None:
        self._viewer = viewer