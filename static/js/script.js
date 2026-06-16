// ============================================
// GLOBAL VARIABLES
// ============================================

const API_BASE = '/api';
let currentMatrixData = null;
let currentMode = 'manual'; // manual, csv, sample
let csvData = null;

// ============================================
// AUTHENTICATION
// ============================================

async function checkUserAuthentication() {
    try {
        const response = await fetch(`${API_BASE}/auth/check`);
        const data = await response.json();
        
        if (!data.authenticated) {
            // Not logged in - redirect to login
            window.location.href = '/login';
            return false;
        }
        
        // Display username if available
        const userInfo = document.getElementById('userInfo');
        if (userInfo && data.username) {
            userInfo.textContent = data.username;
        }
        
        return true;
    } catch (error) {
        console.error('Auth check error:', error);
        // Assume not authenticated if check fails
        return true; // Allow to continue for now
    }
}

// ============================================
// LOGOUT FUNCTION
// ============================================

async function logoutFunc() {
    try {
        const response = await fetch(`${API_BASE}/auth/logout`, {
            method: 'POST'
        });
        
        if (response.ok) {
            localStorage.removeItem('user');
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('Logout error:', error);
        localStorage.removeItem('user');
        window.location.href = '/login';
    }
}

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', async function() {
    // Check authentication first
    await checkUserAuthentication();
    
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
    
    // Delay status checks to avoid startup issues
    setTimeout(() => {
        checkServerStatus();
        loadModelInfo();
    }, 500);
});

function initializeEventListeners() {
    // CSV upload
    const csvUploadZone = document.getElementById('csvUploadZone');
    const csvFile = document.getElementById('csvFile');
    
    if (csvFile) {
        csvFile.addEventListener('change', handleCSVSelect);
    }
    
    if (csvUploadZone) {
        csvUploadZone.addEventListener('dragover', handleDragOver);
        csvUploadZone.addEventListener('dragleave', handleDragLeave);
        csvUploadZone.addEventListener('drop', handleCSVDrop);
    }
}

// ============================================
// TAB SWITCHING
// ============================================

function switchTab(tabName) {
    // Hide all tab contents
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => tab.classList.remove('active'));
    
    // Remove active class from all buttons
    const buttons = document.querySelectorAll('.tab-btn');
    buttons.forEach(btn => btn.classList.remove('active'));
    
    // Show selected tab
    const selectedTab = document.getElementById(`${tabName}-tab`);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }
    
    // Add active class to clicked button
    event.target.classList.add('active');
    currentMode = tabName;
}

// ============================================
// CSV HANDLING
// ============================================

function handleCSVSelect(event) {
    const file = event.target.files[0];
    if (file) {
        parseCSVFile(file);
    }
}

function handleDragOver(event) {
    event.preventDefault();
    event.stopPropagation();
    document.getElementById('csvUploadZone').classList.add('active');
}

function handleDragLeave(event) {
    event.preventDefault();
    event.stopPropagation();
    document.getElementById('csvUploadZone').classList.remove('active');
}

function handleCSVDrop(event) {
    event.preventDefault();
    event.stopPropagation();
    document.getElementById('csvUploadZone').classList.remove('active');
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
        parseCSVFile(files[0]);
    }
}

function parseCSVFile(file) {
    const reader = new FileReader();
    reader.onload = function(e) {
        const csv = e.target.result;
        const rows = csv.trim().split('\n');
        const data = [];
        
        for (const row of rows) {
            if (row.trim()) {
                const values = row.split(/[,\s]+/).map(v => parseFloat(v)).filter(v => !isNaN(v));
                if (values.length > 0) {
                    data.push(values);
                }
            }
        }
        
        if (data.length === 0) {
            showStatus('No valid numerical data in CSV', 'error');
            return;
        }
        
        csvData = data;
        
        // Show preview
        const preview = document.getElementById('csvPreview');
        const content = document.getElementById('csvContent');
        content.innerHTML = `
            <p><strong>Rows:</strong> ${data.length}</p>
            <p><strong>Columns:</strong> ${data[0].length}</p>
            <p><strong>First row:</strong> ${data[0].slice(0, 5).map(v => v.toFixed(3)).join(', ')}...</p>
        `;
        preview.classList.remove('hidden');
        
        showStatus(`CSV loaded: ${data.length} samples`, 'success');
    };
    reader.readAsText(file);
}

function clearCSV() {
    csvData = null;
    document.getElementById('csvFile').value = '';
    document.getElementById('csvPreview').classList.add('hidden');
    showStatus('CSV cleared', 'info');
}

// ============================================
// SAMPLE DATA GENERATION
// ============================================

function loadSampleData(type) {
    const size = 2097;
    let samples = [];
    
    switch(type) {
        case 'random':
            samples = [[...Array(size)].map(() => Math.random())];
            break;
        case 'batch':
            samples = Array(5).fill(0).map(() => [...Array(size)].map(() => Math.random()));
            break;
        case 'normalized':
            samples = [[...Array(size)].map(() => Math.random() * 0.5 + 0.25)];
            break;
    }
    
    // Fill matrix input
    const matrixInput = document.getElementById('matrixInput');
    if (matrixInput) {
        matrixInput.value = samples.map(s => s.join(' ')).join('\n');
    }
    
    showStatus(`Sample data loaded: ${samples.length} samples`, 'success');
    switchTab('manual');
}

// ============================================
// PREDICTION
// ============================================

async function predict() {
    // First, ensure spinner is hidden when function starts
    const loadingSpinner = document.getElementById('loadingSpinner');
    if (loadingSpinner) {
        loadingSpinner.classList.add('hidden');
    }
    
    const resultsSection = document.getElementById('resultsSection');
    if (resultsSection) {
        resultsSection.classList.add('hidden');
    }
    
    // Gather data based on current mode
    let matrixData = null;
    
    if (currentMode === 'manual') {
        matrixData = parseMatrixInput();
    } else if (currentMode === 'csv' && csvData) {
        matrixData = csvData;
    } else {
        showStatus('Please enter or upload data first', 'error');
        return;
    }
    
    if (!matrixData || matrixData.length === 0) {
        showStatus('Invalid data format', 'error');
        return;
    }
    
    // Show spinner and disable button
    const predictBtn = document.getElementById('predictBtn');
    if (loadingSpinner) {
        loadingSpinner.classList.remove('hidden');
    }
    
    predictBtn.disabled = true;
    showStatus('', 'info');
    
    try {
        if (currentMode === 'csv' && csvData && csvData.length > 1) {
            // Batch prediction
            await predictBatch(csvData);
        } else {
            // Single prediction
            await predictSingle(matrixData[0]);
        }
    } catch (error) {
        showStatus(`Error: ${error.message}`, 'error');
        console.error('Prediction error:', error);
    } finally {
        predictBtn.disabled = false;
        if (loadingSpinner) {
            loadingSpinner.classList.add('hidden');
        }
    }
}

function parseMatrixInput() {
    const input = document.getElementById('matrixInput').value.trim();
    if (!input) return null;
    
    const rows = input.split('\n');
    const matrix = [];
    
    for (const row of rows) {
        if (row.trim()) {
            const values = row.split(/[,\s]+/).map(v => parseFloat(v)).filter(v => !isNaN(v));
            if (values.length > 0) {
                matrix.push(values);
            }
        }
    }
    
    return matrix.length > 0 ? matrix : null;
}

async function predictSingle(matrixRow) {
    try {
        const response = await fetch(`${API_BASE}/predict`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ matrix: [matrixRow] })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || `HTTP ${response.status}`);
        }
        
        const result = await response.json();
        displayResults(result);
        showStatus('Analysis complete!', 'success');
    } catch (error) {
        throw error;
    }
}

async function predictBatch(matrixData) {
    try {
        const response = await fetch(`${API_BASE}/predict-csv`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ matrix: matrixData })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || `HTTP ${response.status}`);
        }
        
        const result = await response.json();
        displayBatchResults(result);
        showStatus('Batch analysis complete!', 'success');
    } catch (error) {
        throw error;
    }
}

// ============================================
// DISPLAY RESULTS
// ============================================

function displayResults(result) {
    const resultsSection = document.getElementById('resultsSection');
    
    // Update detection result
    const detectionClass = document.getElementById('detectionClass');
    const detectionConfidence = document.getElementById('detectionConfidence');
    const resultStatus = document.getElementById('resultStatus');
    
    if (detectionClass && detectionConfidence) {
        detectionClass.textContent = result.class_name || 'Unknown';
        detectionConfidence.textContent = `Confidence: ${result.confidence || 0}%`;
        
        // Update status icon based on prediction
        if (result.prediction === 1) {
            resultStatus.style.borderLeft = '4px solid #dc2626';
            resultStatus.querySelector('.status-icon').textContent = '⚠️';
        } else {
            resultStatus.style.borderLeft = '4px solid #10b981';
            resultStatus.querySelector('.status-icon').textContent = '✓';
        }
    }
    
    // Update progress bar
    const progressFill = document.getElementById('progressFill');
    if (progressFill) {
        progressFill.style.width = `${result.confidence || 0}%`;
    }
    
    // Update probability chart
    if (result.all_probabilities && result.class_names) {
        displayProbabilityChart(result.all_probabilities, result.class_names);
    }
    
    // Show results section
    resultsSection.classList.remove('hidden');
    
    // Scroll to results
    setTimeout(() => {
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 100);
}

function displayBatchResults(result) {
    const resultsSection = document.getElementById('resultsSection');
    const batchResultsSection = document.getElementById('batchResultsSection');
    const batchResultsTable = document.getElementById('batchResultsTable');
    
    if (!batchResultsTable) return;
    
    // Create table
    let html = '<table class="results-table-content"><thead><tr><th>Sample</th><th>Result</th><th>Confidence</th></tr></thead><tbody>';
    
    for (const res of result.results) {
        const classIcon = res.prediction === 1 ? '⚠️' : '✓';
        html += `<tr>
            <td>${res.row}</td>
            <td>${classIcon} ${res.class_name}</td>
            <td>${res.confidence}%</td>
        </tr>`;
    }
    
    html += '</tbody></table>';
    batchResultsTable.innerHTML = html;
    batchResultsSection.classList.remove('hidden');
    
    // Show results
    resultsSection.classList.remove('hidden');
    setTimeout(() => {
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 100);
}

function displayProbabilityChart(probabilities, classNames) {
    const chartContainer = document.getElementById('probabilityChart');
    chartContainer.innerHTML = '';
    
    probabilities.forEach((prob, index) => {
        const percentage = (prob * 100).toFixed(1);
        const className = classNames && classNames[index] ? classNames[index] : `Class ${index}`;
        const barHtml = `
            <div class="probability-bar">
                <div class="probability-label">${className}</div>
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
            <p><strong>Type:</strong> ${data.type}</p>
            <p><strong>Classes:</strong> ${data.classes.join(', ')}</p>
            <p><strong>Input Size:</strong> ${data.input_size} features</p>
            <p><strong>Task:</strong> ${data.task}</p>
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

// Refresh server status periodically
setInterval(checkServerStatus, 30000);
