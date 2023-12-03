const matrixRainContainer = document.getElementById('matrix-rain');
const columns = window.innerWidth / 10; // Adjust the '10' for wider/narrower columns
const drops = [];
const chars = []; // Array to store a consistent character for each column

// Initialize the drops array with starting y-positions and generate a random character for each column
for (let i = 0; i < columns; i++) {
    drops[i] = Math.floor(Math.random() * window.innerHeight / 10);
    chars[i] = Math.floor(Math.random() * 10);
}


function drawMatrixRain() {
    matrixRainContainer.innerHTML = ''; // Clear previous frame

    for (let i = 0; i < drops.length; i++) {
        const text = chars[i]; // Use the consistent character stored earlier
        const span = document.createElement('span');
        span.innerText = text;
        span.style.cssText = `position:absolute; top:${drops[i] * 10}px; left:${i * 10}px`;
        matrixRainContainer.appendChild(span);

        // Increment Y and reset at the bottom
        drops[i]++;
        if (drops[i] * 10 > window.innerHeight && Math.random() > 0.975) {
            drops[i] = 0;
        }
    }
}

// Call drawMatrixRain at intervals
setInterval(drawMatrixRain, 30); // Adjust the '30' for faster/slower rain
