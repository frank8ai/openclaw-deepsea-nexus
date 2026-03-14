# SOP三优研究记录

- Date: 2026-02-17
- SOP: `resources/sop/2026-02/2026-02-17-p1-project-kickoff-sop.md`
- SOP Name: 项目启动与范围风险对齐
- Search SOP Tool: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP Tool: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- External evidence pack: `resources/sop/2026-02/2026-02-17-sop-toolchain-research-pack.md`
- Scorecard: `resources/sop/2026-02/2026-02-17-p1-project-kickoff-scorecard.md`

## External Sources Used
- PRISMA 2020: https://www.bmj.com/content/372/bmj.n71
- PRISMA-S: https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z
- NIST Information Quality: https://www.nist.gov/director/nist-information-quality-standards
- Diataxis: https://diataxis.fr/
- DORA: https://dora.dev/

## Internal Evidence Used
- Best Practice evidence rows: 非可协商约束优先 <- SOP_PRINCIPLES.md；基线与门禁 <- agent/patterns/sop-factory.md；strict门禁 <- scripts/validate_sop_factory.py
- Best Method score: Winner B=4.40, Runner-up=3.80, Margin=0.60, Hard constraints=passed
- Best Tool evidence: gain[启动清单模板:漏项率下降 >=30%；风险矩阵:重大风险提前发现 >=25%；依赖图:延误预警提前 >=20%], rollback[启动清单模板->核心字段优先；风险矩阵->双人复核；依赖图->周更新一次]

## Three-Optimal Conclusion
- 最佳实践: 启动前先对齐范围风险依赖
- 最佳方法: 启动会+清单化评审+门禁通过
- 最佳工具: 启动模板+风险矩阵+依赖图

## SOP Upgrade Applied
1. 三优结论回写到 Principle Compliance Declaration。
2. 三优研究段落写入 SOP 主体并挂研究记录路径。
3. 绑定 Search/Research 工具SOP与外部证据包，形成可追溯闭环。
