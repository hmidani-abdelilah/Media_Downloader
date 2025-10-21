# Media Downloader GUI

![Media Downloader GUI Screenshot Application ](https://raw.githubusercontent.com/hmidani-abdelilah/Media_Downloader/refs/heads/main/152342.png "Media Downloader GUI")

## 🌐 English

A graphical application for downloading videos and audio from YouTube and other platforms (Facebook, Instagram, X.com , TikTok ... ) and more using `yt-dlp`, with quality control, subtitle support, language switching, and dark/light themes.

### 🚀 Features

- Download from **YouTube**, **Facebook**, **Instagram**, and **X.com (Twitter)**
- Download video (`mp4`) or audio (`mp3`)
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
- Cross-platform (Windows/Linux/macOS)

### 🧰 Requirements

- Python 3.8+
- FFmpeg (included in `ffmpeg` folder or installed on system)
- Aria2c (included in `aria2` folder or installed on system)

Install dependencies using:

```bash
pip install -r requirements.txt
```

### 💻 How to Run

```bash
python app.py
```

To build an executable (optional):

```bash
pyinstaller --onefile --windowed --add-data=languages;languages --add-data=asset/Icon.ico;asset --add-data=aria2;aria2 --add-data=ffmpeg;ffmpeg --icon=asset/Icon.ico app.py -n MediaDownloader.exe
```

### 📁 Project Structure

```
├── app.py                  # Main entry point
├── downloader.py           # Core download logic using yt-dlp & Aria2c
├── gui.py                  # GUI logic
├── ffmpeg_check.py         # FFmpeg presence checker
├── aria2_check.py          # Aria2c presence checker
├── utils.py                # Resource path utility
├── requirements.txt        # Python dependencies
├── languages/              # Language files (en/ar/fr)
│   ├── en.json
│   ├── ar.json
│   └── fr.json
├── asset/                  # Icons and visuals
│   └── Icon.ico
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
- تحميل الفيديوهات بصيغة `mp4` أو الصوت فقط بصيغة `mp3`
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
- يعمل على Windows وLinux وmacOS

### 🧰 المتطلبات

- Python 3.8 أو أحدث
- FFmpeg (موجود في مجلد ffmpeg أو مثبت على النظام)
- Aria2c (موجود في مجلد aria2 أو مثبت على النظام)

لتثبيت جميع المتطلبات:

```bash
pip install -r requirements.txt
```

### 🖥️ طريقة التشغيل

```bash
python app.py
```

لتحويل البرنامج إلى ملف تنفيذي:

```bash
pyinstaller --onefile --windowed --add-data=languages;languages --add-data=asset/Icon.ico;asset --add-data=aria2;aria2 --add-data=ffmpeg;ffmpeg --icon=asset/Icon.ico app.py -n MediaDownloader.exe
```

### 📁 هيكل المشروع

```
├── app.py                  # نقطة التشغيل الرئيسية
├── downloader.py           # منطق التحميل باستخدام yt-dlp و Aria2c
├── gui.py                  # واجهة المستخدم
├── ffmpeg_check.py         # التحقق من FFmpeg
├── aria2_check.py          # التحقق من Aria2c
├── utils.py                # دوال المسارات
├── requirements.txt        # ملف الاعتماديات
├── languages/              # ملفات الترجمة
│   ├── en.json
│   ├── ar.json
│   └── fr.json
├── asset/                  # الأيقونات والمظهر
│   └── Icon.ico
├── ffmpeg/                 # ملفات FFmpeg (ويندوز)
│   └── bin/
│       └── ffmpeg.exe
├── aria2/                  # ملفات Aria2c (ويندوز)
│   └── aria2c.exe
└── README.md
```

