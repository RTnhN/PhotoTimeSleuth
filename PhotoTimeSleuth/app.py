import argparse
import io
import logging
import os
import shutil
import sys
from datetime import datetime, timedelta

import flask.cli
from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    send_file,
    send_from_directory,
)
from PIL import Image
from werkzeug.utils import secure_filename

from .basic_helper import get_local_ip
from .image_helper import change_image_date


def suppress_banner(*args, **kwargs):
    pass


flask.cli.show_server_banner = suppress_banner


app = Flask(__name__)

SEASON_MAP = {
    "spring": 3,
    "summer": 6,
    "fall": 9,
    "winter": 12,
}


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
    season = data.get("season")
    age = data.get("age")
    if not person_name or ".." in person_name or "/" in person_name:
        return jsonify({"error": "Invalid person name"}), 400
    if not age:
        return jsonify({"error": "Invalid age"}), 400
    if not season:
        return jsonify({"error": "Invalid season"}), 400
    try:
        age = int(age)
    except ValueError:
        return jsonify({"error": "Invalid age"}), 400

    bday = [
        person for person in load_names_and_bdays() if person["name"] == person_name
    ][0]["bday"]

    estimated_date = calculate_date(bday, age, season)

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


def calculate_date(bday, age, season):
    try:
        birthday = datetime.strptime(bday, "%Y-%m-%d")
        estimated_date = birthday + timedelta(days=age * 365.25)
        if season == "birthday":
            return estimated_date.strftime("%Y-%m-%dT%H:%M")
        if season == "christmas":
            return find_closest_season_date(estimated_date, 12, 25)
        season_month = SEASON_MAP[season]
        return find_closest_season_date(estimated_date, season_month, 1)
    except ValueError:
        return None


def find_closest_season_date(estimated_date, month, day):
    same_year_date = estimated_date.replace(month=month, day=day)
    previous_year_date = same_year_date.replace(year=same_year_date.year - 1)
    next_year_date = same_year_date.replace(year=same_year_date.year + 1)

    closest_season_date = min(
        [same_year_date, previous_year_date, next_year_date],
        key=lambda d: abs((d - estimated_date).days),
    )
    closest_season_date = closest_season_date.replace(day=day)
    return closest_season_date.strftime("%Y-%m-%dT%H:%M")


@app.route("/photos/<path:filename>")
def serve_photo(filename):
    """Serve downsized photos from the configured photo directory."""
    photo_dir = app.config.get("PHOTO_DIRECTORY")
    full_path = os.path.join(photo_dir, filename)

    # Check if resizing is requested via query parameters
    width = request.args.get("width", type=int)
    height = request.args.get("height", type=int)

    if width or height:
        # Open the image
        try:
            with Image.open(full_path) as img:
                # If only one dimension is given, maintain aspect ratio
                if width and not height:
                    height = int((width / img.width) * img.height)
                elif height and not width:
                    width = int((height / img.height) * img.width)

                # Resize the image
                img = img.resize((width, height), Image.LANCZOS)

                # Convert image to bytes for response
                img_io = io.BytesIO()
                img.save(img_io, format="JPEG")
                img_io.seek(0)

                return send_file(img_io, mimetype="image/jpeg")
        except Exception as e:
            return f"Error processing image: {str(e)}", 500

    # Serve the original image if no resizing is requested
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
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    main()
