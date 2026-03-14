# SOP三优研究记录

- Date: 2026-02-17
- SOP: `resources/sop/2026-02/2026-02-17-internet-requirements-review-acceptance-sop.md`
- SOP Name: 需求评审与验收标准
- Search SOP Tool: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP Tool: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- External evidence pack: `resources/sop/2026-02/2026-02-17-internet-web3-sop-toolchain-research-pack.md`
- Scorecard: `resources/sop/2026-02/2026-02-17-internet-requirements-review-acceptance-scorecard.md`

## External Sources Used
- PRISMA 2020: https://www.bmj.com/content/372/bmj.n71
- NIST Information Quality: https://www.nist.gov/director/nist-information-quality-standards
- NIST SSDF: https://csrc.nist.gov/pubs/sp/800/218/final

## Internal Evidence Used
- SOP Factory standard: `agent/patterns/sop-factory.md`
- Strict validator: `scripts/validate_sop_factory.py`
- Scorecard weighted selection: Winner A=4.55, runner-up=3.70, margin=0.85

## Three-Optimal Conclusion
- 最佳实践: 需求评审必须绑定验收用例与不可协商约束。
- 最佳方法: 三段评审（需求澄清 -> 约束核对 -> 验收走查）。
- 最佳工具: PRD模板 + 验收用例模板 + 评审看板。

## SOP Upgrade Applied
1. 将三优结论写入 Principle Compliance Declaration 与 Three-Optimal Decision。
2. 绑定风险-证据矩阵、Kill Switch、双轨指标与自动降级门禁。
3. 生成 L0/L1 检索层并写回 Links。
