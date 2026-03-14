# SOP三优研究记录

- Date: 2026-02-17
- SOP: `resources/sop/2026-02/2026-02-17-p2-decision-multi-model-sop.md`
- SOP Name: 复杂决策与多模型评估
- Search SOP Tool: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP Tool: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- External evidence pack: `resources/sop/2026-02/2026-02-17-sop-toolchain-research-pack.md`
- Scorecard: `resources/sop/2026-02/2026-02-17-p2-decision-multi-model-scorecard.md`

## External Sources Used
- PRISMA 2020: https://www.bmj.com/content/372/bmj.n71
- PRISMA-S: https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z
- NIST Information Quality: https://www.nist.gov/director/nist-information-quality-standards
- CEBM levels: https://www.cebm.ox.ac.uk/resources/levels-of-evidence/explanation-of-the-2011-ocebm-levels-of-evidence
- Stanford lateral reading: https://ed.stanford.edu/news/stanford-scholars-observe-experts-see-how-they-evaluate-credibility-information-online

## Internal Evidence Used
- Best Practice evidence rows: 证据强度随风险升级 <- SOP_PRINCIPLES.md；Decision Card门禁 <- resources/decisions/TEMPLATE.decision-card.md；strict校验 <- scripts/validate_sop_factory.py
- Best Method score: Winner B=4.40, Runner-up=3.80, Margin=0.60, Hard constraints=passed
- Best Tool evidence: gain[决策卡模板:漏项率下降 >=30%；多模型对比表:风险识别率提升 >=25%；风险矩阵:止损速度提升 >=20%], rollback[决策卡模板->精简字段；多模型对比表->双人复核；风险矩阵->周期校准]

## Three-Optimal Conclusion
- 最佳实践: 高影响决策必须多模型交叉
- 最佳方法: 三模型对比+风险矩阵+止损线
- 最佳工具: 决策卡+对比表+风险矩阵

## SOP Upgrade Applied
1. 三优结论回写到 Principle Compliance Declaration。
2. 三优研究段落写入 SOP 主体并挂研究记录路径。
3. 绑定 Search/Research 工具SOP与外部证据包，形成可追溯闭环。
