# SingleCellDeathAnnotate

A [napari] plugin combining:
- **Manual cell segmentation** — draw masks, save/load `.npy`, launch btrack, export tracking CSVs
- **Death-event annotation** — click on cells to record death time and event type, export to CSV

---

## Requirements

| Software | Version |
|---|---|
| Python | **3.12** |
| napari | ≥ 0.5.0 |
| PyQt6 | Current conda-forge version |
| NumPy | ≥ 1.26 |
| Pandas | ≥ 2.1 |
| nd2 | ≥ 0.9 |
| btrack | ≥ 0.6 |
| pydantic | ≥ 2.0 |

---

## Installation on another laptop

The plugin is currently a local Python package (it is not published on PyPI), so
the other laptop must first receive either the whole source repository or the
standalone `SingleCellDeathAnnotate` directory. Do not copy an already-created conda
environment between computers; create a fresh environment on each laptop.

### Step 0 — Install prerequisites and copy the code

1. Install [Miniconda](https://docs.conda.io/projects/miniconda/en/latest/) or
   Anaconda on the destination laptop.
2. Obtain the code using one of these methods:
   - clone the source Git repository with Git;
   - copy the repository using a USB drive or shared drive; or
   - copy only `code/annotate/SingleCellDeathAnnotate`.
3. Open **Anaconda Prompt** on Windows, or a terminal on macOS/Linux.

In the commands below, replace `/path/to/project` with the actual location of
the copied or cloned repository. On Windows, a path might look like
`C:\Users\LabUser\Project`.

### Step 1 — Create the conda environment

> **Always use a dedicated environment.** Do **not** install into `base`.

```bash
# Navigate to the copied/cloned repository
cd /path/to/project

# Create the environment (this installs Python 3.12, napari, nd2, btrack, etc.)
conda env create -f code/annotate/SingleCellDeathAnnotate/environment.yml

# Activate it
conda activate single-cell-death-annotate
```

> ⚠️ If you already created the env before and it failed, remove it first:
> ```bash
> conda env remove -n single-cell-death-annotate
> conda env create -f code/annotate/SingleCellDeathAnnotate/environment.yml
> conda activate single-cell-death-annotate
> ```

### Step 2 — Install the plugin

The plugin is a **local** package — it does not exist on PyPI, so it must be installed manually after the environment is ready:

```bash
cd /path/to/project/code/annotate/SingleCellDeathAnnotate
python -m pip install -e .
```

`-e` means editable installation: changes made in this plugin directory become
available after restarting napari. Developers who also need the test tools can
instead run `python -m pip install -e ".[testing]"`.

If only the standalone plugin directory was copied, enter that directory and
run the same `python -m pip install -e .` command. The `environment.yml` file is
inside that directory, so create the environment from there with:

```bash
conda env create -f environment.yml
conda activate single-cell-death-annotate
python -m pip install -e .
```

### Step 3 — Verify the plugin is registered

```bash
python -m pip show single-cell-death-annotate
napari
```

In napari, open **Plugins ▸ SingleCellDeathAnnotate**. If that menu entry is
present and the two-tab widget opens, installation is complete.

### Updating or reinstalling on another laptop

After replacing or updating the source directory, activate the environment and
re-run the installation command, then restart napari:

```bash
conda activate single-cell-death-annotate
cd /path/to/project/code/annotate/SingleCellDeathAnnotate
python -m pip install -e .
napari
```

To perform a clean reinstall of only the plugin package:

```bash
conda activate single-cell-death-annotate
python -m pip uninstall single-cell-death-annotate
cd /path/to/project/code/annotate/SingleCellDeathAnnotate
python -m pip install -e .
```

---

## How to Run the Plugin (Step by Step)

> **One-time setup:** complete Installation steps 1–2 first.

### Every time you want to use the plugin:

**Step 1 — Activate the environment**
```bash
conda activate single-cell-death-annotate
```

**Step 2 — Launch napari**
```bash
napari
```

**Step 3 — Open the plugin widget**

In the napari menu bar:
```
Plugins  ▸  SingleCellDeathAnnotate
```
The plugin dock widget will appear on the right side of the napari window with two tabs.

**Step 4 — Load your image (in either tab)**

Click **"Load Image (TIFF/ND2)"** → a file dialog opens → select your `.tif`, `.tiff`, or `.nd2` file → the image loads into the viewer.

**Step 5a — Segmentation & Tracking tab**

1. Click **"Add Labels Layer (Masks)"** to create an empty drawing canvas.
2. Select the Labels layer in the layer list and use napari's built-in **paintbrush** (press `2`) to draw cell masks.
3. Click **"Save Masks to .npy"** to save your masks.
4. *(Optional)* Click **"Load btrack Widget"** to dock the btrack tracking UI and run automated tracking.
5. After tracking, click **"Save Tracking to CSV"** and choose a CSV filename.
   Track coordinates, available features, and `parent_track_id` lineage data
   are combined into that one CSV file.

**Step 5b — Death Events tab**

1. Click **"Enable Annotation Mode"**. The plugin activates the red Points
   layer and safely handles clicks without letting napari add phantom points.
2. **Click directly on any cell** in the image — a popup will appear asking you to choose the event type:
   - Apoptosis / Necrosis / Mixed / Alive / Other
3. The annotation is stored and a blue persistent marker appears from that frame onward.
4. Repeat for every cell death event in your movie.
5. Click **"Save Decoded Annotations"** to export a CSV with readable event type labels.

**Deleting a mistaken death-event annotation**

1. In napari's toolbar, choose the Points **select tool** (arrow icon; usually
   shortcut `1`). This automatically disables annotation mode, so no separate
   **Disable** click is required.
2. In napari's layer list, keep the red **`death_events`** layer selected (not the blue
   `death_events_persistent` layer).
3. Make sure the Points **select tool** (arrow icon; usually shortcut `1`) is
   active.
4. Click the red point. A selected point normally appears with a highlighted
   outline. For multiple points, drag a selection box around them.
5. Press `Delete`/`Backspace`, click napari's Points-layer delete button, or
   click **Delete Selected Annotation(s)** in the SingleCellDeathAnnotate widget.
6. Save the annotations CSV again if it had already been exported; deleting a
   point in napari does not modify a CSV file previously saved to disk.

The red point is the actual annotation. The blue points are generated display
markers that persist from the annotated death frame onward. Deleting the red
annotation through either napari's native delete action or the plugin button
updates the internal annotation list and automatically removes its corresponding
persistent markers.

---

## Usage

### Tab 1 — Segmentation & Tracking

| Button | Action |
|---|---|
| **Load Image (TIFF/ND2)** | Opens a file dialog to load `.tif`, `.tiff`, or `.nd2` files |
| **Add Labels Layer (Masks)** | Adds an empty Labels layer matching the Image shape |
| **Save Masks to .npy** | Saves the active Labels layer to a `.npy` file |
| **Load Masks from .npy** | Loads a `.npy` array and adds it as a Labels layer |
| **Load btrack Widget** | Docks the btrack tracking widget on the right |
| **Save Tracking to CSV** | Exports track coordinates, features, and lineage information into one CSV file |
| **Load Tracking from CSV** | Loads a tracking CSV previously exported by the plugin |
| **Delete Track** | Removes every row belonging to the Track ID entered in the adjacent field |

### Tab 2 — Death Events

| Button | Action |
|---|---|
| **Load Image (TIFF/ND2)** | Same as above |
| **Enable Annotation Mode** | Lets the plugin intercept image clicks and open the event dialog |
| **Click on the image** | A popup dialog asks for the event type (Apoptosis / Necrosis / Mixed / Alive / Other) |
| **Save Annotations** | Saves `cell_id`, `event_code`, `death_time`, `x`, `y` to a CSV |
| **Save Decoded Annotations** | Same but with human-readable `event_type` labels |
| **Load Annotations** | Re-loads a previously saved CSV |

#### Deleting annotations

- Choose the Points select tool to disable annotation mode automatically, keep
  the red **`death_events`** layer selected, and select one or more red points.
  Use napari's Points delete button, press
  `Delete`/`Backspace`, or click **Delete Selected Annotation(s)**.
- Blue **`death_events_persistent`** points are derived markers; do not delete
  them directly. They are removed automatically when their red source
  annotation is deleted.

---

## Running tests

```bash
conda activate single-cell-death-annotate
cd code/annotate/SingleCellDeathAnnotate
pytest tests/ -v
```

---

## GitHub — publishing

1. Copy the `SingleCellDeathAnnotate/` folder to its own repository.
2. Push to GitHub.
3. Users can then install directly with:

```bash
python -m pip install git+https://github.com/<your-org>/SingleCellDeathAnnotate.git
```

---

## Troubleshooting

| Error | Fix |
|---|---|
| `ModuleNotFoundError: napari` | Make sure you activated the correct conda env (`conda activate single-cell-death-annotate`) |
| `TypeError: add_points() got an unexpected keyword argument` | Your napari version is older than expected. Run `pip install -U napari` |
| `nd2` import error | Run `pip install nd2` inside the activated environment |
| Plugin not visible in napari | Activate `single-cell-death-annotate`, run `python -m pip install -e .` from the plugin directory, and fully restart napari |
| Delete button says `No selection to delete` | Disable drawing, select the red `death_events` layer, activate the Points select tool, then select the red point before clicking the button |
| A deleted point reappears | Confirm that the red `death_events` layer—not the generated blue layer—was selected, then update/reinstall the plugin and restart napari |

---

[napari]: https://napari.org
