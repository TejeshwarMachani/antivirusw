import pyclamd


def init_clamav():
    """
    Initialize connection to ClamAV daemon.

    Returns:
        ClamAV connection object or None if unavailable
    """
    try:
        # Try Unix socket first
        cd = pyclamd.ClamdUnixSocket('/var/run/clamav/clamd.ctl')
        if cd.ping():
            print("Connected to ClamAV via Unix socket")
            return cd
    except Exception:
        pass

    try:
        # Fallback to network socket
        cd = pyclamd.ClamdNetworkSocket('localhost', 3310)
        if cd.ping():
            print("Connected to ClamAV via network socket")
            return cd
    except Exception:
        pass

    print("ClamAV daemon unavailable")
    return None


def scan_file(file_path):
    """
    Scan a file for viruses/malware using ClamAV.

    Args:
        file_path: Absolute path to file to scan

    Returns:
        Dictionary with scan results containing:
        - status: 'clean', 'infected', or 'error'
        - threat_name: Name of threat if infected, None otherwise
        - clamav_version: ClamAV engine version
        - db_version: Virus database version
    """
    cd = init_clamav()

    if cd is None:
        return {
            'status': 'service_unavailable',
            'threat_name': None,
            'clamav_version': None,
            'db_version': None
        }

    try:
        # Scan the file
        scan_result = cd.scan_file(file_path)

        # Get ClamAV version info
        version_info = get_clamav_info(cd)

        # Parse scan result
        if scan_result is None:
            # File is clean
            return {
                'status': 'clean',
                'threat_name': None,
                'clamav_version': version_info['clamav_version'],
                'db_version': version_info['db_version']
            }
        else:
            # File is infected
            # scan_result is a dict: {file_path: ('FOUND', 'threat_name')}
            for path, (status, threat) in scan_result.items():
                if status == 'FOUND':
                    return {
                        'status': 'infected',
                        'threat_name': threat,
                        'clamav_version': version_info['clamav_version'],
                        'db_version': version_info['db_version']
                    }
                elif status == 'ERROR':
                    return {
                        'status': 'error',
                        'threat_name': None,
                        'clamav_version': version_info['clamav_version'],
                        'db_version': version_info['db_version']
                    }

    except Exception as e:
        print(f"Error scanning file: {e}")
        return {
            'status': 'error',
            'threat_name': None,
            'clamav_version': None,
            'db_version': None
        }


def get_clamav_info(cd=None):
    """
    Get ClamAV version and database version.

    Args:
        cd: ClamAV connection object (optional, will create if not provided)

    Returns:
        Dictionary with 'clamav_version' and 'db_version'
    """
    if cd is None:
        cd = init_clamav()

    if cd is None:
        return {
            'clamav_version': 'Unknown',
            'db_version': 'Unknown'
        }

    try:
        version = cd.version()
        # Parse version string: "ClamAV 0.103.8/26756/..."
        parts = version.split('/')
        clamav_version = parts[0].replace('ClamAV ', '') if len(parts) > 0 else 'Unknown'
        db_version = parts[1] if len(parts) > 1 else 'Unknown'

        return {
            'clamav_version': clamav_version,
            'db_version': db_version
        }
    except Exception as e:
        print(f"Error getting ClamAV info: {e}")
        return {
            'clamav_version': 'Unknown',
            'db_version': 'Unknown'
        }
