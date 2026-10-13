#!/usr/bin/env python3
"""حارس الشجرة المشتركة — لا تعديلَ لملفٍ متتبَّعٍ والفرعُ `master`.

‼ الحادثة (قِيس 2026-10-13 في tenders-platform): ثمانية ملفات بقيت
  معلّقةً في الشجرة المشتركة **44 يوماً** — سكربتا لقطة التطوير، حملة
  تسويقٍ كاملة، و87 م.ب مصفوفات متّجهات. وسطرُ الحالة عند بدء كل جلسة
  كان يقولها («معلّق: 8 ملفاً، أقدمها منذ 63366 دقيقة») ولم يتحرّك أحد،
  لأن حارس الدفع يمنع **الدفع** إلى master لا **الكتابة** فيه: تكتب
  الجلسة، فلا تستطيع الالتزام، فتخرج وتترك ما كتبت.
  ⇒ المنع عند أوّل لحظةٍ ممكنة، كحارس الأسرار: قبل الكتابة لا قبل الدفع.

ثلاث نقاط دخول (`hook_event_name`):
  PreToolUse  Write|Edit — يُمنع الملف إن كان مستودعه على master/main
                           ولم يكن متجاهَلاً في git.
  PreToolUse  Bash       — لقطةٌ لـ`git status` في مستودع الجلسة إن كان
                           على master (أوامر الصدفة لا تُقرأ نيّتُها: `sed -i`
                           و heredoc و python يكتب — فالحكم على الأثر).
  PostToolUse Bash       — ما اتّسخ **بعد** اللقطة وزمنُه بعدها يُعاد إلى
                           الوكيل بسببٍ يقرؤه ليصحّح.

‼ **المتجاهَل يمرّ**: `.env.local` والمسودّات ومخرجات البناء ليست عملاً
  يضيع، ومنعُها يُطفئ الحارس في يومه.
‼ **واللقطة هي النسبة في Bash**: جلساتٌ متوازية تكتب في الشجرة نفسها،
  فملفٌ اتّسخ بيدِ غيري قبل أمري في اللقطة ولا يُنسب إليّ ما لم يتغيّر
  زمنُه. (جُرّب شرطُ زمنٍ ثانٍ فنجا من فحص الطفرة: اللقطة تكفيه.)

للإطفاء في حالةٍ مقصودة: `TOPTECH_PROTECT_MASTER=0` (المفتاح نفسه لحارس الدفع).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

PROTECTED = ("master", "main")
SNAP_DIR = os.path.join(tempfile.gettempdir(), "toptech-guards-tree")
FIX = ("افتح worktree لمهمّتك واعمل فيه:\n"
       "   git -C {top} worktree add -b <اسمك>/<مهمتك> ../<مجلد> origin/master\n"
       "الشجرة المشتركة على master للقراءة. ثمنه: 8 ملفات بقيت 44 يوماً "
       "معلّقةً فيها بلا التزام (قِيس 2026-10-13).")


def _git(cwd: str, *args: str) -> str | None:
    try:
        p = subprocess.run(["git", "-C", cwd, *args], capture_output=True,
                           text=True, timeout=8)
    except Exception:
        return None
    return p.stdout.strip() if p.returncode == 0 else None


def _repo(path: str) -> tuple[str, str] | None:
    """(جذر المستودع، الفرع) لأقرب مجلّدٍ موجود — أو None خارج git."""
    d = path if os.path.isdir(path) else os.path.dirname(path)
    while d and not os.path.isdir(d):
        d = os.path.dirname(d)
    if not d:
        return None
    top = _git(d, "rev-parse", "--show-toplevel")
    branch = _git(d, "rev-parse", "--abbrev-ref", "HEAD")
    return (top, branch) if top and branch else None


def _dirty(top: str) -> dict[str, float]:
    """الملفات المتّسخة ← زمن تعديلها (‑1 للمحذوف). `-uall` كي لا يختبئ
    ملفٌ جديد داخل مجلّدٍ غير متتبَّع أصلاً."""
    out = subprocess.run(["git", "-C", top, "status", "--porcelain=v1", "-z", "-uall"],
                         capture_output=True, text=True, timeout=8).stdout
    res: dict[str, float] = {}
    items = out.split("\0")
    i = 0
    while i < len(items):
        e = items[i]
        i += 1
        if len(e) < 4:
            continue
        if e[0] in "RC":            # إعادة تسمية: الاسم القديم في العنصر التالي
            i += 1
        rel = e[3:]
        try:
            res[rel] = os.path.getmtime(os.path.join(top, rel))
        except OSError:
            res[rel] = -1.0
    return res


def _snap_path(data: dict) -> str:
    key = f"{data.get('session_id', 'x')}-{data.get('tool_use_id', 'x')}"
    return os.path.join(SNAP_DIR, "".join(c for c in key if c.isalnum() or c in "-_"))


def on_write(data: dict) -> None:
    path = (data.get("tool_input") or {}).get("file_path") or ""
    if not path:
        return
    path = os.path.abspath(os.path.join(data.get("cwd") or ".", os.path.expanduser(path)))
    r = _repo(path)
    if not r or r[1] not in PROTECTED:
        return
    top, branch = r
    if not os.path.realpath(path).startswith(os.path.realpath(top) + os.sep):
        return
    if _git(top, "check-ignore", "-q", path) is not None:   # متجاهَل ⇒ ليس عملاً يضيع
        return
    json.dump({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": (
            f"⛔ تعديل {os.path.relpath(path, top)} والفرع `{branch}` في {top}.\n"
            + FIX.format(top=top)),
    }}, sys.stdout, ensure_ascii=False)


def on_bash_pre(data: dict) -> None:
    r = _repo(data.get("cwd") or ".")
    if not r or r[1] not in PROTECTED:
        return
    os.makedirs(SNAP_DIR, exist_ok=True)
    with open(_snap_path(data), "w", encoding="utf-8") as fh:
        json.dump({"top": r[0], "before": _dirty(r[0])}, fh)


def on_bash_post(data: dict) -> None:
    p = _snap_path(data)
    try:
        with open(p, encoding="utf-8") as fh:
            snap = json.load(fh)
        os.remove(p)
    except Exception:
        return
    top, before = snap["top"], snap["before"]
    if (_git(top, "rev-parse", "--abbrev-ref", "HEAD") or "") not in PROTECTED:
        return                                    # الأمر نفسه فتح فرعاً — هذا هو المطلوب
    fresh = sorted(rel for rel, m in _dirty(top).items()
                   if rel not in before or m != before[rel])
    if not fresh:
        return
    shown = "\n".join(f"   {f}" for f in fresh[:10]) + (f"\n   … و{len(fresh) - 10} غيرها" if len(fresh) > 10 else "")
    json.dump({"decision": "block", "reason": (
        f"⛔ هذا الأمر عدّل {len(fresh)} ملفاً في {top} والفرع master:\n{shown}\n"
        "انقلها إلى worktree والتزم بها هناك، ثم أعِد هذه الملفات وحدها في "
        "الشجرة المشتركة كما كانت (لا `git stash` ولا `checkout .` — جلساتٌ "
        "أخرى تعمل فيها).\n" + FIX.format(top=top))}, sys.stdout, ensure_ascii=False)


def main() -> None:
    if os.environ.get("TOPTECH_PROTECT_MASTER", "1") == "0":
        return
    try:
        data = json.load(sys.stdin)
    except Exception:
        return
    ev, tool = data.get("hook_event_name"), data.get("tool_name")
    try:
        if tool in ("Write", "Edit") and ev == "PreToolUse":
            on_write(data)
        elif tool == "Bash" and ev == "PreToolUse":
            on_bash_pre(data)
        elif tool == "Bash" and ev == "PostToolUse":
            on_bash_post(data)
    except Exception:                 # noqa: BLE001 — حارسٌ ينهار لا يمنع العمل
        return


if __name__ == "__main__":
    main()
