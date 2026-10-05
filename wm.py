import os
import subprocess
import time
import sys
import socket
import threading

os.environ['DISPLAY'] = ':0'

SOCKET_PATH = os.path.expanduser("~/.nadetop_wm.sock")

# Clean up any leftover dead socket files from old crashes
if os.path.exists(SOCKET_PATH):
    os.remove(SOCKET_PATH)

def wm_ipc_listener():
    """Background thread that listens for instructions from titlebars."""
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(SOCKET_PATH)
    server.listen(5)
    
    while True:
        try:
            conn, _ = server.accept()
            message = conn.recv(1024).decode('utf-8').strip()
            conn.close()
            
            if message.startswith("focus:"):
                target_app_id = message.split(":")[1]
                print(f"[WM IPC] Focusing requested for app: {target_app_id}")
                
                # 1. Globally raise and activate the app using xdotool
                subprocess.Popen(['xdotool', 'windowactivate', str(target_app_id)])
                
                # 2. Immediately bring its matching components to the absolute top
                # (Your existing wm.py loop will maintain alignment, but doing it here prevents focus lag)
                try:
                    res = subprocess.run(['xdotool', 'search', '--name', 'NADETOP_WINDOW_FRAME'], capture_output=True, text=True)
                    for fid in res.stdout.strip().split('\n'):
                        if fid.isdigit():
                            subprocess.Popen(['xdotool', 'windowraise', fid])
                except Exception: pass
                
        except Exception as e:
            # Prevent thread from crashing if communication breaks momentarily
            pass

# Spin up the listener thread cleanly in the background
ipc_thread = threading.Thread(target=wm_ipc_listener, daemon=True)
ipc_thread.start()

# Store processes cleanly: {app_id: {'frame': proc_obj, 'resize': proc_obj}}
active_decorations = {}

def get_visible_apps():
    try:
        # 1. Search for all visible windows
        res = subprocess.run(['xdotool', 'search', '--onlyvisible', '--name', '.*'], capture_output=True, text=True, check=True)
        raw_ids = res.stdout.strip().split('\n')
        
        filtered_ids = []
        for wid in raw_ids:
            if not wid.isdigit():
                continue
            
            # 2. Fetch the window title
            name_res = subprocess.run(['xdotool', 'getwindowname', wid], capture_output=True, text=True)
            title = name_res.stdout.strip()
            
            if "NADETOP" in title or not title:
                continue

            # =====================================================================
            # CONTEXT MENU & POPUP FILTER (The Fix)
            # =====================================================================
            try:
                # Query the window type properties via xprop underlying mapping
                # We target '_NET_WM_WINDOW_TYPE' to see if it's an app or a menu override
                type_res = subprocess.run(
                    ['xprop', '-id', wid, '_NET_WM_WINDOW_TYPE'], 
                    capture_output=True, text=True, timeout=0.1
                )
                type_output = type_res.stdout.lower()
                
                # If the window is explicitly flagged as a menu, popup, or tooltip, skip it!
                if any(x in type_output for x in ["menu", "popup", "dropdown", "tooltip", "notification"]):
                    continue
            except Exception:
                # If xprop fails or times out, proceed cautiously or skip
                pass

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
