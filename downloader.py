# downloader.py
import subprocess # استيراد مكتبة subprocess لتشغيل أوامر النظام من داخل بايثون
import platform # استيراد مكتبة platform للكشف عن نظام التشغيل
import yt_dlp as youtube_dl #  استيراد مكتبة yt_dlp لتحميل الفيديوهات من يوتيوب ومنصات أخرى
import os # استيراد مكتبة التعامل مع نظام الملفات
import threading # استيراد مكتبة threading لدعم العمليات المتعددة
import re # استيراد مكتبة التعبيرات النمطية للتعامل مع النصوص
from utils import resource_path # استيراد الدالة resource_path من ملف utils
from path_ffmpeg import ffmpeg_find_path # استيراد دالة تحديد مسار ffmpeg من ملف path_ffmpeg

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

# -------------- دعم GPU --------------
def detect_gpu():
    """كشف نوع GPU لتحديد خيارات الترميز المناسبة"""
    # الكشف عن نظام التشغيل
    system = platform.system()
    gpu_type = "CPU"

    # 🔹 1. الكشف عن NVIDIA
    try:
        if system != "Darwin":  # macOS لا يحتوي nvidia-smi
            result = subprocess.run(["nvidia-smi"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode == 0:
                return "NVIDIA"
    except Exception:
        pass

    # 🔹 2. الكشف عبر FFmpeg عن Intel أو AMD
    try:
        # تشغيل ffmpeg للتحقق من وحدات تسريع الأجهزة
        result = subprocess.run(
            [ffmpeg_path, "-hide_banner", "-hwaccels"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        # تحليل المخرجات للبحث عن مؤشرات GPU
        output = (result.stdout.decode() + result.stderr.decode()).lower()
        # تحقق من وجود مؤشرات Intel أو AMD
        if "qsv" in output:
            gpu_type = "Intel"
        elif "amf" in output or "vaapi" in output:
            gpu_type = "AMD"
    except Exception:
        pass

    # 🔹 3. macOS يعتمد videotoolbox
    if system == "Darwin":
        gpu_type = "Apple"

    return gpu_type

# -------------- دعم GPU - ترميزات الفيديو --------------
def is_encoder_supported(encoder):
    """يتحقق ما إذا كان الترميز مدعوماً فعلياً في FFmpeg"""
    try:
        # تشغيل ffmpeg للتحقق من الترميزات المدعومة
        result = subprocess.run(
            [ffmpeg_path, "-hide_banner", "-encoders"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        return encoder in result.stdout
    except Exception:
        return False

# -------------- دعم GPU - اختيار الترميز --------------
def get_gpu_encoders():
    """إرجاع قائمة الترميزات المتاحة بناءً على GPU المكتشف"""
    # اكتشاف نوع GPU
    gpu = detect_gpu()
    encoders = ["libx264", "libx265"]  # الترميزات الافتراضية CPU
    candidates = [] # قائمة الترميزات المحتملة بناءً على نوع GPU
    
    # تحديد الترميزات المحتملة بناءً على نوع GPU
    if gpu == "NVIDIA":
        candidates = ["h264_nvenc", "hevc_nvenc"]
    elif gpu == "Intel":
        candidates = ["h264_qsv", "hevc_qsv", "h264_vaapi", "hevc_vaapi"]
    elif gpu == "AMD":
        candidates = ["h264_amf", "hevc_amf", "h264_vaapi", "hevc_vaapi"]
    elif gpu == "Apple":
        candidates = ["h264_videotoolbox", "hevc_videotoolbox"]

    # تحقق من الترميزات الفعلية الموجودة في FFmpeg
    for enc in candidates:
        if is_encoder_supported(enc):
            encoders.insert(0, enc)  # أضفها في بداية القائمة حسب الأولوية

    return encoders

# -------------- دعم GPU - اختيار أفضل ترميز --------------
def choose_best_encoder():
    """اختيار أفضل ترميز بناءً على ما هو مدعوم فعلاً"""
    # الحصول على الترميزات المدعومة
    encoders = get_gpu_encoders()

    # تحديد الأولويات للترميزات
    priority = [
        "hevc_nvenc", "h264_nvenc",     # NVIDIA
        "hevc_qsv", "h264_qsv",         # Intel
        "hevc_amf", "h264_amf",         # AMD
        "hevc_videotoolbox", "h264_videotoolbox",  # macOS
        "libx265", "libx264"            # CPU fallback
    ]

    # اختيار أفضل ترميز متاح 
    for p in priority:
        if p in encoders:
            return p
    return "libx264"


# -------------- ضغط الفيديو --------------
def compress_video(input_path, output_path, encoder=None, crf=23, preset='medium', copy_codec=False):
    """
    ضغط الفيديو باستخدام FFmpeg مع دعم GPU واختيار الترميز الأفضل تلقائياً
    """
    # إذا تم اختيار نسخ الترميز الأصلي
    if copy_codec:
        cmd = [ffmpeg_path, '-i', input_path, '-c', 'copy', output_path]
    else:
        # اختيار الترميز المناسب
        if encoder is None:
            encoder = choose_best_encoder()
        
        # بناء أمر FFmpeg للضغط
        cmd = [
            ffmpeg_path if os.path.exists(ffmpeg_path) else 'ffmpeg',
            '-i', input_path,
            '-c:v', encoder,
            '-crf', str(crf),
            '-preset', preset,
            '-c:a', 'copy',
            output_path ,
            '-y'
        ]

    # تنفيذ أمر FFmpeg
    try:
        subprocess.run(cmd, check=True)
        #✅ تم ضغط الفيديو بنجاح: {output_path}
    # التعامل مع أخطاء FFmpeg
    except subprocess.CalledProcessError as e:
        # في حال فشل الترميز، العودة إلى libx264
        if encoder != "libx264":

            fallback_cmd = [
                ffmpeg_path, '-i', input_path,
                '-c:v', 'libx264',
                '-crf', str(crf),
                '-preset', preset,
                '-c:a', 'copy',
                output_path ,
                '-y'
            ]

            subprocess.run(fallback_cmd, check=True)
        else:
            raise Exception(f"❌ فشل ضغط الفيديو نهائياً: {e}")

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
                    if entry:
                        # رابط لفيديو داخل قائمة التشغيل
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
            
            # إرجاع المعلومات المطلوبة
            return {
                "videos": videos,
                "playlist_title": playlist_title
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

# تابع التحميل الرئيسي مع دعم GPU
# -------------- تحميل الفيديو --------------
def download_video(url, download_dir, quality, file_type, download_subtitles, progress_hook=None, playlist_title=None,ffmpeg_path=ffmpeg_path, use_aria2=False , cookies_path="\U0001F36A" , encoder='libx264', crf=23, preset='medium', copy_codec=False):
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
        # التحقق من حالة الإيقاف
        if stop_event.is_set():
            raise Exception("Download stopped by user")
        # استدعاء دالة التقدم الأصلية إذا كانت موجودة
        if progress_hook:
            # تمرير حالة التقدم إلى الدالة الأصلية
            progress_hook(d)
    
    # إنشاء مجلد لقائمة التشغيل إذا تم تحديدها
    final_download_dir = download_dir
    # إذا كان هناك عنوان لقائمة التشغيل
    if playlist_title:
        # إنشاء مجلد فرعي داخل مجلد التحميل باسم قائمة التشغيل
        sanitized_playlist_title = sanitize_filename(playlist_title)
        
        playlist_dir = os.path.join(download_dir, sanitized_playlist_title)
        # إنشاء المجلد إذا لم يكن موجوداً
        if not os.path.exists(playlist_dir):
            os.makedirs(playlist_dir)

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
            ydl.download([url])

            # بعد التحميل، ضغط الفيديو إذا لم يكن mp3
            if file_type == 'mp4' and not copy_codec:
                # ضغط جميع ملفات الفيديو في المجلد النهائي
                video_files = [os.path.join(final_download_dir, f) for f in os.listdir(final_download_dir) if f.endswith(".mp4")]
                for vf in video_files:
                    # إنشاء اسم ملف جديد للفيديو المضغوط
                    out_file = os.path.join(final_download_dir, "compressed_" + os.path.basename(vf))
                    # ضغط الفيديو
                    compress_video(vf, out_file, encoder=encoder, crf=crf, preset=preset, copy_codec=copy_codec)
                    
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
