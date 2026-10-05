import os
import subprocess
import time
import sys

# Direct to Termux:X11 display port
os.environ['DISPLAY'] = ':0'

# Track running frames matching to application IDs: {app_window_id: frame_process_object}
active_frames = {}

def get_visible_apps():
    """Returns a list of visible window IDs, excluding our own frames."""
    try:
        result = subprocess.run(
            ['xdotool', 'search', '--onlyvisible', '--name', '.*'],
            capture_output=True, text=True, check=True
        )
        all_ids = result.stdout.strip().split('\n')
        
        app_ids = []
        for wid in all_ids:
            if not wid.isdigit():
                continue
            
            # Fetch window title to avoid framing our own frames
            title_res = subprocess.run(['xdotool', 'getwindowname', wid], capture_output=True, text=True)
            title = title_res.stdout.strip()
            
            # Skip empty names or our own frames
            if not title or "NADETOP_WINDOW_FRAME" in title:
                continue
                
            app_ids.append(wid)
        return app_ids
    except subprocess.CalledProcessError:
        return []

def get_geometry(wid):
    """Returns (x, y, w, h) of an X11 window using xdotool."""
    try:
        result = subprocess.run(['xdotool', 'getwindowgeometry', '--shell', str(wid)], capture_output=True, text=True, check=True)
        geo = {}
        for line in result.stdout.strip().split('\n'):
            if '=' in line:
                k, v = line.split('=')
                geo[k] = int(v)
        return geo.get('X'), geo.get('Y'), geo.get('WIDTH'), geo.get('HEIGHT')
    except Exception:
        return None

def sync_frame_and_app(app_id):
    """Checks the app window position and moves/layers its frame to match it."""
    geo = get_geometry(app_id)
    if not geo:
        return False # Window was closed
        
    x, y, w, h = geo
    
    # 1. Find the frame window matching this specific application
    try:
        # Search for our custom Pygame frames
        res = subprocess.run(['xdotool', 'search', '--name', 'NADETOP_WINDOW_FRAME'], capture_output=True, text=True)
        frame_ids = res.stdout.strip().split('\n')
        
        for fid in frame_ids:
            if not fid.isdigit():
                continue
                
            # Position the wframe.py window directly above the app window canvas
            # Width matches app window, height is hardcoded to 32px
            frame_y = y - 32
            subprocess.run(['xdotool', 'windowmove', fid, str(x), str(frame_y)])
            subprocess.run(['xdotool', 'windowsize', fid, str(w), '32'])
            
            # LAYER STRATEGY: Raise frame to top, raise app right underneath it
            subprocess.run(['xdotool', 'windowraise', fid])
            break # Found our target frame
            
    except Exception as e:
        pass
    return True

# =====================================================================
# MAIN WINDOW MANAGER LOOP
# =====================================================================
print("[WM] NADATOP Window Manager Orchestrator Started.")

try:
    while True:
        # 1. Scan for newly opened applications
        apps = get_visible_apps()
        
        for app_id in apps:
            if app_id not in active_frames:
                print(f"[WM] Found application window [{app_id}]. Spawning window frame layer...")
                
                # Fetch app position to spawn the frame nearby initially
                geo = get_geometry(app_id)
                if geo:
                    # Spawn wframe.py as a background subprocess 
                    # We pass the application window ID as a terminal argument!
                    proc = subprocess.Popen([sys.executable, 'wframe.py', app_id])
                    active_frames[app_id] = proc
                    
        # 2. Maintain active frames alignment and window layering
        dead_apps = []
        for app_id, proc in active_frames.items():
            # Check if application window still exists
            alive = sync_frame_and_app(app_id)
            
            # If the application process or frame has been shut down
            if not alive or proc.poll() is not None:
                print(f"[WM] App window [{app_id}] closed. Terminating matching frame...")
                proc.terminate()
                dead_apps.append(app_id)
                
        # Clean up tracking dictionary references
        for da in dead_apps:
            del active_frames[da]
            
        time.sleep(0.05) # Keep loop efficient (~20Hz layout synchronization)

except KeyboardInterrupt:
    print("\n[WM] Shutting down manager loop. Cleaning window decorations...")
    for proc in active_frames.values():
        proc.terminate()
