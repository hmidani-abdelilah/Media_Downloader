# Media Downloader

![Media Downloader GUI Screenshot Application ](https://raw.githubusercontent.com/hmidani-abdelilah/Media_Downloader/refs/heads/main/Screenshot%20From%202026-03-31%2013-45-22.png "Media Downloader GUI")

## 🌐 English

A graphical application for downloading videos and audio from YouTube and other platforms (Facebook, Instagram, X.com , TikTok ... ) and more using `yt-dlp`, with quality control, subtitle support, language switching, and dark/light themes.

### 🚀 Features

- Download from **YouTube**, **Facebook**, **Instagram**, and **X.com (Twitter)**
- Download video (`mp4` `mkv` , `avi`, `flv` , `webm` ) or audio (`mp3`, `aac` , `flac` , `wav` , `opus` , `alac` , `m4a` , `ogg` )
- Select quality: Low (360p), Medium (720p), High (1080p)
- Optional **subtitles** download (supports English, Arabic, French)
- Full **GUI** using `customtkinter`
- Multilingual: **English**, **Arabic**, **French**
- Theme support: Light / Dark / System
- Playlist support with auto-folder creation
- Checks for **FFmpeg** and **Aria2c** availability (local or system)
- Supports **Aria2c** as external downloader for faster downloads
- Cookies file support for private/protected videos
- Export cookies from browser use [Get cookies LOCALLY](https://chromewebstore.google.com/detail/cclelndahbckbenkjhflpdbgdldlbecc?utm_source=item-share-cb)
- Context menu for URL input (cut, paste, clear)
- Notification on download completion
- Automatic update checker for dependencies
- Option to shutdown computer after download
- Ability to stop ongoing downloads
- Menu bar with help and options
- Cross-platform (Windows/Linux/macOS)

### 🧰 Requirements

- Python 3.8+
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

#### **Option 2: Using Windows Batch Scripts**

**For Windows Users**, two convenient batch scripts are provided:

##### **`installer-windows.bat`** 🔧
This script automates the setup process for Windows users:

**What it does:**
- ✅ Checks if Python 3.8+ is installed on your system
- ✅ Installs all required Python dependencies from `requirements.txt`
- ✅ Verifies that FFmpeg and Aria2c are available (either locally in the project folders or system-wide)
- ✅ Sets up the environment for first-time users
- ✅ Displays status messages for each step of the installation
- ✅ Creat shotcut in Desktop to run the application

**How to use:**
1. Simply double-click `installer-windows.bat` 
2. Wait for the installation process to complete
3. Follow any on-screen prompts if dependencies need to be installed manually

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

**For Linux/macOS:**
```bash
pyinstaller --onefile --windowed --add-data=languages:languages --add-data=asset/Icon.png:asset --add-data=bin/aria2c:aria2 --add-data=bin/ffmpeg:ffmpeg --icon=asset/Icon.png app.py -n MediaDownloader
```

### 📁 Project Structure

```
├── app.py                  # Main entry point
├── downloader.py           # Core download logic using yt-dlp & Aria2c
├── gui.py                  # GUI logic and interface
├── notification.py         # Notification system for download completion
├── ffmpeg_check.py         # FFmpeg presence checker
├── path_ffmpeg.py          # Find FFmpeg and return the PATH 
├── aria2_check.py          # Aria2c presence checker
├── utils.py                # Resource path utility
├── installer-windows.bat   # Windows setup script (automated installation)
├── run-it.bat              # Windows batch script to run the application
├── Media_Downloader.desktop # Desktop file for Linux integration
├── requirements.txt        # Python dependencies
├── languages/              # Language files (en/ar/fr)
│   ├── en.json
│   ├── ar.json
│   └── fr.json
├── asset/                  # Icons and visuals
│   ├── Icon.ico
│   └── Icon.png
├── ffmpeg/                 # FFmpeg binaries (Windows)
│   └── bin/
│       └── ffmpeg.exe
├── aria2/                  # Aria2c binaries (Windows)
│   └── aria2c.exe
└── README.md
```

---

## 🌍 العربية

تطبيق رسومي لتحميل الفيديوهات والصوت من YouTube ومنصات أخرى مثل Facebook وInstagram وX.com باستخدام مكتبة `yt-dlp`. يتميز بسهولة الاستخدام، اختيار الجودة، تحميل الترجمة، وتغيير اللغة والمظهر، ودعم التحميل السريع عبر Aria2c، ودعم ملفات الكوكيز للفيديوهات الخاصة.

### ✅ المميزات

- يدعم التحميل من **يوتيوب**، **فيسبوك**، **إنستغرام** و **X.com (تويتر)** و **تيك توك** وغرهم الكثير 
- تحميل الفيديوهات بصيغة (`mp4` `mkv` , `avi`, `flv` , `webm` ) أو الصوت فقط بصيغة (`mp3`, `aac` , `flac` , `wav` , `opus` , `alac` , `m4a` , `ogg` )
- اختيار الجودة: منخفضة (360p)، متوسطة (720p)، عالية (1080p)
- إمكانية تحميل الترجمة (عربي، إنجليزي، فرنسي)
- واجهة رسومية تفاعلية باستخدام `customtkinter`
- يدعم اللغات: **العربية**، **الإنجليزية**، **الفرنسية**
- تغيير المظهر: فاتح / داكن / تلقائي
- دعم تحميل قوائم التشغيل وإنشاء مجلد تلقائي لها
- يتحقق من وجود برنامج **FFmpeg** و **Aria2c** (محلي أو من النظام)
- دعم التحميل السريع عبر **Aria2c**
- دعم ملفات الكوكيز للفيديوهات الخاصة أو المحمية 
- لإستخراج ملف الكوكيز من المتصفح استخدم [Get cookies LOCALLY](https://chromewebstore.google.com/detail/cclelndahbckbenkjhflpdbgdldlbecc?utm_source=item-share-cb)
- قائمة سياق لحقل الرابط (قص، لصق، مسح)
- إشعارات عند اكتمال التحميل
- فاحص تحديثات تلقائي للاعتماديات
- خيار إغلاق الحاسوب بعد التحميل
- إمكانية إيقاف التحميلات الجارية
- شريط قوائم مع المساعدة والخيارات
- يعمل على Windows وLinux وmacOS

### 🧰 المتطلبات

- Python 3.8 أو أحدث
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
#### **الخيار 2: استخدام سكربتات Windows Batch**

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

#### **بدء سريع لمستخدمي Windows:**
1. **للمرة الأولى فقط:** قم بتشغيل `installer-windows.bat` لإعداد كل شيء
2. **لتشغيل التطبيق:** قم بتشغيل `run-it.bat` (أو انقر فوقه نقرًا مزدوجًا)

لتحويل البرنامج إلى ملف تنفيذي:

**لويندوز:**
```bash
pyinstaller --onefile --windowed --add-data=languages;languages --add-data=asset/Icon.ico;asset --add-data=aria2;aria2 --add-data=ffmpeg;ffmpeg --icon=asset/Icon.ico app.py -n MediaDownloader.exe
```

**للينكس/macOS:**
```bash
pyinstaller --onefile --windowed --add-data=languages:languages --add-data=asset/Icon.png:asset --add-data=bin/aria2c:aria2 --add-data=bin/ffmpeg:ffmpeg --icon=asset/Icon.png app.py -n MediaDownloader
```

### 📁 هيكل المشروع

```
├── app.py                  # نقطة التشغيل الرئيسية
├── downloader.py           # منطق التحميل باستخدام yt-dlp و Aria2c
├── gui.py                  # واجهة المستخدم والمنطق
├── notification.py         # نظام الإشعارات عند اكتمال التحميلواجهة المستخدم
├── ffmpeg_check.py         # التحقق من FFmpeg
├── path_ffmpeg.py          # ايجاد مسار تشغيل FFmpeg وارجاعه
├── aria2_check.py          # التحقق من Aria2c
├── utils.py                # دوال المسارات
├── installer-windows.bat   # Windows setup script (سكريبت يأتمت التتيت )
├── run-it.bat              # Windows batch script to run the application ( سكريبت تشغيل البرنامج )
├── requirements.txt        # ملف الاعتماديات
├── languages/              # ملفات الترجمة
│   ├── en.json
│   ├── ar.json
│   └── fr.json
├── asset/                  # الأيقونات والمظهر
│   ├── Icon.ico
│   └── Icon.png
├── ffmpeg/                 # ملفات FFmpeg (ويندوز)
│   └── bin/
│       └── ffmpeg.exe
├── aria2/                  # ملفات Aria2c (ويندوز)
│   └── aria2c.exe
└── README.md
```
```bash 
sudo update-desktop-database
``` 

