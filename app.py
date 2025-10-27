import os
import time
import logging
from datetime import timedelta, datetime
from flask import Flask, render_template, request, jsonify, session, send_file
from apscheduler.schedulers.background import BackgroundScheduler

from utils import scanner, file_manager

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit
app.config['UPLOAD_FOLDER'] = '/tmp/antivirusw_uploads/'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

# Configure logging
logging.basicConfig(
    filename='antivirusw.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Ensure upload directory exists
file_manager.ensure_upload_dir()

# Initialize background cleanup scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=file_manager.cleanup_old_files,
    trigger='interval',
    minutes=10
)
scheduler.start()


@app.route('/')
def index():
    """Serve main application page."""
    if 'sid' not in session:
        session['sid'] = os.urandom(16).hex()
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    """Handle file upload and scanning."""
    try:
        # Check if file exists in request
        if 'file' not in request.files:
            logging.warning("Upload attempt with no file")
            return jsonify({
                'status': 'error',
                'error': 'no_file',
                'message': 'Please select a file to upload'
            }), 400

        file = request.files['file']

        if file.filename == '':
            logging.warning("Upload attempt with empty filename")
            return jsonify({
                'status': 'error',
                'error': 'no_file',
                'message': 'Please select a file to upload'
            }), 400

        # Get session ID
        session_id = session.get('sid', os.urandom(16).hex())
        session['sid'] = session_id

        # Record scan start time
        scan_start = time.time()

        # Save file
        file_path = file_manager.save_uploaded_file(file, session_id)
        logging.info(f"File uploaded: {file.filename} (session: {session_id})")

        # Get file information
        file_info = file_manager.get_file_info(file_path)

        # Calculate file hashes
        hashes = file_manager.calculate_file_hash(file_path)

        # Scan file
        scan_result = scanner.scan_file(file_path)

        # Calculate scan duration
        scan_duration = time.time() - scan_start

        # Store file info in session
        session['file_path'] = file_path
        session['filename'] = file.filename
        session['scan_status'] = scan_result['status']

        # Handle different scan results
        if scan_result['status'] == 'service_unavailable':
            logging.error(f"ClamAV unavailable for file: {file.filename}")
            return jsonify({
                'status': 'error',
                'error': 'service_unavailable',
                'message': 'Scanning service is currently unavailable. Please try again later.'
            }), 503

        elif scan_result['status'] == 'error':
            logging.error(f"Scan error for file: {file.filename}")
            return jsonify({
                'status': 'error',
                'error': 'scan_failed',
                'message': 'Unable to scan this file. The file may be corrupted or in an unsupported format.'
            }), 500

        elif scan_result['status'] == 'clean':
            logging.info(f"File clean: {file.filename}")
            return jsonify({
                'status': 'clean',
                'filename': file.filename,
                'filesize': file_info['size'],
                'filesize_human': file_info['size_human'],
                'scan_time': round(scan_duration, 2),
                'scan_timestamp': datetime.now().isoformat(),
                'file_type': file_info['mime_type'],
                'md5': hashes['md5'],
                'sha256': hashes['sha256'],
                'clamav_version': scan_result['clamav_version'],
                'db_version': scan_result['db_version']
            })

        elif scan_result['status'] == 'infected':
            threat_name = scan_result['threat_name']

            # Parse threat type from threat name
            threat_type = parse_threat_type(threat_name)

            logging.warning(f"Threat detected in {file.filename}: {threat_name}")

            return jsonify({
                'status': 'infected',
                'filename': file.filename,
                'filesize': file_info['size'],
                'filesize_human': file_info['size_human'],
                'threat_name': threat_name,
                'threat_type': threat_type,
                'risk_level': 'High',
                'scan_time': round(scan_duration, 2),
                'scan_timestamp': datetime.now().isoformat(),
                'file_type': file_info['mime_type'],
                'md5': hashes['md5'],
                'sha256': hashes['sha256'],
                'clamav_version': scan_result['clamav_version'],
                'db_version': scan_result['db_version'],
                'file_path': file_path
            })

    except Exception as e:
        logging.error(f"Upload error: {e}")
        return jsonify({
            'status': 'error',
            'error': 'server_error',
            'message': 'An error occurred during upload. Please try again.'
        }), 500


@app.route('/delete', methods=['POST'])
def delete():
    """Delete scanned file from temp storage."""
    try:
        file_path = session.get('file_path')

        if not file_path:
            return jsonify({
                'status': 'error',
                'message': 'File not found or already deleted'
            }), 404

        # Delete file
        if file_manager.delete_file(file_path):
            logging.info(f"File deleted: {file_path}")

            # Clear session data
            session.pop('file_path', None)
            session.pop('filename', None)
            session.pop('scan_status', None)

            return jsonify({
                'status': 'success',
                'message': 'File deleted successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'File not found or already deleted'
            }), 404

    except Exception as e:
        logging.error(f"Delete error: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Error deleting file'
        }), 500


@app.route('/download')
def download():
    """Download clean scanned file."""
    try:
        file_path = session.get('file_path')
        filename = session.get('filename')
        scan_status = session.get('scan_status')

        if not file_path or not os.path.exists(file_path):
            return jsonify({
                'status': 'error',
                'message': 'File not found'
            }), 404

        if scan_status != 'clean':
            return jsonify({
                'status': 'error',
                'message': 'Cannot download infected file'
            }), 403

        logging.info(f"File downloaded: {filename}")
        return send_file(file_path, as_attachment=True, download_name=filename)

    except Exception as e:
        logging.error(f"Download error: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Error downloading file'
        }), 500


def parse_threat_type(threat_name):
    """
    Extract threat type from ClamAV threat name.

    Args:
        threat_name: Full threat name from ClamAV

    Returns:
        Threat type string
    """
    if not threat_name:
        return 'Malware'

    threat_name_lower = threat_name.lower()

    if 'trojan' in threat_name_lower:
        return 'Trojan'
    elif 'virus' in threat_name_lower:
        return 'Virus'
    elif 'worm' in threat_name_lower:
        return 'Worm'
    elif 'adware' in threat_name_lower:
        return 'Adware'
    elif 'spyware' in threat_name_lower:
        return 'Spyware'
    elif 'eicar' in threat_name_lower:
        return 'Test'
    else:
        return 'Malware'


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
