#!/usr/bin/env python3
"""حارس أوامر الصدفة — يمنع ما وقع فعلاً، لا ما يُخشى نظرياً.

كل قاعدة هنا لها عطبٌ مقيسٌ بتاريخه في `docs/` بمستودع toptech.dev.
ولا تُضاف قاعدة بلا حادثة — الحارس الذي يمنع ما لم يقع يُطفأ بعد أسبوع.

المدخل: JSON على stdin فيه tool_name و tool_input.command
المخرَج: عند المنع، JSON بـpermissionDecision=deny وخروج 0.
         الخروج 0 بلا مخرَج = لا رأي، يمضي المسار الطبيعي.

‼ ولا يُستعمل الخروج 2 هنا: مخرَج JSON يحمل **سبباً** يقرؤه الوكيل
  فيصحّح مساره، بينما رمز الخروج يقول «لا» بلا تعليم.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys

# ── إعداد المشروع: `.claude/toptech-guards.json` في جذر المستودع ──────
# ‼ الـplugin عامٌّ وواحدٌ لكل المشاريع (2026-09-02)، وخصوصيّة كل مشروع
#   (مسارات إنتاجه · أداة نشره · مالكه · هل تُشترط الموافقة) في ملفه هو.
#   بلا الملف: لا مسارَ إنتاجٍ محروس، وباقي الحرّاس (الحذف · القاعدة ·
#   master · الوسم · الأسرار) تعمل كما هي.
#
#   { "production_paths": ["/srv/app", "/srv/erp"],
#     "deploy_tools": ["deploy.py"],
#     "owner": "github-login",
#     "require_approval": false }
CONFIG_FILE = ".claude/toptech-guards.json"
_CFG: dict = {}


def load_config(cwd: str | None) -> dict:
    root = os.environ.get("CLAUDE_PROJECT_DIR") or cwd or "."
    try:
        with open(os.path.join(root, CONFIG_FILE), encoding="utf-8") as fh:
            cfg = json.load(fh)
    except Exception:
        cfg = {}
    _CFG.clear()
    _CFG.update({
        "production_paths": tuple(cfg.get("production_paths") or ()),
        "deploy_tools": tuple(cfg.get("deploy_tools") or ("deploy.py",)),
        "owner": cfg.get("owner") or os.environ.get("TOPTECH_OWNER", ""),
        "require_approval": bool(cfg.get("require_approval", False)),
    })
    return _CFG

# ‼ أدواتٌ **وجهتُها الوسيطُ الأخير** — فالقراءة منها تمرّ والكتابة تُمنع
DEST_LAST = ("scp", "rsync", "sftp", "cp", "mv", "install")
# ‼ وأدواتٌ **تعدّل كلَّ ما تسمّيه** — فأيُّ وسيطٍ إنتاجي كتابة
ARGS_ARE_TARGETS = ("rm", "chmod", "chown", "truncate", "tee", "dd", "sed")


def _strip_messages(cmd: str) -> str:
    """ينزع نصوص رسائل الالتزام قبل الفحص — **نصٌّ لا يُنفَّذ**.

    ‼ قِيس 2026-09-01 (ثالث كاذبة في ساعة): رسالةُ التزامٍ تصف الحارس
      نفسه حوت «scp» ومسارَ الإنتاج فمنعت نفسها. ورسائل هذا الفريق عربية
      تصف الإنتاج، فالاصطدام يومي — وحارسٌ يصطدم يومياً يُطفأ.

    ⇒ يُنزع ما بعد `-m` و`--message` وحدهما. وهو آمن: رسالة الالتزام لا
      تصل صدفةً أبداً. ولا يُنزع سواها — فـ`ssh nas "cp … /srv/prod/…"`
      مقتبسٌ أيضاً **ويُنفَّذ**، ويبقى محروساً.
    """
    return re.sub(r"(?:-m|--message)[=\s]+('(?:[^']|'\\'')*'|\"(?:[^\"\\]|\\.)*\")",
                  " ", cmd)


def _is_prod(token: str) -> bool:
    return any(p in token for p in _CFG.get("production_paths", ()))


def _prod_write_target(cmd: str):
    """يعيد أوّل مسار إنتاجٍ **يُكتب عليه**، أو `None`.

    ‼ الفرق بين هذا وبين «ورد مسارُ إنتاجٍ في الأمر» هو الفرق بين حارسٍ
      يُستعمل وحارسٍ يُطفأ. قِيست أربعُ إيجابياتٍ كاذبة في ساعةٍ واحدة
      2026-09-01، وكلُّها قراءةٌ من الإنتاج أو ذكرٌ له:
        · `scp قائمة nas:/tmp/…` ومسارُ الإنتاج في شطرٍ آخر
        · `scp nas:/srv/prod/… .`           ← سحبٌ منه
        · `cp /srv/prod/ledger /srv/backups/`   ← نسخةٌ احتياطية
        · رسالةُ التزامٍ تصفه

    ⇒ فالاتّجاه يُقرأ من دلالة الأداة نفسها، لا من ورود النصّ.
    """
    for part in re.split(r"[;&|]{1,2}|\n", cmd):
        toks = part.split()
        if not toks:
            continue

        # إعادة توجيه: الهدف ما بعد `>` أو `>>`
        for m in re.finditer(r">>?\s*([^\s;&|]+)", part):
            if _is_prod(m.group(1)):
                return m.group(1)

        args = [a for a in toks if not a.startswith("-")]
        if any(re.search(rf"\b{t}\b", part) for t in DEST_LAST):
            if len(args) >= 2 and _is_prod(args[-1]):
                return args[-1]

        if any(re.search(rf"\b{t}\b", part) for t in ARGS_ARE_TARGETS):
            for a in args:
                if _is_prod(a):
                    return a
    return None


def deny(reason: str) -> None:
    json.dump({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}, sys.stdout, ensure_ascii=False)
    sys.exit(0)


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return                      # مدخلٌ غير مفهوم ⇒ لا رأي، لا تعطيل
    cmd = (data.get("tool_input") or {}).get("command") or ""
    if not cmd:
        return
    cmd = _strip_messages(cmd)      # الرسائل نصٌّ لا يُنفَّذ — انظر أعلاه
    load_config(data.get("cwd"))

    # ‼ ١) دهس الإنتاج — قِيس 2026-08-20: طُبع «مُنِع النقل» ثم نُفِّذ
    #     النقل في السطر التالي ودُهست نسخة الإنتاج. الحارس نطق ولم يمنع.
    #
    # ‼ ولا يكفي «ورد مسارُ إنتاجٍ في الأمر»: قِيس 2026-09-01 أن أمراً
    #   يرسل قائمة أسماءٍ **للقراءة** إلى /tmp مُنع لأن `cd <مسار الإنتاج>`
    #   ورد في شطرٍ آخر منه. والإيجابيةُ الكاذبة تُطفئ الحارس — فيصير
    #   غيابه أسوأ من عدمه. ⇒ يُفحص **هدفُ الكتابة** لا ورودُ المسار.
    if not any(t in cmd for t in _CFG["deploy_tools"]):
        target = _prod_write_target(cmd)
        if target:
            deny(f"⛔ كتابةٌ مباشرة على مسار إنتاج: `{target}`\n"
                 "   الإنتاج يصله ما دُمج ورُقّي آلياً، أو أداة النشر المسمّاة في "
                 "`.claude/toptech-guards.json` للطوارئ.\n"
                 "قِيس 2026-08-20: نقلٌ يدوي دهس نسخة الإنتاج بعد أن طُبع "
                 "«مُنِع النقل» — الحارس نطق ولم يمنع، فصار المنع آلياً.")

    # ‼ ٢) حذفٌ مدمّر خارج المساحة المؤقّتة
    if re.search(r"\brm\s+(-[a-zA-Z]*[rR][a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*[rR])", cmd):
        safe = ("scratchpad" in cmd or "/private/tmp/claude-" in cmd
                or "node_modules" in cmd or ".next" in cmd or "__pycache__" in cmd)
        if not safe:
            deny("⛔ `rm -rf` خارج المساحة المؤقّتة. احذف بمسارٍ صريح، أو "
                 "انقل إلى scratchpad أوّلاً. الحذف لا يُستعاد.")

    # ‼ ٣) كتابةٌ على قاعدة الإنتاج بلا شرط — قِيس 2026-08-25: فحصٌ كُتب
    #     ليُثبت أن production_query ترفض الكتابة كان يستدعيها كاملةً
    #     بجملة `DELETE FROM tender`، فمُسح المستودع واستُعيد من نسخة 05:00.
    if re.search(r"\b(psql|docker exec\s+\S*db)\b", cmd, re.I):
        if re.search(r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b", cmd, re.I):
            deny("⛔ `DROP` على قاعدة حيّة. إن كان مقصوداً فنفّذه بيدك خارج "
                 "الوكيل، بعد نسخةٍ محقَّقة.")
        if re.search(r"\b(DELETE\s+FROM|UPDATE)\b", cmd, re.I) and not re.search(r"\bWHERE\b", cmd, re.I):
            deny("⛔ `DELETE`/`UPDATE` بلا `WHERE` على قاعدة حيّة.\n"
                 "قِيس 2026-08-25: جملةٌ كهذه مسحت المستودع كلَّه — "
                 "والفحص الذي كُتب ليمنعها هو الذي نفّذها.")

    # ‼ ٤) دفعٌ قسري إلى الفرع المشترك
    if re.search(r"git\s+push\b", cmd) and re.search(r"(--force(?!-with-lease)|(?<![\w-])-f(?![\w-]))", cmd):
        if re.search(r"\b(master|main)\b", cmd) or "origin" in cmd:
            deny("⛔ `git push --force` على فرعٍ مشترك يمحو عمل غيرك.\n"
                 "استعمل `--force-with-lease` — يرفض الدفع إن تقدّم البعيد.")

    # ‼ ٥) الفرع المشترك — **مشعَلٌ افتراضياً منذ 2026-09-02** (مسار PR
    #     صار هو المسار). يُطفأ بـTOPTECH_PROTECT_MASTER=0 لا يُشعَل بـ1.
    #     قِيس 2026-08-2x: 97 ملفاً معلّقاً يومين عبر سبع جلسات على شجرةٍ
    #     واحدة، والبوابة خضراء عليها طوال الوقت. وقِيس 2026-08-30 ثلاثة
    #     التزاماتٍ حمراء دخلت master وأحدها منشور.
    if os.environ.get("TOPTECH_PROTECT_MASTER", "1") != "0":
        if re.search(r"git\s+push\b", cmd):
            explicit = re.search(r"\b(master|main)\b", cmd)
            # `git push` بلا فرعٍ مسمّى يدفع الفرع الحالي — فيُسأل git.
            implicit = (not re.search(r"\brefs/|\borigin\s+\S+", cmd)
                        and _current_branch(data.get("cwd")) in ("master", "main"))
            if explicit or implicit:
                deny("⛔ الدفع المباشر إلى master مرفوض. افتح فرعاً وPR:\n"
                     "   git switch -c <اسمك>/<مهمتك> && git push -u origin HEAD\n"
                     "قِيس 2026-08-30: ثلاثة التزاماتٍ حمراء دخلت master "
                     "وأحدها منشور، ولا أحد يعلم.")

    # ‼ ٦) وسم `production` لا يحرّكه إلا workflow الترقية — تحريكه بيدٍ
    #     يجعل الإنتاج يسحب ما لم يمرّ بالمسار (هذا الوسم هو الذي يقرؤه
    #     وكيل النشر على الخادم كل دقيقة).
    if re.search(r"git\s+(push|tag)\b", cmd) and re.search(
            r"(?<![\w/-])(refs/tags/)?production(?![\w-])", cmd):
        deny("⛔ وسم `production` يحرّكه workflow الترقية وحده (بعد PR + "
             "Approve + CI). للرجوع: workflow `rollback` من GitHub بسبب.")

    # ‼ ٧) الدمج بلا فحوصٍ خضراء أو بلا موافقة — يُسأل GitHub لا الناشر.
    #     والعجزُ رفض: بلا `gh` لا يُدمج، كما لا يُنشر بلا حكم CI.
    if re.search(r"\bgh\s+pr\s+merge\b", cmd):
        why = _merge_refusal(cmd, data.get("cwd"))
        if why:
            deny(why)

    # ‼ ٨) سرٌّ يُكتب عبر الصدفة — `cat > f <<EOF` يتجاوز حارس Write.
    #     وجلسات bypass مأمورةٌ بالكتابة عبر Bash تحديداً (قِيس 2026-09-02).
    if re.search(r">>?|<<|\btee\b", cmd):
        hit = _secret_in(cmd)
        if hit:
            deny(f"⛔ {hit} داخل أمر كتابة. سرٌّ يدخل ملفاً يدخل git، "
                 "وسرٌّ يدخل git لا يخرج من التاريخ.\n"
                 "استبدله بقيمةٍ نائبة: <في secrets/…> أو ${VAR}.")


def _current_branch(cwd: str | None) -> str:
    try:
        p = subprocess.run(["git", "-C", cwd or ".", "rev-parse",
                            "--abbrev-ref", "HEAD"],
                           capture_output=True, text=True, timeout=5)
        return p.stdout.strip() if p.returncode == 0 else ""
    except Exception:
        return ""


def _merge_refusal(cmd: str, cwd: str | None) -> str | None:
    """سببُ رفض `gh pr merge`، أو `None` إن كان الدمج مستوفياً.

    ما يحرسه workflow الترقية بعد الدمج يُحرس هنا **قبله**، فلا يُدمج ما
    سيُرفض: كل الفحوص خضراء · ولا `--admin` (تجاوزٌ للحماية) · وموافقةُ
    المالك على PR غيره **إن اشترطها عقد المشروع** (`require_approval`).
    قرار 2026-09-02 لمنصة المناقصات: المطوّر يدمج بلا موافقة، CI هو الحكم.
    """
    if re.search(r"\s--admin\b", cmd):
        return "⛔ `--admin` يتخطّى الفحوص — الدمج بشروطه أو لا يُدمج."
    if not shutil.which("gh"):
        return ("⛔ لا `gh` هنا فلا يُقرأ حكم CI ولا الموافقة — ثبّته "
                "وسجّل دخوله. العجز رفضٌ لا تخطٍّ.")
    m = re.search(r"gh\s+pr\s+merge\s+((?:[^-\s]|-(?=\s))\S*)", cmd)
    ref = [m.group(1)] if m else []
    try:
        p = subprocess.run(
            ["gh", "pr", "view", *ref, "--json",
             "author,reviewDecision,statusCheckRollup,state,baseRefName"],
            capture_output=True, text=True, timeout=30, cwd=cwd or None)
    except Exception as exc:                      # noqa: BLE001
        return f"⛔ تعذّر سؤال GitHub عن الـPR: {exc}"
    if p.returncode != 0:
        return f"⛔ تعذّر قراءة الـPR: {(p.stderr or p.stdout).strip()[:200]}"
    try:
        pr = json.loads(p.stdout)
    except json.JSONDecodeError:
        return "⛔ ردّ gh ليس JSON — لا يُدمج على حكمٍ مشكوك."
    bad = []
    for c in pr.get("statusCheckRollup") or []:
        verdict = (c.get("conclusion") or c.get("state") or "").upper()
        if verdict not in ("SUCCESS", "SKIPPED", "NEUTRAL"):
            bad.append(f"{c.get('name') or c.get('context') or '?'}={verdict or 'PENDING'}")
    if bad:
        return "⛔ فحوصٌ ليست خضراء: " + "، ".join(bad)
    if not (pr.get("statusCheckRollup") or []):
        return "⛔ لا فحوص على هذا الـPR — CI لم يجرِ بعد."
    owner = _CFG.get("owner", "")
    author = ((pr.get("author") or {}).get("login") or "")
    if (_CFG.get("require_approval") and owner and author != owner
            and pr.get("reviewDecision") != "APPROVED"):
        return (f"⛔ كاتب الـPR `{author}` ليس المالك، ولا Approve بعد "
                f"(reviewDecision={pr.get('reviewDecision') or 'NONE'}).")
    return None


def _secret_in(cmd: str) -> str | None:
    """يعيد وصف السرّ إن وُجد في نصّ الأمر — بنفس أنماط `guard_write`."""
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import guard_write as W
    except Exception:
        return None
    for line in cmd.splitlines():
        if W.PLACEHOLDER.search(line):
            continue
        for rx, what in W.PATTERNS:
            if rx.search(line):
                return what
    return None


if __name__ == "__main__":
    main()
