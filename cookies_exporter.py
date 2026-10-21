#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cookies_exporter.py
===================
استخراج كوكيز المتصفح إلى ملف ``cookies.txt`` صالح ومضمون العمل،
ويعمل على: لينكس · ويندوز · ماك (macOS).

المزايا
--------
* استخراج الكوكيز من: Chrome, Chromium, Edge, Brave, Opera, Vivaldi, Whale, Firefox, Safari.
  (فك التشفير يتم عبر yt-dlp: DPAPI في ويندوز، Keychain في ماك، libsecret/kwallet في لينكس)
* كشف تلقائي للمتصفح الذي يحتوي على كوكيز مطابقة للنطاقات المطلوبة.
* كتابة الملف بصيغة Netscape الصحيحة (المعتمدة من yt-dlp و curl و wget).
* لا يدمج أبداً مع ملف قديم (الدمج مع كوكيز قديمة يُبطل الجلسة — درس مهم).
* تحقق ثابت (فحص الكوكيز اللازمة) + تحقق حي من أن الجلسة مسجَّلة فعلياً.
* نسخة JSON إضافية، ونسخة احتياطية تلقائية للملف السابق.
* تقرير واضح عند تدهور/انتهاء صلاحية الجلسة.

الاستخدام
---------
    python cookies_exporter.py                          # كشف تلقائي + تصدير + تحقق
    python cookies_exporter.py -b chrome                # متصفح محدّد
    python cookies_exporter.py -b firefox -p default    # ملف تعريف محدّد
    python cookies_exporter.py --list                   # عرض المتصفحات المتاحة
    python cookies_exporter.py --verify cookies.txt     # فحص ملف موجود فقط
    python cookies_exporter.py --test                   # تصدير + اختبار تنزيل حقيقي

المتطلبات
----------
    pip install -U yt-dlp
    # لينكس + متصفح Chromium (اختياري لكن موصى به):
    pip install secretstorage     # يتطلب libsecret-1 (sudo apt install libsecret-1-0)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import time
import urllib.error
import urllib.request
from http.cookiejar import Cookie

try:
    from yt_dlp.cookies import extract_cookies_from_browser
except ImportError:  # pragma: no cover
    sys.exit('خطأ: yt-dlp غير مثبّت.  ثبّته بـ:  pip install -U yt-dlp')


# --------------------------------------------------------------------------- #
# ثوابت
# --------------------------------------------------------------------------- #

BROWSER_ORDER = [
    'chrome', 'chromium', 'edge', 'brave', 'opera', 'vivaldi', 'whale', 'firefox', 'safari',
]

# يوتيوب: قاعدة التحقق نفسها التي تستخدمها yt-dlp في extractor/youtube/_base.py
YT_LOGIN_COOKIE = 'LOGIN_INFO'
YT_SID_COOKIES = ('SAPISID', '__Secure-1PAPISID', '__Secure-3PAPISID')

# يوتيوب يسلّم "VID" و "visitor data" عبر كوكيز إضافية
YT_EXTRA_COOKIES = (
    'VISITOR_INFO1_LIVE', 'VISITOR_PRIVACY_METADATA', 'YSC', 'SOCS', 'PREF',
    '__Secure-ROLLOUT_TOKEN', '__Secure-BUCKET', '__Secure-1PSIDTS', '__Secure-3PSIDTS',
    '__Secure-3PSIDCC', '__Secure-1PSIDCC', 'SIDCC', '__Secure-YNID',
)

# الفارق بالثواني بين 1601-01-01 (مُعتمد كرمز زمني في Chrome) و 1970-01-01
CHROME_EPOCH_OFFSET = 11644473600

DEFAULT_DOMAINS = ('youtube.com', 'google.com')
DEFAULT_OUTPUT = 'cookies.txt'

USER_AGENT = (
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/140.0.0.0 Safari/537.36'
)


# --------------------------------------------------------------------------- #
# أدوات مساعدة
# --------------------------------------------------------------------------- #

class Logger:
    """مُشغّل بسيط يكتم ضجيج استخراج الكوكيز من yt-dlp."""

    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose

    def debug(self, msg) -> None:
        if self.verbose:
            print(f'  [debug] {msg}', file=sys.stderr)

    def info(self, msg) -> None:
        if self.verbose:
            print(f'  [info]  {msg}', file=sys.stderr)

    def warning(self, msg) -> None:
        print(f'  [warn]  {msg}', file=sys.stderr)

    def error(self, msg) -> None:
        print(f'  [error] {msg}', file=sys.stderr)


def eprint(*args) -> None:
    print(*args, file=sys.stderr)


def ok(msg: str) -> None:
    print(f'  \033[32m✔\033[0m {msg}')


def bad(msg: str) -> None:
    print(f'  \033[31m✘\033[0m {msg}')


def warn(msg: str) -> None:
    print(f'  \033[33m!\033[0m {msg}')


def info(msg: str) -> None:
    print(f'  \033[36m•\033[0m {msg}')


def domain_matches(cookie_domain: str, wanted) -> bool:
    """هل ينتمي نطاق الكوكي إلى أحد النطاقات المطلوبة؟ (foo.youtube.com ⊂ youtube.com)"""
    d = (cookie_domain or '').lstrip('.').lower()
    for w in wanted:
        w = w.lstrip('.').lower()
        if d == w or d.endswith('.' + w):
            return True
    return False


def normalize_expiry(expires):
    """توحيد تاريخ الانتهاء إلى «ثواني منذ 1970».

    Chrome (عبر yt-dlp) يمرّر القيمة كما هي بالميكروثواني منذ 1601، بينما
    Firefox/Safari يعطيان ثواني منذ 1970 مباشرة.
    """
    if expires is None:
        return 0
    expires = float(expires)
    if expires > 1e12:                      # ميكروثواني منذ 1601 (Chrome)
        expires = expires / 1_000_000 - CHROME_EPOCH_OFFSET
    return int(expires)


def sanitize(value: str) -> str:
    """منع كسر صيغة Netscape (المفتاح/القيمة لا يحويان tab أو سطر جديد)."""
    return re.sub(r'[\t\r\n]', ' ', value or '')


def read_netscape(path: str):
    """قراءة ملف Netscape يدوياً (للفحص) — تُرجع قائمة من القواميس."""
    entries = []
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            if not line.strip() or line.startswith('#'):
                continue
            parts = line.rstrip('\n').split('\t')
            if len(parts) != 7:
                continue
            entries.append({
                'domain': parts[0],
                'include_subdomains': parts[1] == 'TRUE',
                'path': parts[2],
                'secure': parts[3] == 'TRUE',
                'expires': int(parts[4]) if parts[4].strip().isdigit() else 0,
                'name': parts[5],
                'value': parts[6],
            })
    return entries


def cookie_header(entries, url: str) -> str:
    """بناء ترويسة Cookie من قائمة الكوكيز (مع احترام النطاق والمسار و secure)."""
    host = re.sub(r'^https?://', '', url).split('/')[0].lower()
    now = time.time()
    pairs = []
    for e in entries:
        d = e['domain'].lstrip('.').lower()
        if host != d and not host.endswith('.' + d):
            continue
        if e['secure'] and not url.lower().startswith('https'):
            continue
        if e['expires'] and e['expires'] <= now:
            continue
        pairs.append(f"{e['name']}={e['value']}")
    return '; '.join(pairs)


# --------------------------------------------------------------------------- #
# الاستخراج
# --------------------------------------------------------------------------- #

def extract(browser: str, profile=None, keyring=None, container=None, verbose=False):
    """استخراج كل كوكيز المتصفح — يرمي استثناء عند الفشل."""
    logger = Logger(verbose)
    return extract_cookies_from_browser(browser, profile, logger, keyring=keyring, container=container)


def probe(domains, keyring=None, verbose=False):
    """فحص كل المتصفحات المدعومة وإرجاع {browser: {...}}."""
    results = {}
    for name in BROWSER_ORDER:
        try:
            jar = extract(name, keyring=keyring, verbose=verbose)
        except Exception as exc:                       # المتصفح غير مثبّت/لا كوكيز
            results[name] = {'ok': False, 'error': str(exc)}
            continue
        matched = [c for c in jar if domain_matches(c.domain, domains)]
        names = {c.name for c in matched}
        results[name] = {
            'ok': True,
            'total': len(jar),
            'matched': len(matched),
            'names': names,
            'authenticated': YT_LOGIN_COOKIE in names
                              and any(s in names for s in YT_SID_COOKIES),
        }
    return results


def choose_browser(results):
    """اختيار أفضل متصفح: مُسجَّل الدخول إن وُجد، وإلا الأغنى كوكيز."""
    usable = {k: v for k, v in results.items() if v.get('ok')}
    if not usable:
        return None
    authed = {k: v for k, v in usable.items() if v.get('authenticated')}
    pool = authed or usable
    return max(pool, key=lambda k: pool[k]['matched'])


# --------------------------------------------------------------------------- #
# الكتابة
# --------------------------------------------------------------------------- #

def write_netscape(cookies, path: str) -> int:
    """كتابة كوكيز المتصفح بصيغة Netscape (المعتمدة من yt-dlp)."""
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# Netscape HTTP Cookie File\n')
        f.write('# This file is generated by cookies_exporter.py. Do not edit.\n')
        f.write(f'# Exported: {time.strftime("%Y-%m-%d %H:%M:%S %Z")}\n')
        f.write(f'# Cookies: {len(cookies)}\n')
        f.write('\n')
        for c in cookies:
            domain = c.domain or ''
            include_sub = 'TRUE' if domain.startswith('.') else 'FALSE'
            fields = (
                domain,
                include_sub,
                c.path or '/',
                'TRUE' if c.secure else 'FALSE',
                str(normalize_expiry(c.expires)),
                sanitize(c.name),
                sanitize(c.value),
            )
            f.write('\t'.join(fields) + '\n')
    return len(cookies)


def write_json(cookies, path: str) -> None:
    """نسخة JSON (للأدوات الأخرى / للنسخ الاحتياطي)."""
    data = [{
        'domain': c.domain,
        'path': c.path,
        'secure': bool(c.secure),
        'expirationDate': normalize_expiry(c.expires) or None,
        'name': c.name,
        'value': c.value,
    } for c in cookies]
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def export_cookies(browser='chrome', output=DEFAULT_OUTPUT, domains=DEFAULT_DOMAINS,
                   profile=None, keyring=None, container=None, all_domains=False,
                   json_out=None, backup=True, verbose=False):
    """API برمجي: استخراج + كتابة ملف الكوكيز.

    تُرجع (عدد الكوكيز، مسار الملف). لا تُدمج أبداً مع ملف موجود مسبقاً.
    """
    jar = extract(browser, profile=profile, keyring=keyring,
                  container=container, verbose=verbose)
    cookies = list(jar) if all_domains else [
        c for c in jar if domain_matches(c.domain, domains)]
    if not cookies:
        raise RuntimeError('لم يُعثر على كوكيز مطابقة للنطاقات المطلوبة')

    out_path = os.path.abspath(os.path.expanduser(output))
    if backup and os.path.exists(out_path):
        shutil.copy2(out_path, out_path + '.bak')
    write_netscape(cookies, out_path)
    if json_out:
        write_json(cookies, os.path.abspath(os.path.expanduser(json_out)))
    return len(cookies), out_path


# --------------------------------------------------------------------------- #
# التحقق
# --------------------------------------------------------------------------- #

def static_verify(path: str, domains) -> bool:
    """فحص ثابت: هل يحتوي الملف على الكوكيز التي يحتاجها yt-dlp؟"""
    print('\n\033[1m[1] الفحص الثابت للملف\033[0m')
    entries = read_netscape(path)
    if not entries:
        bad('الملف فارغ أو بصيغة غير صحيحة (Netcape format متوقع).')
        return False

    names = {e['name'] for e in entries}
    matched = [e for e in entries if domain_matches(e['domain'], domains)]
    ok(f'تم قراءة {len(entries)} كوكي ({len(matched)} ضمن النطاقات المطلوبة: {", ".join(domains)})')

    if YT_LOGIN_COOKIE in names:
        ok(f'كوكي "{YT_LOGIN_COOKIE}" موجود (شرط yt-dlp لاعتبار الجلسة مسجّلة).')
    else:
        bad(f'كوكي "{YT_LOGIN_COOKIE}" مفقود → yt-dlp سيعتبر الجلسة غير مسجّلة '
            f'ويظهر خطأ "Sign in to confirm your age". أعد التصدير من المتصفح.')

    if any(s in names for s in YT_SID_COOKIES):
        ok(f'كوكي SID موجود ({", ".join(s for s in YT_SID_COOKIES if s in names)}).')
    else:
        bad(f'لا يوجد أي من {YT_SID_COOKIES} → لا يمكن حساب SAPISIDHASH (المصادقة).')

    missing = [c for c in YT_EXTRA_COOKIES if c not in names]
    if missing:
        warn(f'كوكيز مساعدة ناقصة (قد تقلّل الجودة/تعطّل بعض العملاء): {", ".join(missing)}')
    else:
        ok('كوكيز VID/metadata كاملة.')

    now = time.time()
    expired = [e for e in entries if e['expires'] and e['expires'] <= now]
    if expired:
        warn(f'{len(expired)} كوكي منتهي الصلاحية (سيُتجاهل تلقائياً).')
    else:
        ok('لا توجد كوكيز منتهية الصلاحية.')

    return YT_LOGIN_COOKIE in names and any(s in names for s in YT_SID_COOKIES)


def live_verify(path: str, url: str) -> bool:
    """تحقق حي: هل ترد يوتيوب/الموقع بأن الجلسة مسجّلة فعلاً؟"""
    print('\n\033[1m[2] التحقق الحي من الجلسة\033[0m')
    entries = read_netscape(path)
    header = cookie_header(entries, url)
    if not header:
        bad('لم يُرسل أي كوكي مع الطلب (تحقق من النطاق).')
        return False
    info(f'إرسال {len(header.split("; "))} كوكي إلى {url}')

    request = urllib.request.Request(url, headers={
        'Cookie': header,
        'User-Agent': USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    })
    try:
        with urllib.request.urlopen(request, timeout=25) as resp:
            body = resp.read().decode('utf-8', 'replace')
    except (urllib.error.URLError, OSError) as exc:
        bad(f'فشل الاتصال: {exc}')
        return False

    if 'youtube.com' in url:
        match = re.search(r'"LOGGED_IN":(\w+)', body)
        if match and match.group(1) == 'true':
            ok('الجلسة حيّة: يوتيوب يرد بـ LOGGED_IN=true.')
            return True
        if match:
            bad('الجلسة غير فعّالة: يوتيوب يرد بـ LOGGED_IN=false '
                '(الكوكيز منتهية/مدوَّرة — أعد التصدير من المتصفح).')
            return False
        warn('لم يُعثر على LOGGED_IN في الرد؛ قد يكون الفيديو مقيّداً أو يتطلّب تسجيل دخول.')

    for marker in ('Sign in', 'Log in', 'تسجيل الدخول', 'sso_account'):
        if marker in body[:200000]:
            bad(f'الصفحة تحتوي "{marker}" → الجلسة غير مسجّلة.')
            return False
    ok('الرد لا يحتوي مؤشرات تسجيل الدخول → الجلسة تبدو صالحة.')
    return True


def yt_dlp_selftest(path: str, url: str) -> bool:
    """اختبار فعلي: تشغيل yt-dlp بالملف المستخرج والتأكد من نجاح الاستخراج."""
    print('\n\033[1m[3] اختبار فعلي عبر yt-dlp\033[0m')
    cmd = [sys.executable, '-m', 'yt_dlp', '--cookies', path, '--simulate',
           '--print', 'format=%(format_id)s resolution=%(resolution)s title=%(title)s', url]
    try:
        import subprocess
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except Exception as exc:
        warn(f'تعذّر تشغيل yt-dlp: {exc}')
        return False
    out = (proc.stdout or '').strip()
    err = (proc.stderr or '').strip()
    if proc.returncode == 0 and out:
        for line in out.splitlines():
            ok(line)
        return True
    bad('فشل yt-dlp باستخدام هذا الملف:')
    for line in err.splitlines()[-6:]:
        print(f'      {line}')
    return False


# --------------------------------------------------------------------------- #
# الواجهة
# --------------------------------------------------------------------------- #

def list_browsers(domains, keyring, verbose) -> int:
    print(f'\n\033[1mفحص المتصفحات المثبّتة (النطاقات: {", ".join(domains)})\033[0m')
    results = probe(domains, keyring=keyring, verbose=verbose)
    print(f'  {"المتصفح":<12}{"الحالة":<10}{"الإجمالي":>10}{"المطابق":>10}  ملاحظات')
    print('  ' + '-' * 66)
    for name in BROWSER_ORDER:
        r = results.get(name, {})
        if not r.get('ok'):
            print(f'  {name:<12}{"غير متاح":<10}{"":>10}{"":>10}  {r.get("error", "")[:38]}')
            continue
        state = 'مسجّل' if r['authenticated'] else 'غير مسجّل'
        note = 'يحتوي كوكيز تسجيل الدخول' if r['authenticated'] else ''
        print(f'  {name:<12}{state:<10}{r["total"]:>10}{r["matched"]:>10}  {note}')
    print()
    return 0


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        prog='cookies_exporter.py',
        description='استخراج كوكيز المتصفح إلى ملف cookies.txt صالح لـ yt-dlp (لينكس/ويندوز/ماك).',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
أمثلة:
  %(prog)s                                 # كشف تلقائي + تصدير + تحقق
  %(prog)s -b chrome -o ~/cookies.txt     # متصفح محدّد
  %(prog)s -b firefox -p default          # ملف تعريف فايرفوكس محدّد
  %(prog)s --verify cookies.txt           # فحص ملف موجود دون تصدير
  %(prog)s --test -u <url>                # تصدير ثم اختبار تنزيل حقيقي
''')
    p.add_argument('-b', '--browser', default='auto',
                   choices=BROWSER_ORDER + ['auto'],
                   help='المتصفح المصدر (default: auto = كشف تلقائي)')
    p.add_argument('-p', '--profile', default=None,
                   help='اسم ملف التعريف أو مساره (مثال: Default، أو /path/to/profile)')
    p.add_argument('--keyring', default=None, choices=['kwallet', 'basic', 'gnome'],
                   help='خزنة المفاتيح في لينكس (Chrome/Chromium فقط)')
    p.add_argument('--container', default=None,
                   help='حاوية فايرفوكس (container id / "none")')
    p.add_argument('-d', '--domain', action='append', default=None,
                   help=f'نطاق مطلوب (يمكن تكراره). الافتراضي: {", ".join(DEFAULT_DOMAINS)}')
    p.add_argument('-o', '--output', default=DEFAULT_OUTPUT,
                   help=f'مسار ملف الإخراج (default: {DEFAULT_OUTPUT})')
    p.add_argument('--all-domains', action='store_true',
                   help='تصدير كل النطاقات (بدون فلترة)')
    p.add_argument('--json', dest='json_out', default=None,
                   help='مسار نسخة JSON إضافية')
    p.add_argument('--no-backup', action='store_true',
                   help='عدم حفظ نسخة احتياطية من الملف السابق')
    p.add_argument('--no-verify', action='store_true', help='تخطّي التحقق')
    p.add_argument('--no-live', action='store_true', help='تخطّي التحقق الحي (يتطلّب اتصالاً)')
    p.add_argument('--verify', metavar='FILE', default=None,
                   help='فحص ملف موجود فقط ثم الخروج')
    p.add_argument('--test', action='store_true',
                   help='بعد التصدير: تشغيل yt-dlp لاختبار فعلي')
    p.add_argument('-u', '--url', default='https://youtu.be/IOitbk4qqlk',
                   help='الرابط المستخدم في الاختبار الفعلي')
    p.add_argument('--list', action='store_true', help='عرض المتصفحات المتاحة ثم الخروج')
    p.add_argument('-v', '--verbose', action='store_true', help='تفاصيل إضافية')
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    domains = tuple(args.domain) if args.domain else DEFAULT_DOMAINS

    if args.list:
        return list_browsers(domains, args.keyring, args.verbose)

    # ------------------------------------------------------------------ #
    # وضع الفحص فقط
    # ------------------------------------------------------------------ #
    if args.verify:
        path = args.verify
        print(f'\n\033[1mفحص الملف: {path}\033[0m')
        if not os.path.isfile(path):
            bad('الملف غير موجود.')
            return 1
        static_ok = static_verify(path, domains)
        live_ok = live_verify(path, 'https://www.youtube.com/') if not args.no_live else None
        print()
        if static_ok and (live_ok is not False):
            ok('الملف صالح للاستخدام مع yt-dlp.')
            return 0
        bad('الملف غير صالح — أعد تصديره من المتصفح (cookies_exporter.py).')
        return 1

    # ------------------------------------------------------------------ #
    # اختيار المتصفح
    # ------------------------------------------------------------------ #
    print(f'\n\033[1m[1] اختيار المتصفح\033[0m (النطاقات: {", ".join(domains)})')
    if args.browser == 'auto':
        results = probe(domains, keyring=args.keyring, verbose=args.verbose)
        browser = choose_browser(results)
        for name in BROWSER_ORDER:
            r = results.get(name, {})
            if r.get('ok'):
                state = 'مسجّل الدخول ✔' if r['authenticated'] else 'غير مسجّل'
                info(f'{name}: {r["total"]} كوكي ({r["matched"]} مطابق) — {state}')
            else:
                print(f'  \033[90m• {name}: غير متاح ({r.get("error", "")[:60]})\033[0m')
        if not browser:
            bad('لم يُعثر على أي متصفح يحتوي كوكيز. تأكد من تثبيت المتصفح وتسجيل الدخول فيه.')
            return 1
        ok(f'المتصفح المختار: {browser}')
    else:
        browser = args.browser
        info(f'المتصفح: {browser}')

    # ------------------------------------------------------------------ #
    # الاستخراج
    # ------------------------------------------------------------------ #
    print(f'\n\033[1m[2] استخراج الكوكيز\033[0m')
    try:
        jar = extract(browser, profile=args.profile, keyring=args.keyring,
                      container=args.container, verbose=args.verbose)
    except Exception as exc:
        bad(f'فشل الاستخراج من {browser}: {exc}')
        return 1

    if args.all_domains:
        cookies = list(jar)
    else:
        cookies = [c for c in jar if domain_matches(c.domain, domains)]
    ok(f'تم استخراج {len(cookies)} كوكي من {browser}')

    if not cookies:
        bad(f'لا توجد كوكيز مطابقة للنطاقات {", ".join(domains)} — '
            f'جرّب نطاقاً آخر (-d) أو --all-domains.')
        return 1

    names = {c.name for c in cookies}
    if YT_LOGIN_COOKIE not in names:
        warn(f'كوكي "{YT_LOGIN_COOKIE}" غير موجود — قد تكون الجلسة غير مسجّلة '
             'أو أن هذا المتصفح لا يحتوي حساب يوتيوب مفتوحاً.')

    # ------------------------------------------------------------------ #
    # الكتابة
    # ------------------------------------------------------------------ #
    print(f'\n\033[1m[3] الكتابة\033[0m')
    out_path = os.path.abspath(os.path.expanduser(args.output))
    if os.path.exists(out_path) and not args.no_backup:
        backup = out_path + '.bak'
        shutil.copy2(out_path, backup)
        ok(f'نسخة احتياطية: {backup}')
    write_netscape(cookies, out_path)
    ok(f'تم الكتابة: {out_path}')
    if args.json_out:
        write_json(cookies, os.path.abspath(os.path.expanduser(args.json_out)))
        ok(f'تم الكتابة (JSON): {args.json_out}')

    # ------------------------------------------------------------------ #
    # التحقق
    # ------------------------------------------------------------------ #
    result = 0
    if not args.no_verify:
        static_ok = static_verify(out_path, domains)
        live_ok = True
        if not args.no_live:
            live_ok = live_verify(out_path, 'https://www.youtube.com/')
        if args.test:
            test_ok = yt_dlp_selftest(out_path, args.url)
            live_ok = live_ok and test_ok
        result = 0 if (static_ok and live_ok) else 1
    else:
        live_ok = True

    print()
    if result == 0:
        ok('جاهز للاستخدام:')
        print(f'      yt-dlp --cookies {args.output} -f "bv*+ba/b" {args.url}')
        print('      ملاحظة: يوتيوب يُبطل/يُدوّر الكوكيز بعد كل استخدام —')
        print('              أعد التصدير قبل كل تنزيل، أو استخدم --cookies-from-browser chrome')
    else:
        bad('الملف لا يمرّ بالتحقق الكامل — راجع الرسائل أعلاه.')
    return result


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        eprint('\nتم الإيقاف.')
        sys.exit(130)
