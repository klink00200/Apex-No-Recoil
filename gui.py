from __future__ import annotations

import ctypes
import os
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

# Third-party imports (Windows-specific logic from ex.txt)
try:
    import cv2
    import numpy as np
    import pytesseract
    from mss import mss
except ImportError:
    # These will be missing on non-Windows/non-setup environments
    cv2 = None
    np = None
    pytesseract = None
    mss = None

try:
    import winsound
    import interception
except ImportError:
    winsound = None
    interception = None

from config_store import AppSettings, list_resolutions, load_settings, save_settings
from uuid_generator import get_or_create_uuid

# ==========================================
# 🛡️ Administrator Shield
# ==========================================
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if sys.platform == "win32" and not is_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{os.path.abspath(__file__)}"', None, 1)
    sys.exit()

# ==========================================
# ⚙️ Constants & Globals
# ==========================================
ROOT_DIR = Path(__file__).resolve().parent
SETTINGS_PATH = ROOT_DIR / "settings.ini"
RESOLUTION_DIR = ROOT_DIR / "Resolution"
PATTERN_DIR = ROOT_DIR / "Pattern"
SCRIPT_VERSION = "Python Pro Editor"

# Hardware / OCR paths
if sys.platform == "win32":
    pytesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    if os.path.exists(pytesseract_path):
        pytesseract.pytesseract.tesseract_cmd = pytesseract_path

KNOWN_WEAPONS = [
    "HAVOC", "FLATLINE", "HEMLOK", "R-301", "R301", "NEMESIS",
    "ALTERNATOR", "PROWLER", "R-99", "R99", "VOLT", "C.A.R.", "CAR SMG", "CAR",
    "DEVOTION", "L-STAR", "LSTAR", "SPITFIRE", "RAMPAGE",
    "G7 SCOUT", "TRIPLE TAKE", "30-30", "BOCEK",
    "CHARGE RIFLE", "LONGBOW", "KRABER", "SENTINEL",
    "EVA-8", "EVA8", "MASTIFF", "MOZAMBIQUE", "PEACEKEEPER",
    "RE-45", "RE45", "P2020", "WINGMAN"
]

COLORBLIND_OPTIONS = ["Normal", "Protanopia", "Deuteranopia", "Tritanopia"]
TRIGGER_OPTIONS = ["Capslock", "NumLock", "ScrollLock"]

# ==========================================
# 🏛️ Main Application
# ==========================================
class SettingsApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"Apex Settings {SCRIPT_VERSION}")
        self.resizable(False, False)
        
        # Load core data
        self.app_uuid = get_or_create_uuid(ROOT_DIR / ".app_uuid")
        self.settings = load_settings(SETTINGS_PATH)
        self.available_resolutions = list_resolutions(RESOLUTION_DIR)
        
        # Active State
        self.current_weapon = "NONE"
        self.is_running_logic = False
        self.weapon_patterns = {}
        self.modifier = 1.0
        self._load_patterns()

        # UI Variables
        self.uuid_label_var = tk.StringVar(value=f"UUID: {self.app_uuid}")
        self.weapon_status_var = tk.StringVar(value="Weapon: NONE")
        self.sens_var = tk.DoubleVar(value=self.settings.sens)
        self.sens_label_var = tk.StringVar(value=f"{self.settings.sens:.1f}")
        self.resolution_var = tk.StringVar(value=self.settings.resolution)
        self.colorblind_var = tk.StringVar(value=self.settings.colorblind)
        self.auto_fire_var = tk.BooleanVar(value=self.settings.auto_fire)
        self.ads_only_var = tk.BooleanVar(value=self.settings.ads_only)
        self.debug_var = tk.BooleanVar(value=self.settings.debug)
        self.gold_optics_var = tk.BooleanVar(value=self.settings.gold_optics)
        self.trigger_only_var = tk.BooleanVar(value=self.settings.trigger_only)
        self.trigger_button_var = tk.StringVar(value=self.settings.trigger_button)
        self.zoom_sens_var = tk.StringVar(value=f"{self.settings.zoom_sens:.1f}")
        self.volume_var = tk.StringVar(value=str(self.settings.volume))
        self.rate_var = tk.StringVar(value=str(self.settings.rate))
        
        self._update_modifier()
        self._build_ui()

    def _load_patterns(self):
        if not PATTERN_DIR.exists():
            return
        for file in PATTERN_DIR.glob("*.txt"):
            name = file.stem.upper()
            pattern = []
            try:
                with file.open('r') as f:
                    for line in f:
                        p = line.strip().split(',')
                        if len(p) >= 3:
                            pattern.append((float(p[0]), float(p[1]), float(p[2])))
                self.weapon_patterns[name] = pattern
                # Handle aliases
                if name == "R99": self.weapon_patterns["R-99"] = pattern
                elif name == "R301": self.weapon_patterns["R-301"] = pattern
            except Exception as e:
                print(f"Error loading {file}: {e}")

    def _update_modifier(self):
        # Using formula from ex.txt: (4 / sens)
        try:
            val = float(self.sens_var.get())
            if val > 0:
                self.modifier = 4.0 / val
        except:
            self.modifier = 1.0

    def _build_ui(self) -> None:
        container = ttk.Frame(self, padding=20)
        container.grid(sticky="nsew")

        # Header
        title = ttk.Label(container, text="Apex Master", font=("Verdana", 24, "bold"))
        title.grid(row=0, column=0, columnspan=2, sticky="w")
        
        status_label = ttk.Label(container, textvariable=self.weapon_status_var, font=("Consolas", 14, "bold"), foreground="#2ecc71")
        status_label.grid(row=0, column=2, sticky="e")

        uuid_label = ttk.Label(container, textvariable=self.uuid_label_var, font=("Arial", 9))
        uuid_label.grid(row=1, column=0, columnspan=3, sticky="w", pady=(2, 10))

        # Main Settings Area
        settings_frame = ttk.LabelFrame(container, text=" Configuration ", padding=15)
        settings_frame.grid(row=2, column=0, columnspan=3, sticky="nsew")

        # Sensitivity Row
        ttk.Label(settings_frame, text="Sensitivity").grid(row=0, column=0, sticky="w")
        sens_scale = ttk.Scale(
            settings_frame,
            from_=0.1,
            to=6.0,
            variable=self.sens_var,
            command=self._on_sens_change,
        )
        sens_scale.grid(row=0, column=1, sticky="ew", padx=10)
        ttk.Label(settings_frame, textvariable=self.sens_label_var, width=4).grid(row=0, column=2, sticky="w")

        # Switches Row
        switches_frame = ttk.Frame(settings_frame)
        switches_frame.grid(row=1, column=0, columnspan=3, pady=10, sticky="w")
        
        ttk.Checkbutton(switches_frame, text="Auto Fire", variable=self.auto_fire_var).pack(side="left", padx=(0, 15))
        ttk.Checkbutton(switches_frame, text="ADS Only", variable=self.ads_only_var).pack(side="left", padx=15)
        ttk.Checkbutton(switches_frame, text="Debug Mode", variable=self.debug_var).pack(side="left", padx=15)

        # Dropdowns
        ttk.Label(settings_frame, text="Resolution").grid(row=2, column=0, sticky="w", pady=5)
        res_combo = ttk.Combobox(settings_frame, textvariable=self.resolution_var, values=self.available_resolutions, state="readonly")
        res_combo.grid(row=2, column=1, columnspan=2, sticky="ew", pady=5)

        ttk.Label(settings_frame, text="Trigger").grid(row=3, column=0, sticky="w", pady=5)
        trigger_combo = ttk.Combobox(settings_frame, textvariable=self.trigger_button_var, values=TRIGGER_OPTIONS, state="readonly")
        trigger_combo.grid(row=3, column=1, columnspan=2, sticky="ew", pady=5)

        # Control Buttons
        btn_frame = ttk.Frame(container, padding=(0, 15, 0, 0))
        btn_frame.grid(row=3, column=0, columnspan=3, sticky="ew")

        self.run_btn = ttk.Button(btn_frame, text="START LOGIC", command=self.toggle_logic, width=20)
        self.run_btn.pack(side="left", padx=(0, 10))
        
        ttk.Button(btn_frame, text="SAVE SETTINGS", command=self.save, width=20).pack(side="left")
        
        settings_frame.columnconfigure(1, weight=1)

    def _on_sens_change(self, value: str) -> None:
        self.sens_label_var.set(f"{float(value):.1f}")
        self._update_modifier()

    def toggle_logic(self):
        if not self.is_running_logic:
            if sys.platform != "win32":
                messagebox.showwarning("Platform Warning", "Recoil/OCR logic is Windows-only.")
                return
            
            self.is_running_logic = True
            self.run_btn.config(text="STOP LOGIC")
            threading.Thread(target=self._recoil_loop, daemon=True).start()
            threading.Thread(target=self._ocr_loop, daemon=True).start()
            if winsound: winsound.Beep(800, 200)
        else:
            self.is_running_logic = False
            self.run_btn.config(text="START LOGIC")
            if winsound: winsound.Beep(400, 200)

    def _recoil_loop(self):
        if not interception: return
        user32 = ctypes.windll.user32
        while self.is_running_logic:
            # Check for LButton (0x01) and RButton (0x02)
            if (user32.GetAsyncKeyState(0x01) & 0x8000) and (user32.GetAsyncKeyState(0x02) & 0x8000):
                weapon = self.current_weapon
                if weapon in self.weapon_patterns:
                    for x, y, interval in self.weapon_patterns[weapon]:
                        if not (user32.GetAsyncKeyState(0x01) & 0x8000) or not self.is_running_logic:
                            break
                        interception.move_relative(int(x * self.modifier), int(y * self.modifier))
                        self._precise_sleep(interval)
            time.sleep(0.001)

    def _ocr_loop(self):
        if not mss or not pytesseract: return
        sct = mss()
        # Monitor detection logic from ex.txt
        monitor_idx = 2 if len(sct.monitors) >= 3 else 1
        m = sct.monitors[monitor_idx]
        
        # HUD Coordinates (Tailored for Apex 1080p HUD)
        monitor_hud = {"top": m["top"] + 1025, "left": m["left"] + 1480, "width": 440, "height": 40}
        tess_config = r'--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ-0123456789'

        while self.is_running_logic:
            try:
                sct_img = sct.grab(monitor_hud)
                frame = np.array(sct_img)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                
                # Image processing from ex.txt
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
                _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
                
                text = pytesseract.image_to_string(thresh, config=tess_config).strip().upper()
                
                detected = None
                for weapon in KNOWN_WEAPONS:
                    if weapon in text:
                        detected = weapon
                        break
                
                if detected and detected != self.current_weapon:
                    self.current_weapon = detected
                    self.weapon_status_var.set(f"Weapon: {detected}")
                    if winsound: winsound.Beep(1000, 150)
            except Exception as e:
                if self.debug_var.get(): print(f"OCR Error: {e}")
            
            time.sleep(0.5)

    def _precise_sleep(self, duration_ms):
        target = time.perf_counter() + (duration_ms / 1000.0)
        while time.perf_counter() < target:
            pass

    def save(self) -> None:
        try:
            settings = AppSettings(
                resolution=self.resolution_var.get(),
                colorblind=self.colorblind_var.get(),
                sens=round(float(self.sens_var.get()), 1),
                zoom_sens=round(float(self.zoom_sens_var.get()), 1),
                auto_fire=self.auto_fire_var.get(),
                ads_only=self.ads_only_var.get(),
                volume=int(self.volume_var.get()),
                rate=int(self.rate_var.get()),
                debug=self.debug_var.get(),
                gold_optics=self.gold_optics_var.get(),
                trigger_only=self.trigger_only_var.get(),
                trigger_button=self.trigger_button_var.get(),
            )
            save_settings(SETTINGS_PATH, settings)
            messagebox.showinfo("Success", "Settings applied successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")

if __name__ == "__main__":
    app = SettingsApp()
    app.mainloop()
