"""Core photo tagging logic: EXIF extraction, geocoding, and text overlay."""

import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import exifread
from geopy.geocoders import Nominatim

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.heic'}


def get_decimal_coords(tags):
    """Convert GPS coordinates from EXIF format to decimal degrees."""
    def to_decimal(values, ref):
        d, m, s = [float(v.num) / float(v.den) for v in values.values]
        decimal = d + m / 60 + s / 3600
        if ref in ['S', 'W']:
            decimal = -decimal
        return decimal

    lat = to_decimal(tags['GPS GPSLatitude'], str(tags['GPS GPSLatitudeRef']))
    lon = to_decimal(tags['GPS GPSLongitude'], str(tags['GPS GPSLongitudeRef']))
    return lat, lon


def get_location_string(lat, lon):
    """Reverse geocode coordinates to a location string."""
    for i in range(2):
        try:
            geolocator = Nominatim(user_agent="photo-tagger")
            location = geolocator.reverse(f"{lat}, {lon}", language="en")
        except Exception as e:
            logger.warning("Error reverse geocoding coordinates: %s", e)
            time.sleep(2)

    if not location:
        logger.info("No location found for coordinates: %s, %s", lat, lon)
        return None

    addr = location.raw.get('address', {})
    city = addr.get('city') or addr.get('town') or addr.get('village') or addr.get('municipality')
    state = addr.get('state')
    country = addr.get('country')

    if country in ['United States', 'USA', 'United States of America']:
        if city and state:
            return f"{city}, {state}"
        elif state:
            return state
        return "USA"

    if city and country:
        return f"{city}, {country}"
    return country or "Unknown"


def get_exif_data(image_path):
    """Extract location and datetime from EXIF."""
    with open(image_path, 'rb') as f:
        tags = exifread.process_file(f)

    # Get capture time
    capture_time = None
    if 'EXIF DateTimeOriginal' in tags:
        dt_str = str(tags['EXIF DateTimeOriginal'])
        capture_time = datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")

    # Get GPS location
    location = None
    if 'GPS GPSLatitude' in tags and 'GPS GPSLongitude' in tags:
        lat, lon = get_decimal_coords(tags)
        location = get_location_string(lat, lon)

    return location, capture_time


def fit_to_16_9(img, max_width=1920):
    """Fit image to 16:9 aspect ratio without distortion, max width 1920."""
    target_ratio = 16 / 9
    img_ratio = img.width / img.height

    # Determine final canvas size (max 1920 wide)
    canvas_width = min(img.width, max_width)
    canvas_height = int(canvas_width / target_ratio)

    # Scale the image to fit within the canvas while preserving aspect ratio
    if img_ratio > target_ratio:
        # Image is wider than 16:9 - fit to width
        new_width = canvas_width
        new_height = int(canvas_width / img_ratio)
    else:
        # Image is taller than 16:9 - fit to height
        new_height = canvas_height
        new_width = int(canvas_height * img_ratio)

    # Resize image
    resized = img.resize((new_width, new_height), Image.LANCZOS)

    # Create black canvas and center the image
    canvas = Image.new('RGB', (canvas_width, canvas_height), (0, 0, 0))
    x_offset = (canvas_width - new_width) // 2
    y_offset = (canvas_height - new_height) // 2
    canvas.paste(resized, (x_offset, y_offset))

    return canvas


def overlay_text(image_path, output_path=None, *, output_dir=None):
    """Overlay location and time on the image.

    Returns the output path on success, or None if no EXIF data found.
    """
    location, capture_time = get_exif_data(image_path)

    if not location and not capture_time:
        logger.info("No EXIF location or time data found for %s", image_path)
        return None

    img = Image.open(image_path)

    # Convert to 16:9 with max width 1920
    img = fit_to_16_9(img)

    draw = ImageDraw.Draw(img)

    # Build text
    lines = []
    if location:
        lines.append(location)
    if capture_time:
        lines.append(capture_time.strftime("%B %d, %Y  %I:%M %p"))
    text = "\n".join(lines)

    # Font size based on image width
    font_size = max(16, img.width // 30)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except:
        font = ImageFont.load_default()

    # Position in bottom-right with padding
    padding = 30
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x, y = img.width - text_width - padding, img.height - text_height - padding

    # Draw shadow then text
    draw.text((x+2, y+2), text, font=font, fill=(0, 0, 0, 200))
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))

    # Save
    if output_path is None:
        p = Path(image_path)
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{p.stem}_tagged.png"
        else:
            output_path = p.parent / f"{p.stem}_tagged{p.suffix}"

    img.save(output_path)
    logger.info("Saved: %s", output_path)
    return str(output_path)


def list_images(folder_path):
    """Return a sorted list of image file Paths in the folder, excluding tagged files."""
    folder = Path(folder_path)
    images = []
    for f in sorted(folder.iterdir()):
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS and 'tagged' not in f.stem:
            images.append(f)
    return images


def is_tagged(image_path):
    """Check if a tagged version of this image already exists in the tagged/ subdirectory."""
    p = Path(image_path)
    tagged_dir = p.parent / "tagged"
    tagged_file = tagged_dir / f"{p.stem}_tagged.png"
    return tagged_file.exists()


def generate_thumbnail(image_path, max_size=300):
    """Return a Pillow Image resized for thumbnail display."""
    img = Image.open(image_path)
    img.thumbnail((max_size, max_size), Image.LANCZOS)
    return img


def _cli_main():
    """CLI entry point for console_scripts."""
    if len(sys.argv) < 2:
        print("Usage: photo-tagger <image_path> [output_path]")
        sys.exit(1)
    image_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    overlay_text(image_path, output_path)
