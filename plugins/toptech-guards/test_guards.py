#!/usr/bin/env python3
"""فحص الحرّاس — كلٌّ يُرى وهو يمنع، **وكلٌّ يُرى وهو يسمح**.

‼ الشطر الثاني هو المهمّ: حارسٌ يمنع كلَّ شيء يُطفأ في أوّل يوم، فيصير
  غيابه أسوأ من عدم وجوده — لأنه وَعَد. فلكل قاعدةٍ هنا حالتان: واحدة
  تسقط وواحدة تمرّ.

‼ ولا يستدعي الحارس داخل العملية: يُشغَّل **كما يشغّله كلود** — عمليةٌ
  منفصلة وJSON على stdin. الثمن مدفوع 2026-08-25 حين استدعى فحصٌ دالّةً
  حيّة بجملة حذف فمُسح المستودع.

    python3 test_guards.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.join(HERE, "scripts")

# ‼ مشروعٌ مؤقّت بإعداده — الـplugin عامٌّ ولا يعرف مسار إنتاجٍ بذاته،
#   فكل حالةٍ هنا تجري داخل مشروعٍ يعلن مساراته في `.claude/toptech-guards.json`.
import tempfile
PROJECT = tempfile.mkdtemp(prefix="toptech-guards-test-")
os.makedirs(os.path.join(PROJECT, ".claude"))
with open(os.path.join(PROJECT, ".claude", "toptech-guards.json"), "w", encoding="utf-8") as _fh:
    json.dump({"production_paths": ["/srv/prod-app", "/srv/prod-erp"],
               "deploy_tools": ["deploy.py"], "owner": "owner-login",
               "require_approval": False}, _fh)
BARE = tempfile.mkdtemp(prefix="toptech-guards-bare-")     # مشروعٌ بلا إعداد

# (الوصف، السكربت، المدخل، أيُمنع؟)
from cases_clauses import CLAUSE_CASES  # noqa: E402

CASES = [
    # ── دهس الإنتاج ──────────────────────────────────────────────
    ("نسخٌ مباشر إلى مسار الإنتاج", "guard_bash.py",
     {"tool_input": {"command": "scp api/app/main.py deploy@prod-host:/srv/prod-app/api/app/"}}, True),
    ("كتابةٌ عبر ssh على الإنتاج", "guard_bash.py",
     {"tool_input": {"command": "ssh nas 'cat > /srv/prod-erp/config/odoo.conf'"}}, True),
    ("النشر عبر الأداة — يمرّ", "guard_bash.py",
     {"tool_input": {"command": "python3 tools/deploy.py --by me --files api/app/main.py"}}, False),
    ("قراءةٌ من الإنتاج — تمرّ", "guard_bash.py",
     {"tool_input": {"command": "ssh nas 'cat /srv/prod-app/docker-compose.yml'"}}, False),
    # ‼ إيجابيةٌ كاذبة وقعت 2026-09-01: مسارُ الإنتاج ورد في شطرٍ آخر من
    #   أمرٍ يرسل قائمةً **للقراءة** إلى /tmp، فمُنع. والكاذبة تُطفئ
    #   الحارس فيصير غيابه أسوأ من عدمه ⇒ يُفحص هدفُ الكتابة لا ورودُ المسار.
    ("scp إلى /tmp ومسارُ الإنتاج في شطرٍ آخر — يمرّ", "guard_bash.py",
     {"tool_input": {"command": "scp -q list.txt nas:/tmp/list.txt && ssh nas "
                                "\"cd /srv/prod-app && shasum -a 256 x\""}}, False),
    ("سحبٌ من الإنتاج بـscp — يمرّ", "guard_bash.py",
     {"tool_input": {"command": "scp nas:" + "/srv/prod-app/docker-compose.yml ."}}, False),
    ("رفعٌ إلى الإنتاج بـrsync — يُمنع", "guard_bash.py",
     {"tool_input": {"command": "rsync -av web/ nas:" + "/srv/prod-app/web/"}}, True),
    # ‼ ثالثُ كاذبةٍ في ساعة: رسالةُ التزامٍ تصف الحارس حوت أنماطه فمنعت
    #   نفسها. ورسائل هذا الفريق عربيةٌ تصف الإنتاج ⇒ اصطدامٌ يومي.
    ("رسالةُ التزامٍ تذكر النشر — تمرّ", "guard_bash.py",
     {"tool_input": {"command": 'git commit -m "أصلح النقل بـscp إلى '
                                '/srv/prod-app — والحارس منع"'}}, False),
    ("لكن ssh مقتبساً يكتب على الإنتاج — يُمنع", "guard_bash.py",
     {"tool_input": {"command": 'ssh nas "cp x ' + '/srv/prod-app/api/x"'}}, True),
    # ‼ رابعُ كاذبة: نسخةٌ احتياطية **من** الإنتاج **إلى** مجلد النسخ.
    #   وهي بالضبط ما يُطلب فعلُه قبل النشر — فمنعُها يمنع الاحتياط نفسه.
    ("نسخٌ احتياطي من الإنتاج إلى backups — يمرّ", "guard_bash.py",
     {"tool_input": {"command": "sudo cp " + "/srv/prod-app/ingestion-data/.deploy-ledger.json "
                                "/srv/backups/ledger.json"}}, False),
    ("tar للإنتاج إلى backups — يمرّ", "guard_bash.py",
     {"tool_input": {"command": "sudo tar -czf /srv/backups/code.tar.gz -C /srv prod-apptform"}}, False),
    ("لكن استعادةُ tar فوق الإنتاج — تُمنع", "guard_bash.py",
     {"tool_input": {"command": "sudo tar -xzf code.tar.gz > " + "/srv/prod-app/x"}}, True),
    ("و rm داخل الإنتاج — يُمنع", "guard_bash.py",
     {"tool_input": {"command": "ssh nas 'rm " + "/srv/prod-app/api/app/main.py'"}}, True),
    # ‼ الـplugin عامّ: مشروعٌ بلا `.claude/toptech-guards.json` لا يحرس مساراً —
    #   وباقي الحرّاس تعمل فيه (حالة rm -rf أدناه تجري بلا إعداد أيضاً).
    ("مشروعٌ بلا إعداد: الكتابة على المسار نفسه تمرّ", "guard_bash.py",
     {"cwd": BARE, "tool_input": {"command": "scp x deploy@prod-host:/srv/prod-app/x"}}, False),

    # ── الحذف المدمّر ────────────────────────────────────────────
    ("rm -rf على مجلد حقيقي", "guard_bash.py",
     {"tool_input": {"command": "rm -rf /Users/ibra/Projects/tenders-platform/web"}}, True),
    ("rm -rf في scratchpad — يمرّ", "guard_bash.py",
     {"tool_input": {"command": "rm -rf /private/tmp/claude-501/x/scratchpad/tmp"}}, False),
    ("rm -rf node_modules — يمرّ", "guard_bash.py",
     {"tool_input": {"command": "rm -rf web/node_modules"}}, False),

    # ── قاعدة الإنتاج ────────────────────────────────────────────
    ("DELETE بلا WHERE", "guard_bash.py",
     {"tool_input": {"command": "docker exec tp-db psql -U tenders -c 'DELETE FROM tender'"}}, True),
    ("DROP TABLE", "guard_bash.py",
     {"tool_input": {"command": "psql -U tenders -c 'DROP TABLE invitation'"}}, True),
    ("DELETE بشرط — يمرّ", "guard_bash.py",
     {"tool_input": {"command": "docker exec tp-db psql -U tenders -c \"DELETE FROM outbox_email WHERE id=3\""}}, False),
    ("SELECT — يمرّ", "guard_bash.py",
     {"tool_input": {"command": "docker exec tp-db psql -U tenders -tAc 'select count(*) from tender'"}}, False),

    # ── الدفع القسري ────────────────────────────────────────────
    ("push --force على origin", "guard_bash.py",
     {"tool_input": {"command": "git push --force origin master"}}, True),
    ("force-with-lease إلى فرع — يمرّ", "guard_bash.py",
     {"tool_input": {"command": "git push --force-with-lease origin feat/x"}}, False),

    # ── master محميٌّ افتراضياً (2026-09-02) ────────────────────
    # ‼ قِيس 2026-08-30: ثلاثة التزاماتٍ حمراء دخلت master وأحدها منشور.
    ("push مباشر إلى master — يُمنع", "guard_bash.py",
     {"tool_input": {"command": "git push origin master"}}, True),
    ("push إلى فرع مهمّة — يمرّ", "guard_bash.py",
     {"tool_input": {"command": "git push -u origin ibra/constitution"}}, False),
    ("push إلى master والحماية مطفأة صراحةً — يمرّ", "guard_bash.py",
     {"tool_input": {"command": "git push origin master"}}, False,
     {"TOPTECH_PROTECT_MASTER": "0"}),
    ("رسالة التزام تذكر master — تمرّ", "guard_bash.py",
     {"tool_input": {"command": 'git commit -m "أصلح الدفع إلى master"'}}, False),

    # ── وسم production للـworkflow وحده ─────────────────────────
    ("push وسم production بيد — يُمنع", "guard_bash.py",
     {"tool_input": {"command": "git push -f origin refs/tags/production"}}, True),
    ("git tag production بيد — يُمنع", "guard_bash.py",
     {"tool_input": {"command": "git tag -f production abc123"}}, True),
    ("push وسم إصدار عادي — يمرّ", "guard_bash.py",
     {"tool_input": {"command": "git push origin v1.1.0"}}, False),

    # ── الدمج يُسأل عنه GitHub — والعجز رفض ─────────────────────
    ("gh pr merge بلا gh على المسار — يُمنع", "guard_bash.py",
     {"tool_input": {"command": "gh pr merge 12 --squash"}}, True,
     {"PATH": "/nonexistent"}),
    ("gh pr merge --admin — يُمنع", "guard_bash.py",
     {"tool_input": {"command": "gh pr merge 12 --admin --squash"}}, True),
    ("gh pr view — يمرّ", "guard_bash.py",
     {"tool_input": {"command": "gh pr view 12 --json state"}}, False),

    # ── سرٌّ عبر الصدفة (heredoc / إعادة توجيه) ────────────────
    # ‼ جلسات bypass مأمورةٌ بالكتابة عبر Bash — فحارس Write لا يراها.
    ("heredoc يكتب كلمة قاعدة — يُمنع", "guard_bash.py",
     {"tool_input": {"command": "cat > infra/odoo.conf <<'EOF'\n[options]\ndb_"
                                + "password = " + "Fk9x" * 5 + "\nEOF"}}, True),
    ("heredoc بقيمة نائبة — يمرّ", "guard_bash.py",
     {"tool_input": {"command": "cat > compose.yml <<'EOF'\n  - POSTGRES_"
                                "PASSWORD=${DB_PASSWORD}\nEOF"}}, False),
    ("إعادة توجيه نصٍّ عادي — تمرّ", "guard_bash.py",
     {"tool_input": {"command": "echo '# عنوان' > README.md"}}, False),

    # ── الأسرار ─────────────────────────────────────────────────
    # ‼ كل «سرٍّ» هنا **مصطنعٌ ومركَّبٌ برمجياً** لسببين قِيسا 2026-09-01:
    #   (أ) كلمةٌ حيّة وُضعت هنا كبيانات اختبار فدخلت تاريخ git — وسرٌّ
    #       يدخل التاريخ لا يخرج منه. فحصُ حارسٍ لا يستحقّ سرّاً حقيقياً.
    #   (ب) وحتى العيّنة المزيّفة إن وردت **حرفيةً** يمنعها الحارس نفسه
    #       عند كتابة هذا الملف. فالتركيب البرمجي يحلّ الاثنين معاً.
    ("كلمة قاعدة نصّاً", "guard_write.py",
     {"tool_input": {"file_path": "infra/odoo.conf",
                     "content": "[options]\ndb_" + "password = " + "Fk9x" * 5 + "\n"}}, True),
    ("مفتاح خاص", "guard_write.py",
     {"tool_input": {"file_path": "key.pem",
                     "content": "-----BEGIN OPENSSH PRIVATE " + "KEY-----\nabc\n"}}, True),
    ("كلمة تطبيق جيميل", "guard_write.py",
     {"tool_input": {"file_path": "notes.md",
                     "content": " ".join(["abcd", "efgh", "ijkl", "mnop"]) + "\n"}}, True),
    ("قيمة نائبة — تمرّ", "guard_write.py",
     {"tool_input": {"file_path": "infra/odoo.conf",
                     "content": "db_password = <في secrets/db.txt>\n"}}, False),
    ("متغيّر بيئة — يمرّ", "guard_write.py",
     {"tool_input": {"file_path": "compose.yml",
                     "content": "  - POSTGRES_PASSWORD=${DB_PASSWORD}\n"}}, False),
    ("نصٌّ عادي — يمرّ", "guard_write.py",
     {"tool_input": {"file_path": "README.md", "content": "# عنوان\nسطرٌ عربي.\n"}}, False),
] + CLAUSE_CASES


def run(script: str, payload: dict, env: dict | None = None) -> str:
    # ‼ البيئة تُمرَّر كاملةً ثم تُدهس بمفاتيح الحالة — فحالةُ «الحماية
    #   مطفأة» و«لا gh» تُقاس بلا أن تُفقَد بيئة المفسّر نفسه.
    payload = {"cwd": PROJECT, **payload}          # المشروع المؤقّت ما لم تسمِّ الحالة غيره
    env = {**os.environ, **(env or {})}
    env.pop("CLAUDE_PROJECT_DIR", None)            # وإلا قرأ الحارس إعداد مشروعٍ آخر
    p = subprocess.run([sys.executable, os.path.join(S, script)],
                       input=json.dumps(payload), capture_output=True, text=True,
                       timeout=45, env=env)
    if p.returncode != 0:
        raise SystemExit(f"الحارس {script} انهار: rc={p.returncode}\n{p.stderr}")
    return p.stdout.strip()


def check_executable() -> int:
    """كل سكربتٍ في `scripts/` يُنادى **مباشرةً** من `hooks.json`، فيحتاج
    shebang وبتَ تنفيذٍ في الشجرة **وفي فهرس git** — فالفهرس هو ما يصل
    المطوّرين، والشجرة وحدها تُصلَح بـ`chmod` وتُدهس عند التحديث.

    ‼ قِيس 2026-09-04: `session_start.py` بوضع 100644 فسقط SessionStart
      بـ`EACCES: permission denied, posix_spawn` ولم يُحقن الدستور — وCI
      أخضر لأنه كان يشغّله بـ`python3` لا كما يشغّله كلود.
    """
    fail = 0
    try:
        p = subprocess.run(["git", "-C", HERE, "ls-files", "-s", "--", S],
                           capture_output=True, text=True, timeout=10)
        modes = {os.path.basename(ln.split("\t", 1)[1]): ln.split()[0]
                 for ln in p.stdout.splitlines() if "\t" in ln} if p.returncode == 0 else {}
    except Exception:                                  # noqa: BLE001 — بلا git يبقى فحص الشجرة
        modes = {}
    for name in sorted(os.listdir(S)):
        if not name.endswith(".py"):
            continue
        path = os.path.join(S, name)
        problems = []
        with open(path, "rb") as fh:
            if not fh.read(2) == b"#!":
                problems.append("بلا shebang")
        if not os.access(path, os.X_OK):
            problems.append("بلا بت تنفيذ في الشجرة")
        if name in modes and modes[name] != "100755":
            problems.append(f"وضع git {modes[name]} لا 100755")
        mark = "✘" if problems else "✔"
        print(f"  {mark} تنفيذ  scripts/{name}" + (" — " + "، ".join(problems) if problems else ""))
        fail += bool(problems)
    return fail


def check_tree() -> tuple[int, int, int]:
    """حارس الشجرة المشتركة (`guard_tree.py`) — يُقاس على مستودعٍ حقيقيّ
    مؤقّت: master في الجذر وworktree على فرع، لأن الحارس يسأل git نفسه.

    ‼ ومن حالات المرور ما وقع فعلاً: ملفٌّ اتّسخ قبل الأمر (جلسةٌ أخرى في
      الشجرة نفسها) لا يُنسب إلى الأمر، وإلا صار كلُّ أمرٍ في الشجرة
      المشتركة ممنوعاً بأثر غيره فيُطفأ الحارس.
    """
    import time
    root = tempfile.mkdtemp(prefix="toptech-guards-tree-")
    repo, wt = os.path.join(root, "repo"), os.path.join(root, "wt")
    g = lambda *a, cwd=repo: subprocess.run(["git", "-C", cwd, *a], check=True,  # noqa: E731
                                            capture_output=True, text=True)
    os.makedirs(repo)
    g("init", "-q", "-b", "master")
    g("config", "user.email", "t@t"); g("config", "user.name", "t")
    for name, body in (("a.txt", "a\n"), (".gitignore", "*.local\n")):
        with open(os.path.join(repo, name), "w") as fh:
            fh.write(body)
    g("add", "."); g("commit", "-q", "-m", "init")
    g("worktree", "add", "-q", "-b", "me/task", wt)

    def w(path: str, env=None) -> bool:
        out = run("guard_tree.py", {"cwd": repo, "hook_event_name": "PreToolUse",
                                    "tool_name": "Edit", "tool_input": {"file_path": path}}, env)
        return bool(out) and json.loads(out)["hookSpecificOutput"]["permissionDecision"] == "deny"

    def bash(cwd: str, act, sid: str) -> bool:
        base = {"cwd": cwd, "tool_name": "Bash", "session_id": "s", "tool_use_id": sid,
                "tool_input": {"command": "x"}}
        run("guard_tree.py", {**base, "hook_event_name": "PreToolUse"})
        act()
        out = run("guard_tree.py", {**base, "hook_event_name": "PostToolUse"})
        return bool(out) and json.loads(out).get("decision") == "block"

    def push(cwd: str, cmd: str) -> bool:
        out = run("guard_bash.py", {"cwd": cwd, "tool_input": {"command": cmd}})
        return bool(out) and json.loads(out)["hookSpecificOutput"]["permissionDecision"] == "deny"

    def touch(path: str, mtime: float | None = None):
        with open(path, "a") as fh:
            fh.write("x\n")
        if mtime:
            os.utime(path, (mtime, mtime))

    # جلسةٌ أخرى اتّسخت بملفٍّ قبل ساعة — قبل الأمر
    touch(os.path.join(repo, "other.txt"), time.time() - 3600)
    cases = [
        ("Edit ملفٍ متتبَّع والفرع master", w(os.path.join(repo, "a.txt")), True),
        ("Write ملفٍ جديد والفرع master", w(os.path.join(repo, "new/b.py")), True),
        ("Edit ملفٍ متجاهَل على master — يمرّ", w(os.path.join(repo, "x.local")), False),
        ("Edit في worktree على فرع — يمرّ", w(os.path.join(wt, "a.txt")), False),
        ("Edit خارج أي مستودع — يمرّ", w(os.path.join(root, "notes.md")), False),
        ("Edit على master والحماية مطفأة — يمرّ",
         w(os.path.join(repo, "a.txt"), {"TOPTECH_PROTECT_MASTER": "0"}), False),
        ("Bash يكتب ملفاً على master", bash(repo, lambda: touch(os.path.join(repo, "c.sh")), "1"), True),
        ("Bash يعدّل متتبَّعاً على master", bash(repo, lambda: touch(os.path.join(repo, "a.txt")), "2"), True),
        ("Bash بلا أثر على master — يمرّ", bash(repo, lambda: None, "3"), False),
        ("Bash وملفٌ اتّسخ قبله بيد غيره — يمرّ", bash(repo, lambda: None, "4"), False),
        ("Bash يكتب في worktree على فرع — يمرّ",
         bash(wt, lambda: touch(os.path.join(wt, "d.txt")), "5"), False),
        # ── حارس الدفع يقرأ مجلّد الأمر لا مجلّد الجلسة (كاذبة 2026-10-13) ──
        ("دفعٌ ضمنيّ والجلسة على الفرع الرئيس", push(repo, "git push -q"), True),
        ("cd إلى worktree ثم دفعٌ ضمنيّ — يمرّ", push(repo, f"cd {wt} && git push -q"), False),
        ("git -C worktree ثم دفعٌ ضمنيّ — يمرّ", push(repo, f"git -C {wt} push -q"), False),
        ("الجلسة في worktree وcd إلى الرئيس ثم دفع", push(wt, f"cd {repo} && git push"), True),
        ("الجلسة في worktree وgit -C إلى الرئيس ثم دفع", push(wt, f"git -C {repo} push"), True),
    ]
    b = p = f = 0
    for desc, got, want in cases:
        ok = got == want
        print(f"  {'✔' if ok else '✘'} {'مُنع' if got else 'مرّ '}  {desc}")
        if not ok:
            f += 1
            print(f"       المتوقّع: {'منع' if want else 'مرور'}")
        elif want:
            b += 1
        else:
            p += 1
    return b, p, f


def main() -> int:
    blocked = passed = fail = 0
    fail += check_executable()
    for case in CASES:
        desc, script, payload, want_deny = case[:4]
        env = case[4] if len(case) > 4 else None
        out = run(script, payload, env)
        got_deny = False
        if out:
            try:
                got_deny = json.loads(out).get(
                    "hookSpecificOutput", {}).get("permissionDecision") == "deny"
            except json.JSONDecodeError:
                raise SystemExit(f"مخرَج {script} ليس JSON: {out[:120]}")
        ok = got_deny == want_deny
        mark = "✔" if ok else "✘"
        verb = "مُنع" if got_deny else "مرّ "
        print(f"  {mark} {verb}  {desc}")
        if not ok:
            fail += 1
            print(f"       المتوقّع: {'منع' if want_deny else 'مرور'}")
        elif want_deny:
            blocked += 1
        else:
            passed += 1

    tb, tp, tf = check_tree()
    blocked, passed, fail = blocked + tb, passed + tp, fail + tf

    print("\n" + "═" * 62)
    print(f"مُنع {blocked} · مرّ {passed} · فشل {fail}")
    if fail:
        print("⛔ حارسٌ لا يتصرّف كما يدّعي")
        return 1
    print("✅ كل حارسٍ رُئي يمنع، وكلٌّ رُئي يسمح")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
