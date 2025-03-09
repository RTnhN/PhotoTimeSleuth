import logging
import os
import sys
from datetime import datetime, timedelta
from .image_helper import change_image_date
from .basic_helper import get_local_ip

import shutil
from flask import Flask, jsonify, render_template, request, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)


@app.route("/")
def index():
    """Serve the main HTML page."""
    names_and_bdays = load_names_and_bdays()

    return render_template("index.html", names_and_bdays=names_and_bdays)


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


@app.route("/api/get_age_date", methods=["POST"])
def get_age_date():
    data = request.get_json()
    person_name = data.get("person_name")
    age = data.get("age")
    if not person_name or ".." in person_name or "/" in person_name:
        return jsonify({"error": "Invalid person name"}), 400
    if not age:
        return jsonify({"error": "Invalid age"}), 400
    try:
        age = int(age)
    except ValueError:
        return jsonify({"error": "Invalid age"}), 400

    bday = [
        person for person in load_names_and_bdays() if person["name"] == person_name
    ][0]["bday"]

    estimated_date = calculate_date(bday, age)

    if not estimated_date:
        return jsonify({"error": "Invalid birthday or age"}), 400

    return jsonify({"estimated_date": estimated_date}), 200


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


@app.route("/api/names_and_bdays", methods=["GET"])
def get_names_and_bdays():
    """API route to retrieve the names and birthdays."""
    return jsonify({"names_and_bdays": load_names_and_bdays()}), 200


def load_names_and_bdays():
    """Helper function to load names and birthdays from the bday file."""
    bday_file = app.config.get("BDAY_FILE")
    if not bday_file or not os.path.isfile(bday_file):
        return []  # Return an empty list instead of an error

    names_and_bdays = []
    with open(bday_file, "r") as f:
        for line in f:
            if line.startswith("#"):
                continue
            name, bday = line.strip().split("\t")
            names_and_bdays.append({"name": name, "bday": bday})

    return names_and_bdays


def calculate_date(bday, age):
    try:
        birthday = datetime.strptime(bday, "%Y-%m-%d")
        estimated_date = birthday + timedelta(days=age * 365.25)
        return estimated_date.strftime("%Y-%m-%dT%H:%M")
    except ValueError:
        return None


@app.route("/photos/<path:filename>")
def serve_photo(filename):
    """Serve photos from the configured photo directory."""
    photo_dir = app.config.get("PHOTO_DIRECTORY")
    return send_from_directory(photo_dir, filename)


def make_default_bdays_file(bday_file):
    sample_bdays_file = os.path.join(os.path.dirname(__file__), "default_bday.txt")
    shutil.copyfile(sample_bdays_file, bday_file)


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
    parser.add_argument(
        "--bday-file",
        type=str,
        help=(
            "Path to the file containing birthdays. "
            "If not provided, the current working directory will be used."
        ),
    )
    args = parser.parse_args()

    directory = args.directory
    bday_file = args.bday_file

    if not directory:
        directory = os.getcwd()

    if not bday_file:
        bday_file = os.path.join(directory, "bdays.txt")
        if not os.path.isfile(bday_file):
            make_default_bdays_file(bday_file)

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
    app.config["BDAY_FILE"] = bday_file
    app.run(host="0.0.0.0", port=port, debug=True)


if __name__ == "__main__":
    main()
