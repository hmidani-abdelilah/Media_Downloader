#!/bin/bash

# إيقاف السكريبت فوراً في حال حدوث أي خطأ
set -e

echo "=========================================================="
echo "  بدء بناء حزمتي DEB و RPM لتطبيق Media Downloader (VENV) "
echo "=========================================================="

# 1. تحديث النظام وتثبيت أدوات البناء بالإضافة إلى أداة alien
echo "[*] تثبيت الأدوات والاعتماديات الأساسية وأداة Alien..."
sudo apt update
sudo apt install git python3 python3-pip python3-venv ffmpeg aria2 binutils alien -y

# 2. تنزيل مستودع الكود من جيت هاب أو تحديثه
if [ -d "Media_Downloader" ]; then
    echo "[*] مجلد المشروع موجود مسبقاً، يتم تحديث الكود المصدري..."
    cd Media_Downloader && git pull && cd ..
else
    echo "[*] جاري تحميل المشروع من GitHub..."
    git clone https://github.com/hmidani-abdelilah/Media_Downloader.git
fi

# 3. إعداد وتنظيف مسار بناء الحزمة
PKG_DIR="media-downloader-pkg"
echo "[*] إنشاء الهيكل البنائي للمجلدات داخل $PKG_DIR..."
rm -rf "$PKG_DIR"
mkdir -p "$PKG_DIR"/DEBIAN
mkdir -p "$PKG_DIR"/usr/share/media-downloader
mkdir -p "$PKG_DIR"/usr/bin
mkdir -p "$PKG_DIR"/usr/share/applications
mkdir -p "$PKG_DIR"/usr/share/pixmaps

# 4. نسخ ملفات التطبيق المصدرية إلى المجلد العام للمشاركة
echo "[*] نسخ ملفات المشروع والمكونات الرسومية..."
cp -r Media_Downloader/* "$PKG_DIR"/usr/share/media-downloader/

# محاولة نسخ الأيقونة إن وجدت بأي مسار افتراضي للمستودع
if [ -f "Media_Downloader/assets/icon.png" ]; then
    cp Media_Downloader/assets/icon.png "$PKG_DIR"/usr/share/pixmaps/media-downloader.png
elif [ -f "Media_Downloader/icon.png" ]; then
    cp Media_Downloader/icon.png "$PKG_DIR"/usr/share/pixmaps/media-downloader.png
fi

# 5. إنشاء ملف التشغيل التنفيذي (Launcher) وتوجيهه لـ app.py عبر البيئة المعزولة
echo "[*] إنشاء ملف التشغيل الرابط داخل /usr/bin..."
cat << 'EOF' > "$PKG_DIR"/usr/bin/media-downloader
#!/bin/bash
cd /usr/share/media-downloader
# تشغيل التطبيق عبر مفسر بايثون المعزول وتمرير ملف app.py الصحيح للمستودع
./venv/bin/python3 app.py "$@"
EOF

# 6. إنشاء ملف التحكم الوصفي للحزمة
echo "[*] إنشاء ملف الـ control الأساسي للحزمة..."
cat << 'EOF' > "$PKG_DIR"/DEBIAN/control
Package: media-downloader
Version: 3.0.0
Architecture: all
Maintainer: Abdelilah Hmidani <hmidani.abdelilah@example.com>
Depends: python3, python3-pip, python3-venv, ffmpeg, aria2
Section: utils
Priority: optional
Description: Graphic user interface application to download videos and audio from YouTube, Facebook, Instagram and X using yt-dlp.
EOF

# 7. إنشاء سكريبت التثبيت اللاحق (postinst) لتهيئة الـ VENV وتحميل المكتبات بأمان
echo "[*] إنشاء سكريبت التثبيت التلقائي المعزول (postinst)..."
cat << 'EOF' > "$PKG_DIR"/DEBIAN/postinst
#!/bin/sh
set -e
echo "-> جاري إنشاء بيئة وهمية معزولة (VENV) للتطبيق في /usr/share/media-downloader/venv..."
python3 -m venv /usr/share/media-downloader/venv

echo "-> جاري تثبيت مكتبات بايثون المطلوبة داخل البيئة المعزولة بأمان..."
/usr/share/media-downloader/venv/bin/pip install --upgrade pip
/usr/share/media-downloader/venv/bin/pip install -r /usr/share/media-downloader/requirements.txt
exit 0
EOF

# 8. إنشاء سكريبت ما قبل الحذف (prerm) للتنظيف الشامل عند إزالة التطبيق
echo "[*] إنشاء سكريبت الحذف الذكي والتنظيف (prerm)..."
cat << 'EOF' > "$PKG_DIR"/DEBIAN/prerm
#!/bin/sh
set -e
echo "-> جاري حذف البيئة الوهمية وكافة الملفات المؤقتة لتنظيف النظام..."
rm -rf /usr/share/media-downloader/venv
exit 0
EOF

# 9. إنشاء اختصار سطح المكتب والـ Menu بالإعدادات القياسية الصحيحة والاسم المجرّد للأيقونة
echo "[*] إنشاء ملف الـ Desktop الاختصاري لقائمة البرامج..."
cat << 'EOF' > "$PKG_DIR"/usr/share/applications/media-downloader.desktop
[Desktop Entry]
Version=1.0
Type=Application
Name=Media Downloader
Comment=Download videos and audio from social media using yt-dlp
Exec=media-downloader
Icon=media-downloader
Terminal=false
Categories=Network;Utility;
StartupNotify=true
EOF

# 10. ضبط أذونات وصلاحيات الأمان القياسية لملفات دبيان
echo "[*] ضبط الصلاحيات الأمنية وأذونات التنفيذ القياسية..."
chmod 755 "$PKG_DIR"/DEBIAN
chmod 755 "$PKG_DIR"/DEBIAN/control
chmod 755 "$PKG_DIR"/DEBIAN/postinst
chmod 755 "$PKG_DIR"/DEBIAN/prerm
chmod +x "$PKG_DIR"/usr/bin/media-downloader

# 11. ضغط الحزمة وتوليد ملف .deb
echo "[*] جاري كبس المجلد وتوليد حزمة DEB..."
dpkg-deb --build "$PKG_DIR"
DEB_FILE="media-downloader-pkg.deb"

# 12. تحويل حزمة الـ DEB إلى حزمة RPM عبر أداة Alien
echo "[*] جاري استخدام أداة Alien للتحويل وتوليد حزمة RPM..."
# خيار -r يعني التحويل إلى RPM، وخيار --to-rpm يقوم بتوليد الحزمة مباشرة
sudo alien -r --to-rpm "$DEB_FILE"

# البحث عن اسم ملف rpm الناتج لعرض رسالة واضحة للمستخدم
RPM_FILE=$(ls media-downloader-*.rpm 2>/dev/null || echo "حزمة RPM")

echo "=========================================================="
echo "  تم البناء بنجاح! "
echo "  1. حزمة دبيان الناتجة: $DEB_FILE"
echo "  2. حزمة آر بي إم الناتجة: $RPM_FILE"
echo "=========================================================="
