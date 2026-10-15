"""حالاتُ حارس الدمج — تُشغَّل من `test_guards.py` على `gh` مزيّف.

‼ الحارس يسأل GitHub، والفحصُ لا يسأله: `gh` مزيّفٌ أوّلَ المسار يجيب من
  عالمٍ مكتوبٍ هنا، فتُرى الحالات كلّها بلا شبكة وبلا PR حقيقي. ويُشغَّل
  الحارس نفسه كما يشغّله كلود (عمليةٌ وJSON على stdin) لا دالّةً مستوردة.

‼ **والرقمُ نفسه في مستودعين بحكمين متعاكسين** (o/plat#5 يمرّ وo/lib#5
  يُمنع، والعكس في #6): فكلُّ حالةٍ تشهد **أيَّ مستودعٍ قُرئ** — حارسٌ
  يسأل مجلّد الجلسة يسقط في نصفها. هذه كاذبة #3 (2026-09-04) وعكسُها
  الأخطر (2026-09-15): دمجٌ أحمر يمرّ لأن رقمه أخضر في مستودعٍ آخر.

والحالات المسمّاة بتاريخٍ وقعت فعلاً:
| الحالة | ما وقع |
|---|---|
| القاعدة `claude/fit-v2` | tenders#656 (2026-10-15) دُمج في فرعٍ مدموجٍ قبله فلم يصل master |
| دمجٌ تجريبيٌّ على قاعدةٍ قديمة | الترحيل 0138: PRان أخضران كلٌّ وحده، وmaster أحمر 13:10–13:25؛ وGitHub أبقى `merge_commit_sha` على القاعدة القديمة (tenders#676) |
"""
from __future__ import annotations

import json
import os
import stat
import tempfile

BOT = {"login": "github-actions[bot]"}
GREEN = [{"name": "python", "conclusion": "SUCCESS"}, {"name": "web", "conclusion": "SUCCESS"}]


def stamp(tree: str, who: dict = BOT) -> dict:
    return {"context": "ci/tree", "state": "success", "description": tree, "creator": who}


# ── العالم: مستودعان، ورأسُ القاعدة الآن B2 في كليهما ───────────────────
def _pr(n, branch, head, merge, *, base="master", rollup=GREEN):
    return {"number": n, "branch": branch, "base": base, "head": head,
            "merge": merge, "rollup": rollup}


WORLD = {
    # منصّةٌ تختم `ci/tree`
    "o/plat": {
        "default": "master", "tips": {"master": "B2", "claude/fit-v2": "F1"},
        "prs": [
            _pr(5, "me/ok", "H5", "M5"),
            _pr(6, "me/stale", "H6", "M6"),            # 0138: دمجٌ تجريبي على B1
            _pr(7, "me/recomputed", "H7", "M7"),       # GitHub أعاد الدمج ولم يُعَد CI
            _pr(8, "me/stacked", "H8", "M8", base="claude/fit-v2"),   # tenders#656
            _pr(9, "me/forged", "H9", "M9"),           # ختمٌ مطابق من غير البوت
            _pr(10, "me/oldhead", "H10", "M10"),       # الدمج لرأسٍ سابق
            _pr(11, "me/conflict", "H11", None),       # لا دمج تجريبي
            _pr(12, "me/red", "H12", "M12", rollup=[{"name": "python", "conclusion": "FAILURE"}]),
        ],
        "commits": {
            "M5": {"tree": "T5", "parents": ["B2", "H5"]},
            "M6": {"tree": "T6", "parents": ["B1", "H6"]},
            "M7": {"tree": "T7new", "parents": ["B2", "H7"]},
            "M8": {"tree": "T8", "parents": ["F1", "H8"]},
            "M9": {"tree": "T9", "parents": ["B2", "H9"]},
            "M10": {"tree": "T10", "parents": ["B2", "H10old"]},
            "M12": {"tree": "T12", "parents": ["B2", "H12"]},
        },
        "statuses": {
            "H5": [stamp("T5")], "H6": [stamp("T6")], "H7": [stamp("T7old")],
            "H8": [stamp("T8")], "H9": [stamp("T9", {"login": "someone"}), stamp("T9old")],
            "H10": [stamp("T10")], "H11": [stamp("T11")], "H12": [stamp("T12")],
        },
    },
    # مستودعٌ عامّ لا يختم، وفرعه الافتراضي main
    "o/lib": {
        "default": "main", "tips": {"main": "L2"},
        "prs": [
            _pr(5, "me/lib-five", "K5", "N5", base="feature"),
            _pr(6, "me/lib-six", "K6", "N6", base="main"),
        ],
        "commits": {"N5": {"tree": "U5", "parents": ["L1", "K5"]},
                    "N6": {"tree": "U6", "parents": ["L1", "K6"]}},
        "statuses": {},
    },
}

# ‼ يجيب كما يجيب gh: الرابطُ يعيّن مستودعه، ثم `--repo`، ثم `GH_REPO`، ثم
#   مستودعُ مجلّده (`.fake-repo`) — وبلا مرجعٍ فرعُ مجلّده (`.fake-branch`).
FAKE_GH = r'''#!/usr/bin/env python3
import json, os, re, sys
W = json.load(open(os.environ["FAKE_GH_WORLD"]))
a = sys.argv[1:]

def out(x):
    print(json.dumps(x)); sys.exit(0)

def fail(msg):
    print(msg, file=sys.stderr); sys.exit(1)

def here(name):
    try:
        return open(name).read().strip()
    except OSError:
        return None

if a[:2] == ["pr", "view"]:
    repo = ref = None
    it = iter(a[2:])
    for t in it:
        if t in ("--repo", "-R"):
            repo = next(it)
        elif t == "--json":
            next(it)
        elif not t.startswith("-") and ref is None:
            ref = t
    m = re.fullmatch(r"https://github\.com/([^/]+/[^/]+)/pull/(\d+)", ref or "")
    if m:
        repo, ref = m.groups()
    repo = repo or os.environ.get("GH_REPO") or here(".fake-repo") or fail("not a git repository")
    R = W.get(repo) or fail("Could not resolve to a Repository: " + repo)
    ref = ref or here(".fake-branch") or fail("could not determine current branch")
    pr = next((p for p in R["prs"] if str(p["number"]) == ref or p["branch"] == ref), None)
    if not pr:
        fail('no pull requests found for branch "%s"' % ref)
    out({"url": "https://github.com/%s/pull/%d" % (repo, pr["number"]),
         "author": {"login": "dev"}, "reviewDecision": "", "state": "OPEN",
         "statusCheckRollup": pr["rollup"], "baseRefName": pr["base"], "headRefOid": pr["head"]})

if a[:1] == ["api"]:
    m = re.fullmatch(r"repos/([^/]+/[^/]+)/(.+)", a[1].split("?")[0]) or fail("bad path")
    R = W.get(m.group(1)) or fail("HTTP 404")
    path = m.group(2)
    if (p := re.fullmatch(r"pulls/(\d+)", path)):
        pr = next((x for x in R["prs"] if x["number"] == int(p.group(1))), None) or fail("HTTP 404")
        out({"base": {"ref": pr["base"], "repo": {"default_branch": R["default"]}},
             "head": {"sha": pr["head"]}, "merge_commit_sha": pr["merge"]})
    if (p := re.fullmatch(r"commits/(\w+)/statuses", path)):
        out(R["statuses"].get(p.group(1), []))
    if (p := re.fullmatch(r"git/commits/(\w+)", path)):
        c = R["commits"].get(p.group(1)) or fail("HTTP 404")
        out({"tree": {"sha": c["tree"]}, "parents": [{"sha": s} for s in c["parents"]]})
    if (p := re.fullmatch(r"git/ref/heads/(.+)", path)):
        out({"object": {"sha": R["tips"].get(p.group(1)) or fail("HTTP 404")}})
fail("fake gh: unknown call " + " ".join(a))
'''

BASE = "ليست الفرع الافتراضي"
TREE = "CI لم يفحص الشجرة"
RED = "فحوصٌ ليست خضراء"
UNREAD = "تعذّر قراءة الـPR"
PLAIN = "ليس أمراً صريحاً"


def check_merge(run) -> tuple[int, int, int]:
    root = tempfile.mkdtemp(prefix="toptech-guards-merge-")
    bindir, plat, lib = (os.path.join(root, d) for d in ("bin", "plat", "lib"))
    for d in (bindir, plat, lib):
        os.makedirs(d)
    gh = os.path.join(bindir, "gh")
    with open(gh, "w") as fh:
        fh.write(FAKE_GH)
    os.chmod(gh, os.stat(gh).st_mode | stat.S_IXUSR)
    world = os.path.join(root, "world.json")
    with open(world, "w") as fh:
        json.dump(WORLD, fh)
    for d, repo, branch in ((plat, "o/plat", "me/ok"), (lib, "o/lib", None)):
        with open(os.path.join(d, ".fake-repo"), "w") as fh:
            fh.write(repo)
        if branch:
            with open(os.path.join(d, ".fake-branch"), "w") as fh:
                fh.write(branch)
    env = {"PATH": bindir + os.pathsep + os.environ.get("PATH", ""), "FAKE_GH_WORLD": world}
    env_drop = {"GH_REPO": ""}            # بيئة المطوّر لا تُسرِّب مستودعاً للحالات

    def merge(cmd: str, cwd: str = plat) -> str:
        out = run("guard_bash.py", {"cwd": cwd, "tool_input": {"command": cmd}}, {**env, **env_drop})
        return json.loads(out)["hookSpecificOutput"]["permissionDecisionReason"] if out else ""

    url = "https://github.com/o/{}/pull/{}".format
    cases = [
        # ── (أ) القاعدة غير الافتراضية ──────────────────────────────────
        ("قاعدةٌ غير الافتراضي (tenders#656)", merge("gh pr merge 8 --merge"), BASE),
        ("قاعدةٌ غير main في مستودعٍ افتراضيُّه main", merge(f"gh pr merge {url('lib', 5)}"), BASE),
        ("قاعدةُ main في مستودعٍ افتراضيُّه main — يمرّ", merge(f"gh pr merge {url('lib', 6)}"), None),
        # ── (ب) شجرةٌ لم يفحصها CI ──────────────────────────────────────
        ("كل شيءٍ أخضر والشجرة مختومة — يمرّ", merge("gh pr merge 5 --merge"), None),
        ("الدمج التجريبي على قاعدةٍ قديمة (0138 · tenders#676)", merge("gh pr merge 6 --merge"), TREE),
        ("GitHub أعاد الدمج على القاعدة الحالية ولم يُعَد CI", merge("gh pr merge 7"), TREE),
        ("ختمٌ مطابق من غير github-actions لا يشهد", merge("gh pr merge 9"), TREE),
        ("الدمج التجريبي لرأسٍ أقدم", merge("gh pr merge 10"), TREE),
        ("لا دمج تجريبي (تعارض) والمستودع يختم", merge("gh pr merge 11"), TREE),
        ("مستودعٌ لا يختم — لا رأي، يمرّ", merge(f"gh pr merge {url('lib', 6)}"), None),
        ("فحصٌ أحمر يسبق كلَّ شيء", merge("gh pr merge 12"), RED),
        # ── المستودع كما يقرؤه gh لا مجلّد الجلسة (#3) ──────────────────
        # ‼ الرقم نفسه بحكمين: o/plat#5 يمرّ وo/lib#5 يُمنع، والعكس في #6
        ("الرابط إلى مستودعٍ آخر يُقرأ هو (lib#5)", merge(f"gh pr merge {url('lib', 5)} --squash"), BASE),
        ("‏-R إلى مستودعٍ آخر (lib#5 لا plat#5)", merge("gh pr merge 5 -R o/lib --merge"), BASE),
        ("‏--repo= بعد الأعلام (lib#6 لا plat#6) — يمرّ", merge("gh pr merge --squash -t عنوان 6 --repo=o/lib"), None),
        ("‏-Ro/lib ملتصقاً (lib#6) — يمرّ", merge("gh pr merge 6 -Ro/lib"), None),
        ("GH_REPO قبل الأمر (lib#6) — يمرّ", merge("GH_REPO=o/lib gh pr merge 6 --merge"), None),
        ("cd إلى مستودعٍ آخر ثم اسم فرعه — يمرّ", merge(f"cd {lib} && gh pr merge me/lib-six --merge"), None),
        ("الرقم بلا -R من مجلّد الجلسة (plat#6)", merge("gh pr merge 6 --merge"), TREE),
        ("بلا مرجع: فرعُ المجلّد الحالي (plat me/ok) — يمرّ", merge("gh pr merge --merge"), None),
        ("الجلسة في lib والرابط إلى plat#6", merge(f"gh pr merge {url('plat', 6)}", cwd=lib), TREE),
        ("فرعٌ لا PR له في مستودع الأمر — يُمنع", merge("gh pr merge me/lib-six"), UNREAD),
        # ‼ مقتبساً لا يُخمَّن: فرعُ الجلسة (plat me/ok) أخضر، والمدموج lib#5
        ("الدمج داخل ssh مقتبساً — لا يُحكم على فرع الجلسة",
         merge('ssh nas "gh pr merge 5 -R o/lib"'), PLAIN),
    ]
    b = p = f = 0
    for desc, reason, want in cases:
        ok = (not reason) if want is None else (want in reason)
        print(f"  {'✔' if ok else '✘'} {'مُنع' if reason else 'مرّ '}  {desc}")
        if not ok:
            f += 1
            print(f"       المتوقّع: {'مرور' if want is None else 'منع بـ«' + want + '»'}"
                  f"\n       الفعلي: {reason.splitlines()[0] if reason else 'مرور'}")
        elif want is None:
            p += 1
        else:
            b += 1
    return b, p, f
