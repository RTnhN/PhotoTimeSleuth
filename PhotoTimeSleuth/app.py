import logging
import os
import sys
from .image_helper import change_image_date
from .basic_helper import get_local_ip

import psutil
import piexif
from flask import Flask, jsonify, render_template, request, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)


@app.route("/")
def index():
    """Serve the main HTML page."""
    return render_template("index.html")


@app.route("/api/update_metadata", methods=["POST"])
def update_metadata():
    data = request.get_json()
    image_name = data.get("image_path")
    new_date = data.get("new_date")

    if not image_name or ".." in image_name or "/" in image_name:
        return jsonify({"error": "Invalid image path"}), 400

    photo_dir = app.config.get("PHOTO_DIRECTORY")
    if not photo_dir:
        return jsonify({"error": "Photo directory is not configured"}), 500

    image_path = os.path.join(photo_dir, secure_filename(image_name))

    if not os.path.isfile(image_path):
        return jsonify({"error": "Image not found"}), 404

    # Validate date format
    try:
        datetime.strptime(new_date, "%Y:%m:%d %H:%M:%S")
    except ValueError:
        return jsonify({"error": "Invalid date format. Use 'YYYY:MM:DD HH:MM:SS'"}), 400

    success, message = change_image_date(image_path, new_date)

    if success:
        return jsonify({"message": message}), 200
    else:
        return jsonify({"error": message}), 500


@app.route("/api/folder_path", methods=["GET"])
def get_folder_path():
    """API route to retrieve the folder path."""
    photo_dir = app.config.get("PHOTO_DIRECTORY")
    if not photo_dir:
        return jsonify({"error": "Photo directory is not configured"}), 500
    return jsonify({"folder_path": photo_dir}), 200


@app.route("/api/photos", methods=["GET"])
def get_photos():
    """API route to retrieve a list of photos from the directory."""
    photo_dir = app.config.get("PHOTO_DIRECTORY")
    if not photo_dir or not os.path.isdir(photo_dir):
        return jsonify({"error": "Invalid directory"}), 400

    photos = [
        file
        for file in os.listdir(photo_dir)
        if file.lower().endswith(("jpg", "jpeg", "png"))
    ]
    return jsonify({"photos": photos}), 200


@app.route("/photos/<path:filename>")
def serve_photo(filename):
    """Serve photos from the configured photo directory."""
    photo_dir = app.config.get("PHOTO_DIRECTORY")
    return send_from_directory(photo_dir, filename)


def get_local_ip():
    for _, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == 2 and addr.address.startswith("192.168."):
                return addr.address  # Returns the first 192.168.x.x address found
    return None


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Photo Time Sleuth")
    parser.add_argument(
        "--directory",
        type=str,
        help=(
            "Path to the directory containing photos. "
            "If not provided, the current working directory will be used."
        ),
    )
    args = parser.parse_args()

    directory = args.directory

    if not directory:
        directory = os.getcwd()

    if not os.path.isdir(directory):
        print(f"Error: Directory {directory} does not exist or is not accessible.")
        sys.exit(1)

    # Define the log file path inside the photo directory
    log_file_path = os.path.join(directory, "photo_changes.log")

    # Configure logging dynamically
    logging.basicConfig(
        filename=log_file_path,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    ip_address = get_local_ip()
    port = 5000
    if not ip_address:
        serving_ip = f"http://localhost:{port}"
    else:
        serving_ip = f"http://{ip_address}:{port}"

    print(f"Starting server for directory: {directory}")
    print(f"Log file will be saved at: {log_file_path}")
    print(f"Serving on {serving_ip}")

    app.config["PHOTO_DIRECTORY"] = directory
    app.run(host="0.0.0.0", port=port, debug=True)


if __name__ == "__main__":
    main()
