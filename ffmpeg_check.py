import subprocess
from path_ffmpeg import ffmpeg_find_path
from utils import resource_path  # استيراد الدالة resource_path من ملف utils

def check_ffmpeg_installed():
    """تتحقق من عمل ffmpeg بنسبة 100% وتعيد True أو False"""
    # استدعاء دالة البحث لجلب أفضل مسار متاح
    target_path = ffmpeg_find_path()
    
    if not target_path:
        return False
        
    try:
        # فحص المسار المستخرج للتأكد من أنه يعمل ويستجيب للأوامر
        res = subprocess.run([target_path, "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return res.returncode == 0
    except Exception:
        return False
