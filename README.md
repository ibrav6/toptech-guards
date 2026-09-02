# toptech-guards

حرّاس ودستور قسم التطوير في قمم التقنية — plugin لـClaude Code، **عامٌّ
ليصل كل مطوّرٍ بلا صلاحية، ولا يكتب فيه إلا المالك.** لا أسرار هنا ولا
مسارات: خصوصيّة كل مشروع في ملفه هو.

## التثبيت في مشروع

`.claude/settings.json` في جذر المستودع:

```json
{
  "extraKnownMarketplaces": {
    "toptech": { "source": { "source": "github", "repo": "ibrav6/toptech-guards" } }
  },
  "enabledPlugins": { "toptech-guards@toptech": true }
}
```

ثم `.claude/toptech-guards.json` بما يخصّ المشروع:

```json
{
  "production_paths": ["/srv/app"],
  "deploy_tools": ["deploy.py"],
  "owner": "github-login",
  "require_approval": false
}
```

و`.claude/guarded-paths.json` لربط المسارات بوثائقها الحاكمة (اختياري).
بلا الملفين تعمل الحرّاس العامّة (الحذف · القاعدة · `master` · الوسم ·
الأسرار) ويصمت ما يخصّ الإنتاج.

## ما فيه

| | |
|---|---|
| [`CONSTITUTION.md`](plugins/toptech-guards/CONSTITUTION.md) | الدستور: ستّ قواعد ولكلٍّ آلة — يُحقن عند بدء كل جلسة |
| [`plugins/toptech-guards/`](plugins/toptech-guards/) | الـhooks وفحصها: `python3 plugins/toptech-guards/test_guards.py` |

الشرح والقياسات في مستودع `toptech.dev` (خاصّ): `docs/DEV_ENVIRONMENT.md`.
