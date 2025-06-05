let photos = [];
let updatedPhotos = {};
let currentIndex = 0;
let rotationAngle = 0;
let preloadedImages = {};
let defaultImageWidth = 800;

async function fetchPhotos() {
    try {
        const response = await fetch('/api/photos');
        const data = await response.json();
        if (data.photos) {
            photos = data.photos;
            if (photos.length > 0) {
                currentIndex = 0;
                updatePhoto();
            }
        }
    } catch (error) {
        console.error('Error fetching photos:', error);
    }
}

function preloadImage(index) {
    if (photos.length > 0 && index >= 0 && index < photos.length) {
        const photoSrc = `/photos/${photos[index]}?width=${defaultImageWidth}`;
        if (!preloadedImages[photoSrc]) {
            const img = new Image();
            img.src = photoSrc;
            preloadedImages[photoSrc] = img;
        }
    }
}
function updatePhoto() {
    if (photos.length > 0) {
        const currentPhoto = photos[currentIndex];
        const photoElement = document.getElementById('photo');
        const photoSrc = `/photos/${currentPhoto}?width=${defaultImageWidth}`;

        document.getElementById('photo-name').textContent = currentPhoto;
        photoElement.src = photoSrc;
        document.getElementById('update-indicator').style.display = updatedPhotos[currentPhoto] ? 'block' : 'none';

        rotationAngle = 0;
        photoElement.style.transform = `rotate(${rotationAngle}deg)`;

        // Update progress bar
        updateProgressBar();

        // Preload previous and next images
        preloadImage((currentIndex - 1 + photos.length) % photos.length);
        preloadImage((currentIndex + 1) % photos.length);
    }
}

function updateProgressBar() {
    const progressBar = document.getElementById('photo-progress');
    const progressText = document.getElementById('photo-progress-text');

    if (photos.length > 0) {
        const progressValue = ((currentIndex + 1) / photos.length) * 100;
        progressBar.value = progressValue;
        progressText.textContent = `${currentIndex + 1} / ${photos.length}`;
    } else {
        progressBar.value = 0;
        progressText.textContent = "0 / 0";
    }
}

function returnToStart() {
    if (photos.length > 0) {
        currentIndex = 0;
        updatePhoto();
    }
}

function prevPhoto() {
    if (photos.length > 0) {
        currentIndex = (currentIndex - 1 + photos.length) % photos.length;
        updatePhoto();
    }
}

function nextPhoto() {
    if (photos.length > 0) {
        currentIndex = (currentIndex + 1) % photos.length;
        updatePhoto();
    }
}

function rotateLeft() {
    rotationAngle -= 90;
    document.getElementById('photo').style.transform = `rotate(${rotationAngle}deg)`;
    adjustPhotoContainer(rotationAngle);
}

function rotateRight() {
    rotationAngle += 90;
    document.getElementById('photo').style.transform = `rotate(${rotationAngle}deg)`;
    adjustPhotoContainer(rotationAngle);
}

async function updateMetadata() {
    if (photos.length > 0) {
        const selectedDate = document.getElementById('date-picker').value;
        if (!selectedDate) {
            alert("Please select a date.");
            return;
        }

        const formattedDate = selectedDate.replace("T", " ").replace(/-/g, ":") + ":00";

        try {
            const response = await fetch('/api/update_metadata', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    image_path: photos[currentIndex],
                    new_date: formattedDate
                })
            });
            const data = await response.json();
            if (response.ok) {
                updatedPhotos[photos[currentIndex]] = true;
                document.getElementById('update-indicator').style.display = 'block';
            } else {
                alert("Error: " + data.error);
            }
        } catch (error) {
            console.error('Error updating metadata:', error);
        }
    }
}

async function getAgeDate() {
    const ageInput = document.getElementById('age');
    const nameSelect = document.getElementById('names');
    const seasonSelect = document.getElementById('season');
    const selectedName = nameSelect.value;
    const formattedAge = ageInput.value;
    const selectedSeason = seasonSelect.value;
    if (!selectedName || !formattedAge || !selectedSeason) {
        alert("Please select a name, an age, and a season.");
        return;
    }

    try {
        const response = await fetch('/api/get_age_date', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                person_name: selectedName,
                age: formattedAge,
                season: selectedSeason
            })
        });

        const data = await response.json();
        if (response.ok) {
            const estimatedDate = data.estimated_date;
            if (estimatedDate) {
                document.getElementById('date-picker').value = estimatedDate;
            } else {
                alert("Invalid date format received from the server.");
            }
        } else {
            alert("Error: " + data.error);
        }
    } catch (error) {
        console.error('Error getting age date:', error);
    }
}

async function pickAndSetFolder() {
    if (window.pywebview) {
        const folder = await window.pywebview.api.pick_folder();
        if (folder) {
            // Send the new folder path to Flask
            fetch('/api/update_directory', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ photo_directory: folder })
            })
            .then(response => response.json())
            .then(data => {
                console.log(data.message || data.error);
                document.getElementById('photo-directory').textContent = folder;
                fetchPhotos();
            });
        }
    } else {
        alert("PyWebView API not available.");
    }
}


fetchPhotos();
