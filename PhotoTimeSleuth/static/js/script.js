let photos = [];
let updatedPhotos = {};
let currentIndex = 0;
let rotationAngle = 0;
let preloadedImages = {};
let defaultImageWidth = 400;

async function fetchPhotos() {
    try {
        const response = await fetch('/api/photos');
        const data = await response.json();
        if (data.photos) {
            photos = data.photos;
            currentIndex = 0;
            await updatePhoto();
        }
    } catch (error) {
        console.error('Error fetching photos:', error);
    }
}

async function getCurrentPhotoDate() {
    try {
        const response = await fetch('/api/get_current_photo_date?image_path=' + photos[currentIndex]);
        const data = await response.json();
        if (response.ok) {
            const currentDate = data.current_date;
            if (currentDate) {
                document.getElementById('current-date').textContent = currentDate;
            } else {
                document.getElementById('current-date').textContent = "None";
            }
        } else {
            document.getElementById('current-date').textContent = "None";
        }
    } catch (error) {
        console.error('Error getting current photo date:', error);
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
async function updatePhoto() {
    const photoElement = document.getElementById('photo');
    let photoSrc = ``;
    let currentPhoto = '';
    const photoNameElement = document.getElementById('photo-name');
    if (photos.length > 0) {
        currentPhoto = photos[currentIndex];
        photoSrc = `/photos/${currentPhoto}?width=${defaultImageWidth}`;
        
        // Preload previous and next images
        preloadImage((currentIndex - 1 + photos.length) % photos.length);
        preloadImage((currentIndex + 1) % photos.length);
    } 
    photoNameElement.textContent = currentPhoto;
    photoElement.src = photoSrc;
    rotationAngle = 0;
    photoElement.style.transform = `rotate(${rotationAngle}deg)`;
    // Update progress bar
    updateProgressBar();
    await getCurrentPhotoDate();
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

async function returnToStart() {
    if (photos.length > 0) {
        currentIndex = 0;
        await updatePhoto();
    }
}

async function prevPhoto() {
    if (photos.length > 0) {
        currentIndex = (currentIndex - 1 + photos.length) % photos.length;
        await updatePhoto();
    }
}

async function nextPhoto() {
    if (photos.length > 0) {
        currentIndex = (currentIndex + 1) % photos.length;
        await updatePhoto();
    }
}

function updateTransform() {
    const img = document.getElementById('photo');
    const isHoriz = (rotationAngle % 180 === 0);
    const scaleFactor = isHoriz ? 1 : img.naturalWidth / img.naturalHeight ;
    img.style.transform = `rotate(${rotationAngle}deg) scale(${scaleFactor})`;
}

function rotateLeft() {
    rotationAngle -= 90;
    updateTransform();
}

function rotateRight() {
    rotationAngle += 90;
    updateTransform();
}


async function updateMetadata() {
    if (photos.length > 0) {
        const selectedDate = document.getElementById('date-picker').value;
        if (!selectedDate) {
            alert("Please select a date.");
            return;
        }
        const formattedDate = selectedDate.replace(/-/g, ":");

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
                await getCurrentPhotoDate();
                const autoProgress = document.getElementById('auto-progress').checked;
                if (autoProgress) {
                    await nextPhoto();
                }
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
