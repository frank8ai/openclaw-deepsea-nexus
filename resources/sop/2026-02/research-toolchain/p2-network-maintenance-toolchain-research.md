# SOP三优研究记录

- Date: 2026-02-17
- SOP: `resources/sop/2026-02/2026-02-17-p2-network-maintenance-sop.md`
- SOP Name: 人脉维护与周期触达
- Search SOP Tool: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP Tool: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- External evidence pack: `resources/sop/2026-02/2026-02-17-sop-toolchain-research-pack.md`
- Scorecard: `resources/sop/2026-02/2026-02-17-p2-network-maintenance-scorecard.md`

## External Sources Used
- PRISMA 2020: https://www.bmj.com/content/372/bmj.n71
- PRISMA-S: https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z
- NIST Information Quality: https://www.nist.gov/director/nist-information-quality-standards
- Diataxis: https://diataxis.fr/
- DORA: https://dora.dev/

## Internal Evidence Used
- Best Practice evidence rows: 结果价值优先 <- SOP_PRINCIPLES.md；小步迭代 <- agent/patterns/sop-factory.md；strict校验 <- scripts/validate_sop_factory.py
- Best Method score: Winner B=4.40, Runner-up=3.80, Margin=0.60, Hard constraints=passed
- Best Tool evidence: gain[关系分层清单:触达命中率提升 >=30%；触达节奏表:漏触达率下降 >=25%；触达记录卡:跟进质量提升 >=20%], rollback[关系分层清单->季度复核分层；触达节奏表->允许弹性窗口；触达记录卡->最小字段记录]

## Three-Optimal Conclusion
- 最佳实践: 先关键后泛化，触达后必须记录
- 最佳方法: 分层名单+周期触达+复盘
- 最佳工具: 分层清单+节奏表+触达记录卡

## SOP Upgrade Applied
1. 三优结论回写到 Principle Compliance Declaration。
2. 三优研究段落写入 SOP 主体并挂研究记录路径。
3. 绑定 Search/Research 工具SOP与外部证据包，形成可追溯闭环。
