import os, sys

def resource_path(relative_path):
    """
    إرجاع المسار الصحيح للملفات سواء عند التشغيل من PyInstaller أو بشكل عادي
    """
    try:
        base_path = sys._MEIPASS  # إذا البرنامج مجمع
    except Exception:
        base_path = os.path.abspath(".")  # إذا شغال عادي
    return os.path.join(base_path, relative_path)
