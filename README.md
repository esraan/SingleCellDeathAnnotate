# SingleCellDeathAnnotate

A napari plugin for:

- **Manual cell segmentation** — draw masks and save or load `.npy` files.
- **Cell tracking** — launch btrack, export or reload tracking CSV files, and remove selected tracks.
- **Death-event annotation** — record a cell's death time, position, and event type and export the results to CSV.

## Requirements

| Software | Version |
|---|---|
| Python | 3.12 |
| napari | ≥ 0.5.0 |
| PyQt6 | Current conda-forge version |
| NumPy | ≥ 1.26 |
| Pandas | ≥ 2.1 |
| nd2 | ≥ 0.9 |
| btrack | ≥ 0.6 |
| pydantic | ≥ 2.0 |

## Installation and use

See the complete [Installation and User Instructions](INSTALLATION_AND_USER_INSTRUCTIONS.md) for:

- Anaconda installation on Windows and macOS;
- environment and plugin setup;
- launching the plugin;
- death-event annotation;
- segmentation and tracking;
- saving screenshots and CSV files; and
- troubleshooting.

The guide is the single source of truth for end-user setup and operation.

### Quick start for an existing installation

```bash
conda activate single-cell-death-annotate
napari
```

In napari, select **Plugins > SingleCellDeathAnnotate**.

## Plugin interface

The plugin contains two tabs:

| Tab | Purpose |
|---|---|
| **Segmentation & Tracking** | Create and save masks, launch tracking, import/export tracking CSV files, and delete tracks |
| **Death Events** | Annotate, delete, save, and reload cell-death events |

Supported image formats are `.tif`, `.tiff`, `.png`, `.jpg`, `.jpeg`, and `.nd2`.

## Development

Install the package with testing dependencies from the repository root:

```bash
conda env create -f environment.yml
conda activate single-cell-death-annotate
python -m pip install -e ".[testing]"
```

Run the tests with:

```bash
pytest tests/ -v
```

Editable installation means source changes are available after restarting napari.

## Publishing from GitHub

The plugin is currently a local package and is not published on PyPI. After placing this folder in its own GitHub repository, it can be installed with:

```bash
python -m pip install git+https://github.com/<your-org>/SingleCellDeathAnnotate.git
```

## License

This project is distributed under the [BSD 3-Clause License](LICENSE).
