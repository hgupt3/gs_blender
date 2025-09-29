# GelSight Simulation

Generate synthetic GelSight tactile images and depth maps from 3D meshes using Blender. This repo automates Blender to render samples, then post-processes depth maps into normal maps and provides simple viewers.

### Prerequisites

- Blender 3.x (GUI; i was not able to get background rendering to work for the depth maps)
- Linux recommended (tested on Ubuntu)
- Python 3.10+ for post-processing and viewers

### Setup (post-process + viewers)

Create a virtual environment (recommended) and install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install numpy opencv-python Pillow plotly dash
```

### Project structure

- `gelsight_sampler.blend` — Blender scene containing the GelSight setup
- `scripting.py` — Blender-side generator (runs inside Blender)
- `run_blender.py` — Launches Blender with the scene and script; restarts if Blender crashes
- `post_process.py` — Converts `raw_data/*.npy` depth maps to `dmaps/*.png` and `norms/*.png`
- `meshes/` — Place your input `.obj` meshes here
- `renders/` — Output directory (auto-created)
- `viewers/` — Simple Dash apps to preview results

### Configuration

All sampling and sensor parameters are declared at the top of `scripting.py`.
- Sampling counts: `NUM_SENSORS`, `NUM_CALIBRATION`, `NUM_OBJ_SAMPLES`
- Object ranges: `OBJ_SIZE_MIN/MAX`, `X_MIN/MAX`, `Y_MIN/MAX`, `OBJ_DEPTH_MIN/MAX`
- Sensor parameters: `FOV_MIN/MAX`, `LENGTH_MIN/MAX`, `SMOOTHNESS_MIN/MAX`, `ROUGH_MIN/MAX`, `SCALE_MIN/MAX`, light colors/strengths
- Run mode: `CONTINUE` toggles whether to resume into existing `renders/` or start fresh. Leave it on continue even on fresh run because the blender crashes at times (we have auto restart measures for this). 

Output is written within this repo at `<repo>/renders`. You can override the location with the environment variable `GELSIGHT_RENDER_DIR` if needed.

### Quickstart

- In `scripting.py` set (leave `CONTINUE=True` to tolerate occasional Blender crashes):
  - `CONTINUE = True`
  - `NUM_SENSORS = 1`
  - `NUM_CALIBRATION = 3`
  - `NUM_OBJ_SAMPLES = 5`
- Add at least one `.obj` file to `meshes/`.
- Generate samples:
  ```bash
  python run_blender.py
  ```
- Post-process depth maps to PNG depth and normal maps:
  ```bash
  python post_process.py
  ```
- (Optional) View results:
  - `python viewers/render.py`
  - `python viewers/sensor.py`

### Usage

1) Prepare meshes
- Drop `.obj` files into `meshes/`. They will be imported, scaled, and randomly posed per sample.

2) Generate samples (GUI Blender)
```bash
python run_blender.py
```

3) Post-process depth maps
```bash
python post_process.py
```

This creates `renders/sensor_XXXX/{dmaps,norms}` PNGs from `raw_data/*.npy`.

4) View (optional)
- `python viewers/render.py` — 3D scatter preview of a depth map + sample mosaics
- `python viewers/sensor.py` — Per-sensor image gallery

### Tips and troubleshooting

- To start small for a smoke test, use the Quickstart values.
- If Blender errors about NumPy, install it into Blender’s Python:
  ```bash
  blender --python-expr "import sys; print(sys.executable)"
  /path/to/blender/python -m pip install numpy
  ```
- To redirect output elsewhere, export `GELSIGHT_RENDER_DIR=/path/to/renders`
