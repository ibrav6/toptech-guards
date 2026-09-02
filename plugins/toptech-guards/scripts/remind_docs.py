#!/usr/bin/env python3
"""يحقن الوثيقة الحاكمة في سياق الوكيل **لحظة** لمسه مساراً محروساً.

‼ لا يمنع — يذكّر. لأن القاعدة «اقرأ الوثيقة قبل الكود» لا يمكن فحصها
  آلياً (لا سبيل لإثبات أن أحداً قرأ)، لكن **الحقن** يجعل النسيان
  مستحيلاً: الوثيقة تصل الوكيل سواء تذكّر أم لا.

الثمن مقيس 2026-08-15: عُدّلت خمسة مواضع في السحب من اعتماد **قبل فتح
المرجع**، فهبط عمر جلسة الزحف إلى ساعة بعد أن كان 9–17 ساعة موثّقة —
والسبب مكتوبٌ في المرجع منذ 2026-08-01 بعنوانٍ صريح. وضاعت ساعاتٌ في
تشخيصٍ كان جوابه مكتوباً.

الخريطة **لكل مستودع** في `.claude/guarded-paths.json`:

    { "ingestion/": "docs/ETIMAD_PULL.md — §٤ الجلسة · §٥ حقائق اعتماد",
      "api/app/pricing.py": "docs/PRICING.md" }

بلا الملف لا يفعل شيئاً — فالـplugin واحدٌ والخرائط تختلف.
"""
import json
import os
import sys

MAP_FILE = ".claude/guarded-paths.json"


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return
    ti = data.get("tool_input") or {}
    path = ti.get("file_path") or ""
    if not path:
        return

    root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or "."
    try:
        with open(os.path.join(root, MAP_FILE), encoding="utf-8") as fh:
            guarded = json.load(fh)
    except Exception:
        return                      # لا خريطة لهذا المستودع ⇒ صمت

    rel = os.path.relpath(path, root) if os.path.isabs(path) else path
    hits = [doc for prefix, doc in guarded.items() if rel.startswith(prefix)]
    if not hits:
        return

    json.dump({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "additionalContext": (
            f"⚠ `{rel}` مسارٌ محروس. الوثيقة الحاكمة: "
            + " · ".join(hits)
            + "\nاقرأها **قبل** التعديل لا بعده — قِيس 2026-08-15 أن خمسة "
              "تعديلاتٍ سبقت المرجع أسقطت عمر الجلسة من 9–17 ساعة إلى ساعة، "
              "والجواب كان مكتوباً في المرجع منذ أسبوعين."),
    }}, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
