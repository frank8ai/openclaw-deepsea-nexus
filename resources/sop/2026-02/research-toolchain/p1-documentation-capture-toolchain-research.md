# SOP三优研究记录

- Date: 2026-02-17
- SOP: `resources/sop/2026-02/2026-02-17-p1-documentation-capture-sop.md`
- SOP Name: 文档沉淀与知识归档
- Search SOP Tool: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP Tool: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- External evidence pack: `resources/sop/2026-02/2026-02-17-sop-toolchain-research-pack.md`
- Scorecard: `resources/sop/2026-02/2026-02-17-p1-documentation-capture-scorecard.md`

## External Sources Used
- PRISMA 2020: https://www.bmj.com/content/372/bmj.n71
- PRISMA-S: https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z
- NIST Information Quality: https://www.nist.gov/director/nist-information-quality-standards
- Diataxis: https://diataxis.fr/
- DORA: https://dora.dev/

## Internal Evidence Used
- Best Practice evidence rows: Link over paste <- SOP_PRINCIPLES.md；模板化沉淀 <- resources/sop/TEMPLATE.sop.md；严格路径校验 <- scripts/validate_sop_factory.py
- Best Method score: Winner B=4.40, Runner-up=3.80, Margin=0.60, Hard constraints=passed
- Best Tool evidence: gain[沉淀模板:复用率提升 >=30%；标签规范:检索命中率提升 >=25%；路径校验脚本:失链率下降 >=30%], rollback[沉淀模板->增加自由备注区；标签规范->标签白名单；路径校验脚本->发布前强制校验]

## Three-Optimal Conclusion
- 最佳实践: 决策后快速沉淀并链接原始证据
- 最佳方法: 模板化记录+标签索引+定期清理
- 最佳工具: 沉淀模板+标签规范+路径校验

## SOP Upgrade Applied
1. 三优结论回写到 Principle Compliance Declaration。
2. 三优研究段落写入 SOP 主体并挂研究记录路径。
3. 绑定 Search/Research 工具SOP与外部证据包，形成可追溯闭环。
