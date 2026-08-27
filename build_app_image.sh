#!/bin/bash
#  pyinstaller --noconfirm --onedir --windowed \                                                                     ─╯
#   --name "MediaDownloader" \
#   --icon=asset/Icon.ico \
#   --collect-all typeguard \
#   --collect-all CTkFileDialog \
#   --collect-all customtkinter \
#   --collect-all yt_dlp \
#   --add-data "languages:languages" --collect-submodules PIL \
#   --add-data "asset:asset" --add-data="asset/Icon.ico:asset"  \
#   app.py

set -e

echo "=== 1. تثبيت أدوات النظام المطلوبة ==="
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv appstream desktop-file-utils wget

echo "=== 2. إعداد البيئة الوهمية وتثبيت المكتبات ==="
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install pyinstaller -r requirements.txt

echo "=== 3. تجميع المشروع بواسطة PyInstaller ==="

pyinstaller --noconfirm --onedir --windowed --name "Media_Downloader" --icon=asset/Icon.ico --collect-all typeguard --collect-all CTkFileDialog --collect-all customtkinter --collect-all yt_dlp --add-data "languages:languages" --collect-submodules PIL --add-data "asset:asset" --add-data="asset/Icon.ico:asset" app.py

echo "=== 4. تحميل أداة linuxdeploy ==="
if [ ! -f "linuxdeploy-x86_64.AppImage" ]; then
    wget https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage
    chmod +x linuxdeploy-x86_64.AppImage
fi

echo "=== 5. تجهيز هيكل AppDir ==="
rm -rf AppDir
mkdir -p AppDir/usr/bin
mkdir -p AppDir/usr/share/icons/hicolor/256x256/apps

# 1. نسخ ملفات التطبيق
cp -r dist/Media_Downloader/* AppDir/usr/bin/

# 2. نسخ ملف desktop
cp Media_Downloader.desktop AppDir/

# 3. نسخ الأيقونة بالاسم المطلق وإعادة تسميتها لتطابق خانة Icon في ملف الـ desktop
cp icon.png AppDir/usr/share/icons/hicolor/256x256/apps/Media_Downloader.png
cp icon.png AppDir/Media_Downloader.png
cp icon.png AppDir/.DirIcon

mkdir -p AppDir/usr/share/metainfo
cp Media_Downloader.appdata.xml AppDir/usr/share/metainfo/
mv AppDir/usr/share/metainfo/Media_Downloader.appdata.xml AppDir/usr/share/metainfo/io.github.hmidani_abdelilah.Media_Downloader.appdata.xml


echo "=== 6. بناء ملف AppImage النهائي ==="
# السماح لتشغيل FUSE داخل بيئة البناء إذا لزم الأمر
export APPIMAGE_EXTRACT_AND_RUN=1
./linuxdeploy-x86_64.AppImage --appdir AppDir --desktop-file Media_Downloader.desktop --output appimage

echo "=== تم البناء بنجاح! ستجد ملف الـ AppImage في المجلد الحالي ==="