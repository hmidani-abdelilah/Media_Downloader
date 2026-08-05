# downloader.py
import time

import yt_dlp as youtube_dl #  استيراد مكتبة yt_dlp لتحميل الفيديوهات من يوتيوب ومنصات أخرى
import os # استيراد مكتبة التعامل مع نظام الملفات
import threading # استيراد مكتبة threading لدعم العمليات المتعددة
import re # استيراد مكتبة التعبيرات النمطية للتعامل مع النصوص
import urllib.parse
from utils import resource_path # استيراد الدالة resource_path من ملف utils
from path_ffmpeg import ffmpeg_find_path # استيراد دالة تحديد مسار ffmpeg من ملف path_ffmpeg
from convert import compress_video, get_gpu_encoders, is_encoder_supported # استيراد دوال الضغط والترميزات من ملف convert
# تحديد مسار ffmpeg من داخل bin
# مجلد ffmpeg
ffmpeg_path = ffmpeg_find_path()
# تحديد مسار aria2c من داخل مجلد aria2
ARIA2C_PATH = resource_path("aria2/aria2c.exe")
#cookies_path = resource_path("www.youtube.com_cookies.txt")  # أو المسار الذي تضع فيه الكوكيز

# متغير تحكم لإيقاف التحميل
stop_event = threading.Event()

# -------------- دوال التحكم في الإيقاف --------------
def reset_stop_event():
    """إعادة تعيين حدث الإيقاف"""
    stop_event.clear()

# -------------- دوال التحكم في الإيقاف --------------
def stop_download():
    """تعيين حدث الإيقاف لإيقاف التحميل الحالي"""
    stop_event.set()


# -------------- دوال مساعدة --------------
def get_format(quality, file_type):
    """
    تحديد صيغة التحميل بناءً على الجودة ونوع الملف
    
    Args:
        quality: الجودة المطلوبة (low, medium, high)
        file_type: نوع الملف (mp3 أو mp4)

    Returns:
        الصيغة المناسبة لاستخدامها في yt_dlp
    """
    # تحويل الجودة إلى ارتفاع بكسل
    quality_map = {'low': '360','medium': '720','high': '1080'}
    quality_value = quality_map.get(quality, '720')
    
    # تحديد الصيغة بناءً على نوع الملف
    if file_type == 'mp3':
        # تحميل أفضل صوت فقط
        return f'bestaudio[ext=m4a]/best[height<={quality_value}]'
    else:
        # تحميل فيديو وصوت ودمجهما
        return f'bv*[height<={quality_value}]+ba/best'

# -------------- جلب معلومات الفيديو --------------
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
    # إعداد خيارات yt_dlp
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "skip_download": True,
        "socket_timeout": 30,
    # Explicitly verify SSL (should be default, but verify)
    }

    # ✅ التحقق من ffmpeg المحلي
    if ffmpeg_path != "ffmpeg":
        # تحديد مسار ffmpeg في الخيارات
        ydl_opts['ffmpeg_location'] = ffmpeg_path
        
    # ✅ إضافة الكوكيز إن وجد
    if cookies_path != "\U0001F36A":

        if os.path.exists(cookies_path):
            # إضافة مسار ملف الكوكيز إلى الخيارات
            ydl_opts['cookiefile'] = cookies_path

    # جلب معلومات الفيديو باستخدام yt_dlp
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            # استخراج المعلومات دون تحميل الفيديو
            info = ydl.extract_info(url, download=False)
            videos = []
            playlist_title = None
            
            # إذا كان الرابط لقائمة تشغيل، نحفظ عنوان القائمة
            if "entries" in info:

                playlist_title = info.get("title", "playlist")
                # روابط الفيديوهات داخل قائمة التشغيل
                for entry in info["entries"]:
                    # تحقق من وجود البيانات قبل الإضافة
                    if not entry:
                        continue

                    title = entry.get("title", "No Title")
                    video_url = None
                    is_playlist_item = False

                    # Prefer explicit webpage_url if provided by extractor
                    if entry.get("webpage_url"):
                        video_url = entry.get("webpage_url")
                    # Some extractors provide a full URL in 'url'
                    elif entry.get("url"):
                        u = entry.get("url")
                        if isinstance(u, str):
                            # If it's already an absolute URL
                            if u.startswith("http"):
                                video_url = u
                            # Relative YouTube paths like '/playlist?list=...'
                            elif u.startswith("/") or u.startswith("playlist") or "list=" in u:
                                # ensure leading slash for proper join
                                path = u if u.startswith("/") else "/" + u
                                video_url = urllib.parse.urljoin("https://www.youtube.com", path)
                            # If it's a video id (e.g. YouTube 11-char id)
                            elif re.match(r'^[A-Za-z0-9_-]{11}$', u):
                                video_url = f"https://www.youtube.com/watch?v={u}"
                            else:
                                # fallback: attempt to join with youtube domain
                                video_url = urllib.parse.urljoin("https://www.youtube.com", u)
                    # If only 'id' exists, try to build a YouTube watch URL (common case)
                    elif entry.get("id"):
                        eid = entry.get("id")
                        if isinstance(eid, str) and re.match(r'^[A-Za-z0-9_-]{11}$', eid):
                            video_url = f"https://www.youtube.com/watch?v={eid}"
                        else:
                            # If id is not a plain video id, try to use it as-is
                            video_url = entry.get("id")

                    # As a last resort, try to construct something reasonable or skip
                    if not video_url:
                        continue

                    # Mark only non-video playlist entries for channel playlist pages
                    if entry.get("id") and not re.match(r'^[A-Za-z0-9_-]{11}$', str(entry.get("id"))) and video_url and "playlist?list=" in video_url:
                        is_playlist_item = True

                    item = {
                        "title": title,
                        "url": video_url
                    }
                    if is_playlist_item:
                        item["sub_dir_title"] = title
                        item["item_type"] = "playlist"

                    videos.append(item)
            else:
                # رابط لفيديو فردي
                videos.append({
                    "title": info.get("title", "No Title"),
                    "url": url
                })
            
            # إرجاع المعلومات المطلوبة
            channel_title = info.get("uploader") or info.get("channel") or info.get("uploader_id") or info.get("channel_id")
            if isinstance(channel_title, str):
                channel_title = channel_title.strip()
            else:
                channel_title = None

            return {
                "videos": videos,
                "playlist_title": playlist_title,
                "channel_title": channel_title
            }
    # التعامل مع أخطاء استخراج المعلومات
    except Exception as e:
        raise Exception(f"Error fetching video info: {str(e)}")

# -------------- تنظيف اسم الملف --------------
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
        # إرجاع الاسم المنظف
    return filename.strip()

# -------------- تنظيف مسار الدليل --------------
def sanitize_path(path):
    """
    تنظيف مسار دليل متعدد المستويات مع الحفاظ على بنية المجلد.
    """
    if not path:
        return ""
    parts = re.split(r'[\\/]+', str(path))
    sanitized_parts = [sanitize_filename(part) for part in parts if part]
    return os.path.join(*sanitized_parts) if sanitized_parts else ""

# -------------- ضغط الفيديو بعد التحميل --------------
def compress_downloaded_video(
    downloaded_path,
    file_type,
    final_download_dir,
    encoder='libx264',
    crf=23,
    preset='medium',
    copy_codec=False,
    stop_event=None,
    progress_hook=None,
) -> str:
    """Compress a downloaded video file after yt-dlp finishes.

    This helper keeps the compression logic separate from download logic so the
    UI can show compression state and the stop event can cancel ffmpeg.
    """
    video_containers = {'mp4', 'mkv', 'avi', 'flv', 'webm', 'mov'}
    if file_type not in video_containers:
        return downloaded_path

    base_name = os.path.splitext(os.path.basename(downloaded_path))[0]
    out_ext = file_type
    out_file = os.path.join(final_download_dir, f"compressed_{base_name}.{out_ext}")
    final_encoder = encoder

    if out_ext == 'webm':
        webm_encoders = ['libaom-av1', 'libvpx-vp9', 'libvpx']
        found = None
        for e in webm_encoders:
            try:
                if is_encoder_supported(e):
                    found = e
                    break
            except Exception:
                continue
        if found:
            final_encoder = found
        else:
            if is_encoder_supported('libx264'):
                print('No WebM encoder available; switching compressed output to MP4 using libx264')
                out_file = os.path.join(final_download_dir, f"compressed_{base_name}.mp4")
                final_encoder = 'libx264'
            else:
                raise Exception('No WebM encoder (libvpx/libaom) available. Install one or choose MP4/MKV output.')

    if progress_hook:
        progress_hook({'status': 'compressing'})

    compress_video(
        downloaded_path,
        out_file,
        encoder=final_encoder,
        crf=crf,
        preset=preset,
        copy_codec=copy_codec,
        stop_event=stop_event,
    )
    return out_file

# تابع التحميل الرئيسي مع دعم GPU
# -------------- تحميل الفيديو --------------
def download_video(url, download_dir, quality, file_type, download_subtitles, progress_hook=None, playlist_title=None,ffmpeg_path=ffmpeg_path, use_aria2=False , cookies_path="\U0001F36A" , encoder='libx264', crf=23, preset='medium', copy_codec=False):
    """

    تحميل فيديو من يوتيوب باستخدام yt-dlp و Aria2 (اختياري) و cookies (إختياري)

    

    Args:

        url: رابط الفيديو

        download_dir: مجلد التحميل

        quality: جودة الفيديو ('low', 'medium', 'high')

        file_type: نوع الملف ('mp3', 'mp4', 'mkv', 'avi', 'flv', 'webm', 'opus', 'aac', 'flac', 'wav', 'alac', 'm4a', 'ogg')

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
        # التحقق من حالة الإيقاف
        if stop_event.is_set():
            raise Exception("Download stopped by user")
        # استدعاء دالة التقدم الأصلية إذا كانت موجودة
        if progress_hook:
            # تمرير حالة التقدم إلى الدالة الأصلية
            progress_hook(d)
    
    # إنشاء مجلد لقائمة التشغيل إذا تم تحديدها
    final_download_dir = download_dir
    if playlist_title:
        sanitized_playlist_title = sanitize_path(playlist_title)
        if sanitized_playlist_title:
            playlist_dir = os.path.join(download_dir, sanitized_playlist_title)
            if not os.path.exists(playlist_dir):
                os.makedirs(playlist_dir, exist_ok=True)
            final_download_dir = playlist_dir
    
    # إعداد خيارات yt_dlp
    options = {
        'format': get_format(quality, file_type),
        'outtmpl': os.path.join(final_download_dir, '%(title)s.%(ext)s'),
        'quiet': False,
        'progress_hooks': [custom_progress_hook]
        
    }

    # ✅ التحقق من ffmpeg المحلي
    if ffmpeg_path != "ffmpeg" :
        options['ffmpeg_location'] = ffmpeg_path
        
    # ✅ إضافة الكوكيز إن وجد
    if cookies_path != "\U0001F36A":
        if os.path.exists(cookies_path):
            options['cookiefile'] = cookies_path
    
    # إعدادات Aria2c
    # إذا كان سيتم استخدام Aria2 كأداة تنزيل خارجية
    if use_aria2:
        # إعدادات التحميل المتقدمة لـ Aria2
        downloader_args = ['--min-split-size=1M', 
                            '--max-connection-per-server=16', 
                            '--max-concurrent-downloads=16', 
                            '--split=16'
                            ]
        # تحديد مسار aria2c إذا كان موجوداً في المجلد الجانبي
        if os.path.exists(ARIA2C_PATH):
            options['external_downloader'] = ARIA2C_PATH # استخدام Aria2 كأداة تحميل خارجية من مسارملف مجاور

            options['external_downloader_args'] = downloader_args
        else:
            options['external_downloader'] = 'aria2c'  # استخدام Aria2 كأداة تحميل خارجية

            options['external_downloader_args'] = downloader_args
    
    # إعدادات ما بعد المعالجة بناءً على نوع الملف
    if file_type == 'mp3':
        # تحويل إلى MP3 بعد التحميل
        options['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
        # حذف الملف الأصلي بعد التحويل
        #options['keepvideo'] = False

    elif file_type == 'mp4':
        # دمج الفيديو والصوت إلى صيغة MP4
        options['merge_output_format'] = 'mp4'
    
    elif file_type == 'mkv':
        # دمج الفيديو والصوت إلى صيغة MKV
        options['merge_output_format'] = 'mkv'

    ##
    elif file_type == 'avi':
        # دمج الفيديو والصوت إلى صيغة AVI
        # mkv هو الحاوية التي تدعم معظم الترميزات، بينما avi قد يواجه مشاكل توافق مع بعض الترميزات الحديثة، لذا نستخدم mkv كحاوية وسيتم تحويلها لاحقاً إلى avi
        options['merge_output_format'] = 'mkv'
        options['postprocessors'] = [{
                                        'key': 'FFmpegVideoConvertor',
                                        'preferedformat': 'avi',  # avi 
                                        }]
        # إعدادات ترميز الفيديو لملفات AVI (لتحسين التوافق)
        options['postprocessor_args'] = [
                                            '-c:v', 'libx264',   # كودك حديث
                                            '-crf', '18',        # جودة عالية (كلما قل الرقم زادت الجودة)
                                            '-preset', 'slow',   # ضغط أفضل
                                        ]

    ##
    elif file_type == 'flv':
        # دمج الفيديو والصوت إلى صيغة FLV
        options['merge_output_format'] = 'mkv'
        options['postprocessors'] = [{
                                        'key': 'FFmpegVideoConvertor',
                                        'preferedformat': 'flv', # flv
                                        }]
        # إعدادات ترميز الفيديو لملفات FLV (لتحسين التوافق)
        options['postprocessor_args'] = [
                                            '-c:v', 'libx264',   # كودك حديث
                                            '-crf', '18',        # جودة عالية (كلما قل الرقم زادت الجودة)
                                            '-preset', 'slow',   # ضغط أفضل
                                        ]
        
    elif file_type == 'webm':
        # دمج الفيديو والصوت إلى صيغة WEBM
        options['merge_output_format'] = 'webm'
    
    elif file_type == 'opus':
        # تحويل إلى OPUS بعد التحميل
        options['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'opus',
            'preferredquality': '192',
        }]
        # حذف الملف الأصلي بعد التحويل
        #options['keepvideo'] = False   

    elif file_type == 'aac':
        # تحويل إلى AAC بعد التحميل
        options['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'aac',
            'preferredquality': '192',
        }]
        # حذف الملف الأصلي بعد التحويل
        #options['keepvideo'] = False
    
    elif file_type == 'flac':
        # تحويل إلى FLAC بعد التحميل
        options['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'flac',
            'preferredquality': '192',
        }]
        # حذف الملف الأصلي بعد التحويل
        #options['keepvideo'] = False
    
    elif file_type == 'wav':
        # تحويل إلى WAV بعد التحميل
        options['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }]
        # حذف الملف الأصلي بعد التحويل
        #options['keepvideo'] = False
    
    elif file_type == 'alac':
        # تحويل إلى ALAC بعد التحميل
        options['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'alac',
            'preferredquality': '192',
        }]
        # حذف الملف الأصلي بعد التحويل
        #options['keepvideo'] = False
    
    elif file_type == 'm4a':
        # دمج الفيديو والصوت إلى صيغة M4A
        options['merge_output_format'] = 'm4a'
    
    elif file_type == 'ogg':
        # تحويل إلى OGG بعد التحميل
        options['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'vorbis',
            'preferredquality': '192',
        }]
        # حذف الملف الأصلي بعد التحويل
        #options['keepvideo'] = False   

    
    

    # ✅ التحقق من وجود ترجمات قبل التحميل
    preferred_langs = ['en', 'ar', 'fr']
    has_manual_subs = False
    video_lang = 'en'  # الافتراضية
    # إذا كان يجب تحميل الترجمات
    if download_subtitles:
        try:
            # جلب معلومات الفيديو للتحقق من الترجمات المتاحة
            with youtube_dl.YoutubeDL({'quiet': True}) as ydl: # إنشاء كائن yt_dlp به وضع هادئ
                info = ydl.extract_info(url, download=False) # استخراج معلومات الفيديو بدون تحميله
                available_subs = info.get('subtitles', {})  # استخرج الترجمات اليدوية (subtitles) إن وُجدت وإلا فأرجع قاموس فارغ
                available_auto_subs = info.get('automatic_captions', {})  # استخرج الترجمات التلقائية (automatic captions) إن وُجدت وإلا فأرجع قاموس فارغ
                video_lang = info.get('language', None) or info.get('original_language', None) or 'en' 
                # التحقق مما إذا كانت الترجمات المفضلة متوفرة
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
            # في حال حدوث أي خطأ أثناء جلب المعلومات، نفترض عدم وجود ترجمات يدوية
            has_manual_subs = False
        # إضافة إعدادات الترجمة إلى خيارات التحميل
        if has_manual_subs:
            # إذا وجدت ترجمات يدوية، نحملها
            options['writesubtitles'] = True
            options['subtitleslangs'] = preferred_langs
            options['subtitlesformat'] = 'srt'
        
        else:
            # إذا لم توجد ترجمات يدوية، نحاول تحميل الترجمة التلقائية
            options['writeautomaticsub'] = True
            options['subtitleslangs'] = [video_lang]
            options['subtitlesformat'] = 'srt'


    try:
        # بدء التحميل
        with youtube_dl.YoutubeDL(options) as ydl:
            #ydl.download([url])

            # extract_info تقوم بجلب البيانات وتحميل الملف في نفس الوقت
            # سجل وقت البدء حتى نتمكن من اكتشاف الملف الفعلي عند الانتهاء
            start_time = time.time()
            info = ydl.extract_info(url, download=True)

            # حاول استخراج اسم الملف المتوقع أولًا
            expected_path = ydl.prepare_filename(info)

            # إذا لم يوجد الملف في المسار المتوقع (قد غُيّر الامتداد أثناء المعالجة اللاحقة)،
            # فابحث عن أحدث ملف تم إنشاؤه/تعديله في مجلد التحميل
            downloaded_path = None
            if os.path.exists(expected_path):
                downloaded_path = expected_path
            else:
                # جمع الملفات العادية في مجلد التحميل
                try:
                    candidates = [os.path.join(final_download_dir, f) for f in os.listdir(final_download_dir)]
                    candidates = [p for p in candidates if os.path.isfile(p)]
                    # تجاهل ملفات الجزء المؤقتة
                    candidates = [p for p in candidates if not p.endswith('.part')]
                    # احتفظ بالملفات الأحدث من وقت البدء - مع هامش صغير
                    recent = [p for p in candidates if os.path.getmtime(p) >= start_time - 2]
                    if recent:
                        downloaded_path = max(recent, key=os.path.getmtime)
                except Exception:
                    downloaded_path = None

            # أخيراً، احتفظ بالمسار المتوقع إذا لم نعثر على أي ملف آخر
            if not downloaded_path:
                downloaded_path = expected_path

            print(f"File downloaded path: \n {downloaded_path}\n")

            # بعد التحميل، ضغط الفيديو إذا كان فيديو فعليًا ولم يطلب المستخدم نسخ الترميز
            if file_type not in ('mp3', 'opus', 'aac', 'flac', 'wav', 'alac', 'm4a', 'ogg') and not copy_codec:
                if os.path.exists(downloaded_path):                    
                    try:
                        downloaded_path = compress_downloaded_video(
                            downloaded_path,
                            file_type,
                            final_download_dir,
                            encoder=encoder,
                            crf=crf,
                            preset=preset,
                            copy_codec=copy_codec,
                            stop_event=stop_event,
                            progress_hook=progress_hook,
                        )
                    except Exception as e:
                        err_msg = str(e)
                        print(f"Compression failed: {err_msg}")
                        raise
                else:
                    # إذا لم نتمكن من تحديد الملف، اطرح تحذيراً بدلًا من محاولة ضغط ملف غير موجود
                    raise Exception(f"Cannot find downloaded file to compress: {downloaded_path}")
    except youtube_dl.DownloadError as e:
        # التعامل مع أخطاء التحميل
        raise Exception(f"Error downloading video: {str(e)}")
    # التعامل مع إيقاف التحميل من قبل المستخدم
    except Exception as e:
        # التعامل مع إيقاف التحميل من قبل المستخدم
        if "Download stopped by user" in str(e):
            raise Exception("Download stopped by user")
        # التعامل مع أي أخطاء غير متوقعة أخرى
        raise Exception(f"Unexpected error: {str(e)}")
