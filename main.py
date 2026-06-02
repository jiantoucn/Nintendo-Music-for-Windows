import webview
import sys
import os
import time
import json
import threading
import ctypes
import winreg
from urllib.parse import urlparse
from pathlib import Path

VERSION = "v2.2.0"
APP_NAME = "NintendoMusic"
APP_TITLE = "Nintendo Music for Windows"
ALLOWED_DOMAIN = "nintendo.com"
START_URL = "https://music.nintendo.com/"
CONFIG_DIR = Path(os.environ.get("APPDATA", "")) / APP_NAME
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "auto_start": False,
    "background_run": None,
    "remember_background": False,
    "language": "auto",
}


def load_config():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for key, val in DEFAULT_CONFIG.items():
                    if key not in data:
                        data[key] = val
                return data
        except Exception:
            pass
    return dict(DEFAULT_CONFIG)


def save_config(cfg):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


config = load_config()


def detect_system_lang():
    try:
        lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        primary = lang_id & 0x3FF
        if primary == 0x04:
            return "zh"
    except Exception:
        pass
    return "en"


def get_lang():
    pref = config.get("language", "auto")
    if pref in ("zh", "en"):
        return pref
    return detect_system_lang()


LANG = get_lang()


def build_strings(lang):
    return {
        "settings": {"zh": "设置", "en": "Settings"}[lang],
        "home": {"zh": "返回主页", "en": "Return to Home"}[lang],
        "clear_cookies": {"zh": "清除 Cookies 和缓存", "en": "Clear Cookies and Cache"}[lang],
        "auto_start": {"zh": "开机自启", "en": "Auto Start"}[lang],
        "background_run": {"zh": "后台运行", "en": "Background Run"}[lang],
        "on": {"zh": "开启", "en": "ON"}[lang],
        "off": {"zh": "关闭", "en": "OFF"}[lang],
        "ask": {"zh": "每次询问", "en": "ASK"}[lang],
        "always": {"zh": "始终后台", "en": "Always"}[lang],
        "never": {"zh": "始终退出", "en": "Never"}[lang],
        "about": {"zh": "关于", "en": "About"}[lang],
        "exit_app": {"zh": "退出", "en": "Exit"}[lang],
        "language": {"zh": "语言", "en": "Language"}[lang],
        "lang_auto": {"zh": "跟随系统", "en": "Follow System"}[lang],
        "lang_zh": {"zh": "中文", "en": "Chinese"}[lang],
        "lang_en": {"zh": "英文", "en": "English"}[lang],
        "about_title": {"zh": "关于", "en": "About"}[lang],
        "about_text": {
            "zh": f"{APP_TITLE}\n版本: {VERSION}\n\n此软件由 Sayaka 开发\n使用 Trae CN 配合 MiMo-V2.5-Pro 开发",
            "en": f"{APP_TITLE}\nVersion: {VERSION}\n\nDeveloped by Sayaka\nUsing Trae CN with MiMo-V2.5-Pro",
        }[lang],
        "tray_show": {"zh": "显示窗口", "en": "Show Window"}[lang],
        "tray_quit": {"zh": "退出", "en": "Quit"}[lang],
        "ok": {"zh": "确定", "en": "OK"}[lang],
        "bg_prompt": {
            "zh": "是否在后台运行？\n\n是 = 最小化到系统托盘\n否 = 完全退出\n取消 = 下次再问",
            "en": "Keep running in the background?\n\nYes = Minimize to system tray\nNo = Exit completely\nCancel = Ask me next time",
        }[lang],
        "remember_prompt": {
            "zh": "记住这个选择？\n\n是 = 每次都这样\n否 = 每次都问",
            "en": "Remember this choice?\n\nYes = Always\nNo = Ask each time",
        }[lang],
        "restart_hint": {
            "zh": "语言设置已保存，下次启动时生效。",
            "en": "Language setting saved. It will take effect on next launch.",
        }[lang],
        "already_running": {
            "zh": "Nintendo Music 已经在运行中。\n\n是否关闭之前的实例并重新打开？",
            "en": "Nintendo Music is already running.\n\nDo you want to close the previous instance and reopen?",
        }[lang],
    }


T = build_strings(LANG)

JS_BLOCK_NAV = """
(function() {
    if (window.__nintendo_nav_blocked) return;
    window.__nintendo_nav_blocked = true;
    function isAllowed(url) {
        try {
            var h = new URL(url, document.baseURI).hostname;
            return h === 'nintendo.com' || h.endsWith('.nintendo.com');
        } catch(e) { return true; }
    }
    document.addEventListener('click', function(e) {
        var link = e.target.closest('a');
        if (link && link.href && !isAllowed(link.href)) {
            e.preventDefault();
            e.stopPropagation();
        }
    }, true);
    var origOpen = window.open;
    window.open = function(url) {
        if (!url) return null;
        if (!isAllowed(url)) return null;
        return origOpen.apply(window, arguments);
    };
    document.addEventListener('submit', function(e) {
        var form = e.target;
        if (form && form.action && !isAllowed(form.action)) {
            e.preventDefault();
            e.stopPropagation();
        }
    }, true);
})();
"""

JS_MEDIA_CONTROL = """
(function() {
    if (window.__nintendo_media_ctrl) return;
    window.__nintendo_media_ctrl = true;
    function findPlayer() {
        var audio = document.querySelector('audio');
        var video = document.querySelector('video');
        if (audio || video) return audio || video;
        var btns = document.querySelectorAll('[aria-label]');
        for (var i = 0; i < btns.length; i++) {
            var label = (btns[i].getAttribute('aria-label') || '').toLowerCase();
            if (label.includes('play') || label.includes('pause')) return btns[i];
        }
        return null;
    }
    window.__nintendo_toggle_play = function() {
        var el = findPlayer();
        if (!el) return;
        if (el.tagName === 'AUDIO' || el.tagName === 'VIDEO') {
            el.paused ? el.play() : el.pause();
        } else { el.click(); }
    };
    window.__nintendo_next = function() {
        var el = document.querySelector('[aria-label*="Next"],[aria-label*="next"],[aria-label*="Skip"],[aria-label*="skip"]');
        if (el) el.click();
    };
    window.__nintendo_prev = function() {
        var el = document.querySelector('[aria-label*="Previous"],[aria-label*="previous"],[aria-label*="Back"],[aria-label*="back"]');
        if (el) el.click();
    };
})();
"""


def is_allowed_url(url):
    if not url:
        return False
    lower = url.lower()
    if lower.startswith("about:") or lower.startswith("data:") or lower.startswith("javascript:"):
        return True
    try:
        parsed = urlparse(lower)
        hostname = parsed.hostname or ""
        return hostname == ALLOWED_DOMAIN or hostname.endswith("." + ALLOWED_DOMAIN)
    except Exception:
        return False


def get_resource_path(filename):
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, filename)


def get_icon_path():
    icon = get_resource_path("icon.ico")
    return icon if os.path.isfile(icon) else ""


def set_auto_start(enable):
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    exe_path = sys.executable if getattr(sys, "frozen", False) else f'"{sys.executable}" "{os.path.abspath(__file__)}"'
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            if enable:
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exe_path)
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                except FileNotFoundError:
                    pass
    except Exception:
        pass


def start_hotkey_listener(window):
    try:
        import pynput.keyboard as keyboard

        def on_press(key):
            try:
                if key == keyboard.Key.media_play_pause:
                    window.evaluate_js("window.__nintendo_toggle_play && window.__nintendo_toggle_play()")
                elif key == keyboard.Key.media_next:
                    window.evaluate_js("window.__nintendo_next && window.__nintendo_next()")
                elif key == keyboard.Key.media_previous:
                    window.evaluate_js("window.__nintendo_prev && window.__nintendo_prev()")
            except Exception:
                pass

        listener = keyboard.Listener(on_press=on_press)
        listener.daemon = True
        listener.start()
    except ImportError:
        pass


def create_tray(app):
    try:
        import pystray
        from PIL import Image, ImageDraw

        icon_path = get_icon_path()
        if icon_path and os.path.isfile(icon_path):
            tray_image = Image.open(icon_path)
        else:
            tray_image = Image.new("RGB", (64, 64), (230, 0, 18))
            draw = ImageDraw.Draw(tray_image)
            draw.rectangle([16, 16, 48, 48], fill=(255, 255, 255))

        def on_show(icon, item):
            app.show_window()

        def on_quit(icon, item):
            app.quit_app()

        menu = pystray.Menu(
            pystray.MenuItem(T["tray_show"], on_show, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(T["tray_quit"], on_quit),
        )

        tray = pystray.Icon(APP_NAME, tray_image, APP_TITLE, menu)
        app.tray_icon = tray
        tray.run()
    except ImportError:
        pass


class App:
    def __init__(self):
        self.main_window = None
        self.tray_icon = None
        self.should_exit = False
        self._form = None
        self._menu_refs = {}
        self._mutex = None

    def on_loaded(self, window):
        window.evaluate_js(JS_BLOCK_NAV)
        window.evaluate_js(JS_MEDIA_CONTROL)

    def on_monitor(self, window):
        last_url = ""
        while not self.should_exit:
            try:
                current_url = window.evaluate_js("window.location.href")
                if current_url and isinstance(current_url, str) and current_url != last_url:
                    last_url = current_url
                    if not is_allowed_url(current_url):
                        window.load_url(START_URL)
                        last_url = START_URL
            except Exception:
                pass
            time.sleep(0.5)

    def do_clear_cookies(self):
        if self.main_window:
            self.main_window.clear_cookies()
            self.main_window.load_url(START_URL)

    def do_go_home(self):
        if self.main_window:
            self.main_window.load_url(START_URL)

    def set_auto_start_val(self, val):
        config["auto_start"] = val
        set_auto_start(val)
        save_config(config)
        self._update_menu_checkmarks()

    def set_background_run_val(self, val):
        config["background_run"] = val
        config["remember_background"] = True
        save_config(config)
        self._update_menu_checkmarks()

    def set_language(self, lang_code):
        config["language"] = lang_code
        save_config(config)
        if self._form is not None:
            try:
                import clr
                clr.AddReference('System.Windows.Forms')
                import System
                import System.Windows.Forms as WinForms

                def _msg():
                    WinForms.MessageBox.Show(
                        T["restart_hint"],
                        APP_TITLE,
                        WinForms.MessageBoxButtons.OK,
                        WinForms.MessageBoxIcon.Information,
                    )
                if self._form.InvokeRequired:
                    self._form.Invoke(System.Action(_msg))
                else:
                    _msg()
            except Exception:
                pass

    def show_about(self):
        if self._form is None:
            return
        try:
            import clr
            clr.AddReference('System.Windows.Forms')
            clr.AddReference('System.Drawing')
            import System
            import System.Windows.Forms as WinForms
            from System.Drawing import Size as DSize, Point as DPoint, Image as DImage

            def _show():
                form = WinForms.Form()
                form.Text = T["about_title"]
                form.Size = DSize(440, 280)
                form.StartPosition = WinForms.FormStartPosition.CenterScreen
                form.FormBorderStyle = WinForms.FormBorderStyle.FixedDialog
                form.MaximizeBox = False
                form.MinimizeBox = False

                logo_path = get_resource_path("LOGO.png")
                if os.path.isfile(logo_path):
                    logo = WinForms.PictureBox()
                    logo.Image = DImage.FromFile(logo_path)
                    logo.SizeMode = WinForms.PictureBoxSizeMode.Zoom
                    logo.Size = DSize(120, 120)
                    logo.Location = DPoint(20, 30)
                    form.Controls.Add(logo)

                label = WinForms.Label()
                label.Text = T["about_text"]
                label.Location = DPoint(160, 30)
                label.Size = DSize(250, 150)
                label.Font = System.Drawing.Font(label.Font.FontFamily, 11)
                form.Controls.Add(label)

                ok = WinForms.Button()
                ok.Text = T["ok"]
                ok.Location = DPoint(170, 200)
                ok.Size = DSize(80, 30)
                ok.Click += lambda s, e: form.Close()
                form.Controls.Add(ok)

                form.ShowDialog()

            if self._form.InvokeRequired:
                self._form.Invoke(System.Action(_show))
            else:
                _show()
        except Exception as e:
            print(f"About dialog error: {e}")

    def show_window(self):
        if self.main_window:
            try:
                self.main_window.show()
            except Exception:
                pass

    def hide_window(self):
        if self.main_window:
            try:
                self.main_window.hide()
            except Exception:
                pass

    def quit_app(self):
        self.should_exit = True
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
        if self.main_window:
            try:
                self.main_window.destroy()
            except Exception:
                pass
        release_mutex(self._mutex)
        os._exit(0)

    def start_tray(self):
        if self.tray_icon is not None:
            return
        t = threading.Thread(target=create_tray, args=(self,), daemon=True)
        t.start()

    def setup_menu(self):
        if self._form is None:
            return
        try:
            import clr
            clr.AddReference('System.Windows.Forms')
            import System
            import System.Windows.Forms as WinForms

            refs = self._menu_refs

            def _create():
                menu_strip = WinForms.MenuStrip()
                top_menu = WinForms.ToolStripMenuItem(T["settings"])

                home = WinForms.ToolStripMenuItem(T["home"])
                home.Click += lambda s, e: threading.Thread(target=self.do_go_home, daemon=True).start()

                clear = WinForms.ToolStripMenuItem(T["clear_cookies"])
                clear.Click += lambda s, e: threading.Thread(target=self.do_clear_cookies, daemon=True).start()

                auto_menu = WinForms.ToolStripMenuItem(T["auto_start"])
                auto_off = WinForms.ToolStripMenuItem(T["off"])
                auto_on = WinForms.ToolStripMenuItem(T["on"])
                auto_off.Click += lambda s, e: self.set_auto_start_val(False)
                auto_on.Click += lambda s, e: self.set_auto_start_val(True)
                auto_menu.DropDownItems.Add(auto_off)
                auto_menu.DropDownItems.Add(auto_on)

                bg_menu = WinForms.ToolStripMenuItem(T["background_run"])
                bg_ask = WinForms.ToolStripMenuItem(T["ask"])
                bg_always = WinForms.ToolStripMenuItem(T["always"])
                bg_never = WinForms.ToolStripMenuItem(T["never"])
                bg_ask.Click += lambda s, e: self.set_background_run_val(None)
                bg_always.Click += lambda s, e: self.set_background_run_val(True)
                bg_never.Click += lambda s, e: self.set_background_run_val(False)
                bg_menu.DropDownItems.Add(bg_ask)
                bg_menu.DropDownItems.Add(bg_always)
                bg_menu.DropDownItems.Add(bg_never)

                lang_menu = WinForms.ToolStripMenuItem(T["language"])
                lang_auto = WinForms.ToolStripMenuItem(T["lang_auto"])
                lang_zh = WinForms.ToolStripMenuItem(T["lang_zh"])
                lang_en = WinForms.ToolStripMenuItem(T["lang_en"])
                lang_auto.Click += lambda s, e: self.set_language("auto")
                lang_zh.Click += lambda s, e: self.set_language("zh")
                lang_en.Click += lambda s, e: self.set_language("en")
                lang_menu.DropDownItems.Add(lang_auto)
                lang_menu.DropDownItems.Add(lang_zh)
                lang_menu.DropDownItems.Add(lang_en)

                about = WinForms.ToolStripMenuItem(T["about"])
                about.Click += lambda s, e: threading.Thread(target=self.show_about, daemon=True).start()

                exit_item = WinForms.ToolStripMenuItem(T["exit_app"])
                exit_item.Click += lambda s, e: self.quit_app()

                top_menu.DropDownItems.Add(home)
                top_menu.DropDownItems.Add(WinForms.ToolStripSeparator())
                top_menu.DropDownItems.Add(clear)
                top_menu.DropDownItems.Add(WinForms.ToolStripSeparator())
                top_menu.DropDownItems.Add(auto_menu)
                top_menu.DropDownItems.Add(bg_menu)
                top_menu.DropDownItems.Add(lang_menu)
                top_menu.DropDownItems.Add(WinForms.ToolStripSeparator())
                top_menu.DropDownItems.Add(about)
                top_menu.DropDownItems.Add(WinForms.ToolStripSeparator())
                top_menu.DropDownItems.Add(exit_item)

                menu_strip.Items.Add(top_menu)
                self._form.MainMenuStrip = menu_strip
                self._form.Controls.Add(menu_strip)

                refs["auto_off"] = auto_off
                refs["auto_on"] = auto_on
                refs["bg_ask"] = bg_ask
                refs["bg_always"] = bg_always
                refs["bg_never"] = bg_never
                refs["lang_auto"] = lang_auto
                refs["lang_zh"] = lang_zh
                refs["lang_en"] = lang_en

                self._update_checkmarks_impl()

            if self._form.InvokeRequired:
                self._form.Invoke(System.Action(_create))
            else:
                _create()
        except Exception as e:
            print(f"Menu setup error: {e}")

    def _update_checkmarks_impl(self):
        refs = self._menu_refs
        if not refs:
            return
        auto = config["auto_start"]
        refs["auto_off"].Checked = not auto
        refs["auto_on"].Checked = auto
        bg = config.get("background_run")
        refs["bg_ask"].Checked = (bg is None)
        refs["bg_always"].Checked = (bg is True)
        refs["bg_never"].Checked = (bg is False)
        lang = config.get("language", "auto")
        refs["lang_auto"].Checked = (lang == "auto")
        refs["lang_zh"].Checked = (lang == "zh")
        refs["lang_en"].Checked = (lang == "en")

    def _update_menu_checkmarks(self):
        if self._form is None:
            return
        try:
            import System
            if self._form.InvokeRequired:
                self._form.Invoke(System.Action(self._update_checkmarks_impl))
            else:
                self._update_checkmarks_impl()
        except Exception:
            pass


MUTEX_NAME = "Global\\NintendoMusicSingleInstance"
ERROR_ALREADY_EXISTS = 183


def create_mutex(name):
    return ctypes.windll.kernel32.CreateMutexW(None, True, name)


def release_mutex(handle):
    if handle:
        ctypes.windll.kernel32.ReleaseMutex(handle)
        ctypes.windll.kernel32.CloseHandle(handle)


def check_single_instance():
    mutex = create_mutex(MUTEX_NAME)
    last_error = ctypes.windll.kernel32.GetLastError()
    if last_error == ERROR_ALREADY_EXISTS:
        return False, mutex
    return True, mutex


def find_and_kill_existing_window():
    import ctypes.wintypes

    ENUM_WINDOWS_PROC = ctypes.WINFUNCTYPE(
        ctypes.c_bool, ctypes.wintypes.LPARAM, ctypes.wintypes.LPARAM
    )

    target_title = APP_TITLE
    found_pids = []

    def enum_callback(hwnd, _):
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
            if buf.value == target_title:
                pid = ctypes.wintypes.DWORD()
                ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                if pid.value != os.getpid():
                    found_pids.append(pid.value)
        return True

    ctypes.windll.user32.EnumWindows(ENUM_WINDOWS_PROC(enum_callback), 0)

    for pid in found_pids:
        try:
            handle = ctypes.windll.kernel32.OpenProcess(0x0001, False, pid)
            if handle:
                ctypes.windll.kernel32.TerminateProcess(handle, 0)
                ctypes.windll.kernel32.CloseHandle(handle)
        except Exception:
            pass


def main():
    webview.settings['OPEN_EXTERNAL_LINKS_IN_BROWSER'] = False
    set_auto_start(config["auto_start"])

    is_first, mutex = check_single_instance()
    if not is_first:
        result = ctypes.windll.user32.MessageBoxW(
            0,
            T["already_running"],
            APP_TITLE,
            0x04 | 0x20,
        )
        if result == 6:
            find_and_kill_existing_window()
            time.sleep(1)
            release_mutex(mutex)
            is_first, mutex = check_single_instance()
            if not is_first:
                release_mutex(mutex)
                os._exit(0)
        else:
            release_mutex(mutex)
            os._exit(0)

    app = App()
    app._mutex = mutex
    icon_path = get_icon_path()

    app.main_window = webview.create_window(
        title=APP_TITLE,
        url=START_URL,
        width=1280,
        height=800,
        min_size=(800, 600),
        text_select=True,
    )
    app.main_window.events.loaded += app.on_loaded

    def on_closing(window):
        if app.should_exit:
            return True

        bg_run = config.get("background_run")

        if bg_run is True:
            window.hide()
            app.start_tray()
            return False

        if bg_run is False:
            return True

        result = ctypes.windll.user32.MessageBoxW(
            0,
            T["bg_prompt"],
            APP_TITLE,
            0x03 | 0x20,
        )
        if result == 6:
            remember = ctypes.windll.user32.MessageBoxW(
                0,
                T["remember_prompt"],
                APP_TITLE,
                0x04 | 0x20,
            )
            if remember == 6:
                config["background_run"] = True
                config["remember_background"] = True
                save_config(config)
            window.hide()
            app.start_tray()
            return False
        elif result == 7:
            remember = ctypes.windll.user32.MessageBoxW(
                0,
                T["remember_prompt"],
                APP_TITLE,
                0x04 | 0x20,
            )
            if remember == 6:
                config["background_run"] = False
                config["remember_background"] = True
                save_config(config)
            return True
        return False

    app.main_window.events.closing += on_closing

    def start_app(window):
        window.events.shown.wait(timeout=15)
        time.sleep(1)
        try:
            import clr
            clr.AddReference('System.Windows.Forms')
            import System.Windows.Forms as WinForms
            forms = WinForms.Application.OpenForms
            if forms.Count > 0:
                app._form = forms[0]
        except Exception:
            pass
        app.setup_menu()
        start_hotkey_listener(window)
        t = threading.Thread(target=app.on_monitor, args=(window,), daemon=True)
        t.start()

    start_kwargs = dict(func=start_app, args=(app.main_window,), private_mode=False)
    if icon_path:
        start_kwargs["icon"] = icon_path
    webview.start(**start_kwargs)


if __name__ == "__main__":
    main()
