// ============================================
// GLOBAL VARIABLES
// ============================================

const API_BASE = '/api';
let currentImageFile = null;
let drawingCanvas = null;
let canvasCtx = null;
let isDrawing = false;
let lastX = 0;
let lastY = 0;

// ============================================
// LOGOUT FUNCTION
// ============================================

function logoutFunc() {
    localStorage.removeItem('isLoggedIn');
    localStorage.removeItem('user');
    window.location.href = '/login';
}

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    // IMPORTANT: Hide the spinner immediately on page load
    const loadingSpinner = document.getElementById('loadingSpinner');
    if (loadingSpinner) {
        loadingSpinner.classList.add('hidden');
    }
    
    // Hide results section on load
    const resultsSection = document.getElementById('resultsSection');
    if (resultsSection) {
        resultsSection.classList.add('hidden');
    }
    
    initializeEventListeners();
    setupDrawingCanvas();
    
    // Delay status checks to avoid startup issues
    setTimeout(() => {
        checkServerStatus();
        loadModelInfo();
    }, 500);
});

function initializeEventListeners() {
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');

    // File input
    fileInput.addEventListener('change', handleFileSelect);

    // Drag and drop
    uploadZone.addEventListener('dragover', handleDragOver);
    uploadZone.addEventListener('dragleave', handleDragLeave);
    uploadZone.addEventListener('drop', handleFileDrop);
}

// ============================================
// FILE UPLOAD HANDLERS
// ============================================

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        processFile(file);
    }
}

function handleDragOver(event) {
    event.preventDefault();
    event.stopPropagation();
    document.getElementById('uploadZone').classList.add('active');
}

function handleDragLeave(event) {
    event.preventDefault();
    event.stopPropagation();
    document.getElementById('uploadZone').classList.remove('active');
}

function handleFileDrop(event) {
    event.preventDefault();
    event.stopPropagation();
    document.getElementById('uploadZone').classList.remove('active');

    const files = event.dataTransfer.files;
    if (files.length > 0) {
        processFile(files[0]);
    }
}

function processFile(file) {
    // Validate file type
    const allowedTypes = ['image/png', 'image/jpeg', 'image/gif', 'image/bmp'];
    if (!allowedTypes.includes(file.type)) {
        showStatus('Invalid file type. Please upload an image.', 'error');
        return;
    }

    // Validate file size
    const maxSize = 16 * 1024 * 1024; // 16MB
    if (file.size > maxSize) {
        showStatus('File size too large. Max 16MB allowed.', 'error');
        return;
    }

    currentImageFile = file;

    // Display preview
    const reader = new FileReader();
    reader.onload = function(e) {
        displayPreview(e.target.result);
        showStatus(`Image loaded: ${file.name}`, 'info');
    };
    reader.readAsDataURL(file);
}

function displayPreview(imageSrc) {
    const previewSection = document.getElementById('previewSection');
    const previewImage = document.getElementById('previewImage');

    previewImage.src = imageSrc;
    previewSection.classList.remove('hidden');
}

function clearPreview() {
    currentImageFile = null;
    document.getElementById('previewSection').classList.add('hidden');
    document.getElementById('fileInput').value = '';
    showStatus('', 'info');
}

// ============================================
// DRAWING CANVAS
// ============================================

function setupDrawingCanvas() {
    drawingCanvas = document.getElementById('drawingCanvas');
    canvasCtx = drawingCanvas.getContext('2d');

    // Set canvas size
    const rect = drawingCanvas.getBoundingClientRect();
    drawingCanvas.width = rect.width;
    drawingCanvas.height = rect.height;

    // Set background - dark gray
    canvasCtx.fillStyle = 'rgba(0, 0, 0, 0.5)';
    canvasCtx.fillRect(0, 0, drawingCanvas.width, drawingCanvas.height);

    // Event listeners
    drawingCanvas.addEventListener('mousedown', startDrawing);
    drawingCanvas.addEventListener('mousemove', draw);
    drawingCanvas.addEventListener('mouseup', stopDrawing);
    drawingCanvas.addEventListener('mouseout', stopDrawing);

    // Touch support
    drawingCanvas.addEventListener('touchstart', handleTouchStart);
    drawingCanvas.addEventListener('touchmove', handleTouchMove);
    drawingCanvas.addEventListener('touchend', stopDrawing);
    
    // Ensure currentImageFile is null on init
    currentImageFile = null;
}

function startDrawing(e) {
    isDrawing = true;
    const rect = drawingCanvas.getBoundingClientRect();
    lastX = e.clientX - rect.left;
    lastY = e.clientY - rect.top;
}

function draw(e) {
    if (!isDrawing) return;

    const rect = drawingCanvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    canvasCtx.strokeStyle = '#ffffff';
    canvasCtx.lineWidth = 3;
    canvasCtx.lineCap = 'round';
    canvasCtx.lineJoin = 'round';

    canvasCtx.beginPath();
    canvasCtx.moveTo(lastX, lastY);
    canvasCtx.lineTo(x, y);
    canvasCtx.stroke();

    lastX = x;
    lastY = y;

    // Update currentImageFile with canvas content
    currentImageFile = 'canvas';
}

function stopDrawing() {
    isDrawing = false;
}

function handleTouchStart(e) {
    const touch = e.touches[0];
    const mouseEvent = new MouseEvent('mousedown', {
        clientX: touch.clientX,
        clientY: touch.clientY
    });
    drawingCanvas.dispatchEvent(mouseEvent);
}

function handleTouchMove(e) {
    e.preventDefault();
    const touch = e.touches[0];
    const mouseEvent = new MouseEvent('mousemove', {
        clientX: touch.clientX,
        clientY: touch.clientY
    });
    drawingCanvas.dispatchEvent(mouseEvent);
}

function clearCanvas() {
    canvasCtx.fillStyle = 'rgba(0, 0, 0, 0.5)';
    canvasCtx.fillRect(0, 0, drawingCanvas.width, drawingCanvas.height);
    currentImageFile = null;
    showStatus('Canvas cleared', 'info');
}

function undoCanvas() {
    // Simple undo - clear the canvas
    clearCanvas();
}

// ============================================
// PREDICTION
// ============================================

async function predict() {
    // First, ensure spinner is hidden - we'll only show it if we proceed
    const loadingSpinner = document.getElementById('loadingSpinner');
    if (loadingSpinner) {
        loadingSpinner.classList.add('hidden');
    }
    
    // Check if user has input
    const fileInput = document.getElementById('fileInput');
    const hasFile = fileInput.files && fileInput.files.length > 0;
    const hasCanvas = !isCanvasEmpty(drawingCanvas);
    
    if (!hasFile && !hasCanvas) {
        showStatus('Please upload an image or draw on the canvas', 'error');
        return;
    }

    // Now we proceed - show spinner
    const predictBtn = document.getElementById('predictBtn');
    const resultsSection = document.getElementById('resultsSection');

    if (loadingSpinner) {
        loadingSpinner.classList.remove('hidden');
    }
    
    resultsSection.classList.add('hidden');
    predictBtn.disabled = true;
    showStatus('', 'info');

    try {
        let result;

        if (hasFile) {
            // Predict from uploaded file
            result = await predictFromFile(fileInput.files[0]);
        } else if (hasCanvas) {
            // Predict from canvas
            const imageData = drawingCanvas.toDataURL('image/png');
            result = await predictFromBase64(imageData);
        }

        if (result && result.success) {
            displayResults(result);
            showStatus('✓ Prediction successful!', 'success');
        } else {
            showStatus(result?.error || '✗ Prediction failed', 'error');
        }
    } catch (error) {
        showStatus(`✗ Error: ${error.message}`, 'error');
        console.error('Prediction error:', error);
    } finally {
        predictBtn.disabled = false;
        loadingSpinner.classList.add('hidden');
    }
}

async function predictFromFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE}/predict`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || `HTTP ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('File prediction error:', error);
        throw error;
    }
}

async function predictFromBase64(imageData) {
    try {
        const response = await fetch(`${API_BASE}/predict-base64`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ image: imageData })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || `HTTP ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Base64 prediction error:', error);
        throw error;
    }
}

function displayResults(result) {
    // Show results section
    const resultsSection = document.getElementById('resultsSection');

    // Update prediction result
    const predictionNumber = document.getElementById('predictionNumber');
    const confidenceValue = document.getElementById('confidenceValue');
    
    if (predictionNumber && confidenceValue) {
        predictionNumber.textContent = result.prediction || 0;
        confidenceValue.textContent = `${result.confidence || 0}%`;
    }

    // Update progress bar
    const progressFill = document.getElementById('progressFill');
    if (progressFill) {
        progressFill.style.width = `${result.confidence || 0}%`;
    }

    // Update probability chart
    if (result.all_probabilities) {
        displayProbabilityChart(result.all_probabilities);
    }

    // Show results section
    resultsSection.classList.remove('hidden');

    // Scroll to results
    setTimeout(() => {
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 100);
}

function displayProbabilityChart(probabilities) {
    const chartContainer = document.getElementById('probabilityChart');
    chartContainer.innerHTML = '';

    probabilities.forEach((prob, index) => {
        const percentage = (prob * 100).toFixed(1);
        const barHtml = `
            <div class="probability-bar">
                <div class="probability-label">${index}</div>
                <div class="probability-bar-inner">
                    <div class="probability-bar-fill" style="width: ${percentage}%"></div>
                </div>
                <div class="probability-value">${percentage}%</div>
            </div>
        `;
        chartContainer.innerHTML += barHtml;
    });
}

function toggleDetails() {
    const detailsContent = document.getElementById('detailsContent');
    detailsContent.classList.toggle('hidden');

    if (!detailsContent.classList.contains('hidden')) {
        const prediction = document.getElementById('predictionNumber').textContent;
        const confidence = document.getElementById('confidenceValue').textContent;
        const detailsJson = {
            prediction: parseInt(prediction),
            confidence: confidence,
            timestamp: new Date().toISOString()
        };
        document.getElementById('detailsJson').textContent = JSON.stringify(detailsJson, null, 2);
    }
}

// ============================================
// SERVER STATUS
// ============================================

async function checkServerStatus() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        if (!response.ok) throw new Error('Health check failed');
        
        const data = await response.json();
        const statusIndicator = document.getElementById('statusIndicator');
        const statusText = document.getElementById('statusText');

        if (data.status === 'healthy' && data.model_loaded) {
            statusIndicator.classList.add('online');
            statusText.textContent = 'Active';
        } else if (data.status === 'healthy') {
            statusIndicator.classList.add('online');
            statusText.textContent = 'Ready';
        } else {
            statusIndicator.classList.remove('online');
            statusText.textContent = 'Offline';
        }
    } catch (error) {
        console.log('Status check failed (will retry)');
        const statusText = document.getElementById('statusText');
        if (statusText) statusText.textContent = 'Connecting...';
    }
}

// ============================================
// MODEL INFO
// ============================================

async function loadModelInfo() {
    try {
        const response = await fetch(`${API_BASE}/info`);
        const data = await response.json();

        const infoContent = document.getElementById('modelInfo');
        infoContent.innerHTML = `
            <p><strong>Model:</strong> ${data.model}</p>
            <p><strong>Classes:</strong> ${data.classes.length} classes (0-${data.classes.length - 1})</p>
            <p><strong>Input Size:</strong> ${data.input_size.join(' × ')}</p>
            <p><strong>Framework:</strong> ${data.framework}</p>
            <p><strong>Status:</strong> <span style="color: #10b981;">Ready</span></p>
        `;
    } catch (error) {
        console.error('Failed to load model info:', error);
    }
}

// ============================================
// STATUS MESSAGES
// ============================================

function showStatus(message, type = 'info') {
    const statusElement = document.getElementById('uploadStatus');
    statusElement.textContent = message;
    statusElement.className = `status-message ${type}`;

    if (type === 'success' || type === 'error') {
        setTimeout(() => {
            statusElement.textContent = '';
            statusElement.className = 'status-message';
        }, 5000);
    }
}

// ============================================
// UTILITY FUNCTIONS
// ============================================

function isCanvasEmpty(canvas) {
    const ctx = canvas.getContext('2d');
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const data = imageData.data;
    
    // Check if all pixels are the background color (black with 50% alpha)
    // or if there's any drawing (non-background pixels)
    for (let i = 3; i < data.length; i += 4) {
        // Check alpha channel - if not semi-transparent, there's drawing
        if (data[i] > 200) {
            return false; // Has drawing
        }
    }
    return true; // Empty
}

function isImageLoaded() {
    const previewImage = document.getElementById('previewImage');
    return previewImage.src !== '' && currentImageFile !== null;
}

// Refresh server status periodically
setInterval(checkServerStatus, 30000);
