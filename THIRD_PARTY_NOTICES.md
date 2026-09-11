# Third party notices

## MathModel-Skill formula conversion

- Upstream: https://github.com/yushui2022/MathModel-Skill
- Commit: `0cc261d90d21e4ed540b02b0c71018cdcd47af58`
- Source: `packages/codex/.agents/skills/paper-formal-writer/scripts/formula_omml.py`
- Local copy: [scripts/vendor/formula_omml.py](scripts/vendor/formula_omml.py)
- License: [MIT, Copyright (c) 2026 yushui2022](scripts/vendor/LICENSE.MathModel-Skill)
- Modifications: none.
- SHA-256: `79d8610cc60364c22b611736333d1506ccfe01a590cbe3746258dbf027d1840a`

The upstream source is retained as an isolated helper. The rest of its runtime and platform bundles are not vendored. Authoring contracts, build freshness and rendering checks informed the integration; this repository implements its own adapters to its existing workflow.

Optional dependencies retain their respective licenses. No API keys, private prompts, contest statements or real paper outputs are bundled.
