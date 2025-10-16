import os, sys

def resource_path(relative_path):
    """
    إرجاع المسار الصحيح للملفات سواء أثناء التطوير أو بعد التحزيم بـ PyInstaller.

    Args:
        relative_path (str): المسار النسبي للملف داخل المشروع.
    Returns:
        str: المسار الكامل (المطلق) للملف.
    
    الاستخدام:
    ----------
    >>> resource_path("assets/icon.png")
    ----------
    """
    try:
        base_path = sys._MEIPASS  # إذا البرنامج مجمع
    except Exception:
        base_path = os.path.abspath(".")  # إذا شغال عادي
    return os.path.join(base_path, relative_path)

