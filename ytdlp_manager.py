"""Manage a writable, self-updating yt-dlp package for frozen Linux builds.

PyInstaller applications cannot be updated with ``python -m pip`` because
``sys.executable`` points to the application, not to a normal Python
interpreter.  This module keeps yt-dlp outside the AppImage and activates it
before :mod:`downloader` imports it.

The AppImage contains only a seed copy for first use/offline recovery.  New
versions are downloaded as official PyPI wheels, verified with the SHA-256
digest published by PyPI, extracted to a versioned directory, and activated
with an atomic state-file replacement.

إدارة حزمة yt-dlp قابلة للكتابة والتحديث الذاتي لأنظمة لينكس المُجمدة.

لا يمكن تحديث تطبيقات PyInstaller باستخدام الأمر ``python -m pip`` لأن

``sys.executable`` يشير إلى التطبيق، وليس إلى مُفسِّر بايثون عادي.

تحتفظ هذه الوحدة بـ yt-dlp خارج AppImage وتُفعِّلها
قبل أن يستوردها :mod:`downloader`.

يحتوي AppImage على نسخة أولية فقط للاستخدام الأول/الاستعادة دون اتصال بالإنترنت.

يتم تنزيل الإصدارات الجديدة
كملفات PyPI رسمية، والتحقق منها باستخدام SHA-256
المنشورة بواسطة PyPI، واستخراجها إلى دليل مُرقَّم، وتفعيلها
باستبدال ملف الحالة بشكل كامل.

"""

from __future__ import annotations # تفعيل دعم التعليقات التوضيحية للأنواع المستقبلية في بايثون

import ast # استراد مكتبة ast لتحليل شجرة بناء الجملة في بايثون
import contextlib # استراد مكتبة contextlib لتوفير أدوات إدارة السياق
import hashlib # استراد مكتبة hashlib لتوفير وظائف التشفير والتحقق من صحة البيانات
import hmac # استراد مكتبة hmac لتوفير وظائف التحقق من صحة الرسائل باستخدام HMAC
import importlib # استراد مكتبة importlib لتوفير وظائف استيراد الوحدات البرمجية
import importlib.machinery # استراد مكتبة importlib.machinery لتوفير وظائف إدارة الوحدات البرمجية
import importlib.util # استراد مكتبة importlib.util لتوفير وظائف مساعدة لإدارة الوحدات البرمجية
import json # استراد مكتبة json لتوفير وظائف التعامل مع بيانات JSON
import os # استراد مكتبة os لتوفير وظائف التعامل مع نظام التشغيل
import re # استراد مكتبة re لتوفير وظائف التعامل مع التعبيرات النمطية
import shutil # استراد مكتبة shutil لتوفير وظائف التعامل مع الملفات والمجلدات
import stat # استراد مكتبة stat لتوفير وظائف التعامل مع خصائص الملفات
import sys # استراد مكتبة sys لتوفير وظائف التعامل مع نظام بايثون والبيئة المحيطة
import tempfile # استراد مكتبة tempfile لتوفير وظائف إنشاء ملفات ومجلدات مؤقتة
import time # استراد مكتبة time لتوفير وظائف التعامل مع الوقت والتاريخ
import urllib.parse # استراد مكتبة urllib.parse لتوفير وظائف تحليل وبناء عناوين URL
import urllib.request # استراد مكتبة urllib.request لتوفير وظائف التعامل مع طلبات HTTP
import zipfile # استراد مكتبة zipfile لتوفير وظائف التعامل مع ملفات ZIP
from dataclasses import dataclass # استراد dataclass من مكتبة dataclasses لتوفير دعم إنشاء فئات البيانات بسهولة
from pathlib import Path # استراد Path من مكتبة pathlib لتوفير وظائف التعامل مع مسارات الملفات والمجلدات
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple # استراد أنواع البيانات من مكتبة typing لتوفير دعم التوضيح النوعي للمتغيرات والدوال


PYPI_JSON_URL = "https://pypi.org/pypi/yt-dlp/json" # عنوان URL لواجهة برمجة التطبيقات الخاصة بـ PyPI للحصول على بيانات JSON الخاصة بحزمة yt-dlp
DEFAULT_CHECK_INTERVAL = 24 * 60 * 60 # الفاصل الزمني الافتراضي للتحقق من التحديثات (24 ساعة)
FAILED_CHECK_INTERVAL = 60 * 60 # الفاصل الزمني للتحقق من التحديثات بعد فشل التحقق السابق (1 ساعة)
DEFAULT_NETWORK_TIMEOUT = 5 # الوقت الافتراضي للمهلة الشبكية (5 ثوانٍ)
MAX_METADATA_BYTES = 2 * 1024 * 1024 # الحد الأقصى لحجم بيانات JSON المسترجعة من PyPI (2 ميجابايت)
MAX_WHEEL_BYTES = 50 * 1024 * 1024 # الحد الأقصى لحجم ملف wheel الذي يمكن تنزيله من PyPI (50 ميجابايت)
MAX_EXTRACTED_BYTES = 150 * 1024 * 1024 # الحد الأقصى لحجم البيانات المستخرجة (150 ميجابايت)
STATE_SCHEMA = 1 # رقم إصدار مخطط البيانات المستخدم في ملف الحالة لتتبع حالة التحديثات والإصدارات

# خطأ يُرفع عندما لا يكون هناك yt-dlp خارجي أو مُدمج قابل للاستخدام
class YtDlpUnavailableError(RuntimeError):
    """Raised when neither an external nor bundled yt-dlp is usable."""

# نتيجة مُهيكلة تُرجع إلى واجهة المستخدم الرسومية وإلى كود بدء التشغيل
@dataclass(frozen=True)
class UpdateResult:
    """Structured result returned to the GUI and to startup code."""

    status: str # حالة التحديث
    previous_version: Optional[str] # الإصدار السابق
    current_version: Optional[str] # الإصدار الحالي
    message: str = "" # رسالة إضافية توضح الحالة أو الخطأ
       
    @property # دالة خاصية تُرجع ما إذا كانت الحالة تشير إلى وجود تغيير في الإصدار
    def changed(self) -> bool:
        return self.status in {"seeded", "updated", "recovered"}

# دالة تُرجع ما إذا كان يجب على العملية الحالية استخدام وقت تشغيل yt-dlp القابل للكتابة
def external_management_enabled(environ: Optional[Dict[str, str]] = None) -> bool:
    """Return whether this process should use the writable yt-dlp runtime."""

    env = os.environ if environ is None else environ    # الحصول على متغيرات البيئة
    forced = env.get("MEDIA_DOWNLOADER_FORCE_EXTERNAL_YTDLP", "").lower() # الحصول على قيمة متغير البيئة الذي يفرض استخدام yt-dlp الخارجي
    if forced in {"1", "true", "yes", "on"}:
        return True
    if forced in {"0", "false", "no", "off"}:
        return False
    # التحقق مما إذا كان يتم تشغيل التطبيق داخل صورة AppImage
    appimage_runtime = any(
        env.get(name)
        for name in ("APPIMAGE", "APPDIR", "MEDIA_DOWNLOADER_APPIMAGE")
    )
    return sys.platform.startswith("linux") and (
        appimage_runtime or bool(getattr(sys, "frozen", False))
    )

# دالة تُرجع الدليل الافتراضي لتخزين إعدادات المستخدم القابلة للكتابة
def default_config_dir(environ: Optional[Dict[str, str]] = None) -> Path:
    """Return the per-user writable configuration directory."""

    env = os.environ if environ is None else environ
    explicit = env.get("MEDIA_DOWNLOADER_CONFIG_DIR") # الحصول على قيمة متغير البيئة الذي يحدد الدليل الافتراضي لتخزين إعدادات المستخدم
    if explicit and Path(explicit).expanduser().is_absolute(): # التحقق مما إذا كان الدليل المحدد موجودًا وصحيحًا
        return Path(explicit).expanduser()

    xdg_config = env.get("XDG_CONFIG_HOME") # الحصول على قيمة متغير البيئة الذي يحدد الدليل الافتراضي لتخزين إعدادات المستخدم وفقًا لمعيار XDG
    xdg_path = Path(xdg_config).expanduser() if xdg_config else None # التحقق مما إذا كان الدليل المحدد موجودًا وصحيحًا وفقًا لمعيار XDG
    base = xdg_path if xdg_path and xdg_path.is_absolute() else Path.home() / ".config" # إذا لم يتم تحديد الدليل وفقًا لمعيار XDG، يتم استخدام الدليل الافتراضي ~/.config
    return base / "media-downloader" # إرجاع الدليل النهائي لتخزين إعدادات المستخدم القابلة للكتابة

# دالة تُرجع مفتاحًا قابلًا للمقارنة لإصدارات yt-dlp المستندة إلى التاريخ
def _version_key(version: str) -> Tuple[int, ...]:
    """Return a comparable key for yt-dlp's date-based versions."""

    numbers = tuple(int(part) for part in re.findall(r"\d+", version)) # استخراج الأرقام من الإصدار وتحويلها إلى أعداد صحيحة
    return numbers or (0,) # إرجاع المفتاح القابل للمقارنة، وإذا لم يتم العثور على أرقام، يتم إرجاع (0,)

# دالة تُرجع الإصدار إذا كان آمنًا، أو None إذا لم يكن كذلك
def _safe_version(version: Any) -> Optional[str]:
    if not isinstance(version, str):
        return None
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.+-]{0,79}", version): # التحقق مما إذا كان الإصدار يتوافق مع التنسيق المطلوب
        return None
    if ".." in version:
        return None
    return version

# دالة تُرجع True إذا كان الإصدار موجودًا في قائمة الإصدارات
def _version_in(version: str, versions: Any) -> bool:
    wanted = _version_key(version) # الحصول على المفتاح القابل للمقارنة للإصدار المطلوب
    return any(
        _version_key(candidate) == wanted
        for candidate in versions
        if _safe_version(candidate)
    )

# دالة تتحقق مما إذا كانت متطلبات Python المحددة في PEP 440 تسمح بالإصدار الحالي من Python
def _python_requirement_allows(requirement: Any) -> bool:
    """Check the common PEP 440 Requires-Python forms without pip."""

    if not requirement:
        return True
    if not isinstance(requirement, str):
        return False

    current = tuple(sys.version_info[:3]) # الحصول على الإصدار الحالي من Python كزوج من الأعداد الصحيحة (major, minor, micro)
    for raw_clause in requirement.split(","): # التعامل مع كل شرط من شروط متطلبات Python المحددة في PEP 440
        clause = raw_clause.strip()
        match = re.fullmatch(r"(>=|<=|==|!=|>|<)\s*(\d+(?:\.\d+){0,2})(\.\*)?", clause)
        if not match:
            # Unknown syntax is rejected rather than risking an incompatible
            # package inside a frozen interpreter.
            return False
        operator, raw_version, wildcard = match.groups()
        parts = tuple(int(part) for part in raw_version.split("."))
        if wildcard:
            equal = current[: len(parts)] == parts
        else:
            padded = parts + (0,) * (3 - len(parts))
            equal = current == padded
            if operator == ">=" and not current >= padded:
                return False
            if operator == ">" and not current > padded:
                return False
            if operator == "<=" and not current <= padded:
                return False
            if operator == "<" and not current < padded:
                return False
        if operator == "==" and not equal:
            return False
        if operator == "!=" and equal:
            return False
    return True

# دالة تُرجع إصدار yt-dlp من دليل الحزمة دون استيراد كود غير موثوق به
def _package_version(package_dir: Path) -> str:
    """Read yt-dlp's version without importing untrusted candidate code."""

    version_file = package_dir / "version.py" # تحديد مسار ملف version.py داخل دليل الحزمة
    if not version_file.is_file():
        raise ValueError("yt_dlp/version.py is missing")

    tree = ast.parse(version_file.read_text(encoding="utf-8"), str(version_file)) # تحليل محتوى ملف version.py
    for node in tree.body: # التكرار على عقدة شجرة التحليل
        if not isinstance(node, (ast.Assign, ast.AnnAssign)): # التحقق مما إذا كانت العقدة تمثل تعيينًا أو تعيينًا مع تعليق نوعي
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target] # الحصول على قائمة الأهداف (المتغيرات) في حالة التعيين
        if not any(isinstance(target, ast.Name) and target.id == "__version__" for target in targets):
            continue
        value = node.value # الحصول على القيمة المعينة لمتغير __version__
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            safe = _safe_version(value.value)
            if safe:
                return safe
    raise ValueError("yt_dlp version is invalid")

# دالة تقوم بكتابة بيانات JSON إلى ملف بشكل آمن، مع إنشاء المجلدات اللازمة إذا لم تكن موجودة، واستخدام ملف مؤقت لضمان الكتابة الذرية
def _atomic_json_write(path: Path, value: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True) # إنشاء المجلدات اللازمة إذا لم تكن موجودة
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    ) # إنشاء ملف مؤقت في نفس المجلد الذي سيتم كتابة البيانات فيه
    temporary_path = Path(temporary_name) # 
    try:
        # فتح الملف المؤقت للكتابة وكتابة بيانات JSON فيه، ثم استبدال الملف الأصلي بالملف المؤقت لضمان الكتابة الذرية
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as handle: 
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        with contextlib.suppress(FileNotFoundError):
            temporary_path.unlink()

# دالة سياق تُستخدم لتأمين الوصول إلى ملف القفل أثناء عمليات التشغيل الأولية أو التحديثات المتزامنة، بحيث يتم منع الوصول المتزامن من عمليات متعددة
@contextlib.contextmanager
def _update_lock(path: Path) -> Iterator[None]:
    """Serialize first-run/update operations across simultaneous launches."""

    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+b")
    try:
        if os.name == "nt":
            import msvcrt

            handle.seek(0)
            if handle.read(1) == b"":
                handle.seek(0)
                handle.write(b"0")
                handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        if os.name == "nt":
            import msvcrt

            handle.seek(0)
            with contextlib.suppress(OSError):
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            with contextlib.suppress(OSError):
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()

# فئة YtDlpManager تُستخدم لإدارة حزمة yt-dlp القابلة للكتابة والتحديث الذاتي، بما في ذلك التثبيت، التحديث، التحقق من الصحة، وتفعيل الحزمة الخارجية yt-dlp.
class YtDlpManager:
    """Install, update, validate, and activate an external yt-dlp package."""

    def __init__(
        self,
        config_dir: Optional[Path] = None,
        seed_package: Optional[Path] = None,
        urlopen: Callable[..., Any] = urllib.request.urlopen,
        clock: Callable[[], float] = time.time,
        check_interval: int = DEFAULT_CHECK_INTERVAL,
        network_timeout: int = DEFAULT_NETWORK_TIMEOUT,
    ) -> None:
        self.config_dir = Path(config_dir) if config_dir else default_config_dir()
        self.runtime_dir = self.config_dir / "yt-dlp"
        self.versions_dir = self.runtime_dir / "versions"
        self.state_path = self.runtime_dir / "state.json"
        self.lock_path = self.runtime_dir / "update.lock"
        self._seed_package = Path(seed_package) if seed_package else None
        self._urlopen = urlopen
        self._clock = clock
        self.check_interval = max(0, int(check_interval))
        self.network_timeout = max(1, int(network_timeout))
    # دالة خاصة تُستخدم لقراءة حالة التحديثات والإصدارات من ملف JSON، والتحقق من صحة البيانات وإرجاعها كقاموس، أو إرجاع حالة افتراضية إذا لم يكن الملف موجودًا أو كان غير صالح.
    def _read_state(self) -> Dict[str, Any]:
        try:
            state = json.loads(self.state_path.read_text(encoding="utf-8"))
            if isinstance(state, dict) and state.get("schema") == STATE_SCHEMA:
                broken = state.get("broken_versions")
                state["broken_versions"] = (
                    [item for item in broken if _safe_version(item)]
                    if isinstance(broken, list)
                    else []
                )
                return state
        except (OSError, ValueError, TypeError):
            pass
        return {"schema": STATE_SCHEMA, "broken_versions": []}
    # دالة خاصة تُستخدم لكتابة حالة التحديثات والإصدارات إلى ملف JSON بشكل آمن، مع إضافة رقم إصدار المخطط إلى البيانات قبل الكتابة.
    def _write_state(self, state: Dict[str, Any]) -> None:
        state["schema"] = STATE_SCHEMA
        _atomic_json_write(self.state_path, state)
    # دالة خاصة تُستخدم للحصول على الدليل الجذري لإصدار yt-dlp المحدد، مع التحقق من أن الإصدار آمن وصحيح.
    def _version_root(self, version: str) -> Path:
        safe = _safe_version(version)
        if not safe:
            raise ValueError("Unsafe yt-dlp version")
        return self.versions_dir / safe

    # دالة خاصة تُستخدم للتحقق من صحة الدليل الجذري لإصدار yt-dlp المحدد.
    def _validate_root(
        self,
        root: Path,
        expected_version: Optional[str] = None,
        deep: bool = False,
    ) -> str:
        package_dir = root / "yt_dlp"
        if not package_dir.is_dir() or not (package_dir / "__init__.py").is_file():
            raise ValueError("yt_dlp package is incomplete")

        version = _package_version(package_dir)
        if (
            expected_version is not None
            and _version_key(version) != _version_key(expected_version)
        ):
            raise ValueError(
                f"yt-dlp wheel version mismatch: expected {expected_version}, got {version}"
            )

        if deep:
            # Parse every Python file once at installation.  This catches
            # corrupt downloads and syntax newer than the embedded Python.
            for python_file in package_dir.rglob("*.py"):
                ast.parse(
                    python_file.read_text(encoding="utf-8"),
                    str(python_file),
                )
        return version
    # دالة خاصة تُستخدم للعثور على حزمة yt-dlp الأولية (seed package) التي يمكن استخدامها لتثبيت أو تحديث الحزمة، سواء كانت موجودة في دليل محدد، أو في متغير البيئة، أو مضمنة في التطبيق، أو مثبتة في بيئة Python الحالية.
    def _find_seed_package(self) -> Optional[Path]:
        if self._seed_package and self._seed_package.is_dir():
            return self._seed_package

        env_seed = os.environ.get("MEDIA_DOWNLOADER_YTDLP_SEED")
        if env_seed and Path(env_seed).is_dir():
            return Path(env_seed)

        resource_base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
        bundled_seed = resource_base / "ytdlp_seed" / "yt_dlp"
        if bundled_seed.is_dir():
            return bundled_seed

        # Source/VENV AppImage builds can use their installed package as seed.
        try:
            spec = importlib.util.find_spec("yt_dlp")
        except (ImportError, AttributeError, ValueError):
            spec = None
        if spec and spec.submodule_search_locations:
            candidate = Path(next(iter(spec.submodule_search_locations)))
            if candidate.is_dir():
                return candidate
        return None
    # دالة خاصة تُستخدم لتحديد الدليل الجذري الذي يجب نسخه عند استخدام الحزمة الأولية (seed package) المدمجة، بحيث يتم نسخ الحزمة بأكملها إذا كانت مدمجة، أو نسخ حزمة yt_dlp فقط إذا كانت موجودة في بيئة Python الحالية.
    def _seed_root(self, seed_package: Path) -> Path:
        """Return the data root to copy for the bundled seed.

        The build stores ``yt-dlp[default]`` and its dependencies together in
        ``ytdlp_seed``.  Explicit/test seeds and a source-environment fallback
        copy only the yt_dlp package to avoid copying an entire site-packages.
        """

        resource_base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
        bundled_root = resource_base / "ytdlp_seed"
        try:
            if seed_package.resolve().parent == bundled_root.resolve():
                return bundled_root
        except OSError:
            pass
        return seed_package
    # دالة خاصة تُستخدم لنسخ الحزمة الأولية (seed package) إلى الدليل المخصص للإصدارات، والتحقق من صحة النسخة المنسوخة، وتحديث حالة التحديثات والإصدارات في ملف الحالة.
    def _copy_seed_locked(self, state: Dict[str, Any]) -> str:
        seed = self._find_seed_package() # البحث عن الحزمة الأولية (seed package) التي يمكن استخدامها لتثبيت أو تحديث الحزمة
        if seed is None:
            raise YtDlpUnavailableError("The bundled yt-dlp seed was not found")

        version = _package_version(seed) # الحصول على الإصدار من الحزمة الأولية (seed package)
        target = self._version_root(version) # تحديد الدليل الجذري الذي يجب نسخه عند استخدام الحزمة الأولية (seed package)
        target_valid = False
        if target.exists():
            try:
                self._validate_root(target, version)
                target_valid = True
            except (OSError, SyntaxError, UnicodeError, ValueError):
                target_valid = False
        if not target_valid:
            self.versions_dir.mkdir(parents=True, exist_ok=True)
            staging = Path(
                tempfile.mkdtemp(prefix=".seed-", dir=str(self.versions_dir))
            )
            backup: Optional[Path] = None
            try:
                seed_root = self._seed_root(seed)
                if seed_root == seed:
                    destination = staging / "yt_dlp"
                else:
                    destination = staging
                shutil.copytree(
                    seed_root,
                    destination,
                    dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
                )
                self._validate_root(staging, version, deep=True)
                if target.exists():
                    backup = self.versions_dir / (
                        f".broken-{version}-{os.getpid()}-{time.time_ns()}"
                    )
                    os.replace(target, backup)
                os.replace(staging, target)
                if backup is not None:
                    shutil.rmtree(backup, ignore_errors=True)
                    backup = None
            except Exception:
                if backup is not None and backup.exists() and not target.exists():
                    os.replace(backup, target)
                raise
            finally:
                shutil.rmtree(staging, ignore_errors=True)
                if backup is not None:
                    shutil.rmtree(backup, ignore_errors=True)

        old_version = _safe_version(state.get("active_version"))
        broken = {
            item
            for item in (state.get("broken_versions") or [])
            if _version_key(item) != _version_key(version)
        }
        state["broken_versions"] = sorted(broken)
        state["previous_version"] = old_version
        state["active_version"] = version
        state["seed_version"] = version
        state["last_error"] = None
        self._write_state(state)
        return version
    # دالة خاصة تُستخدم لتحديد الإصدار النشط من yt-dlp الذي يجب استخدامه، والتحقق من صحة الإصدار، وتحديث حالة التحديثات والإصدارات في ملف الحالة إذا تم العثور على إصدار صالح.
    def _active_version_locked(self, state: Dict[str, Any]) -> Optional[str]:
        active = _safe_version(state.get("active_version"))
        broken = set(state.get("broken_versions") or [])
        if active and not _version_in(active, broken):
            try:
                self._validate_root(self._version_root(active), active)
                return active
            except (OSError, SyntaxError, UnicodeError, ValueError):
                pass

        candidates: List[Tuple[Tuple[int, ...], str]] = []
        if self.versions_dir.is_dir():
            for candidate in self.versions_dir.iterdir():
                version = _safe_version(candidate.name)
                if not version or _version_in(version, broken) or not candidate.is_dir():
                    continue
                try:
                    actual = self._validate_root(candidate, version)
                except (OSError, SyntaxError, UnicodeError, ValueError):
                    continue
                candidates.append((_version_key(actual), version))

        if candidates:
            version = max(candidates)[1]
            state["active_version"] = version
            self._write_state(state)
            return version
        return None
    # دالة خاصة تُستخدم لقراءة البيانات من عنوان URL محدد، مع التحقق من أن حجم البيانات لا يتجاوز الحد الأقصى المسموح به، وإرجاع البيانات المقروءة كـ bytes.
    def _read_url(self, url: str, maximum: int) -> bytes:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Media-Downloader/yt-dlp-updater"},
        )
        response = self._urlopen(request, timeout=self.network_timeout)
        try:
            length_header = getattr(response, "headers", {}).get("Content-Length")
            if length_header and int(length_header) > maximum:
                raise ValueError("Download is larger than the allowed limit")
            data = response.read(maximum + 1)
            if len(data) > maximum:
                raise ValueError("Download is larger than the allowed limit")
            return data
        finally:
            close = getattr(response, "close", None)
            if close:
                close()
    # دالة خاصة تُستخدم للحصول على أحدث إصدار من yt-dlp من PyPI، والتحقق من صحة الإصدار ومتطلبات Python، وإرجاع الإصدار، وعنوان URL للملف wheel، وهاش SHA-256 للتحقق من صحة الملف.
    def _latest_wheel(self) -> Tuple[str, str, str]:
        metadata = json.loads(
            self._read_url(PYPI_JSON_URL, MAX_METADATA_BYTES).decode("utf-8")
        )
        version = _safe_version(metadata.get("info", {}).get("version"))
        if not version:
            raise ValueError("PyPI returned an invalid yt-dlp version")
        requires_python = metadata.get("info", {}).get("requires_python")
        if not _python_requirement_allows(requires_python):
            raise ValueError(
                f"yt-dlp {version} does not support Python "
                f"{sys.version_info.major}.{sys.version_info.minor}"
            )

        wheels = [
            item
            for item in metadata.get("urls", [])
            if item.get("packagetype") == "bdist_wheel"
            and item.get("filename", "").endswith("-py3-none-any.whl")
        ]
        if not wheels:
            raise ValueError("PyPI did not return a universal yt-dlp wheel")

        wheel = wheels[0]
        wheel_url = wheel.get("url", "")
        parsed = urllib.parse.urlparse(wheel_url)
        if parsed.scheme != "https" or not (
            parsed.hostname == "files.pythonhosted.org"
            or (parsed.hostname or "").endswith(".pythonhosted.org")
        ):
            raise ValueError("PyPI returned an unsafe wheel URL")

        digest = wheel.get("digests", {}).get("sha256", "")
        if not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
            raise ValueError("PyPI returned an invalid wheel digest")
        return version, wheel_url, digest.lower()
    # دالة خاصة تُستخدم لاستخراج محتويات ملف wheel الخاص بـ yt-dlp إلى دليل مؤقت، والتحقق من صحة الملفات المستخرجة، وإرجاع الدليل المؤقت الذي يحتوي على الملفات المستخرجة.
    def _extract_wheel(
        self,
        wheel_data: bytes,
        expected_version: str,
        base_root: Optional[Path] = None,
    ) -> Path:
        self.versions_dir.mkdir(parents=True, exist_ok=True)
        staging = Path(
            tempfile.mkdtemp(prefix=".candidate-", dir=str(self.versions_dir))
        )
        if base_root is not None:
            shutil.copytree(
                base_root,
                staging,
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
            )
            shutil.rmtree(staging / "yt_dlp", ignore_errors=True)
            for old_metadata in staging.glob("yt_dlp-*.dist-info"):
                shutil.rmtree(old_metadata, ignore_errors=True)
            for old_data in staging.glob("yt_dlp-*.data"):
                shutil.rmtree(old_data, ignore_errors=True)
        wheel_path = staging / "yt-dlp.whl"
        wheel_path.write_bytes(wheel_data)

        try:
            total_size = 0
            with zipfile.ZipFile(wheel_path) as archive:
                for member in archive.infolist():
                    total_size += member.file_size
                    if total_size > MAX_EXTRACTED_BYTES:
                        raise ValueError("yt-dlp wheel expands beyond the allowed limit")

                    member_path = Path(member.filename)
                    if member_path.is_absolute() or ".." in member_path.parts:
                        raise ValueError("yt-dlp wheel contains an unsafe path")
                    file_mode = (member.external_attr >> 16) & 0o170000
                    if file_mode == stat.S_IFLNK:
                        raise ValueError("yt-dlp wheel contains a symbolic link")

                    destination = staging.joinpath(*member_path.parts)
                    if member.is_dir():
                        destination.mkdir(parents=True, exist_ok=True)
                        continue
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(member) as source, destination.open("wb") as target:
                        shutil.copyfileobj(source, target)
            wheel_path.unlink()
            self._validate_root(staging, expected_version, deep=True)
            return staging
        except Exception:
            shutil.rmtree(staging, ignore_errors=True)
            raise
    # دالة خاصة تُستخدم للتحقق من وجود تحديثات جديدة على PyPI، وتنزيل أحدث إصدار من yt-dlp إذا كان متاحًا، والتحقق من صحة الإصدار، وتحديث حالة التحديثات والإصدارات في ملف الحالة.
    def _update_locked(self, state: Dict[str, Any], force: bool) -> UpdateResult:
        current = self._active_version_locked(state)
        now = self._clock()
        last_check = state.get("last_check_at", 0)
        retry_interval = (
            FAILED_CHECK_INTERVAL if state.get("last_error") else self.check_interval
        )
        try:
            elapsed = now - float(last_check or 0)
        except (TypeError, ValueError):
            elapsed = retry_interval
        if not force and current and 0 <= elapsed < retry_interval:
            return UpdateResult("ready", current, current)

        state["last_check_at"] = now
        try:
            latest, wheel_url, expected_digest = self._latest_wheel()
            if current and _version_key(latest) <= _version_key(current):
                state["last_error"] = None
                self._write_state(state)
                return UpdateResult("up_to_date", current, current)

            if _version_in(latest, state.get("broken_versions") or []):
                message = (
                    f"yt-dlp {latest} previously failed its runtime check; "
                    "waiting for a newer release"
                )
                state["last_error"] = message
                self._write_state(state)
                return UpdateResult("rollback", current, current, message)

            wheel_data = self._read_url(wheel_url, MAX_WHEEL_BYTES)
            actual_digest = hashlib.sha256(wheel_data).hexdigest()
            if not hmac.compare_digest(actual_digest, expected_digest):
                raise ValueError("The yt-dlp wheel SHA-256 digest does not match PyPI")

            target = self._version_root(latest)
            if target.exists():
                self._validate_root(target, latest)
            else:
                base_root = self._version_root(current) if current else None
                staging = self._extract_wheel(wheel_data, latest, base_root)
                try:
                    os.replace(staging, target)
                finally:
                    shutil.rmtree(staging, ignore_errors=True)

            state["previous_version"] = current
            state["active_version"] = latest
            state["last_error"] = None
            self._write_state(state)
            return UpdateResult("updated", current, latest)
        except Exception as error:
            state["last_error"] = f"{type(error).__name__}: {error}"
            self._write_state(state)
            if current:
                return UpdateResult("offline", current, current, str(error))
            raise YtDlpUnavailableError(str(error)) from error
    # دالة عامة تُستخدم لضمان وجود نسخة قابلة للكتابة من yt-dlp، والتحقق من وجود تحديثات جديدة على PyPI مرة واحدة يوميًا إذا تم تمكين ذلك.
    def ensure_ready(self, check_updates: bool = True) -> UpdateResult:
        """Ensure a writable copy exists, optionally checking PyPI once daily."""

        with _update_lock(self.lock_path):
            state = self._read_state()
            active = self._active_version_locked(state)
            seeded = False
            if not active:
                active = self._copy_seed_locked(state)
                state = self._read_state()
                seeded = True

            if check_updates and os.environ.get(
                "MEDIA_DOWNLOADER_DISABLE_YTDLP_AUTO_UPDATE", ""
            ).lower() not in {"1", "true", "yes", "on"}:
                result = self._update_locked(state, force=False)
                if result.status != "ready":
                    return result
            return UpdateResult("seeded" if seeded else "ready", None, active)
    # دالة عامة تُستخدم للتحقق من وجود تحديثات جديدة على PyPI وتنزيل أحدث إصدار من yt-dlp إذا كان متاحًا، مع فرض التحديث حتى لو لم يكن هناك حاجة لذلك.
    def update(self, force: bool = True) -> UpdateResult:
        """Check PyPI and atomically install a newer official wheel."""

        with _update_lock(self.lock_path):
            state = self._read_state()
            if not self._active_version_locked(state):
                self._copy_seed_locked(state)
                state = self._read_state()
            return self._update_locked(state, force=force)
    #  دالة عامة تُستخدم لإرجاع الدليل الجذري للإصدار النشط من yt-dlp الذي يجب استخدامه، مع التحقق من صحة الإصدار، وإذا لم يكن هناك إصدار نشط صالح، يتم نسخ الحزمة الأولية (seed package) وتحديث حالة التحديثات والإصدارات في ملف الحالة.
    def active_root(self) -> Path:
        """Return the validated directory that must be prepended to sys.path."""

        with _update_lock(self.lock_path):
            state = self._read_state()
            version = self._active_version_locked(state)
            if not version:
                version = self._copy_seed_locked(state)
            return self._version_root(version)
    # دالة عامة تُستخدم لعزل حزمة yt-dlp التي فشلت أثناء الاستيراد، وإضافة الإصدار النشط إلى قائمة الإصدارات المعطوبة، ومحاولة التراجع إلى الإصدار السابق إذا كان صالحًا، وإذا لم يكن هناك إصدار صالح، يتم إزالة الإصدار النشط من الحالة.
    def mark_active_broken(self, error: BaseException) -> Optional[Path]:
        """Quarantine a package that failed during import and select rollback."""

        with _update_lock(self.lock_path):
            state = self._read_state()
            active = _safe_version(state.get("active_version"))
            broken = set(state.get("broken_versions") or [])
            if active:
                broken.add(active)
            state["broken_versions"] = sorted(broken)
            state["last_error"] = f"Import failed: {type(error).__name__}: {error}"

            previous = _safe_version(state.get("previous_version"))
            if previous and not _version_in(previous, broken):
                try:
                    self._validate_root(self._version_root(previous), previous)
                    state["active_version"] = previous
                    self._write_state(state)
                    return self._version_root(previous)
                except (OSError, SyntaxError, UnicodeError, ValueError):
                    pass

            state.pop("active_version", None)
            self._write_state(state)
            active_version = self._active_version_locked(state)
            return self._version_root(active_version) if active_version else None
    # دالة عامة تُستخدم لتقليص استخدام القرص مع الاحتفاظ بنسخ نشطة، ونسخ التراجع، ونسخ الحزمة الأولية (seed package)، بحيث يتم الاحتفاظ بعدد محدد من الإصدارات الحديثة فقط.
    def prune_versions(self, keep_recent: int = 3) -> None:
        """Bound disk usage while retaining active, rollback, and seed copies."""

        with _update_lock(self.lock_path):
            state = self._read_state()
            protected = {
                version
                for version in (
                    _safe_version(state.get("active_version")),
                    _safe_version(state.get("previous_version")),
                    _safe_version(state.get("seed_version")),
                )
                if version
            }
            candidates = []
            if self.versions_dir.is_dir():
                for path in self.versions_dir.iterdir():
                    version = _safe_version(path.name)
                    if version and path.is_dir():
                        candidates.append((_version_key(version), version, path))
            candidates.sort(reverse=True)
            protected.update(
                version for _key, version, _path in candidates[: max(1, keep_recent)]
            )
            for _key, version, path in candidates:
                if version not in protected:
                    shutil.rmtree(path, ignore_errors=True)


_default_manager: Optional[YtDlpManager] = None
_loaded_module: Any = None
_startup_result: Optional[UpdateResult] = None
_external_finder: Any = None
_external_search_roots: set = set()

# دالة تُرجع مدير yt-dlp الافتراضي، وتقوم بإنشائه إذا لم يكن موجودًا بالفعل
def get_default_manager() -> YtDlpManager:
    global _default_manager
    if _default_manager is None:
        _default_manager = YtDlpManager()
    return _default_manager

# دالة خاصة تُستخدم لإزالة أي وحدات yt_dlp محملة من sys.modules، بحيث يمكن إعادة استيرادها من الإصدار النشط الجديد بعد التحديث أو التراجع.
def _purge_ytdlp_modules() -> None:
    for module_name in list(sys.modules):
        if module_name == "yt_dlp" or module_name.startswith("yt_dlp."):
            sys.modules.pop(module_name, None)

# دالة تُرجع ما إذا كان يجب استخدام إدارة yt-dlp الخارجية (managed) أو الاعتماد على الحزمة المثبتة في بيئة Python الحالية
class _ExternalYtDlpFinder:
    """Resolve yt_dlp only from the selected writable version directory.

    PyInstaller's frozen finder can otherwise win over a normal ``sys.path``
    entry.  Keeping this finder first also ensures later lazy extractor imports
    come from the same external version rather than mixing frozen/new modules.
    
    قم بحل yt_dlp فقط من دليل الإصدار القابل للكتابة المحدد.

    وإلا فقد يتفوق مُحدد البحث المُجمّد في PyInstaller على مسار ``sys.path`` العادي.

    كما أن إبقاء مُحدد البحث هذا في المقدمة يضمن استيراد مُستخرج البيانات الكسول لاحقًا

    من نفس الإصدار الخارجي بدلًا من خلط الوحدات المُجمّدة والجديدة.
    """

    def __init__(self, root: Path) -> None:
        self.root = root
    # دالة تُستخدم للعثور على مواصفات الوحدة yt_dlp من الدليل الجذري المحدد، بحيث يتم البحث فقط في الدليل الجذري للإصدار النشط من yt-dlp، وإذا لم يتم العثور على الوحدة، يتم رفع استثناء ModuleNotFoundError.
    def find_spec(self, fullname: str, path: Any = None, target: Any = None) -> Any:
        if fullname != "yt_dlp" and not fullname.startswith("yt_dlp."):
            return None
        search_path = [str(self.root)] if fullname == "yt_dlp" else path
        if not search_path:
            raise ModuleNotFoundError(
                f"External yt-dlp module has no search path: {fullname}"
            )
        spec = importlib.machinery.PathFinder.find_spec(fullname, search_path)
        if spec is None:
            raise ModuleNotFoundError(
                f"External yt-dlp module is missing: {fullname}"
            )
        return spec

# دالة خاصة تُستخدم لاستيراد حزمة yt-dlp من الدليل الجذري المحدد، بحيث يتم إضافة الدليل الجذري إلى sys.path مؤقتًا، وإنشاء مُحدد البحث الخارجي إذا لم يكن موجودًا بالفعل، والتحقق من أن الوحدة المستوردة تحتوي على الكائنات المطلوبة (YoutubeDL و DownloadError)، وإذا لم يتم استيفاء هذه الشروط، يتم رفع استثناء ImportError.
def _import_from_root(root: Path) -> Any:
    global _external_finder, _external_search_roots
    root_text = str(root)
    _external_search_roots.add(root_text)
    sys.path[:] = [entry for entry in sys.path if entry not in _external_search_roots]
    sys.path.insert(0, root_text)

    if _external_finder is None:
        _external_finder = _ExternalYtDlpFinder(root)
    else:
        _external_finder.root = root
    with contextlib.suppress(ValueError):
        sys.meta_path.remove(_external_finder)
    sys.meta_path.insert(0, _external_finder)

    importlib.invalidate_caches()
    module = importlib.import_module("yt_dlp")

    module_file = Path(module.__file__).resolve()
    expected_package = (root / "yt_dlp").resolve()
    if expected_package != module_file.parent and expected_package not in module_file.parents:
        raise ImportError(f"yt_dlp was loaded from an unexpected path: {module_file}")
    if not callable(getattr(module, "YoutubeDL", None)):
        raise ImportError("The external yt_dlp package does not provide YoutubeDL")
    download_error = getattr(module, "DownloadError", None)
    if not isinstance(download_error, type) or not issubclass(download_error, Exception):
        raise ImportError("The external yt_dlp package does not provide DownloadError")
    return module

# دالة تُستخدم لتحميل حزمة yt-dlp المُدارة في AppImage، أو الحزمة الموجودة في بيئة Python الحالية إذا لم يتم تمكين الإدارة الخارجية، بحيث يتم استيراد الوحدة yt_dlp من الدليل الجذري للإصدار النشط، وإذا لم يتم العثور على الوحدة أو كانت غير صالحة، يتم رفع استثناء YtDlpUnavailableError.
def load_ytdlp() -> Any:
    """Load the managed package in AppImage, or the environment package in source."""

    global _loaded_module, _startup_result
    if _loaded_module is not None:
        return _loaded_module

    if not external_management_enabled():
        _loaded_module = importlib.import_module("yt_dlp")
        return _loaded_module

    manager = get_default_manager()
    try:
        _startup_result = manager.ensure_ready(check_updates=True)
        root = manager.active_root()
    except Exception as error:
        seed = manager._find_seed_package()
        if seed is None:
            raise YtDlpUnavailableError(
                f"yt-dlp could not be prepared: {error}"
            ) from error
        root = seed.parent

    first_error: Optional[BaseException] = None
    attempted_roots = set()
    for _attempt in range(10):
        root_key = str(root.resolve())
        if root_key in attempted_roots:
            break
        attempted_roots.add(root_key)
        _purge_ytdlp_modules()
        try:
            _loaded_module = _import_from_root(root)
            try:
                if root.parent.resolve() == manager.versions_dir.resolve():
                    manager.prune_versions()
            except OSError:
                pass
            return _loaded_module
        except Exception as error:
            first_error = first_error or error
            rollback = None
            try:
                managed_root = root.parent.resolve() == manager.versions_dir.resolve()
            except OSError:
                managed_root = False
            if managed_root:
                try:
                    rollback = manager.mark_active_broken(error)
                except (OSError, YtDlpUnavailableError):
                    rollback = None
            if rollback is not None and str(rollback.resolve()) not in attempted_roots:
                root = rollback
                continue
            seed = manager._find_seed_package()
            if seed is not None and str(seed.parent.resolve()) not in attempted_roots:
                root = seed.parent
                continue
            break

    raise YtDlpUnavailableError(
        f"No usable yt-dlp package could be imported: {first_error}"
    ) from first_error

# دالة تُستخدم لتحديث حزمة yt-dlp المُدارة، بحيث يتم فرض التحقق من وجود تحديثات جديدة على PyPI وتنزيل أحدث إصدار إذا كان متاحًا، وإذا لم يتم تمكين الإدارة الخارجية، يتم إرجاع نتيجة تشير إلى أن yt-dlp مُدار بواسطة بيئة Python الحالية.
def update_ytdlp() -> UpdateResult:
    """Force a check used by the application's Update menu action."""

    if not external_management_enabled():
        try:
            load_ytdlp()
            version = getattr(
                importlib.import_module("yt_dlp.version"), "__version__", None
            )
        except Exception:
            version = None
        return UpdateResult(
            "managed_by_environment",
            version,
            version,
            "yt-dlp is managed by the current Python environment",
        )
    return get_default_manager().update(force=True)

# دالة تُستخدم لإرجاع نتيجة التحديث عند بدء تشغيل التطبيق، بحيث يتم إرجاع النتيجة التي تم الحصول عليها عند استدعاء load_ytdlp() لأول مرة، أو None إذا لم يتم استدعاء load_ytdlp() بعد.
def startup_update_result() -> Optional[UpdateResult]:
    return _startup_result
