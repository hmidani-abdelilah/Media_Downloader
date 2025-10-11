# downloader.py
import yt_dlp as youtube_dl
import os
import threading
import re
from utils import resource_path

# تحديد مسار ffmpeg من داخل bin
ffmpeg_path = resource_path("ffmpeg/bin/ffmpeg.exe")
ARIA2C_PATH = resource_path("aria2/aria2c.exe")
#cookies_path = resource_path("www.youtube.com_cookies.txt")  # أو المسار الذي تضع فيه الكوكيز

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

def get_videos_info(url,cookies_path="\U0001F36A",ffmpeg_path=ffmpeg_path):
    """
    جلب معلومات الفيديوهات (العنوان والرابط) من الرابط المدخل (فيديو أو قائمة تشغيل)

    Args:
                 url: رابط الفيديو أو قائمة التشغيل
        cookies_path: استخدام cookies لحل مشاكل الفيديوهات المحمية 
        ffmpeg_path: مسار اذات ffmpeg من مجلد جانبي ان وجد والى فمن النظام
    Returns:
        dict يحتوي على قائمة الفيديوهات والعنوان إذا كانت قائمة تشغيل
    """

    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "skip_download": True,
    }

    # ✅ التحقق من ffmpeg المحلي
    if ffmpeg_path:
    
        if os.path.exists(ffmpeg_path):
            #[INFO] تم العثور على ffmpeg المحلي في: {ffmpeg_path}
            ydl_opts['ffmpeg_location'] = ffmpeg_path
        #else:
        #    print(f"[WARNING] لم يتم العثور على ffmpeg في المسار المحلي ({ffmpeg_path})")
        #    print("[INFO] سيتم استخدام ffmpeg من النظام (إن وُجد في PATH)")
    #else:
    #    print("[INFO] لم يتم تحديد مسار ffmpeg، سيتم استخدام النسخة المثبتة في النظام.")
        
    # ✅ إضافة الكوكيز إن وجد
    if cookies_path != "\U0001F36A":
        if os.path.exists(cookies_path):
            ydl_opts['cookiefile'] = cookies_path
        #else:
            #print(f"[WARNING] ملف الكوكيز غير موجود في: {cookies_path}")

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

def download_video(url, download_dir, quality, file_type, download_subtitles, progress_hook=None, playlist_title=None,ffmpeg_path=ffmpeg_path, use_aria2=False , cookies_path="\U0001F36A" ):
    """

    تحميل فيديو من يوتيوب باستخدام yt-dlp و Aria2 (اختياري) و cookies (إختياري)

    

    Args:

        url: رابط الفيديو

        download_dir: مجلد التحميل

        quality: جودة الفيديو ('low', 'medium', 'high')

        file_type: نوع الملف ('mp3', 'mp4')

        download_subtitles: هل يجب تحميل الترجمة

        progress_hook: دالة لتتبع التقدم

        playlist_title: عنوان قائمة التشغيل (إن وجد)

        ffmpeg_path: مسار اذات ffmpeg من مجلد جانبي ان وجد والى فمن النظام

        use_aria2: هل سيتم استخدام Aria2 كأداة تحميل خارجية (اختياري)

        cookies_path: استخدام cookies لحل مشاكل الفيديوهات المحمية 

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

     # ✅ التحقق من ffmpeg المحلي
    if ffmpeg_path:
        if os.path.exists(ffmpeg_path):
            #print(f"[INFO] تم العثور على ffmpeg المحلي في: {ffmpeg_path}")
            options['ffmpeg_location'] = ffmpeg_path
        #else:
        #    print(f"[WARNING] لم يتم العثور على ffmpeg في المسار المحلي ({ffmpeg_path})")
        #    print("[INFO] سيتم استخدام ffmpeg من النظام (إن وُجد في PATH)")
    #else:
    #    print("[INFO] لم يتم تحديد مسار ffmpeg، سيتم استخدام النسخة المثبتة في النظام.")

    # ✅ إضافة الكوكيز إن وجد
    if cookies_path != "\U0001F36A":
        if os.path.exists(cookies_path):
            options['cookiefile'] = cookies_path
        else:
            print(f"[WARNING] ملف الكوكيز غير موجود في: {cookies_path}")
    # إذا كان سيتم استخدام Aria2 كأداة تنزيل خارجية
    if use_aria2:
        downloader_args = ['--min-split-size=1M', 
                            '--max-connection-per-server=16', 
                            '--max-concurrent-downloads=16', 
                            '--split=16'
                            ]
        if os.path.exists(ARIA2C_PATH):
            options['external_downloader'] = ARIA2C_PATH # استخدام Aria2 كأداة تحميل خارجية من مسارملف مجاور

            options['external_downloader_args'] = downloader_args
        else:
            options['external_downloader'] = 'aria2c'  # استخدام Aria2 كأداة تحميل خارجية

            options['external_downloader_args'] = downloader_args
    
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
    
#    if download_subtitles:
        
        #options['writesubtitles'] = True,
        #options['subtitleslangs'] = ['en', 'ar', 'fr'],
        
#        options['writeautomaticsub'] = True,
#        options['subtitlesformat']= 'srt'

    # ✅ التحقق من وجود ترجمات قبل التحميل
    preferred_langs = ['en', 'ar', 'fr']
    has_manual_subs = False
    video_lang = 'en'  # الافتراضية

    if download_subtitles:
        try:
            with youtube_dl.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                available_subs = info.get('subtitles', {})
                available_auto_subs = info.get('automatic_captions', {})
                video_lang = info.get('language', None) or info.get('original_language', None) or 'en'

                has_manual_subs = any(lang in available_subs for lang in preferred_langs)

                # إذا لم توجد ترجمة يدوية، نحاول معرفة لغة الترجمة التلقائية المتاحة
                if not has_manual_subs and available_auto_subs:
                    # نحاول استخدام اللغة الأصلية إن كانت متوفرة
                    if video_lang in available_auto_subs:
                        auto_lang = video_lang
                    else:
                        # fallback: نأخذ أول لغة متاحة تلقائياً
                        auto_lang = list(available_auto_subs.keys())[0]
                    video_lang = auto_lang

        except Exception:
            has_manual_subs = False

        if has_manual_subs:
            options['writesubtitles'] = True
            options['subtitleslangs'] = preferred_langs
            options['subtitlesformat'] = 'srt'
        else:
            options['writeautomaticsub'] = True
            options['subtitleslangs'] = [video_lang]
            options['subtitlesformat'] = 'srt'


    try:
        with youtube_dl.YoutubeDL(options) as ydl:
            ydl.download([url])
    except youtube_dl.DownloadError as e:
        raise Exception(f"Error downloading video: {str(e)}")
    except Exception as e:
        if "Download stopped by user" in str(e):
            raise Exception("Download stopped by user")
        raise Exception(f"Unexpected error: {str(e)}")
