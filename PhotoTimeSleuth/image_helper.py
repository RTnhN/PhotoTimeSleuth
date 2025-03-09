import piexif
import logging

logger = logging.getLogger(__name__)


def change_image_date(image_path, new_date):
    """
    Change the date in the metadata of an image and log the change.

    :param image_path: Path to the input image.
    :param new_date: New date as a string in the format 'YYYY:MM:DD HH:MM:SS'.
    :return: (Success: True/False, Message: str)
    """
    try:
        # Load EXIF data
        exif_dict = piexif.load(image_path)

        # Extract old date values if available
        old_date_original = exif_dict["Exif"].get(
            piexif.ExifIFD.DateTimeOriginal, "UNKNOWN"
        )
        old_date_digitized = exif_dict["Exif"].get(
            piexif.ExifIFD.DateTimeDigitized, "UNKNOWN"
        )
        old_date_image = exif_dict["0th"].get(piexif.ImageIFD.DateTime, "UNKNOWN")

        # Update EXIF metadata with the new date
        exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = new_date
        exif_dict["Exif"][piexif.ExifIFD.DateTimeDigitized] = new_date
        exif_dict["0th"][piexif.ImageIFD.DateTime] = new_date
        exif_bytes = piexif.dump(exif_dict)

        # Apply new EXIF data to the image
        piexif.insert(exif_bytes, image_path, image_path)

        # Log the change with old and new date values
        logging.info(
            f"SUCCESS: Updated '{image_path}' | "
            f"Old Date (Original: {old_date_original}, Digitized: {old_date_digitized}, Image: {old_date_image}) | "
            f"New Date: {new_date}"
        )
        return True, f"Date changed successfully. Image saved to: {image_path}"

    except Exception as e:
        logging.error(f"ERROR: Failed to update '{image_path}' | Reason: {str(e)}")
        return False, str(e)
