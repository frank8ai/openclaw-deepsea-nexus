# SOP三优研究记录

- Date: 2026-02-17
- SOP: `resources/sop/2026-02/2026-02-17-p1-home-maintenance-sop.md`
- SOP Name: 家务与周期维护
- Search SOP Tool: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP Tool: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- External evidence pack: `resources/sop/2026-02/2026-02-17-sop-toolchain-research-pack.md`
- Scorecard: `resources/sop/2026-02/2026-02-17-p1-home-maintenance-scorecard.md`

## External Sources Used
- PRISMA 2020: https://www.bmj.com/content/372/bmj.n71
- PRISMA-S: https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z
- NIST Information Quality: https://www.nist.gov/director/nist-information-quality-standards
- Diataxis: https://diataxis.fr/
- DORA: https://dora.dev/

## Internal Evidence Used
- Best Practice evidence rows: 简洁可维护原则 <- SOP_PRINCIPLES.md；周期任务机制 <- agent/patterns/sop-factory.md；严格校验 <- scripts/validate_sop_factory.py
- Best Method score: Winner B=4.40, Runner-up=3.80, Margin=0.60, Hard constraints=passed
- Best Tool evidence: gain[周期清单:漏项率下降 >=30%；固定窗口日历:完成率提升 >=25%；维护记录表:复发问题下降 >=20%], rollback[周期清单->月度刷新；固定窗口日历->预留备选窗口；维护记录表->最小字段强制]

## Three-Optimal Conclusion
- 最佳实践: 周期化和可视化优先
- 最佳方法: 固定窗口执行+完成后记录
- 最佳工具: 周期清单+日历提醒+维护记录

## SOP Upgrade Applied
1. 三优结论回写到 Principle Compliance Declaration。
2. 三优研究段落写入 SOP 主体并挂研究记录路径。
3. 绑定 Search/Research 工具SOP与外部证据包，形成可追溯闭环。
