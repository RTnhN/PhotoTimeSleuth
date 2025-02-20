let photos = [];
let updatedPhotos = {};
let currentIndex = 0;
let rotationAngle = 0;

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

function updatePhoto() {
    if (photos.length > 0) {
        document.getElementById('photo-name').textContent = photos[currentIndex];
        document.getElementById('photo').src = `/photos/${photos[currentIndex]}`;
        document.getElementById('update-indicator').style.display = updatedPhotos[photos[currentIndex]] ? 'block' : 'none';
        rotationAngle = 0;
        document.getElementById('photo').style.transform = `rotate(${rotationAngle}deg)`;
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

fetchPhotos();
