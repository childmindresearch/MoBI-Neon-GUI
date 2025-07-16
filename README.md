# Neon Scene Camera Recorder

A simple, clean GUI application for recording video from Pupil Labs Neon devices with synchronized LSL markers.

## Features

- Real-time video preview from Neon device
- GUI for easy recording control
- LSL marker synchronization for precise timing
- Configurable save directory
- Modern Python project structure with uv

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- Pupil Labs Neon device

## Installation

1. Install uv if you haven't already:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Clone/navigate to this project directory

3. Install dependencies:
   ```bash
   uv sync
   ```

## Usage

Run the GUI application:
```bash
uv run mobi-neon
```

Or alternatively:
```bash
uv run main.py
```

The GUI provides:
- Device connection controls
- Real-time video preview
- Recording start/stop buttons
- Save directory selection
- Activity log

For command-line usage, see the `script.py` file in the parent directory.

## Dependencies

- `opencv-python`: Video processing and display
- `pylsl`: LSL marker streaming
- `pupil-labs-realtime-api`: Neon device communication
- `pyqt6`: GUI framework

## Development

This project uses uv for all dependency management. To add new dependencies:
```bash
uv add package-name
```

For linting and type checking:
```bash
uv run ruff check
uv run mypy src/
```

## Output

Video files are saved as MP4 format with timestamps in the filename.
LSL markers are sent for precise synchronization:
- `scene_start`: When recording begins
- `scene_end`: When recording stops
