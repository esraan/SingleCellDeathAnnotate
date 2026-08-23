import pytest
import napari
import numpy as np
import pandas as pd
from single_cell_death_annotate._widget import (
    DeathEventTab,
    QFileDialog,
    SegmentationTrackingTab,
    SingleCellDeathAnnotateWidget,
)

def test_widget_creation(make_napari_viewer):
    viewer = make_napari_viewer()
    widget = SingleCellDeathAnnotateWidget(viewer)
    assert widget is not None
    assert widget.tabs.count() == 2
    assert isinstance(widget.tabs.widget(0), SegmentationTrackingTab)
    assert isinstance(widget.tabs.widget(1), DeathEventTab)

def test_segmentation_add_labels(make_napari_viewer):
    viewer = make_napari_viewer()
    viewer.add_image(np.random.random((10, 10)), name='image')
    
    tab = SegmentationTrackingTab(viewer)
    tab._add_labels_layer()
    
    labels_layers = [lay for lay in viewer.layers if isinstance(lay, napari.layers.Labels)]
    assert len(labels_layers) == 1
    assert labels_layers[0].name == 'Masks'
    assert labels_layers[0].data.shape == (10, 10)

def test_death_event_enable_drawing(make_napari_viewer):
    viewer = make_napari_viewer()
    tab = DeathEventTab(viewer)
    
    assert 'death_events_persistent' in viewer.layers
    assert 'death_events' in viewer.layers
    
    tab._toggle_drawing()
    assert tab._drawing_active is True
    assert viewer.layers.selection.active is tab.points
    assert viewer.layers['death_events'].mode == 'pan_zoom'


def test_select_tool_disables_annotation_mode(make_napari_viewer):
    viewer = make_napari_viewer()
    tab = DeathEventTab(viewer)

    tab._toggle_drawing()
    tab.points.mode = 'select'

    assert tab._drawing_active is False
    assert "Enable Annotation Mode" in tab._btn_enable.text()


def test_add_points_tool_enables_annotation_mode_and_syncs_button(
    make_napari_viewer,
):
    viewer = make_napari_viewer()
    tab = DeathEventTab(viewer)

    tab.points.mode = 'add'

    assert tab._drawing_active is True
    assert viewer.layers.selection.active is tab.points
    assert tab.points.mode == 'pan_zoom'
    assert "Annotation Mode Active" in tab._btn_enable.text()

    # The plugin button controls the same state after tool activation.
    tab._toggle_drawing()
    assert tab._drawing_active is False
    assert tab.points.mode == 'select'
    assert "Enable Annotation Mode" in tab._btn_enable.text()

    # Activating again with the button and choosing another tool also stays
    # synchronized in the opposite direction.
    tab._toggle_drawing()
    tab.points.mode = 'select'
    assert tab._drawing_active is False
    assert "Enable Annotation Mode" in tab._btn_enable.text()


def test_changing_layer_disables_annotation_mode(make_napari_viewer):
    viewer = make_napari_viewer()
    image = viewer.add_image(np.zeros((10, 10)), name='image')
    tab = DeathEventTab(viewer)

    tab._toggle_drawing()
    viewer.layers.selection.active = image

    assert tab._drawing_active is False


def _seed_death_annotations(tab):
    tab.annotations = [
        (np.array([1, 10, 20]), 1, 1, 1),
        (np.array([3, 30, 40]), 3, 2, 2),
    ]
    tab.cell_id_map = {(10, 20): 1, (30, 40): 2}
    tab.next_cell_id = 3
    tab._rebuild_red_layer()
    tab._update_persistent_layer()


def test_native_points_delete_synchronizes_annotations(make_napari_viewer):
    viewer = make_napari_viewer()
    viewer.add_image(np.zeros((5, 64, 64)), name='image')
    tab = DeathEventTab(viewer)
    _seed_death_annotations(tab)

    tab.points.selected_data = {0}
    tab.points.remove_selected()

    assert len(tab.points.data) == 1
    assert len(tab.annotations) == 1
    assert tab.annotations[0][3] == 2
    assert (10, 20) not in tab.cell_id_map
    persistent_spatial = {tuple(row) for row in np.asarray(tab.persistent_points.data)[:, 1:]}
    assert persistent_spatial == {(30, 40)}


def test_plugin_delete_button_still_synchronizes_annotations(make_napari_viewer):
    viewer = make_napari_viewer()
    viewer.add_image(np.zeros((5, 64, 64)), name='image')
    tab = DeathEventTab(viewer)
    _seed_death_annotations(tab)

    tab.points.selected_data = {1}
    tab._delete_selected()

    assert len(tab.points.data) == 1
    assert len(tab.annotations) == 1
    assert tab.annotations[0][3] == 1
    assert (30, 40) not in tab.cell_id_map


def test_load_annotations_overlays_legacy_csv_and_can_continue(
    make_napari_viewer, monkeypatch, tmp_path
):
    """A legacy zero-filled z column must not turn 3D points into 4D."""
    viewer = make_napari_viewer()
    viewer.add_image(np.zeros((5, 64, 64)), name='image')
    tab = DeathEventTab(viewer)
    csv_path = tmp_path / 'annotations.csv'
    pd.DataFrame({
        'cell_id': [7, 8],
        'event_code': [1, 2],
        'death_time': [1, 3],
        'x': [20, 40],
        'y': [10, 30],
        'z': [0, 0],
    }).to_csv(csv_path, index=False)
    monkeypatch.setattr(
        QFileDialog, 'getOpenFileName', lambda *args, **kwargs: (str(csv_path), '')
    )

    tab._load_annotations()

    np.testing.assert_array_equal(
        np.asarray(tab.points.data),
        np.array([[1, 10, 20], [3, 30, 40]]),
    )
    assert tab.points.ndim == 3
    assert tab.next_cell_id == 9
    assert viewer.layers.selection.active is tab.points

    # A newly added annotation continues after the restored cell IDs.
    monkeypatch.setattr(
        'single_cell_death_annotate._widget.QInputDialog.getItem',
        lambda *args, **kwargs: ('Alive', True),
    )
    tab._add_annotation(np.array([4, 50, 51]))
    assert tab.annotations[-1][3] == 9
    assert len(tab.points.data) == 3


def test_load_annotations_uses_napari_4d_axis_order(
    make_napari_viewer, monkeypatch, tmp_path
):
    viewer = make_napari_viewer()
    viewer.add_image(np.zeros((5, 3, 64, 64)), name='image')
    tab = DeathEventTab(viewer)
    csv_path = tmp_path / 'annotations_4d.csv'
    pd.DataFrame({
        'cell_id': [1],
        'event_type': ['  aPoPtOsIs  '],
        'death_time': [2],
        'x': [20],
        'y': [10],
        'z': [1],
    }).to_csv(csv_path, index=False)
    monkeypatch.setattr(
        QFileDialog, 'getOpenFileName', lambda *args, **kwargs: (str(csv_path), '')
    )

    tab._load_annotations()

    np.testing.assert_array_equal(np.asarray(tab.points.data), [[2, 1, 10, 20]])
    assert tab.annotations[0][2] == 1


def test_load_annotations_uses_channel_zero_as_background(
    make_napari_viewer, monkeypatch, tmp_path
):
    viewer = make_napari_viewer()
    shared = {'source': 'nd2', 'path': 'movie.nd2', 'channel_count': 2}
    channel_zero = viewer.add_image(
        np.zeros((5, 64, 64)),
        name='channel 0',
        metadata={**shared, 'channel_index': 0},
        scale=(2, 0.5, 0.5),
    )
    channel_one = viewer.add_image(
        np.ones((5, 64, 64)),
        name='channel 1',
        metadata={**shared, 'channel_index': 1},
    )
    tab = DeathEventTab(viewer)
    csv_path = tmp_path / 'annotations_channels.csv'
    pd.DataFrame({
        'cell_id': [1],
        'event_type': ['NECROSIS'],
        'death_time': [2],
        'x': [20],
        'y': [10],
    }).to_csv(csv_path, index=False)
    monkeypatch.setattr(
        QFileDialog, 'getOpenFileName', lambda *args, **kwargs: (str(csv_path), '')
    )

    tab._load_annotations()

    assert channel_zero.visible is True
    assert channel_one.visible is False
    np.testing.assert_array_equal(np.asarray(tab.points.data), [[2, 10, 20]])
    np.testing.assert_array_equal(tab.points.scale, channel_zero.scale)
    assert tab.annotations[0][2] == 2
