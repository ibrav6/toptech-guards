#!/usr/bin/env python3
"""حارس الأسرار — يمنع كتابة سرٍّ في ملف قبل أن يصل git.

‼ لماذا قبل الكتابة لا قبل الالتزام: سرٌّ يدخل ملفاً يدخل غالباً git،
  وسرٌّ يدخل git **لا يخرج من التاريخ** إلا بإعادة كتابته. فالمنع عند
  أوّل لحظةٍ ممكنة.

الثمن مقيس 2026-08-31: `rand-erp/odoo.conf` جُلب من الـNAS وفيه
`db_password` و`admin_passwd` نصّاً صريحاً — لأن ملف `.conf` لا يقرأ
متغيّرات البيئة فتُكتب الكلمة حرفياً.

⚠ ولا يفحص القيم النائبة: `<…>` و`${…}` و`example`/`xxx` مستثناة عمداً،
  وإلا صار الحارس يمنع القوالب نفسها فيُطفأ.
"""
import json
import re
import sys

PATTERNS = [
    (re.compile(r"(admin_passwd|db_password|POSTGRES_PASSWORD|SMTP_PASSWORD|"
                r"API_KEY|SECRET_KEY|ACCESS_TOKEN)\s*[=:]\s*\S{8,}", re.I),
     "كلمة مرور أو مفتاح نصّاً صريحاً"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
     "مفتاح خاص"),
    (re.compile(r"^[a-z]{4} [a-z]{4} [a-z]{4} [a-z]{4}$", re.M),
     "كلمة تطبيق جيميل (أربع رباعيات)"),
    (re.compile(r'"AccountTag"\s*:|"TunnelSecret"\s*:'),
     "بيانات نفق كلاودفلير"),
]
# قيمٌ نائبة لا تُعدّ سرّاً
PLACEHOLDER = re.compile(r"<[^>]{2,}>|\$\{[^}]+\}|\bexample\b|\bxxx+\b|\bREDACTED\b|\bchangeme\b", re.I)


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return
    ti = data.get("tool_input") or {}
    # Write يحمل content · Edit يحمل new_string
    text = ti.get("content") or ti.get("new_string") or ""
    path = ti.get("file_path") or ""
    if not text:
        return

    for line_no, line in enumerate(text.splitlines(), 1):
        if PLACEHOLDER.search(line):
            continue
        for rx, what in PATTERNS:
            if rx.search(line):
                json.dump({"hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        f"⛔ {what} في {path or 'الملف'} سطر {line_no}.\n"
                        "استبدله بقيمةٍ نائبة تشير إلى موضع السرّ الحقيقي، مثل:\n"
                        "   admin_passwd = <في secrets/odoo_admin_passwd.txt>\n"
                        "سرٌّ يدخل git لا يخرج من التاريخ إلا بإعادة كتابته."),
                }}, sys.stdout, ensure_ascii=False)
                return


if __name__ == "__main__":
    main()
