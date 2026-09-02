#!/usr/bin/env python3
"""بدء الجلسة — يحقن الدستور وسطرَ الحالة، بلا شبكة وفي أقلّ من ثانية.

‼ لماذا الحقن لا النسخ: `CLAUDE.md` في كل مشروعٍ كان يعيد كتابة القواعد
  بصياغته (قِيس 2026-09-02: 1106 · 428 · 213 سطراً في ثلاثة مستودعات)،
  فتبلى نسخةٌ ولا تبلى الأخرى. الدستور نصٌّ واحد في الـplugin يصل كل
  جلسةٍ كما هو، وتحديثه في مكانٍ واحد يبلغ الجميع في الجلسة التالية.

‼ ولماذا سطرُ الحالة: «هل كل شي برودكشن؟» تكرّر 33 مرّةً في 18 جلسة
  (قياس 2026-08-20)، و97 ملفاً بقيت معلّقةً يومين عبر سبع جلسات لأن لا
  أحد رآها. فالفرع والمعلّق وعمرُه تُقال قبل أن تُسأل.

المخرَج JSON بـ`additionalContext` — يُضاف إلى سياق الوكيل ولا يُعرض
للمستخدم إلا حين يُطبع. وأي فشلٍ داخلي يُكتم: حارسٌ يُسقط الجلسة أسوأ
من غيابه.
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.dirname(HERE)


def _git(cwd: str, *args: str) -> str:
    try:
        p = subprocess.run(["git", "-C", cwd, *args], capture_output=True,
                           text=True, timeout=5)
        return p.stdout.strip() if p.returncode == 0 else ""
    except Exception:
        return ""


def status_line(cwd: str) -> str:
    branch = _git(cwd, "rev-parse", "--abbrev-ref", "HEAD")
    if not branch:
        return "▸ ليس مستودع git."
    lines = []
    if branch in ("master", "main"):
        lines.append(f"‼ أنت على `{branch}`: افتح فرعاً لمهمّتك "
                     "(`git switch -c <اسمك>/<المهمة>`) — الدفع إلى "
                     f"`{branch}` مرفوضٌ بالحارس.")
    else:
        lines.append(f"▸ الفرع: `{branch}`")

    porcelain = _git(cwd, "status", "--porcelain")
    dirty = [ln[3:] for ln in porcelain.splitlines() if ln.strip()]
    if dirty:
        now = time.time()
        ages = []
        for rel in dirty:
            path = os.path.join(cwd, rel.split(" -> ")[-1])
            try:
                ages.append((now - os.path.getmtime(path)) / 60)
            except OSError:
                pass
        oldest = int(max(ages)) if ages else 0
        mark = "‼" if oldest >= 60 else "▸"
        lines.append(f"{mark} معلّق: {len(dirty)} ملفاً، أقدمها منذ "
                     f"{oldest} دقيقة — التزِمْ انتقائياً قبل أن تنتهي.")
    else:
        lines.append("▸ الشجرة نظيفة.")

    base = "origin/master" if _git(cwd, "rev-parse", "--verify", "-q",
                                   "origin/master") else "origin/main"
    counts = _git(cwd, "rev-list", "--left-right", "--count",
                  f"{base}...HEAD")
    if counts:
        behind, ahead = counts.split()
        if behind != "0" or ahead != "0":
            lines.append(f"▸ مقابل `{base}`: متقدّمٌ بـ{ahead} · متأخّرٌ "
                         f"بـ{behind}" + (" — اسحب قبل أن تبني." if behind != "0" else ""))

    tag = _git(cwd, "rev-parse", "--short", "refs/tags/production")
    if tag:
        head = _git(cwd, "rev-parse", "--short", base)
        lines.append(f"▸ الإنتاج (وسم `production` كما عُرف آخر مرّة): "
                     f"{tag}" + ("" if tag == head else f" · `{base}` عند {head}"))
    return "\n".join(lines)


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}
    cwd = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    try:
        with open(os.path.join(PLUGIN, "CONSTITUTION.md"), encoding="utf-8") as fh:
            constitution = fh.read().strip()
    except OSError:
        constitution = ""
    try:
        with open(os.path.join(PLUGIN, ".claude-plugin", "plugin.json"),
                  encoding="utf-8") as fh:
            version = json.load(fh).get("version", "?")
    except Exception:
        version = "?"
    try:
        state = status_line(cwd)
    except Exception:
        state = ""
    protect = os.environ.get("TOPTECH_PROTECT_MASTER", "1") != "0"
    head = (f"[toptech-guards {version} · حماية master "
            f"{'مشعَلة' if protect else '‼ مطفأة'}]")
    json.dump({"hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": "\n\n".join(x for x in (constitution, head + "\n" + state) if x),
    }}, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
