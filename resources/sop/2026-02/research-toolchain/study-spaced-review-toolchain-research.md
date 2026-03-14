# SOP三优研究记录

- Date: 2026-02-17
- SOP: `resources/sop/2026-02/2026-02-17-study-spaced-review-sop.md`
- SOP Name: 学习间隔复习
- Search SOP Tool: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP Tool: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- External evidence pack: `resources/sop/2026-02/2026-02-17-sop-toolchain-research-pack.md`
- Scorecard: `resources/sop/2026-02/2026-02-17-study-spaced-review-scorecard.md`

## External Sources Used
- PRISMA 2020: https://www.bmj.com/content/372/bmj.n71
- PRISMA-S: https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z
- NIST Information Quality: https://www.nist.gov/director/nist-information-quality-standards
- Retrieval practice: https://pubmed.ncbi.nlm.nih.gov/16719566/
- Spacing effect: https://pubmed.ncbi.nlm.nih.gov/16507066/
- Learning techniques review: https://pubmed.ncbi.nlm.nih.gov/26173288/

## Internal Evidence Used
- Best Practice evidence rows: Spacing effect <- https://pubmed.ncbi.nlm.nih.gov/16507066/；阈值化调整 <- SOP_PRINCIPLES.md；规则回写 <- agent/patterns/sop-factory.md
- Best Method score: Winner B=4.40, Runner-up=3.80, Margin=0.60, Hard constraints=passed
- Best Tool evidence: gain[复习队列:漏复习率下降 >=30%；间隔规则表:保持率提升 >=20%；结果日志:调参速度提升 >=25%], rollback[复习队列->每周清理；间隔规则表->退回基础间隔；结果日志->最小字段强制]

## Three-Optimal Conclusion
- 最佳实践: 间隔复习优先，按遗忘曲线安排回看节奏
- 最佳方法: 固定间隔+阈值自适应（低分缩短间隔）
- 最佳工具: 复习队列 + 间隔规则表 + 结果日志

## SOP Upgrade Applied
1. 三优结论回写到 Principle Compliance Declaration。
2. 三优研究段落写入 SOP 主体并挂研究记录路径。
3. 绑定 Search/Research 工具SOP与外部证据包，形成可追溯闭环。
