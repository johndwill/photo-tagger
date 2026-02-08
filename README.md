# photo-tagger

A Python utility that reads EXIF metadata from photos and overlays the capture location and time directly onto the image.

## Features

- Extracts GPS coordinates from EXIF data and reverse geocodes them to human-readable locations (e.g. "San Francisco, California")
- Extracts and formats the capture date/time
- Overlays location and timestamp as white text with a drop shadow in the bottom-right corner
- Resizes images to 16:9 aspect ratio (max 1920px wide) with black letterboxing
- Supports batch processing via a shell script

## Requirements

- Python 3
- macOS (uses Helvetica system font; falls back to default font on other platforms)

## Setup

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

### Single image

```sh
python photo_tagger.py <image_path> [output_path]
```

If no output path is given, the tagged image is saved alongside the original with a `_tagged` suffix.

### Batch processing

Edit `tagimgs.sh` to set the `dir` variable to your image directory, then run:

```sh
./tagimgs.sh
```

This processes all images in the directory, skips already-tagged files, and writes output to a `tagged/` subdirectory.

## Dependencies

| Package | Purpose |
|---------|---------|
| [Pillow](https://pypi.org/project/Pillow/) | Image resizing and text overlay |
| [exifread](https://pypi.org/project/ExifRead/) | EXIF metadata extraction |
| [geopy](https://pypi.org/project/geopy/) | Reverse geocoding via OpenStreetMap Nominatim |
