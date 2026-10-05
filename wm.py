import os
import subprocess

# Ensure we are targeting the Termux X11 display
os.environ['DISPLAY'] = ':0'

def list_windows():
    """Returns a list of open windows with their IDs and titles."""
    try:
        # Runs 'wmctrl -l' to list all managed windows
        result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True, check=True)
        windows = []
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split(maxsplit=3)
                window_id = parts[0]
                window_title = parts[3] if len(parts) > 3 else "Unknown"
                windows.append({'id': window_id, 'title': window_title})
        return windows
    except subprocess.CalledProcessError:
        return []

def focus_window(window_title_or_id):
    """Brings a window to the front and focuses it."""
    # -a activates (focuses) the window matching the title or ID
    subprocess.run(['wmctrl', '-a', window_title_or_id])

def move_and_resize_window(window_title_or_id, x, y, width, height):
    """Moves a window to (x, y) and resizes it to width x height."""
    # -r targets the window
    # -e format is: gravity,X,Y,width,height (0 means use default gravity)
    geometry_string = f"0,{x},{y},{width},{height}"
    subprocess.run(['wmctrl', '-r', window_title_or_id, '-e', geometry_string])

# ==========================================
# EXAMPLE USAGE
# ==========================================
if __name__ == "__main__":
    print("Scanning active windows...")
    open_windows = list_windows()
    
    for win in open_windows:
        print(f"Found Window -> ID: {win['id']} | Title: {win['title']}")
        
    # Example: If you have an app open named "Leafpad"
    # focus_window("Leafpad")
    # move_and_resize_window("Leafpad", x=100, y=100, width=800, height=600)
