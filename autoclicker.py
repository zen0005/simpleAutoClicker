import tkinter as tk
import customtkinter as ctk
import keyboard
from pynput import keyboard as pynkeys
from pynput import mouse as pynmouse
from pynput.mouse import Button, Controller as MouseController
import time
import threading
import pyautogui
import ctypes
from ctypes import wintypes

pyautogui.PAUSE = 0


# Define SendInput structs once at module level
class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class _INP(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT),
                ("mi", MOUSEINPUT)]

class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD),
                ("_input", _INP)]


#Main class that stores the auto clicker and macor
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Simple Automation utility")
        self.geometry("300x500")
        self.resizable(False, False)
        ctk.set_appearance_mode("light")

        self.createNavBar()

        self.frames = {}
        for Page in (AutoClicker, Macro):
            frame = Page(self.container, self)
            self.frames[Page] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.showFrame(AutoClicker)

    def createNavBar(self):
        navbar = ctk.CTkFrame(self)
        navbar.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(navbar, text="Auto Clicker", command=lambda: self.showFrame(AutoClicker)).pack(side="left", padx=5)
        ctk.CTkButton(navbar, text="Macro", command=lambda: self.showFrame(Macro)).pack(side="left", padx=5)

        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

    def showFrame(self, page):
        self.frames[page].tkraise()

    def rebindAllHotkeys(self):
        self.frames[AutoClicker].bindHotkeys()
        self.frames[Macro].bindHotkeys()


#The class storing auto clicker
class AutoClicker(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.rowPos = 0
        self.app = app

        self.timeVars = {
            "hour": tk.IntVar(value=0),
            "minute": tk.IntVar(value=0),
            "second": tk.IntVar(value=0),
            "millisecond": tk.IntVar(value=100)
        }
        self.hotkey = "f6"
        self.hotkeyHook = None
        self.is_running = False
        self.mouse = pynmouse.Controller()

        self.createInterface()

    #Creates the interface for the auto clicker
    def createInterface(self):
        columnPos = 0
        for name, var in self.timeVars.items():
            xAxisPadding = (20, 0) if name == "hour" or name == "second" else (0, 20)
            tk.Label(self, text=name.capitalize()).grid(row=self.rowPos, column=columnPos, padx=xAxisPadding)
            tk.Entry(self, textvariable=var, width=10).grid(row=self.rowPos + 1, column=columnPos, padx=xAxisPadding)
            if name == "minute" or name == "millisecond":
                self.rowPos += 2
            columnPos = (columnPos + 1) % 2

        self.startBtn = ctk.CTkButton(self, text="Start", command=self.toggle, width=75)
        self.startBtn.grid(row=self.rowPos, column=0, padx=(20, 0), pady=(20, 20))

        self.stopBtn = ctk.CTkButton(self, text="Stop", command=self.toggle, state="disabled", width=75)
        self.stopBtn.grid(row=self.rowPos, column=1, padx=(0, 20), pady=(20, 20))
        self.rowPos += 1

        ctk.CTkLabel(self, text="Hotkey").grid(row=self.rowPos, column=0, columnspan=2, pady=(5, 0))
        self.rowPos += 1
        self.hotkeyBtn = ctk.CTkButton(self, text=f"Current: {self.hotkey}", command=self.listenForHotkey)
        self.hotkeyBtn.grid(row=self.rowPos, column=0, columnspan=2, pady=5)
        self.rowPos += 1
        self.bindHotkeys()

    #Toggles the auto clicker
    def toggle(self):
        if not self.is_running:
            self.is_running = True
            self.after(0, lambda: self.startBtn.configure(state="disabled"))
            self.after(0, lambda: self.stopBtn.configure(state="normal"))
            threading.Thread(target=self.clicker, daemon=True).start()
        else:
            self.is_running = False
            self.after(0, lambda: self.startBtn.configure(state="normal"))
            self.after(0, lambda: self.stopBtn.configure(state="disabled"))

    #Gets the delay the user set
    def getDelaySeconds(self):
        hour = self.timeVars["hour"].get()
        minute = self.timeVars["minute"].get()
        second = self.timeVars["second"].get()
        millisecond = self.timeVars["millisecond"].get()
        return (hour * 3600) + (minute * 60) + second + (millisecond / 1000)

    #The function that does the automatic click
    def clicker(self):
        delay = self.getDelaySeconds()
        while self.is_running:
            start = time.perf_counter()
            self.mouse.click(Button.left)
            elapsed = time.perf_counter() - start
            remaining = delay - elapsed
            if remaining > 0:
                time.sleep(remaining)

    #Listens for hotkey
    def listenForHotkey(self):
        self.hotkeyBtn.configure(text="Press any key...")
        keyboard.hook(self.captureHotkey)

    #Captures the hotkey user want to set
    def captureHotkey(self, event):
        if event.event_type != "down":
            return
        if event.name in ("shift", "ctrl", "alt", "left shift", "right shift", "left ctrl", "right ctrl", "left alt", "right alt"):
            return

        keyboard.unhook_all()

        mods = []
        if keyboard.is_pressed("ctrl"):
            mods.append("ctrl")
        if keyboard.is_pressed("shift"):
            mods.append("shift")
        if keyboard.is_pressed("alt"):
            mods.append("alt")

        mods.append(event.name)
        self.hotkey = "+".join(mods)
        self.hotkeyBtn.configure(text=f"Current: {self.hotkey}")
        threading.Thread(target=self.rebindHotkey, daemon=True).start()

    #Allows the app to rebind hotkey
    def rebindHotkey(self):
        keyboard.unhook_all()
        self.app.rebindAllHotkeys()

    #Binds the hotkey
    def bindHotkeys(self):
        if self.hotkeyHook:
            try:
                keyboard.remove_hotkey(self.hotkeyHook)
            except:
                pass
        self.hotkeyHook = keyboard.add_hotkey(self.hotkey, self.toggle)

#Class that store the macro
class Macro(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.is_recording = False
        self.is_playing = False
        self.recorded_events = []
        self.startTime = None

        self.app = app

        self.recordHotkey = "f7"
        self.playHotkey = "f8"
        self.recordHotkeyHook = None
        self.playHotkeyHook = None

        self.mouseController = pynmouse.Controller()
        self.keyboardController = pynkeys.Controller()

        self.createInterface()
        self.bindHotkeys()

    #Creates the interface for the macro
    def createInterface(self):
        self.recordBtn = ctk.CTkButton(self, text="Record", command=self.toggleRecord)
        self.recordBtn.pack(pady=10)

        self.playBtn = ctk.CTkButton(self, text="Play", command=self.play, state="disabled")
        self.playBtn.pack(pady=5)

        self.statusLabel = ctk.CTkLabel(self, text="Idle")
        self.statusLabel.pack(pady=5)

        ctk.CTkLabel(self, text="Record Hotkey").pack(pady=(10, 0))
        self.recordHotkeyBtn = ctk.CTkButton(self, text=f"Current: {self.recordHotkey}", command=self.listenForRecordHotkey)
        self.recordHotkeyBtn.pack(pady=5)

        ctk.CTkLabel(self, text="Play Hotkey").pack(pady=(5, 0))
        self.playHotkeyBtn = ctk.CTkButton(self, text=f"Current: {self.playHotkey}", command=self.listenForPlayHotkey)
        self.playHotkeyBtn.pack(pady=5)


    #Records user input
    def startRecording(self):
        self.recorded_events = []
        self.startTime = time.perf_counter()
        self.is_recording = True
        self.recordBtn.configure(text="Stop Recording")
        self.statusLabel.configure(text="Recording...")

        self.mouseListener = pynmouse.Listener(
            on_move=self.onMove,
            on_click=self.onClick,
            on_scroll=self.onScroll
        )
        self.keyListener = pynkeys.Listener(
            on_press=self.onKeyPress,
            on_release=self.onKeyRelease
        )
        self.mouseListener.start()
        self.keyListener.start()

    #Stops the input recording
    def stopRecording(self):
        self.is_recording = False
        self.mouseListener.stop()
        self.keyListener.stop()
        self.recordBtn.configure(text="Record")
        self.statusLabel.configure(text=f"Recorded {len(self.recorded_events)} events")
        self.playBtn.configure(state="normal")


    #Functions to append the input to the list
    def onMove(self, x, y):
        self.recorded_events.append(("move", time.perf_counter() - self.startTime, x, y))

    def onClick(self, x, y, button, pressed):
        self.recorded_events.append(("click", time.perf_counter() - self.startTime, x, y, button, pressed))

    def onScroll(self, x, y, dx, dy):
        self.recorded_events.append(("scroll", time.perf_counter() - self.startTime, x, y, dx, dy))

    def onKeyPress(self, key):
        resolved = self.resolveKey(key)
        if resolved == self.recordHotkey:
            return
        self.recorded_events.append(("keypress", time.perf_counter() - self.startTime, key))

    def onKeyRelease(self, key):
        resolved = self.resolveKey(key)
        if resolved == self.recordHotkey:
            return
        self.recorded_events.append(("keyrelease", time.perf_counter() - self.startTime, key))

    #Toggles the macro recording
    def toggleRecord(self):
        if not self.is_recording:
            self.startRecording()
        else:
            self.stopRecording()

    #Toggles the macro playing
    def play(self):
        if self.is_playing or self.is_recording:
            return
        threading.Thread(target=self.playback, daemon=True).start()

    #Converts the following key to readable key
    def resolveKey(self, key):
        if hasattr(key, 'char') and key.char:
            return key.char
        name = key.name if hasattr(key, 'name') else str(key)
        key_map = {
            "space": "space", "enter": "enter", "backspace": "backspace",
            "tab": "tab", "shift": "shift", "shift_l": "shiftleft",
            "shift_r": "shiftright", "ctrl_l": "ctrlleft", "ctrl_r": "ctrlright",
            "alt_l": "altleft", "alt_r": "altright", "caps_lock": "capslock",
            "esc": "escape", "delete": "delete", "home": "home", "end": "end",
            "page_up": "pageup", "page_down": "pagedown",
            "up": "up", "down": "down", "left": "left", "right": "right",
            "f1": "f1", "f2": "f2", "f3": "f3", "f4": "f4",
            "f5": "f5", "f6": "f6", "f7": "f7", "f8": "f8",
            "f9": "f9", "f10": "f10", "f11": "f11", "f12": "f12",
        }
        return key_map.get(name, name)

    #Simulates keyboard press on window using the Win32 API
    def sendKey(self, key, key_up=False):
        vk = None
        if hasattr(key, 'vk') and key.vk:
            vk = key.vk
        elif hasattr(key, 'value') and hasattr(key.value, 'vk'):
            vk = key.value.vk
        elif hasattr(key, 'char') and key.char:
            vk = ctypes.windll.user32.VkKeyScanA(ord(key.char)) & 0xFF
        if vk is None:
            return
        
        scan = ctypes.windll.user32.MapVirtualKeyW(vk, 0)
        KEYEVENTF_SCANCODE = 0x0008
        KEYEVENTF_KEYUP = 0x0002
        flags = KEYEVENTF_SCANCODE | (KEYEVENTF_KEYUP if key_up else 0)
        inp = INPUT(type=1, _input=_INP(ki=KEYBDINPUT(
            wVk=0, wScan=scan, dwFlags=flags, time=0,
            dwExtraInfo=ctypes.pointer(ctypes.c_ulong(0)))))
        ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

    #Plays the recording of user's input
    def playback(self):
        self.is_playing = True
        self.after(0, lambda: self.statusLabel.configure(text="Starting in 3s..."))
        time.sleep(0.001)
        self.after(0, lambda: self.statusLabel.configure(text="Playing..."))

        startTime = time.perf_counter()
        for event in self.recorded_events:
            while time.perf_counter() - startTime < event[1]:
                time.sleep(0.001)

            if event[0] == "move":
                pyautogui.moveTo(event[2], event[3])

            elif event[0] == "click":
                pyautogui.moveTo(event[2], event[3])
                btn = event[4].name
                if event[5]:
                    pyautogui.mouseDown(button=btn)
                else:
                    pyautogui.mouseUp(button=btn)

            elif event[0] == "scroll":
                pyautogui.scroll(int(event[5]), x=event[2], y=event[3])

            elif event[0] == "keypress":
                try:
                    self.sendKey(event[2], key_up=False)
                except Exception:
                    pass

            elif event[0] == "keyrelease":
                try:
                    self.sendKey(event[2], key_up=True)
                except Exception:
                    pass

        self.is_playing = False
        self.after(0, lambda: self.statusLabel.configure(text="Done"))


    #Binds hotkey to key specified by user
    def bindHotkeys(self):
        if self.recordHotkeyHook:
            try:
                keyboard.remove_hotkey(self.recordHotkeyHook)
            except:
                pass
        if self.playHotkeyHook:
            try:
                keyboard.remove_hotkey(self.playHotkeyHook)
            except:
                pass
        self.recordHotkeyHook = keyboard.add_hotkey(self.recordHotkey, self.toggleRecord)
        self.playHotkeyHook = keyboard.add_hotkey(self.playHotkey, self.play)

    def listenForRecordHotkey(self):
        self.recordHotkeyBtn.configure(text="Press any key...")
        keyboard.hook(lambda e: self.captureHotkey(e, "record"))

    def listenForPlayHotkey(self):
        self.playHotkeyBtn.configure(text="Press any key...")
        keyboard.hook(lambda e: self.captureHotkey(e, "play"))

    def captureHotkey(self, event, target):
        if event.event_type != "down":
            return
        if event.name in ("shift", "ctrl", "alt", "left shift", "right shift", "left ctrl", "right ctrl", "left alt", "right alt"):
            return

        keyboard.unhook_all()

        mods = []
        if keyboard.is_pressed("ctrl"):  mods.append("ctrl")
        if keyboard.is_pressed("shift"): mods.append("shift")
        if keyboard.is_pressed("alt"):   mods.append("alt")
        mods.append(event.name)
        hotkey = "+".join(mods)

        if target == "record":
            self.recordHotkey = hotkey
            self.after(0, lambda: self.recordHotkeyBtn.configure(text=f"Current: {hotkey}"))
        else:
            self.playHotkey = hotkey
            self.after(0, lambda: self.playHotkeyBtn.configure(text=f"Current: {hotkey}"))

        threading.Thread(target=self.rebindHotkeys, daemon=True).start()

    def rebindHotkeys(self):
        keyboard.unhook_all()
        self.app.rebindAllHotkeys()


if __name__ == "__main__":
    app = App()
    app.mainloop()