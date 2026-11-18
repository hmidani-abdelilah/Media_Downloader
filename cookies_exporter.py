# ملف استخراج  cookies من متصفح الويب باستخدام yt-dlp
#
import pathlib
import yt_dlp
import os

# دالة لتحديد مسار مجلد التكوين XDG_CONFIG_HOME، والذي يستخدم بشكل افتراضي ~/.config على نظام Linux.
def _xdg_config() -> pathlib.Path:
    """
    Return XDG_CONFIG_HOME — defaults to ~/.config on Linux.
    ارجاع XDG_CONFIG_HOME - الافتراضي هو ~/.config على نظام Linux.
    """
    return pathlib.Path(os.environ.get("XDG_CONFIG_HOME", str(pathlib.Path.home() / ".config")))

# ---------------------------------------------------------------------------
# All supported browsers: (yt-dlp key, display name, profile paths per OS) 
# كل المتصفحات المدعومة: (مفتاح yt-dlp، الاسم المعروض، مسارات الملفات الشخصية لكل نظام تشغيل)
# Covers: classic Linux, XDG Base Dir (Fedora/openSUSE/…), snap, flatpak, macOS, Windows
# يغطي: Linux الكلاسيكي، XDG Base Dir (Fedora/openSUSE/…) ، snap، flatpak، macOS، Windows
# ---------------------------------------------------------------------------
BROWSERS = [
    {
        "key":  "firefox",
        "name": "Firefox",
        "paths": [
            pathlib.Path.home() / ".mozilla" / "firefox",                                            # Linux classic
            _xdg_config() / "mozilla" / "firefox",                                                   # Linux XDG (Fedora, openSUSE…)
            pathlib.Path.home() / "snap" / "firefox" / "common" / ".mozilla" / "firefox",            # Linux snap
            pathlib.Path.home() / ".var" / "app" / "org.mozilla.firefox" / ".mozilla" / "firefox",   # Linux flatpak
            pathlib.Path.home() / "Library" / "Application Support" / "Firefox",                     # macOS
            pathlib.Path(os.environ.get("APPDATA", "")) / "Mozilla" / "Firefox",                     # Windows
        ],
    },
    {
        "key":  "chrome",
        "name": "Chrome",
        "paths": [
            pathlib.Path.home() / ".config" / "google-chrome",                                       # Linux classic
            _xdg_config() / "google-chrome",                                                          # Linux XDG
            pathlib.Path.home() / "snap" / "google-chrome" / "common" / "default",                   # Linux snap
            pathlib.Path.home() / ".var" / "app" / "com.google.Chrome" / "config" / "google-chrome", # Linux flatpak
            pathlib.Path.home() / "Library" / "Application Support" / "Google" / "Chrome",           # macOS
            pathlib.Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "User Data",    # Windows
        ],
    },
    {
        "key":  "chromium",
        "name": "Chromium",
        "paths": [
            pathlib.Path.home() / ".config" / "chromium",
            _xdg_config() / "chromium",
            pathlib.Path.home() / "snap" / "chromium" / "common" / "chromium",                       # Linux snap
            pathlib.Path.home() / ".var" / "app" / "org.chromium.Chromium" / "config" / "chromium",  # Linux flatpak
            pathlib.Path.home() / "Library" / "Application Support" / "Chromium",                    # macOS
            pathlib.Path(os.environ.get("LOCALAPPDATA", "")) / "Chromium" / "User Data",             # Windows
        ],
    },
    {
        "key":  "brave",
        "name": "Brave",
        "paths": [
            pathlib.Path.home() / ".config" / "BraveSoftware" / "Brave-Browser",
            _xdg_config() / "BraveSoftware" / "Brave-Browser",
            pathlib.Path.home() / ".var" / "app" / "com.brave.Browser" / "config" / "BraveSoftware" / "Brave-Browser",  # flatpak
            pathlib.Path.home() / "Library" / "Application Support" / "BraveSoftware" / "Brave-Browser",  # macOS
            pathlib.Path(os.environ.get("LOCALAPPDATA", "")) / "BraveSoftware" / "Brave-Browser" / "User Data",  # Windows
        ],
    },
    {
        "key":  "edge",
        "name": "Edge",
        "paths": [
            pathlib.Path.home() / ".config" / "microsoft-edge",
            _xdg_config() / "microsoft-edge",
            pathlib.Path.home() / "Library" / "Application Support" / "Microsoft Edge",              # macOS
            pathlib.Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Edge" / "User Data",  # Windows
        ],
    },
    {
        "key":  "opera",
        "name": "Opera",
        "paths": [
            pathlib.Path.home() / ".config" / "opera",
            _xdg_config() / "opera",
            pathlib.Path.home() / "Library" / "Application Support" / "com.operasoftware.Opera",    # macOS
            pathlib.Path(os.environ.get("APPDATA", "")) / "Opera Software" / "Opera Stable",        # Windows
        ],
    },
    {
        "key":  "vivaldi",
        "name": "Vivaldi",
        "paths": [
            pathlib.Path.home() / ".config" / "vivaldi",
            _xdg_config() / "vivaldi",
            pathlib.Path.home() / "Library" / "Application Support" / "Vivaldi",                    # macOS
            pathlib.Path(os.environ.get("LOCALAPPDATA", "")) / "Vivaldi" / "User Data",             # Windows
        ],
    },
    {
        "key":  "safari",
        "name": "Safari",
        "paths": [
            pathlib.Path.home() / "Library" / "Safari",   # macOS only
        ],
    },
]


def is_browser_installed(browser: dict) -> bool:
    """
    Return True if any known profile path for this browser exists.
    ارجاع True إذا كان أي مسار ملف تعريف معروف لهذا المتصفح موجودًا.
    """
    return any(p.exists() for p in browser["paths"])


def cookies_to_netscape(cookies) -> str:
    """
    Convert a list of http.cookiejar.Cookie objects to Netscape format string.
    تحول قائمة من كائنات http.cookiejar.Cookie إلى سلسلة بتنسيق Netscape.
    """
    lines = ["# Netscape HTTP Cookie File\n"]
    for c in cookies:
        domain  = c.domain or ""
        flag    = "TRUE" if domain.startswith(".") else "FALSE"
        secure  = "TRUE" if c.secure else "FALSE"
        expires = str(int(c.expires)) if c.expires else "0"
        value   = c.value if c.value is not None else ""
        lines.append(f"{domain}\t{flag}\t{c.path}\t{secure}\t{expires}\t{c.name}\t{value}\n")
    return "".join(lines)


def extract_cookies_from_browser(browser_key: str) -> list:
    """
    Use yt-dlp to load cookies from the given browser.
    Returns a list of http.cookiejar.Cookie objects.
    Raises an exception on failure.
    Works on Linux, macOS, Windows.

    استخدم yt-dlp لتحميل ملفات تعريف الارتباط من المتصفح المحدد.
    يعيد قائمة من كائنات http.cookiejar.Cookie.
    يثير استثناءً عند الفشل.
    يعمل على Linux و macOS و Windows.
    """
    ydl_opts = {
        "cookiesfrombrowser": (browser_key, None, None, None),
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return list(ydl.cookiejar)
