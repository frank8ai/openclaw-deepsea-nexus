# SOP三优研究记录

- Date: 2026-02-17
- SOP: `resources/sop/2026-02/2026-02-17-sop-factory-production-sop.md`
- SOP Name: SOP Factory Production
- Search SOP Tool: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP Tool: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- External evidence pack: `resources/sop/2026-02/2026-02-17-sop-toolchain-research-pack.md`
- Scorecard: `resources/sop/2026-02/2026-02-17-sop-factory-production-scorecard.md`

## External Sources Used
- PRISMA 2020: https://www.bmj.com/content/372/bmj.n71
- PRISMA-S: https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z
- NIST Information Quality: https://www.nist.gov/director/nist-information-quality-standards
- Diataxis: https://diataxis.fr/
- DORA: https://dora.dev/

## Internal Evidence Used
- Best Practice evidence rows: Non-compensatory standard stack <- `agent/patterns/sop-factory.md`；Mandatory hard gates and release checks <- `resources/sop/TEMPLATE.sop.md`；Strict machine validation with R/E mapping <- `scripts/validate_sop_factory.py`
- Best Method score: Winner B=4.55, Runner-up=3.80, Margin=0.75, Hard constraints=passed
- Best Tool evidence: gain[Markdown templates:>=30% drafting consistency gain；`validate_sop_factory.py --strict`:>=40% reduction in gate-miss defects；`rg`:>=30% reduction in manual review time], rollback[Markdown templates->keep custom notes in appendix；`validate_sop_factory.py --strict`->keep draft mode until pilot is complete；`rg`->manual section-by-section review]

## Three-Optimal Conclusion
- 最佳实践: non-compensatory standard stack with explicit hard-gate release policy.
- 最佳方法: six-step factory pipeline (classify -> baseline -> scorecard -> author -> pilot -> iterate).
- 最佳工具: markdown templates, strict validator, and `rg` checks for completeness and references.

## SOP Upgrade Applied
1. 三优结论回写到 Principle Compliance Declaration。
2. 三优研究段落写入 SOP 主体并挂研究记录路径。
3. 绑定 Search/Research 工具SOP与外部证据包，形成可追溯闭环。
