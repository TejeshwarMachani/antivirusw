import os
import time
import hashlib
import mimetypes
from werkzeug.utils import secure_filename

UPLOAD_DIR = '/tmp/antivirusw_uploads/'


def ensure_upload_dir():
    """Create upload directory if it doesn't exist with proper permissions."""
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR, mode=0o700)
        print(f"Created upload directory: {UPLOAD_DIR}")


def save_uploaded_file(file, session_id):
    """
    Save uploaded file with unique name and delete previous session file.

    Args:
        file: werkzeug FileStorage object
        session_id: Session identifier string

    Returns:
        Full path to saved file
    """
    # Delete previous files for this session
    delete_session_files(session_id)

    # Generate unique filename
    timestamp = int(time.time() * 1000)  # Millisecond timestamp
    original_filename = secure_filename(file.filename)
    unique_filename = f"{session_id}_{timestamp}_{original_filename}"

    # Save file
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    file.save(file_path)

    return file_path


def delete_file(file_path):
    """
    Delete a file from storage.

    Args:
        file_path: Absolute path to file

    Returns:
        True on success, False on failure
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        print(f"Error deleting file {file_path}: {e}")
        return False


def delete_session_files(session_id):
    """
    Delete all files belonging to a specific session.

    Args:
        session_id: Session identifier string
    """
    if not os.path.exists(UPLOAD_DIR):
        return

    for filename in os.listdir(UPLOAD_DIR):
        if filename.startswith(session_id):
            file_path = os.path.join(UPLOAD_DIR, filename)
            delete_file(file_path)


def cleanup_old_files():
    """
    Delete files older than 1 hour from temp directory.
    Called by background scheduler every 10 minutes.

    Returns:
        Count of deleted files
    """
    if not os.path.exists(UPLOAD_DIR):
        return 0

    deleted_count = 0
    current_time = time.time()
    one_hour_ago = current_time - 3600  # 3600 seconds = 1 hour

    for filename in os.listdir(UPLOAD_DIR):
        file_path = os.path.join(UPLOAD_DIR, filename)

        try:
            file_mtime = os.path.getmtime(file_path)

            if file_mtime < one_hour_ago:
                if delete_file(file_path):
                    deleted_count += 1
                    print(f"Cleaned up old file: {filename}")
        except Exception as e:
            print(f"Error checking file {filename}: {e}")

    return deleted_count


def calculate_file_hash(file_path):
    """
    Calculate MD5 and SHA256 hashes of a file.

    Args:
        file_path: Absolute path to file

    Returns:
        Dictionary with 'md5' and 'sha256' keys
    """
    md5_hash = hashlib.md5()
    sha256_hash = hashlib.sha256()

    with open(file_path, 'rb') as f:
        # Read file in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b''):
            md5_hash.update(chunk)
            sha256_hash.update(chunk)

    return {
        'md5': md5_hash.hexdigest(),
        'sha256': sha256_hash.hexdigest()
    }


def get_file_info(file_path):
    """
    Get file size and MIME type information.

    Args:
        file_path: Absolute path to file

    Returns:
        Dictionary with 'size', 'size_human', and 'mime_type' keys
    """
    size = os.path.getsize(file_path)

    # Calculate human-readable size
    if size < 1024:
        size_human = f"{size} bytes"
    elif size < 1024 * 1024:
        size_human = f"{size / 1024:.1f} KB"
    else:
        size_human = f"{size / (1024 * 1024):.1f} MB"

    # Get MIME type
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        mime_type = "application/octet-stream"

    return {
        'size': size,
        'size_human': size_human,
        'mime_type': mime_type
    }
