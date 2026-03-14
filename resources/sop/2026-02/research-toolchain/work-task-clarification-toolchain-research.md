# SOP三优研究记录

- Date: 2026-02-17
- SOP: `resources/sop/2026-02/2026-02-17-work-task-clarification-sop.md`
- SOP Name: 工作任务澄清与成功标准
- Search SOP Tool: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP Tool: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- External evidence pack: `resources/sop/2026-02/2026-02-17-sop-toolchain-research-pack.md`
- Scorecard: `resources/sop/2026-02/2026-02-17-work-task-clarification-scorecard.md`

## External Sources Used
- PRISMA 2020: https://www.bmj.com/content/372/bmj.n71
- PRISMA-S: https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z
- NIST Information Quality: https://www.nist.gov/director/nist-information-quality-standards
- Scrum Guide: https://scrumguides.org/scrum-guide.html
- DORA: https://dora.dev/

## Internal Evidence Used
- Best Practice evidence rows: 目标先行且可量化 <- SOP_PRINCIPLES.md；必填约束与非目标 <- resources/sop/TEMPLATE.sop.md；strict release gate <- scripts/validate_sop_factory.py
- Best Method score: Winner B=4.40, Runner-up=3.80, Margin=0.60, Hard constraints=passed
- Best Tool evidence: gain[澄清卡模板:返工率下降 >=30%；strict validator:漏项率下降 >=40%；issue 看板:状态可见性提升 >=30%], rollback[澄清卡模板->增加备注区；strict validator->草稿先宽后严；issue 看板->每日收盘更新]

## Three-Optimal Conclusion
- 最佳实践: 先定义目标与验收，再进入执行，禁止“边做边猜”
- 最佳方法: 双轮澄清（首轮提取目标/约束，二轮复述确认并冻结MVP边界）
- 最佳工具: 任务澄清卡 + 必填字段检查 + strict validator

## SOP Upgrade Applied
1. 三优结论回写到 Principle Compliance Declaration。
2. 三优研究段落写入 SOP 主体并挂研究记录路径。
3. 绑定 Search/Research 工具SOP与外部证据包，形成可追溯闭环。
