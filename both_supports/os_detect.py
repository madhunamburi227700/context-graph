import platform


def os_detect() -> str:
    """Detect OS: return 'linux' or 'other'"""
    return "linux" if platform.system().lower() == "linux" else "other"


def run_os_detection():

    os_type = os_detect()

    return os_type
