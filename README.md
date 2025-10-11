
# Media Downloader GUI

![Alt text](https://raw.githubusercontent.com/hmidani-abdelilah/Media_Downloader/refs/heads/main/141522.png "Media Downloader GUI")

## 🌐 English

A graphical application for downloading videos and audio from YouTube and other platforms (Facebook, Instagram, X.com) using `yt-dlp`, with quality control, subtitle support, language switching, and dark/light themes.

### 🚀 Features

- Download from **YouTube**, **Facebook**, **Instagram**, and **X.com (Twitter)**
- Download video (`mp4`) or audio (`mp3`)
- Select quality: Low (360p), Medium (720p), High (1080p)
- Optional **subtitles** download (supports English, Arabic, French)
- Full **GUI** using `customtkinter`
- Multilingual: **English**, **Arabic**, **French**
- Theme support: Light / Dark / System
- Playlist support with auto-folder creation
- Checks for **FFmpeg** availability
- Cross-platform (Windows/Linux/macOS)

### 🧰 Requirements

- Python 3.8+
- FFmpeg (must be installed on the system)

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
pyinstaller --onefile --windowed --add-data=languages:languages --add-data=asset/Icon.ico:asset --icon=asset/Icon.ico app.py -n MediaDownloader.exe
```

### 📁 Project Structure

```
├── app.py                  # Main entry point
├── downloader.py           # Core download logic using yt-dlp
├── gui.py                  # GUI logic
├── ffmpeg_check.py         # FFmpeg presence checker
├── requirements.txt        # Python dependencies
├── languages/              # Language files (en/ar/fr)
│   ├── en.json
│   ├── ar.json
│   └── fr.json
├── asset/                  # Icons and visuals
│   └── Icon.ico
└── README.md
```

---

## 🌍 العربية

تطبيق رسومي لتحميل الفيديوهات والصوت من YouTube ومنصات أخرى مثل Facebook وInstagram وX.com باستخدام مكتبة `yt-dlp`. يتميز بسهولة الاستخدام، اختيار الجودة، تحميل الترجمة، وتغيير اللغة والمظهر.

### ✅ المميزات

- **X.com (تويتر)**  يدعم التحميل من  **يوتيوب**، **فيسبوك**، **إنستغرام** و ، 
- أو الصوت فقط `mp3` تحميل الفيديوهات بصيغة `mp4` 
-  منخفضة (360p)، متوسطة (720p)، عالية (1080p) : اختيار الجودة
- إمكانية تحميل الترجمة (عربي، إنجليزي، فرنسي)
- واجهة رسومية تفاعلية باستخدام `customtkinter`
- يدعم اللغات: **العربية**، **الإنجليزية**، **الفرنسية**
- تغيير المظهر: فاتح / داكن / تلقائي
- دعم تحميل قوائم التشغيل وإنشاء مجلد تلقائي لها
- للتشغيل السليم `FFmpeg` يتحقق من وجود برنامج  
- Windows وLinux وmacOS يعمل على 

### 🧰 المتطلبات

- أو أحدث Python 3.8
- يجب أن يكون  مثبتًا على النظام FFmpeg


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
pyinstaller --onefile --windowed --add-data=languages:languages --add-data=asset/Icon.ico:asset --icon=asset/Icon.ico app.py -n MediaDownloader.exe
```

### 📁 هيكل المشروع

```
├── app.py                  # نقطة التشغيل الرئيسية
├── downloader.py           # منطق التحميل باستخدام yt-dlp
├── gui.py                  # واجهة المستخدم
├── ffmpeg_check.py         # التحقق من FFmpeg
├── requirements.txt        # ملف الاعتماديات
├── languages/              # ملفات الترجمة
│   ├── en.json
│   ├── ar.json
│   └── fr.json
├── asset/                  # الأيقونات والمظهر
│   └── Icon.ico
└── README.md
```
