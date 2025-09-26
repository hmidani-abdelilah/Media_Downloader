import subprocess

def check_aria2_installed():
    try:
        # محاولة تشغيل Aria2 من سطر الأوامر للتحقق من وجوده
        subprocess.run(["aria2c", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except FileNotFoundError:
        return False
