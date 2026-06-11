#!/bin/bash

# -----------------------------------------------------------------------------
# مشروع: Media_Downloader
# وصف: سكريبت التثبيت الاحترافي - يجلب المتطلبات من requirements.txt ويضبط الأيقونة
# المطور والمؤلف الأصلي: Abdelilah Hmidani
# -----------------------------------------------------------------------------

GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== بدء تثبيت برنامج Media Downloader ===${NC}"

# 1. التحقق من تشغيل السكريبت بـ sudo/root لتثبيت حزم النظام
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[ خطأ ] يرجى تشغيل السكريبت بصلاحيات الـ Root (sudo ./installer.sh)${NC}"
    exit 1
fi

# تحديد المستخدم الحقيقي لتفادي مشاكل صلاحيات ملفات البايثون والـ venv
REAL_USER=${SUDO_USER:-$USER}
USER_HOME=$(eval echo ~$REAL_USER)

# 2. التعرف على التوزيعة وتثبيت Python3 و FFmpeg
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    LIKE=$ID_LIKE
else
    echo -e "${RED}[ خطأ ] تعذر التعرف على النظام.${NC}"
    exit 1
fi

install_system_deps() {
    case "$OS" in
        ubuntu|debian|kali|raspbian|linuxmint)
            echo -e "${BLUE}[ تثبيت ] تحديث الحزم وتثبيت python3-venv و ffmpeg...${NC}"
            apt-get update -y
            apt-get install -y python3 python3-pip python3-venv ffmpeg
            ;;
        fedora)
            echo -e "${BLUE}[ تثبيت ] تثبيت python3 و ffmpeg عبر DNF...${NC}"
            dnf install -y python3 python3-pip ffmpeg
            ;;
        rhel|centos|rocky|almalinux)
            echo -e "${BLUE}[ تثبيت ] تفعيل مستودع EPEL وتثبيت المتطلبات...${NC}"
            if [ "$OS" != "fedora" ]; then
                dnf install -y epel-release || yum install -y epel-release
            fi
            dnf install -y python3 python3-pip ffmpeg || yum install -y python3 python3-pip ffmpeg
            ;;
        arch|manjaro|endeavouros|garuda)
            echo -e "${BLUE}[ تثبيت ] تحديث المستودعات وتثبيت python و ffmpeg عبر Pacman...${NC}"
            pacman -Sy --noconfirm --needed python python-pip ffmpeg
            ;;
        *)
            if [[ "$LIKE" == *"arch"* ]]; then
                pacman -Sy --noconfirm --needed python python-pip ffmpeg
            elif [[ "$LIKE" == *"debian"* || "$LIKE" == *"ubuntu"* ]]; then
                apt-get update -y && apt-get install -y python3 python3-pip python3-venv ffmpeg
            elif [[ "$LIKE" == *"rhel"* || "$LIKE" == *"fedora"* ]]; then
                dnf install -y python3 python3-pip ffmpeg || yum install -y python3 python3-pip ffmpeg
            else
                echo -e "${RED}[ تحذير ] التوزيعة غير مدعومة تلقائياً، تأكد من تثبيت بايثون و ffmpeg يدوياً.${NC}"
            fi
            ;;
    esac
}

install_system_deps

# 3. إعداد البيئة الوهمية وتثبيت ملف الـ requirements.txt
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$APP_DIR/venv"
REQ_FILE="$APP_DIR/requirements.txt"

if [ ! -f "$REQ_FILE" ]; then
    echo -e "${RED}[ خطأ ] لم يتم العثور على ملف requirements.txt في مجلد المشروع!${NC}"
    exit 1
fi

echo -e "${BLUE}[ إعداد ] إنشاء بيئة بايثون وهمية...${NC}"
# إنشاء البيئة باسم المستخدم العادي لتجنب مشاكل الصلاحيات (Permission Denied)
su - "$REAL_USER" -c "python3 -m venv $VENV_DIR"

echo -e "${BLUE}[ تثبيت ] جلب وتنصيب التبعيات من ملف requirements.txt...${NC}"
# تفعيل البيئة وتثبيت المتطلبات الفعلية للمستودع باسم المستخدم العادي
su - "$REAL_USER" -c "$VENV_DIR/bin/pip install --upgrade pip"
su - "$REAL_USER" -c "$VENV_DIR/bin/pip install -r $REQ_FILE"

# 4. ضبط مسار الأيقونة والملف الرئيسي
MAIN_SCRIPT="$APP_DIR/main.py"

# التحقق من الأيقونة الخاصة بالمستودع (icon.png أو logo.png أو المتوفرة في المجلد)
if [ -f "$APP_DIR/logo.png" ]; then
    ICON_PATH="$APP_DIR/logo.png"
elif [ -f "$APP_DIR/icon.png" ]; then
    ICON_PATH="$APP_DIR/icon.png"
else
    ICON_PATH="video-player" # أيقونة النظام الافتراضية في حال عدم التوفر
fi

# 5. بناء وتثبيت ملف الـ Desktop (.desktop)
DESKTOP_FILE="/usr/share/applications/media-downloader.desktop"
echo -e "${BLUE}[ إعداد ] إنشاء ملف تشغيل سطح المكتب في $DESKTOP_FILE...${NC}"

cat <<EOF > "$DESKTOP_FILE"
[Desktop Entry]
Version=1.0
Type=Application
Name=Media Downloader
Comment=Download videos and audio from the internet using CustomTkinter & yt-dlp
Exec="$VENV_DIR/bin/python3" "$MAIN_SCRIPT"
Icon=$ICON_PATH
Terminal=false
Categories=Network;Utility;
StartupNotify=true
EOF

# منح الصلاحيات لملف الاختصار لكي يظهر في القائمة فوراً
chmod 644 "$DESKTOP_FILE"

echo -e "${GREEN}[ نجاح ] تم التثبيت بنجاح تام! تم الاعتماد على requirements.txt وتجهيز الأيقونة.${NC}"
