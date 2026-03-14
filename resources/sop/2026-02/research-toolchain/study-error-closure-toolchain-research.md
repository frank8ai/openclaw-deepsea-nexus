# SOP三优研究记录

- Date: 2026-02-17
- SOP: `resources/sop/2026-02/2026-02-17-study-error-closure-sop.md`
- SOP Name: 学习错题与薄弱点闭环
- Search SOP Tool: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP Tool: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- External evidence pack: `resources/sop/2026-02/2026-02-17-sop-toolchain-research-pack.md`
- Scorecard: `resources/sop/2026-02/2026-02-17-study-error-closure-scorecard.md`

## External Sources Used
- PRISMA 2020: https://www.bmj.com/content/372/bmj.n71
- PRISMA-S: https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z
- NIST Information Quality: https://www.nist.gov/director/nist-information-quality-standards
- Retrieval practice: https://pubmed.ncbi.nlm.nih.gov/16719566/
- Spacing effect: https://pubmed.ncbi.nlm.nih.gov/16507066/
- Learning techniques review: https://pubmed.ncbi.nlm.nih.gov/26173288/

## Internal Evidence Used
- Best Practice evidence rows: 根因联动 <- SOP_PRINCIPLES.md；错误闭环记录 <- agent/patterns/sop-factory.md；学习技术证据 <- https://pubmed.ncbi.nlm.nih.gov/26173288/
- Best Method score: Winner B=4.40, Runner-up=3.80, Margin=0.60, Hard constraints=passed
- Best Tool evidence: gain[错题本模板:漏记率下降 >=30%；根因标签:复发率下降 >=20%；复测清单:修复率提升 >=25%], rollback[错题本模板->最小字段；根因标签->每周校准；复测清单->固定窗口]

## Three-Optimal Conclusion
- 最佳实践: 错误按根因分类，优先处理高频高影响错误
- 最佳方法: 错因分桶 -> 定向修复 -> 再测闭环
- 最佳工具: 错题本 + 根因标签 + 复测清单

## SOP Upgrade Applied
1. 三优结论回写到 Principle Compliance Declaration。
2. 三优研究段落写入 SOP 主体并挂研究记录路径。
3. 绑定 Search/Research 工具SOP与外部证据包，形成可追溯闭环。
