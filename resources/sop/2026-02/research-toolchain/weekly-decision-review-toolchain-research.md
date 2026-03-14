# SOP三优研究记录

- Date: 2026-02-17
- SOP: `resources/sop/2026-02/2026-02-17-weekly-decision-review-sop.md`
- SOP Name: Weekly Decision Review and Rule Update
- Search SOP Tool: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP Tool: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- External evidence pack: `resources/sop/2026-02/2026-02-17-sop-toolchain-research-pack.md`
- Scorecard: `resources/sop/2026-02/2026-02-17-weekly-decision-review-scorecard.md`

## External Sources Used
- PRISMA 2020: https://www.bmj.com/content/372/bmj.n71
- PRISMA-S: https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z
- NIST Information Quality: https://www.nist.gov/director/nist-information-quality-standards
- CEBM levels: https://www.cebm.ox.ac.uk/resources/levels-of-evidence/explanation-of-the-2011-ocebm-levels-of-evidence
- Stanford lateral reading: https://ed.stanford.edu/news/stanford-scholars-observe-experts-see-how-they-evaluate-credibility-information-online

## Internal Evidence Used
- Best Practice evidence rows: Hard gate before execution <- internal decision card runs；Limit rule updates to 1-3 <- internal weekly reviews；Threshold-based triggers <- internal model cards
- Best Method score: Winner A=4.15, Runner-up=3.30, Margin=0.85, Hard constraints=passed
- Best Tool evidence: gain[Markdown templates:immediate standardization；`rg`:fast presence checks；`git`:auditable iteration history], rollback[Markdown templates->keep template strict and reviewed；`rg`->fallback to manual checklist；`git`->branch per cycle]

## Three-Optimal Conclusion
- 最佳实践: hard-gated checklist review with explicit pass/fail.
- 最佳方法: batch review by threshold filters then 3-model comparison.
- 最佳工具: markdown templates plus `rg` for fast field validation.

## SOP Upgrade Applied
1. 三优结论回写到 Principle Compliance Declaration。
2. 三优研究段落写入 SOP 主体并挂研究记录路径。
3. 绑定 Search/Research 工具SOP与外部证据包，形成可追溯闭环。
