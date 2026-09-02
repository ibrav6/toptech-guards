# toptech-guards

الطبقة التي كانت ناقصة: **إنفاذٌ آلي** لقواعد كانت مكتوبةً ولم تمنع
شيئاً. الدستور نفسه في [`CONSTITUTION.md`](CONSTITUTION.md) — يُحقن في
كل جلسة عند بدئها، ولا يُنسخ إلى المشاريع. الشرح الكامل في
[`docs/DEV_ENVIRONMENT.md`](../../docs/DEV_ENVIRONMENT.md).

```bash
claude plugin marketplace add ibrav6/toptech-guards --scope project
claude plugin install toptech-guards@toptech
python3 test_guards.py        # يطبع عدد ما مُنع وما مرّ — لا يُكتب هنا بيد
```

**خصوصيّة المشروع في ملفه** `.claude/toptech-guards.json` (مسارات الإنتاج ·
أداة النشر · المالك · هل تُشترط موافقته على PR غيره) — الـplugin عامٌّ ولا
يحمل مساراً ولا عنواناً. الصيغة في README الجذر.

| السكربت | متى | يفعل |
|---|---|---|
| `session_start.py` | بدء الجلسة | يحقن الدستور وسطر الحالة: الفرع · المعلّق وعمره · مقابل `origin/master` · وسم `production` |
| `guard_bash.py` | قبل كل أمر Bash | يمنع: دهس الإنتاج · `DELETE`/`DROP` بلا شرط · `rm -rf` · `push --force` · **الدفع إلى `master`** · **تحريك وسم `production` بيد** · **`gh pr merge` بلا فحوصٍ خضراء وموافقة** · **سرٌّ عبر heredoc/إعادة توجيه** |
| `guard_write.py` | قبل Write/Edit | يمنع كتابة سرٍّ في ملف — **قبل** أن يصل git |
| `remind_docs.py` | قبل Write/Edit | **لا يمنع** — يحقن الوثيقة الحاكمة لحظة لمس مسارٍ محروس (`.claude/guarded-paths.json` في المشروع) |

**حماية `master` مشعَلةٌ افتراضياً منذ 2026-09-02** (مسار PR هو المسار).
للإطفاء في حالةٍ مقصودة: `TOPTECH_PROTECT_MASTER=0`. وموافقة المالك على PR
غيره تُشترط فقط إن قال عقد المشروع `"require_approval": true`.

**ولا تُضاف قاعدة بلا حادثةٍ مقيسة** — الحارس الذي يمنع ما لم يقع
يُطفأ في أسبوع، فيصير غيابه أسوأ من عدمه لأنه وَعَد. ولكل قاعدة حالتان
في `test_guards.py`: واحدة تُرى تمنع وواحدة تُرى تسمح.
