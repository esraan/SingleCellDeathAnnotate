import pytest
import napari
import numpy as np
from single_cell_death_annotate._widget import (
    DeathEventTab,
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
