# SingleCellDeathAnnotate: Installation and User Instructions

The installation has several steps, so please be patient. 🙂  
Instructions are provided for both Windows and macOS.

> **Important:** The plugin is now installed as a local napari plugin. You do **not** need a `run.py` file.

## A. Install Anaconda

1. Go to the [Anaconda download page](https://www.anaconda.com/download/success).
2. Download the installer for your operating system. The website usually detects it automatically.
3. Open the downloaded installer.

### Windows

1. Continue through the installer screens.
2. Choose **Just Me** unless the computer administrator has told you otherwise.
3. Keep the suggested installation folder. The username shown in the path should be your Windows username.
4. Keep the recommended/default options selected.
5. Click **Install**, wait for installation to finish, and then click **Finish**.

### macOS

1. Launch the downloaded installer package.
2. Continue through the introduction and licence screens.
3. Choose the installation location you prefer. The default option is suitable for most users.
4. Click **Install** and enter your Mac password if requested.
5. When installation is complete, click **Finish**. You may move the installer to the Trash.

## B. Install SingleCellDeathAnnotate and its required packages

### 1. Obtain the plugin folder

Download or copy the complete `SingleCellDeathAnnotate` folder to your computer. Do not move or delete it after installation.

The folder must contain at least these files and folders:

- `environment.yml`
- `pyproject.toml`
- `src`

### 2. Open a command window

- **Windows:** Open the Start menu and search for **Anaconda Prompt**.
- **macOS:** Press `Command + Space`, search for **Terminal**, and open it.

### 3. Copy the plugin folder path

- **Windows:** Hold `Shift`, right-click the `SingleCellDeathAnnotate` folder, and select **Copy as path**.
- **macOS:** Hold `Option`, right-click the `SingleCellDeathAnnotate` folder, and select **Copy “SingleCellDeathAnnotate” as Pathname**.

### 4. Go to the plugin folder

In Anaconda Prompt or Terminal, type `cd`, add one space, paste the copied folder path, and press `Enter`.

Example:

```text
cd "C:\Users\YourName\Downloads\SingleCellDeathAnnotate"
```

### 5. Create the environment

Enter each command separately. Wait for a command to finish before entering the next one.

```text
conda env create -f environment.yml
```

This step can take several minutes. If you are asked whether to proceed, type `y` and press `Enter`.

Activate the new environment:

```text
conda activate single-cell-death-annotate
```

Install the local plugin:

```text
python -m pip install -e .
```

### 6. Start napari

```text
napari
```

In napari, select:

```text
Plugins > SingleCellDeathAnnotate
```

The plugin opens on the right side of the napari window. It has two tabs: **Segmentation & Tracking** and **Death Events**.

## C. Start the plugin on later occasions

Each time you want to use the plugin:

1. Open **Anaconda Prompt** on Windows or **Terminal** on macOS.
2. Enter:

   ```text
   conda activate single-cell-death-annotate
   ```

3. Enter:

   ```text
   napari
   ```

4. In napari, select **Plugins > SingleCellDeathAnnotate**.

## D. Use the plugin

### 1. Load an image

1. Open either plugin tab.
2. Click **Load Image (TIFF/ND2)**.
3. Select an image and click **Open**.

The file chooser supports `.tif`, `.tiff`, `.png`, `.jpg`, `.jpeg`, and `.nd2` images.

### 2. Understand the napari window

The main areas are:

1. **Viewer and toolbar:** display, pan, zoom, select, paint, and annotate.
2. **Layer list:** select a layer or click its eye icon to show/hide it.
3. **Layer controls:** options for the currently selected layer.
4. **SingleCellDeathAnnotate panel:** the plugin tools in two tabs.

Use napari's pan/zoom tool to move around the image and zoom in or out.

## E. Death-event annotation

1. Open the **Death Events** tab.
2. Click **Enable Annotation Mode**. The button changes to **Annotation Mode Active**.
3. Move to the frame where the cell dies. This frame is recorded automatically as `death_time`.
4. Click directly on the cell at the time of death.
5. In the popup, choose the event type:
   - Apoptosis
   - Necrosis
   - Mixed
   - Alive
   - Other
6. Click **OK**.

The annotation receives a unique cell number. A red point represents the original annotation, and blue markers keep that annotation visible from the death frame onward.

### Delete an incorrect annotation

1. Choose the Points **select** tool (arrow icon, usually shortcut `1`). This automatically leaves annotation mode.
2. In the layer list, select the red **death_events** layer. Do not select `death_events_persistent`.
3. Click the red point. To select several points, drag a selection box around them.
4. Click **Delete Selected Annotation(s)** in the plugin, press `Delete`/`Backspace`, or use napari's Points delete button.

The associated blue persistent markers are deleted automatically. If you already exported a CSV, save it again after making changes.

### Save annotations

Two save options are available:

- **Save Annotations:** saves the numeric event code.
- **Save Decoded Annotations:** saves both the numeric code and the readable event name. This is the recommended option for analysis in Excel.

Click the required button, choose the destination folder and filename, and click **Save**.

### Load previous annotations

Click **Load Annotations**, choose a CSV previously saved by the plugin, and click **Open**.

## F. Segmentation and tracking

1. Open the **Segmentation & Tracking** tab.
2. Load an image if one is not already open.
3. Click **Add Labels Layer (Masks)**.
4. Select the new Labels layer and use napari's paintbrush (shortcut `2`) to draw cell masks.
5. Click **Save Masks to .npy** to save the masks.

You can also:

- use **Load Masks from .npy** to reopen saved masks;
- use **Load btrack Widget** to open the tracking interface;
- use **Save Tracking to CSV** to export tracking data;
- use **Load Tracking from CSV** to reopen tracking data; and
- enter a Track ID and click **Delete Track** to remove that complete track.

## G. Save a screenshot

When annotation is complete, use napari's screenshot option from its **File** menu, choose the destination and filename, and save the image.

## H. Open the annotation CSV in Excel

The decoded annotation file contains one row per annotation and normally includes:

| Column | Meaning |
|---|---|
| `cell_id` | Unique cell number |
| `event_code` | Numeric event code |
| `event_type` | Readable event name |
| `death_time` | Frame at which the event was annotated |
| `x`, `y` | Click coordinates |
| `z` | Z coordinate, or `0` for a 2D image |

Open the `.csv` file in Excel. If you edit it in Excel, preserve the column names so the plugin can load it again.

## I. Troubleshooting

- **`conda` is not recognized:** use **Anaconda Prompt** on Windows. On macOS, close and reopen Terminal after installing Anaconda.
- **The plugin is missing from the Plugins menu:** activate `single-cell-death-annotate`, return to the plugin folder, run `python -m pip install -e .`, and restart napari.
- **`ModuleNotFoundError: napari`:** the correct environment is not active. Run `conda activate single-cell-death-annotate`.
- **The environment already exists but is damaged:** remove and recreate it:

  ```text
  conda env remove -n single-cell-death-annotate
  conda env create -f environment.yml
  conda activate single-cell-death-annotate
  python -m pip install -e .
  ```

