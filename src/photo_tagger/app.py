"""Flask web frontend for photo-tagger."""

import io
import logging
from pathlib import Path

from flask import Flask, render_template, request, jsonify, send_file, abort
from .tagger import list_images, generate_thumbnail, overlay_text, is_tagged

logger = logging.getLogger(__name__)


app = Flask(__name__)


@app.route("/")
def index():
    """Serve the main page."""
    return render_template("index.html")


@app.route("/api/browse")
def api_browse():
    """List subdirectories of a given path for the folder browser.

    Query params:
        path: Directory to list (defaults to user home).
    """
    path = request.args.get("path", "").strip()
    if not path:
        path = str(Path.home())

    folder = Path(path)
    if not folder.is_dir():
        return jsonify({"error": f"Not a directory: {path}"}), 404

    dirs = []
    try:
        for entry in sorted(folder.iterdir()):
            if entry.is_dir() and not entry.name.startswith("."):
                dirs.append(entry.name)
    except PermissionError:
        logger.warning("Permission denied listing %s", folder)

    return jsonify(
        {
            "current": str(folder),
            "parent": str(folder.parent) if folder.parent != folder else None,
            "dirs": dirs,
        }
    )


@app.route("/api/images")
def api_list_images():
    """List images in the given folder.

    Query params:
        folder: Absolute path to the image folder.
    """
    folder = request.args.get("folder", "").strip()
    if not folder:
        return jsonify({"error": "No folder specified"}), 400

    folder_path = Path(folder)
    if not folder_path.is_dir():
        return jsonify({"error": f"Directory not found: {folder}"}), 404

    images = list_images(folder_path)
    image_list = [
        {"filename": img_path.name, "tagged": is_tagged(img_path)}
        for img_path in images
    ]

    logger.info("Listed %d images in %s", len(image_list), folder_path)
    return jsonify({"folder": str(folder_path), "images": image_list})


@app.route("/api/thumbnail/<path:filename>")
def api_thumbnail(filename):
    """Serve a dynamically generated thumbnail.

    Query params:
        folder: The folder containing the image.
        size:   Max thumbnail dimension (default 300).
    """
    folder = request.args.get("folder", "").strip()
    if not folder:
        abort(400)

    image_path = Path(folder) / filename
    if not image_path.is_file():
        abort(404)

    size = request.args.get("size", 300, type=int)
    thumb = generate_thumbnail(str(image_path), max_size=size)

    buf = io.BytesIO()
    thumb.save(buf, format="JPEG")
    buf.seek(0)
    return send_file(buf, mimetype="image/jpeg")


@app.route("/api/tag", methods=["POST"])
def api_tag_image():
    """Tag a single image.

    JSON body: {"folder": "/absolute/path", "filename": "IMG_001.jpg"}
    """
    data = request.get_json()
    if not data or "folder" not in data or "filename" not in data:
        return jsonify({"error": "Missing folder or filename"}), 400

    folder = Path(data["folder"])
    filename = data["filename"]
    image_path = folder / filename

    if not image_path.is_file():
        return (
            jsonify(
                {
                    "filename": filename,
                    "status": "error",
                    "message": f"File not found: {image_path}",
                }
            ),
            404,
        )

    tagged_dir = folder / "tagged"

    if is_tagged(image_path):
        return jsonify(
            {
                "filename": filename,
                "status": "skipped",
                "message": "Already tagged",
            }
        )

    try:
        output = overlay_text(str(image_path), output_dir=str(tagged_dir))
        if output is None:
            logger.info("Skipped %s: no EXIF data", filename)
            return jsonify(
                {
                    "filename": filename,
                    "status": "skipped",
                    "message": "No EXIF location or time data found",
                }
            )
        logger.info("Tagged %s -> %s", filename, Path(output).name)
        return jsonify(
            {
                "filename": filename,
                "status": "success",
                "output": Path(output).name,
                "message": "Tagged successfully",
            }
        )
    except Exception as e:
        logger.exception("Error tagging %s", filename)
        return (
            jsonify(
                {
                    "filename": filename,
                    "status": "error",
                    "message": str(e),
                }
            ),
            500,
        )


def main():
    """Entry point for running the Flask dev server."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    app.run(debug=True, port=5001)


if __name__ == "__main__":
    main()
