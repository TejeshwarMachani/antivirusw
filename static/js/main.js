// DOM Elements
const uploadView = document.getElementById('upload-view');
const scanningView = document.getElementById('scanning-view');
const resultsView = document.getElementById('results-view');
const dropZone = document.getElementById('drop-zone');
const browseBtn = document.getElementById('browse-btn');
const fileInput = document.getElementById('file-input');
const uploadError = document.getElementById('upload-error');
const detailsModal = document.getElementById('details-modal');
const closeModal = document.getElementById('close-modal');

// Stored scan result data
let currentScanResult = null;

// Initialize event listeners
function init() {
    // Browse button click
    browseBtn.addEventListener('click', () => {
        fileInput.click();
    });

    // File input change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });

    // Drag and drop events
    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('drag-over');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');

        if (e.dataTransfer.files.length > 0) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    });

    // Modal close events
    closeModal.addEventListener('click', () => {
        detailsModal.style.display = 'none';
    });

    detailsModal.addEventListener('click', (e) => {
        if (e.target === detailsModal) {
            detailsModal.style.display = 'none';
        }
    });
}

// Handle file selection
function handleFileSelect(file) {
    // Validate file size
    const maxSize = 100 * 1024 * 1024; // 100MB

    if (file.size > maxSize) {
        showError('File exceeds 100MB limit. Please select a smaller file.');
        return;
    }

    // Clear any previous errors
    hideError();

    // Upload the file
    uploadFile(file);
}

// Upload file to server
function uploadFile(file) {
    // Show scanning view
    showView('scanning-view');

    // Display file details
    document.getElementById('scanning-filename').textContent = file.name;
    document.getElementById('scanning-filesize').textContent = formatFileSize(file.size);

    // Start progress animation
    const progressFill = document.getElementById('progress-fill');
    progressFill.style.width = '0%';

    // Animate to 90% over 2 seconds
    setTimeout(() => {
        progressFill.style.width = '90%';
    }, 100);

    // Create form data
    const formData = new FormData();
    formData.append('file', file);

    // Upload and scan
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        // Complete progress bar
        progressFill.style.width = '100%';

        return response.json().then(data => ({
            status: response.status,
            data: data
        }));
    })
    .then(result => {
        // Wait a moment for visual feedback
        setTimeout(() => {
            currentScanResult = result.data;
            displayResults(result.data);
        }, 500);
    })
    .catch(error => {
        console.error('Upload error:', error);
        showError('Network error. Please check your connection and try again.');
        showView('upload-view');
    });
}

// Display scan results
function displayResults(result) {
    showView('results-view');

    const alertBox = document.getElementById('alert-box');
    const alertIcon = document.getElementById('alert-icon');
    const alertTitle = document.getElementById('alert-title');
    const alertMessage = document.getElementById('alert-message');
    const resultDetails = document.getElementById('result-details');
    const actionButtons = document.getElementById('action-buttons');

    // Clear previous content
    resultDetails.innerHTML = '';
    actionButtons.innerHTML = '';

    if (result.status === 'clean') {
        // Clean file
        alertBox.className = 'success';
        alertIcon.textContent = '✓';
        alertTitle.textContent = 'FILE IS CLEAN';
        alertMessage.textContent = 'No threats detected. Your file is safe.';

        // File details
        resultDetails.innerHTML = `
            <p><strong>File Name:</strong> ${result.filename}</p>
            <p><strong>File Size:</strong> ${result.filesize_human}</p>
            <p><strong>File Type:</strong> ${result.file_type}</p>
            <p><strong>Scan Time:</strong> ${result.scan_time} seconds</p>
            <p><strong>Status:</strong> Safe</p>
        `;

        // Action buttons
        actionButtons.innerHTML = `
            <a href="/download" class="download-link" style="width: 100%; margin-bottom: 15px;">Download File</a>
            <button class="btn-secondary" onclick="scanAnother()">Scan Another File</button>
        `;

    } else if (result.status === 'infected') {
        // Infected file
        alertBox.className = 'danger';
        alertIcon.textContent = '⚠️';
        alertTitle.textContent = 'THREAT DETECTED';
        alertMessage.textContent = 'Malicious content found in this file. Do not open or execute.';

        // File details with threat info
        resultDetails.innerHTML = `
            <p><strong>File Name:</strong> ${result.filename}</p>
            <p><strong>File Size:</strong> ${result.filesize_human}</p>
            <p><strong>Threat Name:</strong> ${result.threat_name}</p>
            <p><strong>Threat Type:</strong> ${result.threat_type}</p>
            <p><strong>Risk Level:</strong> ${result.risk_level}</p>
            <p><strong>Scan Time:</strong> ${result.scan_time} seconds</p>
        `;

        // Action buttons
        actionButtons.innerHTML = `
            <button class="btn-danger" onclick="deleteFile()">Delete File</button>
            <button class="btn-secondary" onclick="viewDetails()">View Details</button>
            <button class="btn-secondary" onclick="scanAnother()">Scan Another</button>
        `;

    } else if (result.status === 'error') {
        // Error
        alertBox.className = 'warning';
        alertIcon.textContent = '⚠️';
        alertTitle.textContent = 'Scan Error';
        alertMessage.textContent = result.message;

        // Action buttons
        actionButtons.innerHTML = `
            <button class="btn-secondary" onclick="scanAnother()">Try Again</button>
        `;
    }
}

// Delete file
function deleteFile() {
    fetch('/delete', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Show confirmation
            const alertBox = document.getElementById('alert-box');
            const alertTitle = document.getElementById('alert-title');
            const alertMessage = document.getElementById('alert-message');

            alertBox.className = 'success';
            alertTitle.textContent = 'File Deleted';
            alertMessage.textContent = data.message;

            // Clear action buttons
            document.getElementById('action-buttons').innerHTML = '';

            // Return to upload view after 2 seconds
            setTimeout(() => {
                resetApp();
            }, 2000);
        } else {
            alert('Error deleting file: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Delete error:', error);
        alert('Error deleting file. Please try again.');
    });
}

// View detailed scan report
function viewDetails() {
    if (!currentScanResult) {
        return;
    }

    const fullReport = document.getElementById('full-report');

    fullReport.innerHTML = `
        <p><strong>File Name:</strong> ${currentScanResult.filename}</p>
        <p><strong>File Size:</strong> ${currentScanResult.filesize_human} (${currentScanResult.filesize} bytes)</p>
        <p><strong>File Type:</strong> ${currentScanResult.file_type}</p>
        <p><strong>MD5 Hash:</strong> ${currentScanResult.md5}</p>
        <p><strong>SHA256 Hash:</strong> ${currentScanResult.sha256}</p>
        <p><strong>Scan Timestamp:</strong> ${currentScanResult.scan_timestamp}</p>
        <p><strong>Scan Duration:</strong> ${currentScanResult.scan_time} seconds</p>
        <p><strong>Threat Name:</strong> ${currentScanResult.threat_name}</p>
        <p><strong>Threat Type:</strong> ${currentScanResult.threat_type}</p>
        <p><strong>Risk Level:</strong> ${currentScanResult.risk_level}</p>
        <p><strong>ClamAV Version:</strong> ${currentScanResult.clamav_version}</p>
        <p><strong>Database Version:</strong> ${currentScanResult.db_version}</p>
    `;

    detailsModal.style.display = 'flex';
}

// Scan another file
function scanAnother() {
    resetApp();
}

// Show specific view
function showView(viewName) {
    uploadView.style.display = 'none';
    scanningView.style.display = 'none';
    resultsView.style.display = 'none';

    if (viewName === 'upload-view') {
        uploadView.style.display = 'block';
    } else if (viewName === 'scanning-view') {
        scanningView.style.display = 'block';
    } else if (viewName === 'results-view') {
        resultsView.style.display = 'block';
    }
}

// Show error message
function showError(message) {
    uploadError.textContent = message;
    uploadError.style.display = 'block';
}

// Hide error message
function hideError() {
    uploadError.style.display = 'none';
    uploadError.textContent = '';
}

// Reset app to initial state
function resetApp() {
    showView('upload-view');
    fileInput.value = '';
    hideError();
    currentScanResult = null;

    // Reset progress bar
    const progressFill = document.getElementById('progress-fill');
    progressFill.style.width = '0%';
}

// Format file size to human-readable format
function formatFileSize(bytes) {
    if (bytes < 1024) {
        return bytes + ' B';
    } else if (bytes < 1024 * 1024) {
        return (bytes / 1024).toFixed(1) + ' KB';
    } else {
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }
}

// Parse threat type from threat name
function parseThreatType(threatName) {
    if (!threatName) {
        return 'Malware';
    }

    const threatLower = threatName.toLowerCase();

    if (threatLower.includes('trojan')) {
        return 'Trojan';
    } else if (threatLower.includes('virus')) {
        return 'Virus';
    } else if (threatLower.includes('worm')) {
        return 'Worm';
    } else if (threatLower.includes('adware')) {
        return 'Adware';
    } else if (threatLower.includes('spyware')) {
        return 'Spyware';
    } else if (threatLower.includes('eicar')) {
        return 'Test';
    } else {
        return 'Malware';
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', init);
