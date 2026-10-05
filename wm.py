import os
import subprocess
import time
import sys

os.environ['DISPLAY'] = ':0'

# Store processes cleanly: {app_id: {'frame': proc_obj, 'resize': proc_obj}}
active_decorations = {}

def get_visible_apps():
    try:
        # Search for all visible windows
        res = subprocess.run(['xdotool', 'search', '--onlyvisible', '--name', '.*'], capture_output=True, text=True, check=True)
        raw_ids = res.stdout.strip().split('\n')
        
        filtered_ids = []
        for wid in raw_ids:
            if not wid.isdigit():
                continue
            
            # Fetch the actual window name
            name_res = subprocess.run(['xdotool', 'getwindowname', wid], capture_output=True, text=True)
            title = name_res.stdout.strip()
            
            # CRUCIAL FIX: If the window is a NADETOP element or blank, completely ignore it!
            if "NADETOP" in title or not title:
                continue
                
            filtered_ids.append(wid)
        return filtered_ids
    except Exception:
        return []

def get_geometry(wid):
    try:
        res = subprocess.run(['xdotool', 'getwindowgeometry', '--shell', str(wid)], capture_output=True, text=True, check=True)
        g = {line.split('=')[0]: int(line.split('=')[1]) for line in res.stdout.strip().split('\n') if '=' in line}
        return g.get('X'), g.get('Y'), g.get('WIDTH'), g.get('HEIGHT')
    except Exception:
        return None

print("[WM] NADETOP Clean Orchestrator Active.")
try:
    while True:
        apps = get_visible_apps()
        
        # Spawn components for genuine apps only
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
            
            # 1. Stacking: Keep everything cleanly ordered over the window layout stack
            try:
                # Find the frame matching our identifier
                f_id = subprocess.run(['xdotool', 'search', '--name', 'NADETOP_WINDOW_FRAME'], capture_output=True, text=True).stdout.strip().split('\n')[0]
                if f_id.isdigit():
                    subprocess.Popen(['xdotool', 'windowraise', f_id])
            except Exception: pass
            
            # 2. Bottom-Right: Align resize grip handle box precisely POKING OUT
            try:
                r_id = subprocess.run(['xdotool', 'search', '--name', 'NADETOP_RESIZE_GRIP'], capture_output=True, text=True).stdout.strip().split('\n')[0]
                if r_id.isdigit():
                    mouse_check = subprocess.run(['xdotool', 'getmouselocation', '--shell'], capture_output=True, text=True)
                    is_clicking = "button=1" in mouse_check.stdout
                    
                    if not is_clicking:
                        subprocess.Popen(['xdotool', 'windowmove', r_id, str(x + w), str(y + h)])
                    
                    subprocess.Popen(['xdotool', 'windowraise', r_id])
            except Exception: pass
            
        for da in dead_apps:
            del active_decorations[da]
            
        time.sleep(0.05) # Slipped frequency slightly to prevent CPU stutter
except KeyboardInterrupt:
    for procs in active_decorations.values():
        procs['frame'].terminate()
        procs['resize'].terminate()
