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

        // Preload previous and next images
        preloadImage((currentIndex - 1 + photos.length) % photos.length);
        preloadImage((currentIndex + 1) % photos.length);
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
    const selectedName = nameSelect.value;
    const formattedAge = ageInput.value;
    if (!selectedName || !formattedAge) {
        alert("Please select a name and an age.");
        return;
    }

    try {
        const response = await fetch('/api/get_age_date', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                person_name: selectedName,
                age: formattedAge
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

fetchPhotos();
