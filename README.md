# Antivirus File Scanner

A web-based antivirus file scanner that allows users to upload files, scan them for malicious content using ClamAV, and manage detected threats with an intuitive, modern UI.

## Features

- **Drag-and-Drop Upload**: Easily upload files by dragging them into the browser or using the browse button
- **Virus Scanning**: Industry-standard ClamAV engine scans files for malware, viruses, trojans, and other threats
- **Detailed Reports**: View comprehensive scan reports including file hashes, threat names, and scan metadata
- **File Management**: Delete infected files directly from the web interface
- **Clean UI**: Modern, responsive design that works on desktop, tablet, and mobile devices
- **Automatic Cleanup**: Background job automatically removes old files from temporary storage
- **Session-Based**: Each user session maintains its own isolated file storage

## Technology Stack

- **Backend**: Flask (Python 3)
- **Scanning Engine**: ClamAV with pyClamd
- **Frontend**: HTML5, CSS3, JavaScript (vanilla)
- **Scheduler**: APScheduler for background cleanup tasks

## Prerequisites

Before running the application, ensure you have the following installed:

1. **Python 3.7+**
2. **ClamAV** with `clamd` daemon running
3. **Fresh virus definitions** (updated via `freshclam`)

### Installing ClamAV

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install clamav clamav-daemon
sudo systemctl start clamav-daemon
sudo systemctl enable clamav-daemon
sudo freshclam
```

**macOS:**
```bash
brew install clamav
cp /usr/local/etc/clamav/clamd.conf.sample /usr/local/etc/clamav/clamd.conf
# Edit clamd.conf and comment out "Example" line
freshclam
clamd
```

**Verify ClamAV is running:**
```bash
sudo systemctl status clamav-daemon  # Linux
# or check process: ps aux | grep clamd
```

## Installation

1. **Clone or navigate to the repository:**
```bash
cd antivirusw
```

2. **Create a virtual environment (recommended):**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

## Running the Application

1. **Ensure ClamAV daemon is running** (see prerequisites above)

2. **Start the Flask application:**
```bash
python app.py
```

3. **Open your browser and navigate to:**
```
http://localhost:5000
```

## Usage

1. **Upload a File**:
   - Drag and drop a file onto the upload zone, or click "Browse Files" to select a file
   - Maximum file size: 100MB
   - All file types are supported

2. **View Scan Results**:
   - **Clean Files**: Shows a green success message with file details and a download option
   - **Infected Files**: Shows a red alert with threat information and action buttons (Delete, View Details, Scan Another)
   - **Errors**: Shows appropriate error messages with retry options

3. **Manage Infected Files**:
   - Click **Delete File** to permanently remove the infected file from temporary storage
   - Click **View Details** to see a comprehensive scan report including MD5/SHA256 hashes
   - Click **Scan Another** to return to the upload page

4. **Download Clean Files**:
   - For clean files, click the "Download File" link to retrieve your scanned file

## Configuration

Edit `app.py` to customize settings:

- **File Size Limit**: Change `MAX_CONTENT_LENGTH` (default: 100MB)
- **Session Timeout**: Modify `PERMANENT_SESSION_LIFETIME` (default: 30 minutes)
- **Cleanup Interval**: Adjust scheduler interval in `scheduler.add_job()` (default: 10 minutes)
- **Upload Directory**: Change `UPLOAD_FOLDER` path (default: `/tmp/antivirusw_uploads/`)

## File Cleanup

Files are automatically cleaned up in the following scenarios:

1. **Session Expiry**: Files are deleted when Flask session expires (30 minutes of inactivity)
2. **Manual Delete**: User clicks "Delete File" button
3. **New Upload**: Previous file is deleted when a new file is uploaded in the same session
4. **Background Job**: Files older than 1 hour are automatically deleted every 10 minutes

## Testing

### Test with EICAR File

To test virus detection without using actual malware, use the EICAR test file:

```bash
echo 'X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*' > eicar.txt
```

Upload this file to verify that ClamAV correctly detects it as a test virus.

### Manual Testing

Refer to the planning documentation for comprehensive manual testing procedures covering:
- Clean file upload
- Malicious file detection
- Drag-and-drop functionality
- File size validation
- Delete operations
- Download functionality
- Error handling
- Responsive design
- Session isolation

## Troubleshooting

### "Scanning service is currently unavailable"

**Cause**: ClamAV daemon is not running or not accessible

**Solution**:
```bash
# Check if clamd is running
sudo systemctl status clamav-daemon

# Start if not running
sudo systemctl start clamav-daemon

# Check socket location
ls -la /var/run/clamav/clamd.ctl
```

### "Unable to scan this file"

**Cause**: File may be corrupted or ClamAV encountered an error

**Solution**:
- Try a different file
- Check ClamAV logs: `sudo tail -f /var/log/clamav/clamav.log`
- Ensure virus definitions are updated: `sudo freshclam`

### Module Import Errors

**Cause**: Python dependencies not installed

**Solution**:
```bash
pip install -r requirements.txt
```

## Project Structure

```
antivirusw/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── antivirusw.log             # Application logs (created at runtime)
├── README.md                   # This file
├── .gitignore                  # Git ignore rules
├── templates/
│   └── index.html              # Single-page application UI
├── static/
│   ├── css/
│   │   └── style.css          # Application styling
│   └── js/
│       └── main.js             # Frontend JavaScript
└── utils/
    ├── __init__.py             # Python package marker
    ├── scanner.py              # ClamAV integration
    └── file_manager.py         # File operations
```

## Security Considerations

- Files are stored in temporary storage with unique session-based filenames
- Infected files are never executed or opened by the application
- All file uploads are validated for size on both client and server side
- Session IDs prevent file access across different user sessions
- Automatic cleanup prevents accumulation of old/orphaned files
- Flask's secure_filename() prevents directory traversal attacks

## Limitations

- Single file upload at a time (not batch upload)
- Requires ClamAV to be installed and running on the same system
- Scanning performance depends on ClamAV configuration and file size
- No user authentication (single-user or trusted environment)
- Temporary storage only (files not persisted long-term)

## License

This project is provided as-is for educational and practical use.

## Contributing

Contributions are welcome! Please ensure any changes maintain the security and simplicity of the application.