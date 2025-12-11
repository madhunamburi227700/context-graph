import platform

def os_detect():
    if platform.system().lower() == "windows":
        return "windows"
    else:
        return "linux"
