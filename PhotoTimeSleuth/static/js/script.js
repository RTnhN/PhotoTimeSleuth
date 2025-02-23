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




// Generate dates from 2000 to 2025
const startDate = new Date('2000-01-01');
const endDate = new Date('2025-12-31');
const dates = [];
const probabilities = [];

// Function to calculate Gaussian probability for short-term events (SD < 180 days)
function shortTermGaussian(date, centerDate, sigma) {
    const msPerDay = 1000 * 60 * 60 * 24;
    const daysDiff = (date - centerDate) / msPerDay;
    const wrappedDaysDiff = Math.min(
        Math.abs(daysDiff),
        Math.abs(daysDiff + 365),
        Math.abs(daysDiff - 365)
    );
    return Math.exp(-0.5 * Math.pow(wrappedDaysDiff / sigma, 2));
}

// Function to calculate Gaussian probability for long-term events (SD >= 180 days)
function longTermGaussian(date, centerDate, sigma) {
    const msPerDay = 1000 * 60 * 60 * 24;
    const daysDiff = (date - centerDate) / msPerDay;
    return Math.exp(-0.5 * Math.pow(daysDiff / sigma, 2));
}

let totalProbability = 0;
let maxProbability = 0;
let maxLikelihoodDate = null;

for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
    const christmas = new Date(d.getFullYear(), 11, 25); // Dec 25 of current year
    const october15 = new Date(2001, 9, 15); // Fixed Oct 15, 2001

    const christmasProbability = shortTermGaussian(d, christmas, 14); // 2 weeks SD
    const october15Probability = longTermGaussian(d, october15, 200); // 200 days SD

    // Combine probabilities
    const combinedProbability = christmasProbability * october15Probability;

    if (combinedProbability > 0.01) { // Only plot significant probabilities
        dates.push(d.toISOString().split('T')[0]);
        probabilities.push(combinedProbability);
        totalProbability += combinedProbability;

        // Track maximum likelihood date
        if (combinedProbability > maxProbability) {
            maxProbability = combinedProbability;
            maxLikelihoodDate = new Date(d);
        }
    }
}

// Normalize probabilities to sum to 1
const normalizedProbabilities = probabilities;

// Display maximum likelihood date
if (maxLikelihoodDate) {
    document.getElementById('maxLikelihood').innerText = `Date of Maximum Likelihood: ${maxLikelihoodDate.toISOString().split('T')[0]}`;
}

// Create the plot
const trace = {
    x: dates,
    y: normalizedProbabilities.map(p => p * 100),
    type: 'bar', // Bar chart instead of scatter
    name: 'Probability'
};

const layout = {
    height: 200,
    xaxis: {
        title: 'Date',
        type: 'date',
        fixedrange: false // Allow zooming only on x-axis
    },
    yaxis: {
        tickformat: '.0f%%', // Format y-axis with percentage
        fixedrange: true, // Prevent zooming on y-axis
        range: [0, 110],
        tickvals: [0, 25, 50, 75, 100], // Specific tick positions (in percentage)
        ticktext: ['0%', '25%', '50%', '75%', '100%'] // Labels for the ticks


    },
    margin: { l: 40, r: 20, t: 30, b: 40 },
    hovermode: 'closest'
};

Plotly.newPlot('plot', [trace], layout, {
    responsive: true,
    scrollZoom: true,
    displayModeBar: false // Remove toolbar
});

// script.js:194 The specified value "2001-12-25" does not conform to the required format.  The format is "yyyy-MM-ddThh:mm" followed by optional ":ss" or ":ss.SSS".
function updateDateFromMaxLikelihood() {
    if (maxLikelihoodDate) {
        let formattedDate = maxLikelihoodDate
            .toISOString()
            .slice(0, 16);

        document.getElementById('date-picker').value = formattedDate;
    }
}