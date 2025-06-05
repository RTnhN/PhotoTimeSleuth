import argparse
import io
import logging
import os
import shutil
import sys
import threading
from datetime import datetime

import flask.cli
from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    send_file,
    send_from_directory,
)
from PIL import Image, ImageOps
from werkzeug.utils import secure_filename
import webview  # PyWebView import

from PhotoTimeSleuth.Helpers.basic_helper import get_local_ip
from PhotoTimeSleuth.Helpers.image_helper import change_image_date, get_image_date
from PhotoTimeSleuth.Helpers.file_helper import load_names_and_bdays
from PhotoTimeSleuth.Helpers.date_helper import calculate_date


class API:
    def __init__(self, window):
        self.window = window

    def pick_folder(self):
        result = self.window.create_file_dialog(webview.FOLDER_DIALOG)
        if result:
            return result[0]
        return None


def suppress_banner(*args, **kwargs):
    pass


flask.cli.show_server_banner = suppress_banner


if hasattr(sys, "_MEIPASS"):
    base_path = sys._MEIPASS
else:
    base_path = os.path.abspath(".")

app = Flask(
    __name__,
    template_folder=os.path.join(base_path, "PhotoTimeSleuth", "templates"),
    static_folder=os.path.join(base_path, "PhotoTimeSleuth", "static"),
)


@app.route("/")
def index():
    """Serve the main HTML page."""
    names_and_bdays = load_names_and_bdays(app.config.get("BDAY_FILE"))
    return render_template(
        "index.html",
        names_and_bdays=names_and_bdays,
        ip_address_port=app.config.get("SERVER_IP_PORT"),
        photo_directory=app.config.get("PHOTO_DIRECTORY"),
    )


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

    try:
        datetime.strptime(new_date, "%Y:%m:%d")
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

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
        person
        for person in load_names_and_bdays(app.config.get("BDAY_FILE"))
        if person["name"] == person_name
    ][0]["bday"]

    estimated_date = calculate_date(bday, age, season)

    if not estimated_date:
        return jsonify({"error": "Invalid birthday or age"}), 400

    return jsonify({"estimated_date": estimated_date}), 200


@app.route("/api/get_current_photo_date", methods=["GET"])
def get_current_photo_date():
    """API route to retrieve the current photo date."""
    photo_dir = app.config.get("PHOTO_DIRECTORY")
    if not photo_dir or not os.path.isdir(photo_dir):
        return jsonify({"error": "Invalid directory"}), 400

    image_path = os.path.join(
        photo_dir, secure_filename(request.args.get("image_path"))
    )

    if not os.path.isfile(image_path):
        return jsonify({"error": "Image not found"}), 404

    try:
        date = get_image_date(image_path)
        if date:
            return jsonify({"current_date": date}), 200
        else:
            return jsonify({"error": "No date found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
    try:
        return (
            jsonify(
                {"names_and_bdays": load_names_and_bdays(app.config.get("BDAY_FILE"))}
            ),
            200,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/update_directory", methods=["POST"])
def update_directory():
    data = request.get_json()
    photo_dir = data.get("photo_directory")
    if not photo_dir or ".." in photo_dir or "/" in photo_dir:
        return jsonify({"error": "Invalid photo directory"}), 400

    app.config["PHOTO_DIRECTORY"] = photo_dir
    return jsonify({"message": "Directory updated successfully"}), 200


@app.route("/photos/<path:filename>")
def serve_photo(filename):
    """Serve downsized photos from the configured photo directory."""
    photo_dir = app.config.get("PHOTO_DIRECTORY")
    full_path = os.path.join(photo_dir, filename)

    width = request.args.get("width", type=int)
    height = request.args.get("height", type=int)

    if width or height:
        try:
            with Image.open(full_path) as img:
                img = ImageOps.exif_transpose(img)  # Respect EXIF orientation
                orig_width, orig_height = img.size
                if width and not height:
                    height = int((width / orig_width) * orig_height)
                elif height and not width:
                    width = int((height / orig_height) * orig_width)
                elif width and height:
                    aspect_ratio = orig_width / orig_height
                    target_ratio = width / height

                    if target_ratio > aspect_ratio:
                        width = int(height * aspect_ratio)
                    else:
                        height = int(width / aspect_ratio)

                img = img.resize((width, height), Image.LANCZOS)
                img_io = io.BytesIO()
                img.save(img_io, format="JPEG")
                img_io.seek(0)
                return send_file(img_io, mimetype="image/jpeg")
        except Exception as e:
            return f"Error processing image: {str(e)}", 500

    return send_file(full_path, mimetype="image/jpeg")


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static/images"), "favicon.ico"
    )


def make_default_bdays_file(bday_file):
    sample_bdays_file = os.path.join(os.path.dirname(__file__), "default_bday.txt")
    shutil.copyfile(sample_bdays_file, bday_file)


def run_flask_app(bday_file):
    directory = os.getcwd()

    if not bday_file:
        home_dir = os.path.expanduser("~")
        if not os.path.isdir(os.path.join(home_dir, "phototimesleuth")):
            os.makedirs(os.path.join(home_dir, "phototimesleuth"))
        bday_file = os.path.join(home_dir, "phototimesleuth", "bdays.txt")
        if not os.path.isfile(bday_file):
            make_default_bdays_file(bday_file)
            print(f"Created default bday file at {bday_file}")
        else:
            print(f"Using existing bday file at {bday_file}")

    if not os.path.isdir(directory):
        print(f"Error: Directory {directory} does not exist or is not accessible.")
        sys.exit(1)

    log_file_path = os.path.join(home_dir, "photo_changes.log")
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

    app.config["SERVER_IP_PORT"] = f"{ip_address}:{port}"
    app.config["PHOTO_DIRECTORY"] = directory
    app.config["BDAY_FILE"] = bday_file
    app.run(host="0.0.0.0", port=port, debug=False)


def main():
    parser = argparse.ArgumentParser(description="Photo Time Sleuth")
    parser.add_argument(
        "--bday-file",
        type=str,
        help=(
            "Path to the file containing birthdays. "
            "If not provided, the current working directory will be used."
        ),
    )
    args = parser.parse_args()

    bday_file = args.bday_file

    # Start Flask in a separate thread
    flask_thread = threading.Thread(
        target=run_flask_app, args=(bday_file,), daemon=True
    )
    flask_thread.start()

    # Give Flask a moment to start
    import time

    time.sleep(1)

    # Determine the local URL for the webview
    local_url = "http://127.0.0.1:5000"

    min_width = 600
    min_height = 800

    # Create and show the PyWebView window
    window = webview.create_window(
        "Photo Time Sleuth",
        local_url,
        width=min_width,
        min_size=(min_width, min_height)
    )
    api = API(window)
    window.expose(api.pick_folder)
    webview.start(None, window, icon="./static/images/favicon.png")

    # When the WebView window closes, exit the script
    sys.exit(0)


if __name__ == "__main__":
    main()
