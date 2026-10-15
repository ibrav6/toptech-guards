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
import shlex
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


HEREDOC_BODY = r"<<-?\s*[\'\"]?(\w+)[\'\"]?\n.*?\n\1\b"
CLAUSE_SEP = r"[;&|]{1,2}|\n"


def _strip_heredocs(cmd: str) -> str:
    """ينزع **أجساد** الـheredoc — نصٌّ يُغذّى لأمرٍ، لا أمرٌ يُنفَّذ.

    ‼ قِيس 2026-09-03 (سادس كاذبة): رسالةُ التزامٍ مرّت بعلم الملف عبر
      heredoc وفيها اسمُ الفرع الرئيس عشر مرّات، فمنعها حارسُ الفرع
      المشترك. و`_strip_messages` لا تراها لأنها تنزع علم الرسالة وحده.
      ثم منع الحارسُ **سكربتَ إصلاحه نفسه** لأن نصّه يحوي أنماطه.

    ⚠ **ولا تُنادى إلا من فحصَي الدفع.** جُرّبت عالميةً 2026-09-03
      فأعمت حارسَ الأسرار: كلمةُ قاعدةٍ تُكتب داخل heredoc صارت غير
      مرئيّة. والفرق أن نصّ الرسالة **يُغذّى ولا يُنفَّذ**، أما ما
      يُغذّى لأداةِ كتابةٍ فمحتوىً يستقرّ على القرص ويجب أن يُفحص.
      ⇒ علاجُ كاذبةٍ لا يُشترى بثغرة.
    """
    return re.sub(HEREDOC_BODY, "<<STRIPPED", cmd, flags=re.S)


def _clauses(cmd: str) -> list[str]:
    """يشظّي الأمر المركّب إلى شقوقٍ تُفحص كلٌّ على حدة.

    ‼ **وهذا علاج عائلة الكاذبات كلّها** — ستٌّ في يومين. كان كلُّ فحصٍ
      يسأل «أيرد النمط في الأمر؟» والسؤال الصحيح «أيرد في الشقّ الذي
      يفعل الفعل؟». علمُ حذفٍ في شطرٍ منع دفعاً في شطرٍ آخر، وانتقالٌ
      إلى مسار إنتاجٍ منع نسخاً إلى مجلدٍ مؤقّت.
    """
    return re.split(CLAUSE_SEP, cmd)


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
    # ‼ **على شقّه وحده** — قِيس 2026-09-03: علمُ حذفٍ من أمرٍ في
    #     الشطر السابق منع دفعاً سليماً، وأصاب جلستين في يوم.
    for part in _clauses(_strip_heredocs(cmd)):
        if not re.search(r"git\s+push\b", part):
            continue
        if re.search(r"(--force(?!-with-lease)|(?<![\w-])-f(?![\w-]))", part) and (
                re.search(r"\b(master|main)\b", part) or "origin" in part):
            deny("⛔ `git push --force` على فرعٍ مشترك يمحو عمل غيرك.\n"
                 "استعمل `--force-with-lease` — يرفض الدفع إن تقدّم البعيد.")

    # ‼ ٥) الفرع المشترك — **مشعَلٌ افتراضياً منذ 2026-09-02** (مسار PR
    #     صار هو المسار). يُطفأ بـTOPTECH_PROTECT_MASTER=0 لا يُشعَل بـ1.
    #     قِيس 2026-08-2x: 97 ملفاً معلّقاً يومين عبر سبع جلسات على شجرةٍ
    #     واحدة، والبوابة خضراء عليها طوال الوقت. وقِيس 2026-08-30 ثلاثة
    #     التزاماتٍ حمراء دخلت master وأحدها منشور.
    if os.environ.get("TOPTECH_PROTECT_MASTER", "1") != "0":
        for part in _clauses(_strip_heredocs(cmd)):
            # ‼ و`git -C X push` دفعٌ أيضاً — كان يمرّ بلا فحصٍ أصلاً (طفرة 2026-10-13)
            if not re.search(r"git\s+(?:-C\s+\S+\s+)?push\b", part):
                continue
            explicit = re.search(r"\b(master|main)\b", part)
            # `git push` بلا فرعٍ مسمّى يدفع الفرع الحالي — فيُسأل git.
            implicit = (not re.search(r"\brefs/|\borigin\s+\S+", part)
                        and _current_branch(_cmd_dir(cmd, part, data.get("cwd")))
                        in ("master", "main"))
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


def _cmd_dir(cmd: str, part: str, cwd: str | None) -> str | None:
    """المجلّد الذي يعمل فيه الأمر فعلاً: `git -C X` في شقّه، أو آخر
    `cd X` قبله في الأمر — لا مجلّد الجلسة. يقرؤه حارس الدفع (أيُّ فرعٍ
    يُدفع) وحارس الدمج (أيُّ مستودعٍ يسأل فيه gh).

    ‼ كاذبةٌ قِيست 2026-10-13: `cd ../worktree && git commit … && git push`
      من جلسةٍ مجلّدها الشجرة المشتركة على الفرع الرئيس ⇒ مُنع دفعُ فرعٍ
      سليم، وضاع الالتزام معه لأن الأمر كلّه رُفض.
    """
    base = os.path.expanduser(cwd or ".")
    m = re.search(r"\bgit\s+-C\s+(\S+)", part)
    if m:
        return os.path.join(base, os.path.expanduser(m.group(1).strip("'\"")))
    head = cmd[:cmd.find(part)] if part in cmd else ""
    cds = re.findall(r"(?:^|[;&|]\s*)cd\s+(\S+)", head)
    if cds:
        return os.path.join(base, os.path.expanduser(cds[-1].strip("'\"")))
    return cwd


def _current_branch(cwd: str | None) -> str:
    try:
        p = subprocess.run(["git", "-C", cwd or ".", "rev-parse",
                            "--abbrev-ref", "HEAD"],
                           capture_output=True, text=True, timeout=5)
        return p.stdout.strip() if p.returncode == 0 else ""
    except Exception:
        return ""


# أعلامُ الدمج التي تأخذ قيمة — تُتخطّى قيمتُها وإلا قُرئت مرجعَ الـPR
_MERGE_VALUE_FLAGS = ("-t", "--subject", "-b", "--body", "-F", "--body-file",
                      "-A", "--author-email", "--match-head-commit")
# ختمُ الشجرة الخضراء: وظيفةٌ في CI المشروع تكتبه على رأس الـPR بعد أن
# تخضرّ الفحوص، ووصفُه شجرةُ الدمج التجريبي الذي فحصته (tenders-platform
# منذ #610). ولا يُقبل إلا من `github-actions` — ختمٌ يكتبه غيرُه لا يشهد.
TREE_STAMP = "ci/tree"
STAMP_BOT = "github-actions[bot]"


class _GhError(Exception):
    pass


def _gh(args: list[str], cwd: str | None = None, env: dict | None = None):
    # ‼ مهلةٌ لكلّ نداء كي تبقى النداءات الخمسة تحت مهلة الـhook (40ث)؛
    #   والنداء ~2ث (قِيس 2026-10-15)، والحارس كلّه 2–8ث على PRات حيّة.
    try:
        p = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=7,
                           cwd=cwd or None, env={**os.environ, **(env or {})})
    except Exception as exc:                      # noqa: BLE001
        raise _GhError(f"تعذّر سؤال GitHub: {exc}") from None
    if p.returncode != 0:
        raise _GhError((p.stderr or p.stdout).strip()[:200])
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError:
        raise _GhError("ردّ gh ليس JSON — لا يُدمج على حكمٍ مشكوك.") from None


def _merge_target(cmd: str, cwd: str | None) -> tuple[list[str], str | None, dict] | None:
    """ما يعيّن الـPR **كما يعيّنه gh نفسه**: (وسائط `gh pr view`، مجلّده، بيئته)،
    أو `None` إن لم يكن الدمج أمراً صريحاً في شقّه.

    ‼ قِيس 2026-09-04 و09-15 (#3): كان الحارس يلتقط الرقم وحده ويسأل عنه
      في مجلّد الجلسة ويتجاهل `-R` — فحَكَم على فحوص tenders#2 والدمجُ في
      FAED#2. لو كان ذاك أخضر لمرّ دمجٌ أحمر. فيُقرأ ما يقرؤه gh: الرابط،
      و`-R`/`--repo`، و`GH_REPO=` قبل الأمر، ومجلّد الأمر (`cd X &&`).
    ‼ و`None` لا تخمين: الدمج داخل نصٍّ مقتبس (`ssh h "…"` · `bash -c '…'`)
      لا يُعرف مجلّده ولا مستودعه، والسؤال عن فرع الجلسة يحكم على PR آخر.
    """
    part = next((c for c in _clauses(cmd) if re.search(r"\bgh\s+pr\s+merge\b", c)), cmd)
    try:
        toks = shlex.split(part)
    except ValueError:
        toks = part.split()
    at = next((i for i in range(len(toks) - 2)
               if toks[i:i + 3] == ["gh", "pr", "merge"]), None)
    if at is None:
        return None
    env = dict(t.split("=", 1) for t in toks[:at] if re.fullmatch(r"GH_(?:REPO|HOST)=\S*", t))
    ref = repo = None
    rest = iter(toks[at + 3:])
    for t in rest:
        if t in ("-R", "--repo"):
            repo = next(rest, None)
        elif t.startswith("--repo=") or (t.startswith("-R") and len(t) > 2):
            repo = t.split("=", 1)[1] if "=" in t else t[2:]
        elif t in _MERGE_VALUE_FLAGS:
            next(rest, None)
        elif not t.startswith("-") and ref is None:
            ref = t
    return ([ref] if ref else []) + (["--repo", repo] if repo else []), \
        _cmd_dir(cmd, part, cwd), env


def _merge_refusal(cmd: str, cwd: str | None) -> str | None:
    """سببُ رفض `gh pr merge`، أو `None` إن كان الدمج مستوفياً.

    ما يحرسه workflow الترقية بعد الدمج يُحرس هنا **قبله**، فلا يُدمج ما
    سيُرفض: كل الفحوص خضراء · ولا `--admin` (تجاوزٌ للحماية) · وموافقةُ
    المالك على PR غيره **إن اشترطها عقد المشروع** (`require_approval`).
    قرار 2026-09-02 لمنصة المناقصات: المطوّر يدمج بلا موافقة، CI هو الحكم.
    وقاعدتُه الفرعُ الافتراضي · وشجرتُه هي ما فحصه CI (`_untested_tree`).
    """
    if re.search(r"\s--admin\b", cmd):
        return "⛔ `--admin` يتخطّى الفحوص — الدمج بشروطه أو لا يُدمج."
    if not shutil.which("gh"):
        return ("⛔ لا `gh` هنا فلا يُقرأ حكم CI ولا الموافقة — ثبّته "
                "وسجّل دخوله. العجز رفضٌ لا تخطٍّ.")
    target = _merge_target(cmd, cwd)
    if target is None:
        return ("⛔ لا يُعرف أيُّ PR يُدمج: الدمج ليس أمراً صريحاً في شقّه "
                "(داخل نصٍّ مقتبس أو `ssh`/`bash -c`).\n"
                "   المخرج: اكتبه أمراً مستقلاً بالرابط الكامل. وإن كان نصّاً يصف "
                "الحارس فاكتبه في ملفٍ بـWrite ومرّره بـ`--body-file`.")
    args, where, env = target
    try:
        pr = _gh(["pr", "view", *args, "--json", "url,author,reviewDecision,"
                  "statusCheckRollup,state,baseRefName,headRefOid"], where, env)
        m = re.match(r"https://[^/]+/([^/]+/[^/]+)/pull/(\d+)", pr.get("url") or "")
        if not m:
            return f"⛔ رابط الـPR غير مفهوم ({pr.get('url')!r}) — لا يُدمج ما لا يُعرف مستودعه."
        repo, num = m.groups()
        api = _gh(["api", f"repos/{repo}/pulls/{num}"], env=env)
    except _GhError as exc:
        return f"⛔ تعذّر قراءة الـPR: {exc}"

    # ‼ قاعدةٌ غير الافتراضي لا تصل الإنتاج — قِيس 2026-10-15: tenders#656
    #   دُمج في `claude/fit-v2` (فرعٌ دُمج قبله) فلم يصل master ونُقل بيده
    #   في #666. وقبله #117 (2026-09-22) في فرعٍ أُغلق PRُّه بلا دمج: دمجان
    #   من 423 في تاريخ المنصة كلّه بقاعدةٍ أخرى، **وكلاهما ضاع**.
    base = pr.get("baseRefName") or ""
    default = ((api.get("base") or {}).get("repo") or {}).get("default_branch") or ""
    if not default or base != default:
        return (f"⛔ قاعدة الـPR `{base}` ليست الفرع الافتراضي `{default or '?'}` — "
                "دمجُه لا يصل الفرع الافتراضي ولا الإنتاج.\n"
                f"   المخرج: gh pr edit {pr['url']} --base {default or '<الافتراضي>'}\n"
                "   ثم انتظر CI (شجرة الدمج تتغيّر) وادمج. وإن كان مكدَّساً على PR "
                "آخر: ادمج ذاك أوّلاً ثم غيّر القاعدة.\n"
                "قِيس 2026-10-15: tenders#656 دُمج في فرعٍ مدموجٍ قبله فلم يصل "
                "master؛ والدمجان الوحيدان بقاعدةٍ أخرى في تاريخ المنصة ضاعا كلاهما.")

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
    return _untested_tree(repo, pr, api, env)


def _untested_tree(repo: str, pr: dict, api: dict, env: dict) -> str | None:
    """أفَحَص CI **الشجرةَ التي ستدخل** القاعدة الآن؟ شجرةُ الدمج التجريبي
    الحالي مقابل أختام `ci/tree` الخضراء على رأس الـPR.

    ‼ قِيس 2026-10-15: PRان أخضران كلٌّ وحده أخذا الترحيل `0138`، فبقي
      master أحمر 13:10–13:25 بلا نشر. وفي أسبوع 10-08..10-15: 46 من 105
      دمجات (44٪) دخلت بشجرةٍ لم تُفحص، وجولتا master الحمراوان كلتاهما
      بعد دمجٍ منها. والرفضُ لا يزيد CI: الدمجُ المتقادم يُفحص كاملاً على
      master اليوم (`reuse` يخطئ)، فالمنعُ ينقل الجولة نفسها (وسيطها 2.7 د)
      إلى ما قبل الدمج حيث يُحمِّر الـPR لا master.

    ‼ و`merge_commit_sha` وحده يكذب: قِيس 2026-10-15 على tenders#676 أن
      GitHub أبقاه على قاعدةٍ قديمة (`mergeable_state=clean`) بعد أن تقدّم
      master، ولم يُعِد حسابه بالقراءة المتكرّرة — وختمُه يطابق شجرتَه
      القديمة. فيُشترط أن يكون أبواه **رأسَ القاعدة الآن** ورأسَ الـPR.

    بلا ختمٍ أصلاً لا رأي: المستودع لا يختم (حارسٌ عامّ، والختم عقدُ مشروع).
    """
    head, base, url = pr.get("headRefOid") or "", pr.get("baseRefName") or "", pr["url"]
    try:
        stamps = {s.get("description") for s in
                  _gh(["api", f"repos/{repo}/commits/{head}/statuses?per_page=100"], env=env)
                  if s.get("context") == TREE_STAMP and s.get("state") == "success"
                  and (s.get("creator") or {}).get("login") == STAMP_BOT}
        if not stamps:
            return None
        merge = api.get("merge_commit_sha")
        commit = _gh(["api", f"repos/{repo}/git/commits/{merge}"], env=env) if merge else {}
        tip = _gh(["api", f"repos/{repo}/git/ref/heads/{base}"], env=env)["object"]["sha"]
    except (_GhError, KeyError, TypeError) as exc:
        return f"⛔ تعذّر التحقّق من شجرة الدمج: {exc}"
    parents = [p.get("sha") for p in commit.get("parents") or []]
    tree = (commit.get("tree") or {}).get("sha")
    if parents == [tip, head] and tree in stamps:
        return None
    if not merge:
        why = "لا دمج تجريبي عند GitHub (تعارض؟)"
    elif parents[:1] != [tip]:
        why = (f"تقدّم `{base}` إلى {tip[:8]} بعد آخر دمجٍ تجريبي "
               f"(على {(parents or ['?'])[0][:8]})")
    elif parents[1:] != [head]:
        why = "الدمج التجريبي لرأسٍ أقدم من رأس الـPR"
    else:
        why = f"شجرة الدمج {str(tree)[:8]} بلا ختمٍ أخضر (المختوم: {', '.join(sorted(s[:8] for s in stamps if s))})"
    return (f"⛔ CI لم يفحص الشجرة التي ستدخل `{base}`: {why}.\n"
            "   الأخضر على الـPR فحصَ دمجاً على قاعدةٍ أقدم، ودمجٌ دخل بينهما "
            "قد يصطدم به وكلاهما أخضر.\n"
            f"   المخرج: gh pr update-branch {url}  ثم الدمج حين يخضرّ CI.\n"
            "   ‼ و«Re-run» للجولة نفسها لا يكفي: يعيد فحص الدمج التجريبي القديم بعينه.\n"
            "قِيس 2026-10-15: PRان أخضران كلٌّ وحده أخذا الترحيل 0138 فاحمرّ "
            "master ربع ساعة بلا نشر.")


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
