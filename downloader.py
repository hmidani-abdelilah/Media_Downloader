# downloader.py
import yt_dlp as youtube_dl
import os
import threading
import re

# متغير تحكم لإيقاف التحميل
stop_event = threading.Event()

def reset_stop_event():
    """إعادة تعيين حدث الإيقاف"""
    stop_event.clear()

def stop_download():
    """تعيين حدث الإيقاف لإيقاف التحميل الحالي"""
    stop_event.set()

def get_format(quality, file_type):
    """
    تحديد صيغة التحميل بناءً على الجودة ونوع الملف
    
    Args:
        quality: الجودة المطلوبة (low, medium, high)
        file_type: نوع الملف (mp3 أو mp4)

    Returns:
        الصيغة المناسبة لاستخدامها في yt_dlp
    """
    quality_map = {
        'low': '360',
        'medium': '720',
        'high': '1080'
    }
    quality_value = quality_map.get(quality, '720')
    
    if file_type == 'mp3':
        # تحميل أفضل صوت فقط
        return f'bestaudio[ext=m4a]/best[height<={quality_value}]'
    else:
        # تحميل فيديو وصوت ودمجهما
        return f'bv*[height<={quality_value}]+ba/best'

def get_videos_info(url):
    """
    جلب معلومات الفيديوهات (العنوان والرابط) من الرابط المدخل (فيديو أو قائمة تشغيل)

    Args:
        url: رابط الفيديو أو قائمة التشغيل

    Returns:
        dict يحتوي على قائمة الفيديوهات والعنوان إذا كانت قائمة تشغيل
    """
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "skip_download": True,
    }
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            videos = []
            playlist_title = None
            
            # إذا كان الرابط لقائمة تشغيل، نحفظ عنوان القائمة
            if "entries" in info:
                playlist_title = info.get("title", "playlist")
                for entry in info["entries"]:
                    if entry:
                        videos.append({
                            "title": entry.get("title", "No Title"),
                            "url": f"https://www.youtube.com/watch?v={entry['id']}"
                        })
            else:
                # رابط لفيديو فردي
                videos.append({
                    "title": info.get("title", "No Title"),
                    "url": url
                })
            
            return {
                "videos": videos,
                "playlist_title": playlist_title
            }
    except Exception as e:
        raise Exception(f"Error fetching video info: {str(e)}")

def sanitize_filename(filename):
    """
    تنظيف اسم الملف من الأحرف غير المسموح بها في أسماء المجلدات

    Args:
        filename: اسم الملف الأصلي

    Returns:
        اسم الملف بعد التنظيف
    """
    # إزالة الأحرف غير المسموح بها
    filename = re.sub(r'[\\/*?:"<>|]', "_", filename)
    # إزالة المسافات المتكررة
    filename = re.sub(r'\s+', " ", filename)
    # تقليص طول الاسم إذا كان طويلاً جداً
    if len(filename) > 100:
        filename = filename[:97] + "..."
    return filename.strip()

def download_video(url, download_dir, quality, file_type, download_subtitles, progress_hook=None, playlist_title=None, use_aria2=False):
    """

    تحميل فيديو من يوتيوب باستخدام yt-dlp و Aria2 (اختياري)

    

    Args:

        url: رابط الفيديو

        download_dir: مجلد التحميل

        quality: جودة الفيديو ('low', 'medium', 'high')

        file_type: نوع الملف ('mp3', 'mp4')

        download_subtitles: هل يجب تحميل الترجمة

        progress_hook: دالة لتتبع التقدم

        playlist_title: عنوان قائمة التشغيل (إن وجد)

        use_aria2: هل سيتم استخدام Aria2 كأداة تحميل خارجية (اختياري)

    """
    # إعادة تعيين حدث الإيقاف قبل بدء التحميل
    reset_stop_event()
    
    # دالة للتحقق من حالة الإيقاف
    def custom_progress_hook(d):
        if stop_event.is_set():
            raise Exception("Download stopped by user")
        if progress_hook:
            progress_hook(d)
    
    # إنشاء مجلد لقائمة التشغيل إذا تم تحديدها
    final_download_dir = download_dir
    if playlist_title:
        sanitized_playlist_title = sanitize_filename(playlist_title)
        playlist_dir = os.path.join(download_dir, sanitized_playlist_title)
        
        if not os.path.exists(playlist_dir):
            os.makedirs(playlist_dir)
        
        final_download_dir = playlist_dir
    
    options = {
        'format': get_format(quality, file_type),
        'outtmpl': os.path.join(final_download_dir, '%(title)s.%(ext)s'),
        'quiet': False,
        'progress_hooks': [custom_progress_hook]
    }
        # إذا كان سيتم استخدام Aria2 كأداة تنزيل خارجية

    if use_aria2:

        options['external_downloader'] = 'aria2c'  # استخدام Aria2 كأداة تحميل خارجية

        options['external_downloader_args'] = [

            '--min-split-size=1M', 

            '--max-connection-per-server=16', 

            '--max-concurrent-downloads=16', 

            '--split=16'

        ]

    
    if file_type == 'mp3':
        # تحويل إلى MP3 بعد التحميل
        options['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    elif file_type == 'mp4':
        # دمج الفيديو والصوت إلى صيغة MP4
        options['merge_output_format'] = 'mp4'
    
    if download_subtitles:
        options['writesubtitles'] = True
        options['subtitleslangs'] = ['en', 'ar', 'fr']
    
    try:
        with youtube_dl.YoutubeDL(options) as ydl:
            ydl.download([url])
    except youtube_dl.DownloadError as e:
        raise Exception(f"Error downloading video: {str(e)}")
    except Exception as e:
        if "Download stopped by user" in str(e):
            raise Exception("Download stopped by user")
        raise Exception(f"Unexpected error: {str(e)}")
