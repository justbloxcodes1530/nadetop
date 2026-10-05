import os
import subprocess
import time
import sys

os.environ['DISPLAY'] = ':0'

# Store processes cleanly: {app_id: {'frame': proc_obj, 'resize': proc_obj}}
active_decorations = {}

def get_visible_apps():
    try:
        res = subprocess.run(['xdotool', 'search', '--onlyvisible', '--name', '.*'], capture_output=True, text=True, check=True)
        return [wid for wid in res.stdout.strip().split('\n') if wid.isdigit() and "NADETOP" not in subprocess.run(['xdotool', 'getwindowname', wid], capture_output=True, text=True).stdout]
    except Exception:
        return []

def get_geometry(wid):
    try:
        res = subprocess.run(['xdotool', 'getwindowgeometry', '--shell', str(wid)], capture_output=True, text=True, check=True)
        g = {line.split('=')[0]: int(line.split('=')[1]) for line in res.stdout.strip().split('\n') if '=' in line}
        return g.get('X'), g.get('Y'), g.get('WIDTH'), g.get('HEIGHT')
    except Exception:
        return None

print("[WM] NADETOP Haiku Architecture Active.")
try:
    while True:
        apps = get_visible_apps()
        
        # Spawn components for new apps
        for app_id in apps:
            if app_id not in active_decorations:
                print(f"[WM] Decorating Window {app_id}")
                f_proc = subprocess.Popen([sys.executable, 'wframe.py', app_id])
                r_proc = subprocess.Popen([sys.executable, 'wresize.py', app_id])
                active_decorations[app_id] = {'frame': f_proc, 'resize': r_proc}
        
        # Maintain positioning anchors 
        dead_apps = []
        for app_id, procs in active_decorations.items():
            geo = get_geometry(app_id)
            if not geo or procs['frame'].poll() is not None:
                procs['frame'].terminate()
                procs['resize'].terminate()
                dead_apps.append(app_id)
                continue
                
            x, y, w, h = geo
            
            # Use xdotool to anchor elements based on the client window box
            # 1. Top-Left: Place Haiku Yellow Tab Frame 32px above app
            try:
                f_id = subprocess.run(['xdotool', 'search', '--name', 'NADETOP_WINDOW_FRAME'], capture_output=True, text=True).stdout.strip().split('\n')[0]
                if f_id.isdigit():
                    # Only map frame if user isn't actively holding down the drag loop
                    # Let wframe.py handle movements, wm.py syncs layering
                    subprocess.Popen(['xdotool', 'windowraise', f_id])
            except Exception: pass
            
            # 2. Bottom-Right: Align resize grip handle box precisely at (x+w-16, y+h-16)
            try:
                r_id = subprocess.run(['xdotool', 'search', '--name', 'NADETOP_RESIZE_GRIP'], capture_output=True, text=True).stdout.strip().split('\n')[0]
                if r_id.isdigit():
                    subprocess.Popen(['xdotool', 'windowmove', r_id, str(x + w - 16), str(y + h - 16)])
                    subprocess.Popen(['xdotool', 'windowraise', r_id])
            except Exception: pass
            
        for da in dead_apps:
            del active_decorations[da]
            
        time.sleep(0.03)
except KeyboardInterrupt:
    for procs in active_decorations.values():
        procs['frame'].terminate()
        procs['resize'].terminate()
