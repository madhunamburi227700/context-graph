import platform


def write_output(message: str, report_file):
    """Write message to report file"""
    with open(report_file, "a", encoding="utf-8") as f:
        f.write(message + "\n")


def os_detect():
    """Detect operating system"""
    if platform.system().lower() == "windows":
        return "windows"
    return "linux"


def run_os_detection(report_file):
    # ------------------ 1st section ----------------------
    write_output("------------------ 1st section ----------------------", report_file)

    os_type = os_detect()
    write_output(f"🖥 Detected OS: {os_type}", report_file)

    write_output("\n---------------------------------------------------", report_file)

    return os_type