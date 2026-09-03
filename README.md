# <div align="center"> Media Downloader  </div>   
<div align="center">
   
[![Python](https://img.shields.io/badge/Python-3.14-blueviolet.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![MIT License](https://img.shields.io/badge/License-MIT-orange.svg?style=for-the-badge&logo=MIT)](https://github.com/hmidani-abdelilah/Media_Downloader?tab=MIT-1-ov-file)
[![linux](https://img.shields.io/badge/linux-Distribution-FCC624.svg?style=for-the-badge&logo=linux)](#option-2-using-linux-installation-script-)
[![Windows](https://img.shields.io/badge/Windows-OS-blue.svg?style=for-the-badge&logo=wine)](https://github.com/hmidani-abdelilah/Media_Downloader/releases/download/v3.1.0/Media_Downloader-3.1.0-Windows.zip)
[![Ubuntu](https://img.shields.io/badge/Ubuntu-PPA-E95420.svg?style=for-the-badge&logo=ubuntu)](https://launchpad.net/~kiraxq/+archive/ubuntu/ppa)
[![Bugs Report](https://img.shields.io/badge/Issues-Report%20a%20bug-important?style=for-the-badge&logo=github&logoColor=white)](https://github.com/hmidani-abdelilah/Media_Downloader/issues)<br>
<a href="https://github.com/hmidani-abdelilah/Media_Downloader/tree/main/.github/workflows" target="_blank"><img alt="Build Status" src="https://raw.githubusercontent.com/hmidani-abdelilah/Media_Downloader/c198b34776a74979d43498c161e968d85e2084f7/.github/workflows/badge.svg" /></a><br>
<a href="https://github.com/hmidani-abdelilah/Media_Downloader/releases/latest"><img alt="Get it on GitHub" src="https://raw.githubusercontent.com/hmidani-abdelilah/Media_Downloader/refs/heads/main/get-github.png" height="45" /></a>

**[English](#-english) · [العربية](#-العربية)**


</div>   

![Media Downloader GUI Screenshot Application ](https://raw.githubusercontent.com/hmidani-abdelilah/Media_Downloader/refs/heads/main/Screenshots/Screenshot%20From%202026-08-24%2013-22-57.png "Media Downloader GUI")

## 🌐 English

A graphical application for downloading videos and audio from YouTube and other platforms (Facebook, Instagram, X.com , TikTok ... ) and more using `yt-dlp`, with quality control, subtitle support, language switching, and dark/light themes.

### 🚀 Features

- Download from **YouTube**, **Facebook**, **Instagram**, and **X.com (Twitter)**
- Download video (`mp4` `mkv` , `avi`, `flv` , `webm` ) or audio (`mp3`, `aac` , `flac` , `wav` , `opus` , `alac` , `m4a` , `ogg` )
- Select quality: Low (360p), Medium (720p), High (1080p), Ultra (1440p)
- Optional **subtitles** download with language selection (supports English, Arabic, French)
- Full **GUI** using `customtkinter`
- Multilingual: **English**, **Arabic**, **French**
- Theme support: Light / Dark / System
- Playlist support with auto-folder creation and an optional inclusive video range (for example, 5–10; leave the end empty to continue to the last video)
- Optional video/audio cutting by start/end time, with subtitle timestamps adjusted to the selected clip
- Checks for **FFmpeg** and **Aria2c** availability (local or system)
- Supports **Aria2c** as external downloader for faster downloads
- Cookies file support for private/protected videos
- Export cookies from browser use [Get cookies LOCALLY](https://chromewebstore.google.com/detail/cclelndahbckbenkjhflpdbgdldlbecc?utm_source=item-share-cb)
- **Drag-and-drop URL support** - Simply drag URLs into the input field
- Context menu for URL input (cut, paste, clear)
- Notification on download completion
- Automatic external yt-dlp updates in AppImage builds
- Option to shutdown computer after download
- Ability to stop ongoing downloads
- Menu bar with help and options
- Cross-platform (Windows/Linux/macOS)

Compression support:
- After a video is downloaded the app can optionally compress/re-encode it using FFmpeg (CRF + preset, encoder selection).
- Compression runs as a separate post-download step so the UI shows a "Compressing video..." state.
- The Stop button cancels both downloading and any ongoing FFmpeg compression (requires FFmpeg on the system).

### 🧰 Requirements

- Python 3.10+
- FFmpeg (included in `ffmpeg` folder or installed on system) [FFmpeg _Windows](https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip) or install by command CMD by package manager

```bash
winget install ffmpeg
```

- Aria2c (included in `aria2` folder or installed on system) [Aria2c_Windows](https://github.com/aria2/aria2/releases/download/release-1.37.0/aria2-1.37.0-win-64bit-build1.zip) 

Install dependencies using:

```bash
pip install -r requirements.txt
```

### 💻 How to Run

#### **Option 1: Using Python (All Platforms)**

```bash
python app.py
```

#### **Option 2: Using Linux Installation Script 🐧**

**For Linux Users**, an automated installer script is provided:

##### **`installer.sh`** 🔧
This script automates the complete setup process for Linux users:

**What it does:**
- ✅ Checks if the script is run with sudo/root privileges
- ✅ Detects your Linux distribution (Ubuntu, Debian, Fedora, Arch, etc.)
- ✅ Installs system dependencies (Python3, pip, venv, FFmpeg, Git)
- ✅ Clones the Media_Downloader repository (or updates it if already present)
- ✅ Creates a Python virtual environment
- ✅ Installs all Python dependencies from `requirements.txt`
- ✅ Sets up a desktop entry for easy application launching
- ✅ Configures the application icon

**How to use:**
1. Make the script executable:
   ```bash
   chmod +x installer.sh
   ```
2. Run the installer with sudo:
   ```bash
   sudo ./installer.sh
   ```
3. To uninstall later, run:
   ```bash
   sudo ./installer.sh uninstall
   ```
4. To see help and usage options:
   ```bash
   sudo ./installer.sh --help
   ```
5. Wait for the process to complete
6. The application will be available in your applications menu

**Supported Distributions 🐧:**
- Ubuntu, Debian, Linux Mint, Kali Linux, Raspbian
- Fedora
- RHEL, CentOS, Rocky Linux, AlmaLinux
- Arch Linux, Manjaro, EndeavourOS, Garuda Linux

Prebuilt packages are also available:

- [DEB package](https://github.com/hmidani-abdelilah/Media_Downloader/releases/download/v3.1.0/media-downloader_3.1.0_all.deb)
- [RPM package](https://github.com/hmidani-abdelilah/Media_Downloader/releases/download/v3.1.0/media-downloader-3.1.0-1.noarch.rpm)
- [AppImage](https://github.com/hmidani-abdelilah/Media_Downloader/releases/download/v3.1.0/Media_Downloader-3.1.0-x86_64.AppImage)

Ubuntu and Ubuntu-based distributions can use the PPA:

```bash
sudo add-apt-repository ppa:kiraxq/ppa
sudo apt update
sudo apt install media-downloader
```

**Note:** The script requires `sudo` privileges to install system packages. You will be prompted for your password during installation.

---

#### **Option 3: Using Windows Batch Scripts**

**For Windows Users**, two convenient batch scripts are provided:

##### **`installer-windows.bat`** 🔧
This script automates the setup process for Windows users:

**What it does:**
- ✅ Checks if Python 3.8+ is installed on your system
- ✅ Installs all required Python dependencies from `requirements.txt`
- ✅ Verifies that FFmpeg and Aria2c are available (either locally in the project folders or system-wide)
- ✅ Sets up the environment for first-time users
- ✅ Displays status messages for each step of the installation
- ✅ Creates a shortcut on Desktop to run the application

**How to use:**
1. Simply double-click `installer-windows.bat` 
2. Wait for the installation process to complete
3. Follow any on-screen prompts if dependencies need to be installed manually
By default, the stable installation is placed in `%LOCALAPPDATA%\Programs\Media_Downloader`

**Note:** You must have Python installed and added to your system PATH. If you see an error about Python not being found, download and install Python from [python.org](https://www.python.org/downloads/) and make sure to check "Add Python to PATH" during installation.

---

##### **`run-it.bat`** ▶️
This script starts the application after installation:

**What it does:**
- ✅ Launches the Media Downloader GUI application
- ✅ Handles any environment setup needed
- ✅ Displays helpful error messages if something goes wrong

**How to use:**
1. Double-click `run-it.bat`
2. The application GUI will open

---

#### **Quick Start for Linux Users:**
1. **First time only:** Make the installer executable and run it with sudo:
   ```bash
   chmod +x installer.sh
   sudo ./installer.sh
   ```
2. **To launch the app:** Search for "Media Downloader" in your applications menu, or run:
   ```bash
   ~/Media_Downloader/venv/bin/python3 ~/Media_Downloader/app.py
   ```

---

#### **Quick Start for Windows Users:**
1. **First time only:** Run `installer-windows.bat` to set up everything
2. **To launch the app:** Run `run-it.bat` (or double-click it)
   
To build an executable (optional):
**For Windows:**
```bash
pyinstaller --onefile --windowed --add-data=languages;languages --add-data=asset/Icon.ico;asset --add-data=aria2;aria2 --add-data=ffmpeg;ffmpeg --icon=asset/Icon.ico app.py -n MediaDownloader.exe
```
or 
```bash
pyinstaller --onedir --windowed --collect-all typeguard --collect-all CTkFileDialog --add-data=languages;languages --add-data=asset/Icon.ico;asset  --icon=asset/Icon.ico -n MediaDownloader app.py
```
or 

```bash
pyinstaller --onedir --windowed --collect-all typeguard --collect-all CTkFileDialog --add-data "languages;languages" --add-data "asset/Icon.ico;asset" --add-data "aria2;aria2" --add-data "ffmpeg;ffmpeg" --icon "asset/Icon.ico" -n MediaDownloader app.py
```

**For Linux/macOS development builds (not the release AppImage):**
```bash
pyinstaller --onefile --windowed --add-data=languages:languages --add-data=asset/Icon.png:asset --add-data=bin/aria2c:aria2 --add-data=bin/ffmpeg:ffmpeg --icon=asset/Icon.png app.py -n MediaDownloader
```

For the release AppImage, use `./build_app_image.sh` instead of the generic
PyInstaller command. The build stores `yt-dlp[default]` as seed data. A frozen
copy is retained only so PyInstaller collects the complete import graph; a
priority loader ensures normal operation uses the writable external copy. On
first launch the application copies the seed to:

```text
$XDG_CONFIG_HOME/media-downloader/yt-dlp/
# fallback: $HOME/.config/media-downloader/yt-dlp/
```

The application checks PyPI at most once every 24 hours before loading
yt-dlp. A downloaded wheel is verified against PyPI's SHA-256 digest, installed
in a versioned directory, and activated atomically. Offline starts keep using
the last known-good copy; a broken update is rolled back automatically. The
Options → Check for Updates action forces an immediate check. Set
`MEDIA_DOWNLOADER_DISABLE_YTDLP_AUTO_UPDATE=1` only when automatic checks must
be disabled.


---

#### **Option 4: Flatpak** 📦

Media Downloader can be distributed and installed as a sandboxed Flatpak.

##### **Requirements**

Flatpak sandboxing requires the **X11** socket because the Tkinter-based UI
does not support Wayland natively. Install the build tools:

```bash
sudo apt install flatpak flatpak-builder
flatpak remote-add --user --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
```

##### **Build & Install (one command)**

A helper script automates building, installing, and forcing X11:
[`build_flatpak.sh`](build_flatpak.sh)

```bash
chmod +x build_flatpak.sh
./build_flatpak.sh            # build + install
./build_flatpak.sh --bundle   # also generate a distributable .flatpak file
```

Or do it manually:

```bash
flatpak-builder --force-clean --disable-rofiles-fuse --repo=repo builddir flatpak/io.github.hmidani_abdelilah.Media_Downloader.json
flatpak remote-add --user --if-not-exists --no-gpg-verify media-downloader-local repo
flatpak install --user media-downloader-local io.github.hmidani_abdelilah.Media_Downloader
# Force X11 only (required on Wayland sessions — Tkinter needs X11):
flatpak override --user --socket=x11 io.github.hmidani_abdelilah.Media_Downloader
```

##### **Run**

```bash
flatpak run io.github.hmidani_abdelilah.Media_Downloader
```

> **Note about the `fallback-x11` fix:** The manifest keeps only `--socket=x11`.
> If `--socket=wayland` and `--socket=fallback-x11` are present together, Flatpak
> on Wayland sessions prefers Wayland and drops X11, which makes the Tkinter
> window fail with `no display name and no $DISPLAY environment variable`.
> Keeping only `--socket=x11` makes the GUI work on both X11 and Wayland
> (via XWayland) sessions.

##### **Create a distributable bundle**

```bash
flatpak build-bundle repo io.github.hmidani_abdelilah.Media_Downloader.flatpak io.github.hmidani_abdelilah.Media_Downloader master
# Install it on another machine:
flatpak install --user io.github.hmidani_abdelilah.Media_Downloader.flatpak
```

---

### 🛠️ Troubleshooting Subtitle Downloads

If subtitles are not downloaded, try the following steps in the **same Python environment** used to run the application.

1. Install `yt-dlp` with its default dependencies and `curl-cffi`:

   ```bash
   pip install "yt-dlp[default,curl-cffi]"
   ```

2. Install a supported JavaScript runtime. **Deno is recommended on macOS/Linux**. On macOS, you can use:

   ```bash
   brew install deno
   deno --version
   ```

   On Linux, install a current Deno release using the method available for your distribution, such as its `apt` or `pacman` package when available. The bundled `yt-dlp` version requires Deno 2.3.0 or newer.

3. Alternatively, use **Node.js 22.0.0 or newer**. Check the installed version:

   ```bash
   node -v
   ```

   If Node.js is missing or too old, activate the project's Python virtual environment, then install Node.js into it with `nodeenv`:

   ```bash
   pip install nodeenv && nodeenv -p
   ```

4. When using `yt-dlp` directly from the terminal, enable Node.js with:

   ```bash
   yt-dlp --js-runtimes node "VIDEO_URL"
   ```

   Replace `VIDEO_URL` with the actual video or playlist link.

The Media Downloader GUI detects supported Deno and Node.js runtimes automatically; restart the application after installing one. These steps help with JavaScript challenge or HTTP/403-related subtitle failures, but subtitles may still be unavailable for the requested language or require valid cookies.

### 📁 Project Structure

```
Media_Downloader/
├── app.py                         # Application entry point
├── gui.py                         # Main window and user interactions
├── downloader.py                  # Aria2c,yt-dlp download and playlist logic
├── ytdlp_manager.py               # Writable yt-dlp seed, updates, and rollback for AppImage
├── convert.py                     # FFmpeg conversion and compression helpers
├── ffmpeg_check.py                # FFmpeg availability checks
├── path_ffmpeg.py                 # FFmpeg executable path resolution
├── aria2_check.py                 # Aria2c availability checks
├── notification.py                # Cross-platform desktop notifications
├── utils.py                       # Shared resource-path helpers
├── languages/                     # Interface translations
│   ├── en.json                    # English
│   ├── ar.json                    # Arabic
│   └── fr.json                    # French
├── asset/                         # Icons used by packaged applications
│   ├── Icon.ico
│   └── Icon.png
├── Screenshots/                   # README and application screenshots
├── debian/                        # Debian / Ubuntu PPA package metadata and maintainer scripts
│   ├── control
│   ├── rules
│   ├── changelog
│   ├── postinst
│   └── prerm
├── installer.sh                   # Linux installer and uninstaller
├── installer-windows.bat          # Windows installer and repair 
├── run-it.bat                     # Windows launcher 
├── build_app_image.sh             # AppImage build script
├── build_deb_rmp.sh               # DEB and RPM build script
├── Media_Downloader.desktop       # Linux desktop entry
├── Media_Downloader.appdata.xml   # AppStream application metadata
├── requirements.txt               # Python dependencies
├── test files/                    # Experimental scripts and packaging tests
├── LICENSE                        # MIT license
├── ffmpeg/                        # FFmpeg binaries (Windows)
│   └── bin/
│       └── ffmpeg.exe
├── aria2/                         # Aria2c binaries (Windows)
│   └── aria2c.exe
└── README.md                      # Project documentation
```

---

## 🌍 العربية

تطبيق رسومي لتحميل الفيديوهات والصوت من YouTube ومنصات أخرى مثل Facebook وInstagram وX.com باستخدام مكتبة `yt-dlp`. يتميز بسهولة الاستخدام، اختيار الجودة، تحميل الترجمة، وتغيير اللغة والمظهر، ودعم التحميل السريع عبر Aria2c، ودعم ملفات الكوكيز للفيديوهات الخاصة.

### ✅ المميزات

- يدعم التحميل من **يوتيوب**، **فيسبوك**، **إنستغرام** و **X.com (تويتر)** و **تيك توك** وغرهم الكثير 
- تحميل الفيديوهات بصيغة (`mp4` `mkv` , `avi`, `flv` , `webm` ) أو الصوت فقط بصيغة (`mp3`, `aac` , `flac` , `wav` , `opus` , `alac` , `m4a` , `ogg` )
- اختيار الجودة: منخفضة (360p)، متوسطة (720p)، عالية (1080p)، عالية جدا (1440p)
- إمكانية تحميل الترجمة مع اختيار اللغة (عربي، إنجليزي، فرنسي)
- واجهة رسومية تفاعلية باستخدام `customtkinter`
- يدعم اللغات: **العربية**، **الإنجليزية**، **الفرنسية**
- تغيير المظهر: فاتح / داكن / تلقائي
- دعم تحميل قوائم التشغيل وإنشاء مجلد تلقائي لها، مع إمكانية تحديد نطاق شامل (مثل 5–10، وترك النهاية فارغة يعني المتابعة حتى آخر فيديو)
- إمكانية قص الفيديو أو الصوت بتحديد وقت البداية والنهاية، مع ضبط توقيت الترجمة ليتوافق مع المقطع
- يتحقق من وجود برنامج **FFmpeg** و **Aria2c** (محلي أو من النظام)
- دعم التحميل السريع عبر **Aria2c**
- دعم ملفات الكوكيز للفيديوهات الخاصة أو المحمية 
- لإستخراج ملف الكوكيز من المتصفح استخدم [Get cookies LOCALLY](https://chromewebstore.google.com/detail/cclelndahbckbenkjhflpdbgdldlbecc?utm_source=item-share-cb)
- **دعم السحب والإفلات للروابط** - يمكنك ببساطة سحب الروابط إلى حقل الإدخال
- قائمة سياق لحقل الرابط (قص، لصق، مسح)
- إشعارات عند اكتمال التحميل
- تحديث تلقائي لنسخة yt-dlp الخارجية في إصدار AppImage
- خيار إغلاق الحاسوب بعد التحميل
- إمكانية إيقاف التحميلات الجارية
- شريط قوائم مع المساعدة والخيارات
- يعمل على Windows وLinux وmacOS
- دعم الضغط:
- بعد تحميل الفيديو، يمكن للتطبيق اختياريًا ضغط/إعادة ترميز الفيديو باستخدام FFmpeg (قيمة CRF + الإعداد المسبق، واختيار الترميز).
- يعمل الضغط كخطوة منفصلة بعد التحميل لذلك تعرض واجهة المستخدم حالة "Compressing video...".
- زر الإيقاف يُلغي كلاً من التحميل وأي عملية ضغط FFmpeg جارية (يتطلب توفر FFmpeg على النظام).

### 🧰 المتطلبات

- Python 3.10 أو أحدث
- FFmpeg (موجود في مجلد ffmpeg أو مثبت على النظام) [FFmpeg _Windows](https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip) او نصب الاداة عبر CMD بواسطة مدير الحزم في  Windows 

```bash
winget install ffmpeg
```
- Aria2c (موجود في مجلد aria2 أو مثبت على النظام) [Aria2c_Windows](https://github.com/aria2/aria2/releases/download/release-1.37.0/aria2-1.37.0-win-64bit-build1.zip)

لتثبيت جميع المتطلبات:

```bash
pip install -r requirements.txt
```

### 🖥️ طريقة التشغيل

#### **الطريقة 1: استخدام Python (جميع الأنظمة)**


```bash
python app.py
```

#### **الخيار 2: استخدام سكريبت التثبيت على Linux 🐧**

**لمستخدمي نظام Linux**، تم توفير سكريبت تثبيت آلي:

##### **`installer.sh`** 🔧
هذا السكريبت يؤتمت عملية الإعداد الكاملة لمستخدمي Linux:

**ماذا يفعل:**
- ✅ يتحقق من تشغيل السكريبت بصلاحيات sudo/root
- ✅ يكتشف توزيعة Linux (Ubuntu, Debian, Fedora, Arch، إلخ)
- ✅ يثبت المتطلبات (Python3, pip, venv, FFmpeg, Git)
- ✅ ينسخ مستودع Media_Downloader (أو يحدثه إن كان موجوداً)
- ✅ ينشئ بيئة Python وهمية
- ✅ يثبت جميع مكتبات Python من `requirements.txt`
- ✅ ينشئ ملف تشغيل سطح المكتب للتطبيق
- ✅ يضبط أيقونة التطبيق

**كيفية الاستخدام:**
1. جعل السكريبت قابلاً للتنفيذ:
   ```bash
   chmod +x installer.sh
   ```
2. تشغيل المثبت مع sudo:
   ```bash
   sudo ./installer.sh
   ```
3. لإلغاء التثبيت لاحقًا، شغّل:
   ```bash
   sudo ./installer.sh uninstall
   ```
4. لعرض التعليمات وخيارات الاستخدام:
   ```bash
   sudo ./installer.sh --help
   ```
5. انتظر اكتمال عملية التثبيت
6. سيكون التطبيق متاحاً في قائمة التطبيقات

**التوزيعات المدعومة 🐧:**
- Ubuntu, Debian, Linux Mint, Kali Linux, Raspbian
- Fedora
- RHEL, CentOS, Rocky Linux, AlmaLinux
- Arch Linux, Manjaro, EndeavourOS, Garuda Linux

**ملاحظة:** السكريبت يتطلب صلاحيات sudo لتثبيت حزم النظام. ستُطلب كلمة المرور خلال التثبيت.

تتوفر كذلك حزم جاهزة:

- [حزمة DEB](https://github.com/hmidani-abdelilah/Media_Downloader/releases/download/v3.1.0/media-downloader_3.1.0_all.deb)
- [حزمة RPM](https://github.com/hmidani-abdelilah/Media_Downloader/releases/download/v3.1.0/media-downloader-3.1.0-1.noarch.rpm)
- [ملف AppImage](https://github.com/hmidani-abdelilah/Media_Downloader/releases/download/v3.1.0/Media_Downloader-3.1.0-x86_64.AppImage)

يمكن لمستخدمي Ubuntu والتوزيعات المبنية عليه استخدام PPA:

```bash
sudo add-apt-repository ppa:kiraxq/ppa
sudo apt update
sudo apt install media-downloader
```


#### **الخيار 3: استخدام سكربتات Windows Batch**

**لمستخدمي نظام Windows**، تم توفير سكربتين Batch مريحين للاستخدام:

##### **`installer-windows.bat`** 🔧
يقوم هذا السكربت بأتمتة عملية الإعداد لمستخدمي Windows:

**ماذا يفعل:**
- ✅ يتحقق مما إذا كان Python 3.8+ مثبتًا على نظامك
- ✅ يثبت جميع مكتبات Python المطلوبة من ملف `requirements.txt`
- ✅ يتأكد من توفر FFmpeg و Aria2c (إما محليًا في مجلدات المشروع أو على مستوى النظام بالكامل)
- ✅ يجهز البيئة للمستخدمين الجدد لأول مرة
- ✅ يعرض رسائل حالة لكل خطوة من خطوات التثبيت
- ✅ ينشئ اختصار على سطح المكتب لتشغيل البرنامج


**كيفية الاستخدام:**
1. ما عليك سوى النقر المزدوج فوق ملف `installer-windows.bat`
2. انتظر حتى تكتمل عملية التثبيت
3. اتبع أي إرشادات تظهر على الشاشة إذا كانت هناك مكتبات تحتاج إلى تثبيت يدوي

**ملاحظة:** يجب أن يكون Python مثبتًا ومضافًا إلى مسار النظام (System PATH). إذا ظهر لك خطأ يفيد بعدم العثور على Python، فقم بتحميل وتثبيت Python من موقع [python.org](https://python.org) وتأكد من تفعيل خيار "Add Python to PATH" أثناء التثبيت.

يُثبَّت التطبيق افتراضيًا داخل `%LOCALAPPDATA%\Programs\Media_Downloader`.
---

##### **`run-it.bat`** ▶️
يقوم هذا السكربت بتشغيل التطبيق بعد انتهاء التثبيت:

**ماذا يفعل:**
- ✅ يطلق واجهة المستخدم الرسومية (GUI) لبرنامج Media Downloader
- ✅ يتعامل مع أي إعدادات بيئة مطلوبة للتشغيل
- ✅ يعرض رسائل خطأ مفيدة في حال حدوث أي مشكلة

**كيفية الاستخدام:**
1. انقر نقرًا مزدوجًا فوق ملف `run-it.bat`
2. ستفتح واجهة المستخدم الرسومية للتطبيق فورًا

---

#### **بدء سريع لمستخدمي Linux:**
1. **للمرة الأولى فقط:** اجعل المثبت قابلاً للتنفيذ وشغله مع sudo:
   ```bash
   chmod +x installer.sh
   sudo ./installer.sh
   ```
2. **لتشغيل التطبيق:** ابحث عن "Media Downloader" في قائمة التطبيقات، أو شغل:
   ```bash
   ~/Media_Downloader/venv/bin/python3 ~/Media_Downloader/app.py
   ```

---

#### **بدء سريع لمستخدمي Windows:**
1. **للمرة الأولى فقط:** قم بتشغيل `installer-windows.bat` لإعداد كل شيء
2. **لتشغيل التطبيق:** قم بتشغيل `run-it.bat` (أو انقر فوقه نقرًا مزدوجًا)

لتحويل البرنامج إلى ملف تنفيذي:

**لويندوز:**
```bash
pyinstaller --onefile --windowed --add-data=languages;languages --add-data=asset/Icon.ico;asset --add-data=aria2;aria2 --add-data=ffmpeg;ffmpeg --icon=asset/Icon.ico app.py -n MediaDownloader.exe
```

**لبناءات التطوير على لينكس/macOS (وليس AppImage النهائي):**
```bash
pyinstaller --onefile --windowed --add-data=languages:languages --add-data=asset/Icon.png:asset --add-data=bin/aria2c:aria2 --add-data=bin/ffmpeg:ffmpeg --icon=asset/Icon.png app.py -n MediaDownloader
```

لبناء إصدار AppImage النهائي استعمل `./build_app_image.sh` بدل أمر PyInstaller
العام. يضع البناء نسخة أولية من `yt-dlp[default]` كبيانات احتياطية. تبقى نسخة
مجمّدة فقط كي يجمع PyInstaller شجرة الاستيراد كاملة؛ لكن محمّلًا ذا أولوية
يضمن أن التشغيل العادي يستخدم النسخة الخارجية القابلة للكتابة. عند أول تشغيل
تُنسخ إلى:

```text
$XDG_CONFIG_HOME/media-downloader/yt-dlp/
# المسار الافتراضي: $HOME/.config/media-downloader/yt-dlp/
```

يفحص التطبيق PyPI مرة واحدة كحد أقصى كل 24 ساعة قبل تحميل yt-dlp. يتحقق من
بصمة SHA-256 المنشورة، ويثبت كل إصدار في مجلد مستقل، ثم يفعّله بطريقة ذرية.
عند انقطاع الإنترنت يستمر آخر إصدار سليم، وإذا كان التحديث تالفًا يرجع التطبيق
تلقائيًا إلى الإصدار السابق. خيار «التحقق من التحديثات» يفرض فحصًا مباشرًا.
يمكن تعطيل الفحص التلقائي فقط عند الحاجة عبر
`MEDIA_DOWNLOADER_DISABLE_YTDLP_AUTO_UPDATE=1`.


---

#### **الخيار 4: Flatpak** 📦

يمكن توزيع وتثبيت Media Downloader كحزمة Flatpak معزولة (Sandboxed).

##### **المتطلبات**

تتطلب بيئة Flatpak مقبس **X11** لأن واجهة Tkinter لا تدعم Wayland بشكل أصلي.

```bash
sudo apt install flatpak flatpak-builder
flatpak remote-add --user --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
```

##### **البناء والتثبيت (أمر واحد)**

سكريبت مساعد يؤتمت البناء والتثبيت وفرض X11:
[`build_flatpak.sh`](build_flatpak.sh)

```bash
chmod +x build_flatpak.sh
./build_flatpak.sh            # البناء + التثبيت
./build_flatpak.sh --bundle   # وأيضًا توليد ملف .flatpak للتوزيع
```

أو يدويًا:

```bash
flatpak-builder --force-clean --disable-rofiles-fuse --repo=repo builddir flatpak/io.github.hmidani_abdelilah.Media_Downloader.json
flatpak remote-add --user --if-not-exists --no-gpg-verify media-downloader-local repo
flatpak install --user media-downloader-local io.github.hmidani_abdelilah.Media_Downloader
# فرض مقبس X11 فقط (مطلوب في جلسات Wayland — Tkinter يحتاج X11):
flatpak override --user --socket=x11 io.github.hmidani_abdelilah.Media_Downloader
```

##### **التشغيل**

```bash
flatpak run io.github.hmidani_abdelilah.Media_Downloader
```

> **ملاحظة إصلاح `fallback-x11`:** يحتفظ الـ manifest بـ `--socket=x11` فقط. إذا
> وُجد `--socket=wayland` و`--socket=fallback-x11` معًا، فإن Flatpak في جلسات
> Wayland يفضّل Wayland ويهمل X11، فيفشل تطبيق Tkinter بالخطأ
> `no display name and no $DISPLAY environment variable`. إبقاء `--socket=x11`
> فقط يجعل الواجهة تعمل في جلسات X11 وWayland (عبر XWayland).

##### **توليد ملف قابل للنشر**

```bash
flatpak build-bundle repo io.github.hmidani_abdelilah.Media_Downloader.flatpak io.github.hmidani_abdelilah.Media_Downloader master
# تثبيته على جهاز آخر:
flatpak install --user io.github.hmidani_abdelilah.Media_Downloader.flatpak
```

---
### 🛠️ حل مشكلة عدم تحميل الترجمة

إذا لم تُحمَّل الترجمة، جرّب الخطوات التالية داخل **بيئة Python نفسها** التي يُشغَّل منها التطبيق.

1. ثبّت `yt-dlp` مع الاعتماديات الافتراضية و`curl-cffi`:

   ```bash
   pip install "yt-dlp[default,curl-cffi]"
   ```

2. ثبّت محرك JavaScript مدعومًا. يُنصح باستخدام **Deno على macOS/Linux**. على macOS يمكنك استعمال:

   ```bash
   brew install deno
   deno --version
   ```

   على Linux، ثبّت إصدارًا حديثًا من Deno بالطريقة المتاحة لتوزيعتك، مثل حزمة `apt` أو `pacman` عند توفرها. إصدار `yt-dlp` المرفق يتطلب Deno 2.3.0 أو أحدث.

3. يمكن بدلًا من ذلك استخدام **Node.js بالإصدار 22.0.0 أو أحدث**. تحقق من الإصدار المثبت:

   ```bash
   node -v
   ```

   إذا لم يكن Node.js مثبتًا أو كان إصداره قديمًا، فعّل بيئة Python الافتراضية الخاصة بالمشروع ثم ثبّته داخلها باستخدام `nodeenv`:

   ```bash
   pip install nodeenv && nodeenv -p
   ```

4. عند استخدام `yt-dlp` مباشرة من الطرفية، فعّل Node.js هكذا:

   ```bash
   yt-dlp --js-runtimes node "VIDEO_URL"
   ```

   استبدل `VIDEO_URL` برابط الفيديو أو قائمة التشغيل الفعلي.

يكتشف تطبيق Media Downloader محركات Deno وNode.js المدعومة تلقائيًا؛ أعد تشغيل التطبيق بعد تثبيت أحدهما. تساعد هذه الخطوات عند فشل الترجمة بسبب تحديات JavaScript أو أخطاء HTTP/403، لكن قد تبقى الترجمة غير متاحة للغة المطلوبة أو تحتاج إلى ملف cookies صالح.

### 📁 هيكل المشروع

```
Media_Downloader/
├── app.py                         # نقطة تشغيل التطبيق
├── gui.py                         # النافذة الرئيسية وتفاعلات المستخدم
├── downloader.py                  # منطق التحميل وقوائم التشغيل عبر yt-dlp , Aria2c
├── ytdlp_manager.py               # نسخ yt-dlp الخارجية وتحديثها والرجوع الآمن في AppImage
├── convert.py                     # أدوات التحويل والضغط عبر FFmpeg
├── ffmpeg_check.py                # التحقق من توفر FFmpeg
├── path_ffmpeg.py                 # تحديد مسار ملف FFmpeg التنفيذي
├── aria2_check.py                 # التحقق من توفر Aria2c
├── notification.py                # إشعارات سطح المكتب عبر الأنظمة
├── utils.py                       # أدوات مشتركة لتحديد مسارات الموارد
├── languages/                     # ترجمات واجهة التطبيق
│   ├── en.json                    # الإنجليزية
│   ├── ar.json                    # العربية
│   └── fr.json                    # الفرنسية
├── asset/                         # أيقونات الحزم التنفيذية
│   ├── Icon.ico
│   └── Icon.png
├── Screenshots/                   # صور التطبيق المستخدمة في التوثيق
├── debian/                        # بيانات حزمة Debian / Ubuntu PPA وسكربتات الصيانة
│   ├── control
│   ├── rules
│   ├── changelog
│   ├── postinst
│   └── prerm
├── installer.sh                   # مثبّت Linux وأداة إلغاء التثبيت
├── installer-windows.bat          # مثبّت Windows ومسار الإصلاح
├── run-it.bat                     # مشغّل Windows وأداة التشخيص
├── build_app_image.sh             # سكربت بناء AppImage
├── build_deb_rmp.sh               # سكربت بناء حزمتَي DEB وRPM
├── Media_Downloader.desktop       # اختصار التطبيق على Linux
├── Media_Downloader.appdata.xml   # بيانات AppStream الخاصة بالتطبيق
├── requirements.txt               #  ملف إعتماديات بايتون
├── test files/                    # سكربتات تجريبية واختبارات الحزم
├── LICENSE                        # رخصة MIT
├── ffmpeg/                        # ملفات FFmpeg (ويندوز)
│   └── bin/
│       └── ffmpeg.exe
├── aria2/                         # ملفات Aria2c (ويندوز)
│   └── aria2c.exe
└── README.md                      # توثيق المشروع
```
```
```bash 
sudo update-desktop-database
```
