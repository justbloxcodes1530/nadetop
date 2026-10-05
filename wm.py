import os
import subprocess
import random
import math

# Ensure we map directly to Termux:X11
os.environ['DISPLAY'] = ':0'

def list_windows():
    """Returns a list of all raw X11 window IDs and their titles."""
    try:
        # Search for all windows (using a blank regex pattern matching everything)
        result = subprocess.run(
            ['xdotool', 'search', '--onlyvisible', '--name', '.*'], 
            capture_output=True, text=True, check=True
        )
        window_ids = result.stdout.strip().split('\n')
        
        windows = []
        for wid in window_ids:
            if not wid.isdigit():
                continue
            # Get the name/title of each specific window ID
            name_res = subprocess.run(['xdotool', 'getwindowname', wid], capture_output=True, text=True)
            title = name_res.stdout.strip()
            if title:
                windows.append({'id': wid, 'title': title})
        return windows
    except subprocess.CalledProcessError:
        return []

def focus_window(window_id):
    """Brings the specific window ID to focus."""
    subprocess.run(['xdotool', 'windowactivate', str(window_id)])

def move_and_resize_window(window_id, x, y, width, height):
    """Moves and resizes the target window ID instantly."""
    # Move the window
    subprocess.run(['xdotool', 'windowmove', str(window_id), str(x), str(y)])
    # Resize the window
    subprocess.run(['xdotool', 'windowsize', str(window_id), str(width), str(height)])

# ==========================================
# SANITY CHECK TEST RUN
# ==========================================
if __name__ == "__main__":
    print("Scanning active Termux:X11 windows via xdotool...")
    windows = list_windows()
    
    if not windows:
        print("No windows detected yet. Open a window (like 'xfce4-terminal' or an app) in Termux:X11 first!")
    
    for win in windows:
        move_and_resize_window(win['id'], int(random.random() * 100), int(random.random() * 100), 640, 480)
        print(f" Found -> ID: {win['id']} | Title: {win['title']}")
        
        # Example Test: If you see your window, you can uncomment this to move it!
        # print(f"Moving {win['title']} to top left...")
        # move_and_resize_window(win['id'], x=50, y=50, width=600, height=400)
        # focus_window(win['id'])
