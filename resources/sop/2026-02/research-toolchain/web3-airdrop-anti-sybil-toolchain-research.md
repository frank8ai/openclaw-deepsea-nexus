# SOP三优研究记录

- Date: 2026-02-17
- SOP: `resources/sop/2026-02/2026-02-17-web3-airdrop-anti-sybil-sop.md`
- SOP Name: 空投与活动反作弊
- Search SOP Tool: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP Tool: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- External evidence pack: `resources/sop/2026-02/2026-02-17-internet-web3-sop-toolchain-research-pack.md`
- Scorecard: `resources/sop/2026-02/2026-02-17-web3-airdrop-anti-sybil-scorecard.md`

## External Sources Used
- Gitcoin Passport Docs: https://docs.passport.xyz/
- NIST Information Quality: https://www.nist.gov/director/nist-information-quality-standards
- PRISMA-S: https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z

## Internal Evidence Used
- SOP Factory standard: `agent/patterns/sop-factory.md`
- Strict validator: `scripts/validate_sop_factory.py`
- Scorecard weighted selection: Winner A=4.55, runner-up=3.70, margin=0.85

## Three-Optimal Conclusion
- 最佳实践: 空投执行前必须完成反女巫检测并保留申诉通道。
- 最佳方法: 规则检测 -> 风险分层 -> 冻结复核 -> 申诉复审。
- 最佳工具: 女巫检测规则引擎 + 地址标签库 + 申诉工单系统。

## SOP Upgrade Applied
1. 将三优结论写入 Principle Compliance Declaration 与 Three-Optimal Decision。
2. 绑定风险-证据矩阵、Kill Switch、双轨指标与自动降级门禁。
3. 生成 L0/L1 检索层并写回 Links。
