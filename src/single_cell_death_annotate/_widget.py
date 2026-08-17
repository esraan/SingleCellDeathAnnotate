import os
import sys
import importlib
import types
from pathlib import Path

import napari
import numpy as np
import pandas as pd
from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QInputDialog, QFileDialog, QTabWidget, QLineEdit
)

def _load_image_file_dialog(parent_widget, viewer):
    file_path, _ = QFileDialog.getOpenFileName(
        parent_widget,
        "Select Image File",
        "",
        "Image Files (*.tif *.tiff *.png *.jpg *.jpeg *.nd2)"
    )
    if not file_path:
        return

    ext = os.path.splitext(file_path)[1].lower()
    
    if ext != ".nd2":
        viewer.open(file_path)
        print(f"Loaded image {file_path}")
        return

    try:
        import nd2
    except ImportError:
        print("ND2 detected but the 'nd2' package is not installed. Install with: pip install nd2")
        return

    with nd2.ND2File(file_path) as f:
        data = f.to_dask() if hasattr(f, "to_dask") else f.asarray()
        axes = getattr(f, "axes", None)
        try:
            channel_names = [c.name for c in getattr(f, "channels", [])] or None
        except Exception:
            channel_names = None

    if axes is not None:
        axes_list = list(axes)
        desired = [a for a in ["T", "Z", "C", "Y", "X"] if a in axes_list]
        perm = [axes_list.index(a) for a in desired]
        data = data.transpose(perm)
        channel_axis = desired.index("C") if "C" in desired else None
    else:
        channel_axis = None

    if channel_axis is not None:
        viewer.add_image(
            data,
            name=os.path.basename(file_path),
            channel_axis=channel_axis,
            rgb=False,
            metadata={"source": "nd2", "path": file_path, "channel_names": channel_names},
        )
    else:
        viewer.add_image(
            data,
            name=os.path.basename(file_path),
            metadata={"source": "nd2", "path": file_path},
        )
    print(f"Loaded ND2 image {file_path}")


# ----------------------------------------------------
# TAB 1: Segmentation & Tracking
# ----------------------------------------------------
class SegmentationTrackingTab(QWidget):
    def __init__(self, viewer: napari.Viewer):
        super().__init__()
        self.viewer = viewer
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel("<b>Manual Segmentation & Tracking</b>"))
        
        btn_load_img = QPushButton("Load Image (TIFF/ND2)")
        btn_load_img.clicked.connect(lambda: _load_image_file_dialog(self, self.viewer))
        layout.addWidget(btn_load_img)
        
        btn_add_labels = QPushButton("Add Labels Layer (Masks)")
        btn_add_labels.clicked.connect(self._add_labels_layer)
        layout.addWidget(btn_add_labels)
        
        btn_save_npy = QPushButton("Save Masks to .npy")
        btn_save_npy.clicked.connect(self._save_masks_npy)
        layout.addWidget(btn_save_npy)
        
        btn_load_npy = QPushButton("Load Masks from .npy")
        btn_load_npy.clicked.connect(self._load_masks_npy)
        layout.addWidget(btn_load_npy)
        
        btn_load_btrack = QPushButton("Load btrack Widget")
        btn_load_btrack.clicked.connect(self._load_btrack)
        layout.addWidget(btn_load_btrack)
        
        btn_save_csv = QPushButton("Save Tracking to CSV")
        btn_save_csv.clicked.connect(self._save_tracking_csv)
        layout.addWidget(btn_save_csv)
        
        btn_load_csv = QPushButton("Load Tracking from CSV")
        btn_load_csv.clicked.connect(self._load_tracking_csv)
        layout.addWidget(btn_load_csv)
        
        # Delete Track UI
        layout.addWidget(QLabel("<b>Delete Specific Track</b>"))
        delete_layout = QHBoxLayout()
        self.track_id_input = QLineEdit()
        self.track_id_input.setPlaceholderText("Enter Track ID to delete")
        btn_delete_track = QPushButton("Delete Track")
        btn_delete_track.clicked.connect(self._delete_track)
        delete_layout.addWidget(self.track_id_input)
        delete_layout.addWidget(btn_delete_track)
        layout.addLayout(delete_layout)
        
        layout.addStretch()
        self.setLayout(layout)

    def _add_labels_layer(self):
        shape = None
        for layer in self.viewer.layers:
            if isinstance(layer, napari.layers.Image):
                shape = layer.data.shape
                break
        
        if shape is None:
            print("No image layer found to infer shape.")
            return

        self.viewer.add_labels(np.zeros(shape, dtype=int), name='Masks')
        print("Added empty Labels layer.")

    def _save_masks_npy(self):
        layer = self.viewer.layers.selection.active
        if not isinstance(layer, napari.layers.Labels):
            print("Please select a Labels layer to save.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Save Masks", "", "Numpy Arrays (*.npy)")
        if file_path:
            np.save(file_path, layer.data)
            print(f"Masks saved to {file_path}")

    def _load_masks_npy(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Masks", "", "Numpy Arrays (*.npy)")
        if file_path:
            data = np.load(file_path)
            self.viewer.add_labels(data, name=os.path.basename(file_path))
            print(f"Loaded masks from {file_path}")

    def _load_btrack(self) -> None:
        """Try to dock the btrack widget. If btrack is unavailable or broken,
        fall back to napari-laptrack (another cell-tracking plugin).
        """
        # ---- Attempt 1: btrack ----
        try:
            import pydantic as _p2
            try:
                _p1 = importlib.import_module('pydantic.v1')
            except ImportError:
                _p1 = _p2

            _proxy = types.ModuleType('pydantic')
            for _k in dir(_p1):
                try:
                    setattr(_proxy, _k, getattr(_p1, _k))
                except Exception:
                    pass

            for _m in list(sys.modules):
                if _m == 'btrack' or _m.startswith('btrack.'):
                    sys.modules.pop(_m, None)

            sys.modules['pydantic'] = _proxy
            try:
                _mod = importlib.import_module('btrack.napari.main')
                w = _mod.create_btrack_widget()
                self.viewer.window.add_dock_widget(w, area='right', name='btrack')
                print("✅ btrack widget loaded successfully.")
                return
            finally:
                sys.modules['pydantic'] = _p2

        except Exception as e:
            print(f"⚠️  btrack failed to load: {e}")

        # ---- Attempt 2: napari-laptrack ----
        try:
            from napari_laptrack import LapTrackWidget  # type: ignore
            w = LapTrackWidget(self.viewer)
            self.viewer.window.add_dock_widget(w, area='right', name='napari-laptrack')
            print("✅ napari-laptrack widget loaded as btrack alternative.")
            return
        except ImportError:
            pass
        except Exception as e:
            print(f"⚠️  napari-laptrack failed: {e}")

        # ---- Both unavailable ----
        print(
            "\n❌ No tracking plugin could be loaded.\n"
            "Install one of the following inside your conda environment:\n\n"
            "Option A — btrack:\n"
            "    pip install btrack\n\n"
            "Option B — napari-laptrack (recommended, simpler):\n"
            "    pip install napari-laptrack\n\n"
            "Then restart napari and try again.\n"
        )

    def _save_tracking_csv(self):
        layer = self.viewer.layers.selection.active
        if getattr(layer, '_type_string', '') != 'tracks':
            layer = next((ly for ly in self.viewer.layers if getattr(ly, '_type_string', '') == 'tracks'), None)
        
        if layer is None:
            print("No Tracks layer selected/found.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Tracking Data", 
            "", 
            "CSV Files (*.csv);;All Files (*)"
        )
        if not file_path:
            return
            
        if not file_path.lower().endswith('.csv'):
            file_path += '.csv'
            
        data = np.asarray(layer.data)
        cols = ['track_id', 't', 'y', 'x'] if data.shape[1] == 4 else ['track_id','t','z','y','x']
        df = pd.DataFrame(data, columns=cols)
        
        # 1. Merge Features (napari features are row-aligned with data)
        features = getattr(layer, "features", None)
        if features is not None and not features.empty:
            feat_df = pd.DataFrame(features).reset_index(drop=True)
            # Avoid duplicate columns if features already include track_id or t
            cols_to_drop = [c for c in feat_df.columns if c in df.columns]
            feat_df = feat_df.drop(columns=cols_to_drop)
            df = pd.concat([df, feat_df], axis=1)
            
        # 2. Merge Graph (map child track_id -> parent track_id)
        graph = getattr(layer, "graph", None)
        if graph is not None and len(graph):
            parent_map = {}
            for child, parents in graph.items():
                if isinstance(parents, (list, tuple)):
                    parent_map[child] = parents[0] if len(parents) > 0 else None
                else:
                    parent_map[child] = parents
            
            # Map the parent_id to every row belonging to the child track
            df['parent_track_id'] = df['track_id'].map(parent_map)
            # Convert NaN to pandas NA or leave as float, but Int64 allows NaN with integers
            df['parent_track_id'] = df['parent_track_id'].astype('Int64')

        df.to_csv(file_path, index=True, index_label='')
        print(f"Saved merged tracking data to: {file_path}")

    def _delete_track(self):
        track_id_str = self.track_id_input.text().strip()
        if not track_id_str:
            return
        
        try:
            track_id = int(float(track_id_str))
        except ValueError:
            print("Track ID must be a number.")
            return

        layer = self.viewer.layers.selection.active
        if getattr(layer, '_type_string', '') != 'tracks':
            layer = next((ly for ly in self.viewer.layers if getattr(ly, '_type_string', '') == 'tracks'), None)
            
        if layer is None:
            print("No Tracks layer selected/found.")
            return

        data = layer.data
        if data is None or len(data) == 0:
            print("Tracks layer is empty.")
            return

        mask = data[:, 0] != track_id
        if mask.sum() == len(data):
            print(f"Track ID {track_id} not found.")
            return
            
        new_data = data[mask]
        
        features = getattr(layer, "features", None)
        if features is not None and not features.empty:
            new_features = features.iloc[mask].reset_index(drop=True)
        else:
            new_features = None
            
        graph = getattr(layer, "graph", None)
        new_graph = {}
        if graph is not None:
            for child, parents in graph.items():
                if child == track_id:
                    continue
                if isinstance(parents, (list, tuple)):
                    new_parents = [p for p in parents if p != track_id]
                    if new_parents:
                        new_graph[child] = new_parents
                else:
                    if parents != track_id:
                        new_graph[child] = parents
                        
        name = layer.name
        kwargs = {
            "name": name,
            "features": new_features,
            "graph": new_graph,
            "tail_width": getattr(layer, "tail_width", 2),
            "tail_length": getattr(layer, "tail_length", 30),
            "head_length": getattr(layer, "head_length", 30),
            "color_by": getattr(layer, "color_by", "track_id"),
            "colormap": getattr(layer, "colormap", "turbo"),
            "blending": getattr(layer, "blending", "additive"),
            "visible": getattr(layer, "visible", True),
        }
        self.viewer.layers.remove(layer)
        self.viewer.add_tracks(new_data, **kwargs)

        print(f"Track ID {track_id} deleted successfully.")
        self.track_id_input.clear()

    def _load_tracking_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Tracking Data",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        if not file_path:
            return

        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            print(f"Failed to read CSV: {e}")
            return

        # Determine coordinate columns (5D or 4D)
        coord_cols_5 = ['track_id', 't', 'z', 'y', 'x']
        coord_cols_4 = ['track_id', 't', 'y', 'x']

        if all(c in df.columns for c in coord_cols_5):
            coord_cols = coord_cols_5
        elif all(c in df.columns for c in coord_cols_4):
            coord_cols = coord_cols_4
        else:
            print("CSV missing required columns: 'track_id', 't', 'y', 'x'.")
            return

        data = df[coord_cols].values

        # Reconstruct lineage graph from parent_track_id column
        graph = {}
        if 'parent_track_id' in df.columns:
            df_parents = df.dropna(subset=['parent_track_id'])
            if not df_parents.empty:
                parent_map = df_parents.groupby('track_id')['parent_track_id'].first().to_dict()
                graph = {int(child): [int(parent)] for child, parent in parent_map.items()}

        # Filter graph: remove edges where child or any parent is not a known track_id
        # (can happen after track stitching which renumbers track IDs)
        valid_ids = set(df['track_id'].astype(float).unique())
        graph = {
            child: parents
            for child, parents in graph.items()
            if child in valid_ids and all(p in valid_ids for p in parents)
        }

        # Everything else becomes features
        skip_cols = set(coord_cols) | {'parent_track_id', 'index'}
        feature_cols = [c for c in df.columns if c not in skip_cols]
        features = df[feature_cols].reset_index(drop=True) if feature_cols else None

        self.viewer.add_tracks(
            data,
            features=features,
            graph=graph,
            name=os.path.basename(file_path)
        )
        print(f"Loaded tracks from {file_path}")

# ----------------------------------------------------
# TAB 2: Death Time Annotation
# ----------------------------------------------------
class DeathEventTab(QWidget):
    def __init__(self, viewer: napari.Viewer):
        super().__init__()
        self.viewer = viewer

        self.event_type_mapping = {
            'Apoptosis': 1,
            'Necrosis':  2,
            'Mixed':     3,
            'Alive':     4,
            'Other':     5
        }
        self.annotations = []
        self.cell_id_map = {}
        self.next_cell_id = 1
        self._syncing_points_data = False
        self._points_data_snapshot = np.empty((0, self.viewer.dims.ndim))
        self._changing_annotation_tool = False

        # --- FIX 1: use a flag instead of napari 'add' mode.
        # This means we never let napari auto-add a phantom point — we add
        # the point manually ONLY after the user confirms the dialog.
        self._drawing_active = False

        layout = QVBoxLayout()
        layout.addWidget(QLabel("<b>Death Event Annotator</b>"))

        btn_load_img = QPushButton("Load Image (TIFF/ND2)")
        btn_load_img.clicked.connect(lambda: _load_image_file_dialog(self, self.viewer))
        layout.addWidget(btn_load_img)

        # Toggle button: stores reference so we can update its label
        self._btn_enable = QPushButton("🟢 Enable Annotation Mode")
        self._btn_enable.setToolTip(
            "Toggle annotation mode.\n"
            "While ON, every left-click opens the event-type dialog.\n"
            "Choose napari's Points select tool to leave annotation mode."
        )
        self._btn_enable.clicked.connect(self._toggle_drawing)
        layout.addWidget(self._btn_enable)

        lbl_info = QLabel(
            "<i>Enable annotation mode then click on a cell. "
            "A dialog asks for the event type. "
            "Choose the Points select tool when you want to select/delete.</i>"
        )
        lbl_info.setWordWrap(True)
        layout.addWidget(lbl_info)

        # --- FIX 2: explicit Delete button (more reliable than key bindings).
        # Capture selected_data BEFORE napari's own Delete handler can fire.
        btn_delete = QPushButton("🗑  Delete Selected Annotation(s)")
        btn_delete.setToolTip(
            "Select one or more red points in 'death_events', then click here.\n"
            "The annotation AND all corresponding persistent markers at every "
            "time-point are removed."
        )
        btn_delete.clicked.connect(self._delete_selected)
        layout.addWidget(btn_delete)

        btn_save = QPushButton("Save Annotations")
        btn_save.clicked.connect(self._save_annotations)
        layout.addWidget(btn_save)

        btn_save_decoded = QPushButton("Save Decoded Annotations")
        btn_save_decoded.clicked.connect(self._save_decoded_annotations)
        layout.addWidget(btn_save_decoded)

        btn_load = QPushButton("Load Annotations")
        btn_load.clicked.connect(self._load_annotations)
        layout.addWidget(btn_load)

        layout.addStretch()
        self.setLayout(layout)

        # Hook mouse release via napari's public callback API (napari >= 0.5)
        # Falls back to the vispy canvas for older versions
        try:
            self.viewer.mouse_release_callbacks.append(self._on_mouse_release)
        except AttributeError:
            canvas = self.viewer.window.qt_viewer.canvas  # type: ignore[attr-defined]
            canvas.events.mouse_release.connect(self._on_mouse_release)

        self._ensure_points_layers(self.viewer.dims.ndim)
        self.viewer.layers.selection.events.active.connect(self._on_active_layer_changed)

    def _ensure_points_layers(self, target_ndim: int) -> None:
        recreate = False
        if getattr(self, 'points', None) not in self.viewer.layers:
            recreate = True
        elif self.points.ndim != target_ndim:
            recreate = True
        if getattr(self, 'persistent_points', None) not in self.viewer.layers:
            recreate = True
        elif self.persistent_points.ndim != target_ndim:
            recreate = True

        if not recreate:
            return

        if getattr(self, 'points', None) in self.viewer.layers:
            self.viewer.layers.remove(self.points)
        if getattr(self, 'persistent_points', None) in self.viewer.layers:
            self.viewer.layers.remove(self.persistent_points)

        self.persistent_points = self.viewer.add_points(
            data=np.empty((0, target_ndim)),
            size=20,
            face_color='blue',
            name='death_events_persistent',
        )
        self.points = self.viewer.add_points(
            data=np.empty((0, target_ndim)),
            size=20,
            face_color='red',
            name='death_events',
        )
        # Always keep in 'select' mode — we manage all point-adding ourselves.
        self.points.mode = 'select'
        self.persistent_points.mode = 'select'
        self.points.events.data.connect(self._on_points_data_changed)
        self.points.events.mode.connect(self._on_points_mode_changed)
        self._points_data_snapshot = np.asarray(self.points.data).copy()

    def _set_points_data(self, data: np.ndarray, text) -> None:
        """Update the editable red layer without treating it as a user edit."""
        self._syncing_points_data = True
        try:
            self.points.data = data
            self.points.text = text
            self._points_data_snapshot = np.asarray(self.points.data).copy()
        finally:
            self._syncing_points_data = False

    def _on_points_data_changed(self, event=None) -> None:
        """Synchronize deletions made with napari's native Points controls."""
        if self._syncing_points_data or not hasattr(self, 'points'):
            return

        current = np.asarray(self.points.data).copy()
        previous = np.asarray(self._points_data_snapshot)

        # A native delete removes rows while preserving the order of the rows
        # that remain. Other native point edits are not part of this workflow.
        if len(current) >= len(previous):
            self._points_data_snapshot = current
            return

        kept_old_indices = []
        new_idx = 0
        for old_idx, old_coord in enumerate(previous):
            if new_idx < len(current) and np.array_equal(old_coord, current[new_idx]):
                kept_old_indices.append(old_idx)
                new_idx += 1

        if new_idx != len(current) or len(previous) != len(self.annotations):
            # Restore the authoritative plugin data if an unsupported edit or
            # an unexpected external mutation made row matching ambiguous.
            self._rebuild_red_layer()
            print("Could not identify the deleted annotation; the red layer was restored.")
            return

        self.annotations = [self.annotations[i] for i in kept_old_indices]
        self._prune_cell_id_map()
        self._points_data_snapshot = current
        self._refresh_red_text()
        self._update_persistent_layer()
        print(f"Deleted {len(previous) - len(current)} annotation(s) with napari's Points delete control.")

    def _prune_cell_id_map(self) -> None:
        remaining_keys = {tuple(np.asarray(ann[0]).astype(int)[1:]) for ann in self.annotations}
        for key in list(self.cell_id_map):
            if key not in remaining_keys:
                del self.cell_id_map[key]

    def _refresh_red_text(self) -> None:
        self._syncing_points_data = True
        try:
            self.points.text = {
                'string': [str(ann[3]) for ann in self.annotations],
                'color': 'yellow',
                'size': 20,
                'anchor': 'center',
            } if self.annotations else []
        finally:
            self._syncing_points_data = False

    def _rebuild_red_layer(self) -> None:
        ndim = len(self.annotations[0][0]) if self.annotations else self.viewer.dims.ndim
        coords = (np.stack([ann[0] for ann in self.annotations], axis=0)
                  if self.annotations else np.empty((0, ndim)))
        text = ({
            'string': [str(ann[3]) for ann in self.annotations],
            'color': 'yellow',
            'size': 20,
            'anchor': 'center',
        } if self.annotations else [])
        self._set_points_data(coords, text)

    def _set_drawing_active(self, active: bool, select_tool: bool = False) -> None:
        self._drawing_active = active
        self._changing_annotation_tool = True
        try:
            if active:
                self.viewer.layers.selection.active = self.points
                # pan_zoom does not add points itself; our callback adds only
                # after the event dialog is confirmed. Selecting napari's
                # Points select tool changes this mode and disables annotation.
                self.points.mode = 'pan_zoom'
                self._btn_enable.setText("🔴 Annotation Mode Active")
            else:
                if select_tool and self.points in self.viewer.layers:
                    self.viewer.layers.selection.active = self.points
                    self.points.mode = 'select'
                self._btn_enable.setText("🟢 Enable Annotation Mode")
        finally:
            self._changing_annotation_tool = False

    def _toggle_drawing(self):
        self._set_drawing_active(
            not self._drawing_active,
            select_tool=self._drawing_active,
        )

    def _on_points_mode_changed(self, event=None) -> None:
        if self._changing_annotation_tool or not self._drawing_active:
            return
        if self.points.mode != 'pan_zoom':
            self._set_drawing_active(False)
            print("Annotation mode disabled because a napari Points tool was selected.")

    def _on_active_layer_changed(self, event=None) -> None:
        if self._changing_annotation_tool or not self._drawing_active:
            return
        if self.viewer.layers.selection.active is not self.points:
            self._set_drawing_active(False)
            print("Annotation mode disabled because another layer was selected.")

    def _delete_selected(self):
        if not hasattr(self, 'points'): return
        self._delete_by_indices(self.points, self.points.selected_data, delete_mode='row')

    def _on_mouse_release(self, event) -> None:
        """Intercept clicks when drawing mode is active.

        We check self._drawing_active (set by the toggle button) rather than
        the layer mode, so napari is NEVER in 'add' mode and can never slip
        a phantom point into the layer before the dialog is shown.
        """
        if not self._drawing_active:
            return

        # Normalise event signature: napari>=0.5 passes (event,) with a
        # .position attribute; vispy passes a MouseEvent with .button/type.
        button = getattr(event, 'button', None)
        ev_type = getattr(event, 'type', None)
        if button != 1:
            return
        if ev_type is not None and ev_type != 'mouse_release':
            # vispy event that is not a release
            return

        if getattr(self, 'points', None) is None or self.points not in self.viewer.layers:
            return

        world_pos = np.array(self.viewer.cursor.position, dtype=float)
        ndim = self.viewer.dims.ndim
        disp = self.viewer.dims.displayed
        full = np.zeros(ndim, dtype=float)

        for ax in disp:
            full[ax] = world_pos[ax]
        for ax in set(range(ndim)) - set(disp):
            full[ax] = self.viewer.dims.current_step[ax]

        pixel = np.round(full).astype(int)

        try:
            event.handled = True
        except AttributeError:
            pass

        self._ensure_points_layers(len(pixel))
        # _add_annotation shows dialog; if user cancels, no point is added.
        self._add_annotation(pixel)

    def _add_annotation(self, pixel: np.ndarray) -> None:
        choices = list(self.event_type_mapping.keys())
        choice, ok = QInputDialog.getItem(
            self,
            'Select Death Event Type',
            'Event type:',
            choices,
            current=0,
            editable=False
        )
        if not ok:
            return

        code = self.event_type_mapping[choice]
        frame_idx = int(self.viewer.dims.current_step[0]) if self.viewer.dims.ndim > 2 else 0

        coord_key = tuple(pixel[1:])
        if coord_key not in self.cell_id_map:
            self.cell_id_map[coord_key] = self.next_cell_id
            self.next_cell_id += 1
        cell_id = self.cell_id_map[coord_key]

        self.annotations.append((pixel.copy(), frame_idx, code, cell_id))

        coords = np.stack([ann[0] for ann in self.annotations], axis=0)
        self._rebuild_red_layer()

        self._update_persistent_layer()
        print(f"Annotated {choice} (code={code}) at {pixel} on frame {frame_idx} (cell id={cell_id})")

    def _delete_by_indices(self, layer, selected_indices, delete_mode: str = 'row') -> None:
        """Remove annotations matching *selected_indices* and sync both layers.

        delete_mode='row'  → match by exact full coordinate (red-layer delete)
        delete_mode='cell' → match by spatial coord only, all frames (blue-layer delete)
        """
        # Snapshot selected coords NOW, before any napari state changes.
        if not selected_indices:
            print("No selection to delete.")
            return
        if not self.annotations:
            print("No annotations to delete.")
            return

        to_remove_idx: set[int] = set()

        if delete_mode == 'row':
            # Match by full coordinate tuple (t, y, x[, z])
            layer_data = np.asarray(layer.data)
            sel_coords = {tuple(layer_data[i].astype(int)) for i in selected_indices}
            for i, (pix, *_rest) in enumerate(self.annotations):
                if tuple(np.asarray(pix).astype(int)) in sel_coords:
                    to_remove_idx.add(i)
        else:
            # Match by spatial coord only (ignore time axis 0)
            layer_data = np.asarray(layer.data)
            sel_spatial = {tuple(layer_data[i].astype(int)[1:]) for i in selected_indices}
            for i, (pix, *_rest) in enumerate(self.annotations):
                if tuple(np.asarray(pix).astype(int)[1:]) in sel_spatial:
                    to_remove_idx.add(i)

        if not to_remove_idx:
            print("No matching annotations found for current selection.")
            return

        # Remove in reverse order to keep indices valid.
        for idx in sorted(to_remove_idx, reverse=True):
            self.annotations.pop(idx)

        # Prune cell_id_map.
        self._prune_cell_id_map()

        # Explicitly rebuild the RED layer.
        if self.annotations:
            ndim = len(self.annotations[0][0])
            self._ensure_points_layers(ndim)
            self._rebuild_red_layer()
        else:
            self._rebuild_red_layer()

        # Rebuild the BLUE persistent layer (removes all time-point markers
        # for the deleted cell automatically).
        self._update_persistent_layer()
        self.points.selected_data = set()
        self.persistent_points.selected_data = set()

    def _update_persistent_layer(self):
        if not self.annotations:
            self.persistent_points.data = np.empty((0, self.viewer.dims.ndim))
            self.persistent_points.text = []
            return

        target_ndim = len(self.annotations[0][0])
        self._ensure_points_layers(target_ndim)

        earliest = {}
        for (pixel, frame_idx, code, cell_id) in self.annotations:
            coord_key = tuple(pixel[1:])
            if coord_key not in earliest or frame_idx < earliest[coord_key][1]:
                earliest[coord_key] = (pixel, frame_idx, code, cell_id)

        persistent_coords = []
        persistent_ids = []
        max_frame = int(self.viewer.dims.range[0][1]) if self.viewer.dims.ndim > 1 else 0

        for (pixel, frame_idx, code, cell_id) in earliest.values():
            start_t = int(frame_idx)
            end_t = max_frame
            for t in range(start_t, end_t + 1):
                coord = np.array(pixel, dtype=int).copy()
                coord[0] = t
                persistent_coords.append(coord)
                persistent_ids.append(cell_id)

        if persistent_coords:
            persistent_coords = np.stack(persistent_coords, axis=0)
            self.persistent_points.data = persistent_coords
            self.persistent_points.text = {
                'string': [str(i) for i in persistent_ids],
                'color': 'yellow',
                'size': 20,
                'anchor': 'center',
            }
        else:
            self.persistent_points.data = np.empty((0, target_ndim))
            self.persistent_points.text = []

    def _load_annotations(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Annotations", "", "CSV Files (*.csv)")
        if not file_path:
            return

        df = pd.read_csv(file_path)
        if not {'x', 'y', 'death_time', 'event_type'}.issubset(df.columns) and not {'x', 'y', 'death_time', 'event_code'}.issubset(df.columns):
            print("Invalid CSV format. Required columns missing.")
            return

        self.annotations = []
        self.cell_id_map = {}
        self.next_cell_id = 1

        for _, row in df.iterrows():
            pixel = [row['death_time'], row['y'], row['x']]
            if 'z' in df.columns:
                pixel.append(row['z'])
            coord_key = tuple(pixel[1:])
            if coord_key not in self.cell_id_map:
                if 'cell_id' in row:
                    self.cell_id_map[coord_key] = int(row['cell_id'])
                    self.next_cell_id = max(self.next_cell_id, int(row['cell_id']) + 1)
                else:
                    self.cell_id_map[coord_key] = self.next_cell_id
                    self.next_cell_id += 1
            cell_id = self.cell_id_map[coord_key]
            
            code = int(row['event_code']) if 'event_code' in row else int(row['event_type'])
            self.annotations.append((np.array(pixel, dtype=int), int(row['death_time']), code, cell_id))

        if self.annotations:
            target_ndim = len(self.annotations[0][0])
            self._ensure_points_layers(target_ndim)
            self._rebuild_red_layer()
            self._update_persistent_layer()
            
        print(f"Loaded annotations from {file_path}")

    def _save_annotations(self):
        if not self.annotations:
            print("No annotations to save.")
            return

        coords = np.stack([ann[0] for ann in self.annotations], axis=0)
        frames = [ann[1] for ann in self.annotations]
        codes = [ann[2] for ann in self.annotations]
        cell_ids = [ann[3] for ann in self.annotations]

        disp = self.viewer.dims.displayed
        x_vals = coords[:, disp[-1]]
        y_vals = coords[:, disp[-2]]

        data = {
            'cell_id': cell_ids,
            'event_code': codes,
            'death_time': frames,
            'x': x_vals,
            'y': y_vals,
        }
        all_axes = set(range(coords.shape[1]))
        z_axes = list(all_axes - set(disp))
        if z_axes and coords.shape[1] > 3:
            data['z'] = coords[:, z_axes[0]]
        else:
            data['z'] = np.zeros(coords.shape[0])

        cols = ['cell_id', 'event_code', 'death_time', 'x', 'y'] + (['z'] if 'z' in data else [])
        df = pd.DataFrame(data, columns=cols)
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Annotations",
            "",
            "CSV Files (*.csv)"
        )
        if file_path:
            df.to_csv(file_path, index=False)
            print(f"Saved annotations → {file_path}")
        else:
            print("Save cancelled.")

    def _save_decoded_annotations(self):
        if not self.annotations:
            print("No annotations to save.")
            return

        coords = np.stack([ann[0] for ann in self.annotations], axis=0)
        frames = [ann[1] for ann in self.annotations]
        codes = [ann[2] for ann in self.annotations]
        cell_ids = [ann[3] for ann in self.annotations]
        reverse_map = {v: k for k, v in self.event_type_mapping.items()}
        labels = [reverse_map.get(c, 'Unknown') for c in codes]

        disp = self.viewer.dims.displayed
        x = coords[:, disp[-1]]
        y = coords[:, disp[-2]]

        data_decoded = {
            'cell_id': cell_ids,
            'event_code': codes,
            'event_type': labels,
            'death_time': frames,
            'x': x,
            'y': y,
        }
        all_axes = set(range(coords.shape[1]))
        z_axes = list(all_axes - set(disp))
        if z_axes and coords.shape[1] > 3:
            data_decoded['z'] = coords[:, z_axes[0]]
        else:
            data_decoded['z'] = np.zeros(coords.shape[0])

        cols_decoded = ['cell_id', 'event_code', 'event_type', 'death_time', 'x', 'y'] + (['z'] if 'z' in data_decoded else [])
        df_decoded = pd.DataFrame(data_decoded, columns=cols_decoded)
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Annotations",
            "",
            "CSV Files (*.csv)"
        )
        if file_path:
            df_decoded.to_csv(file_path, index=False)
            print(f"Saved annotations → {file_path}")
        else:
            print("Save cancelled.")

# ----------------------------------------------------
# MAIN PLUGIN WIDGET
# ----------------------------------------------------
class SingleCellDeathAnnotateWidget(QWidget):
    def __init__(self, napari_viewer: napari.Viewer):
        super().__init__()
        self.viewer = napari_viewer
        
        layout = QVBoxLayout()
        
        self.tabs = QTabWidget()
        
        self.tab_segmentation = SegmentationTrackingTab(self.viewer)
        self.tab_death = DeathEventTab(self.viewer)
        
        self.tabs.addTab(self.tab_segmentation, "Segmentation & Tracking")
        self.tabs.addTab(self.tab_death, "Death Events")
        
        layout.addWidget(self.tabs)
        self.setLayout(layout)
