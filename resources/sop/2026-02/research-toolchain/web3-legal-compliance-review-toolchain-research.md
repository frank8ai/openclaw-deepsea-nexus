# SOP三优研究记录

- Date: 2026-02-17
- SOP: `resources/sop/2026-02/2026-02-17-web3-legal-compliance-review-sop.md`
- SOP Name: 法务合规审查（Web3）
- Search SOP Tool: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP Tool: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- External evidence pack: `resources/sop/2026-02/2026-02-17-internet-web3-sop-toolchain-research-pack.md`
- Scorecard: `resources/sop/2026-02/2026-02-17-web3-legal-compliance-review-scorecard.md`

## External Sources Used
- FATF Virtual Assets Guidance: https://www.fatf-gafi.org/en/publications/Fatfrecommendations/Guidance-rba-virtual-assets-2021.html
- OFAC Virtual Currency Sanctions Action: https://ofac.treasury.gov/recent-actions/20221011
- NIST SCRM: https://csrc.nist.gov/pubs/sp/800/161/r1/upd1/final

## Internal Evidence Used
- SOP Factory standard: `agent/patterns/sop-factory.md`
- Strict validator: `scripts/validate_sop_factory.py`
- Scorecard weighted selection: Winner A=4.55, runner-up=3.70, margin=0.85

## Three-Optimal Conclusion
- 最佳实践: 跨地区Web3业务必须先完成合规门禁再上线。
- 最佳方法: 地区映射 -> 规则判定 -> 合规审批 -> 发布复核。
- 最佳工具: 合规清单 + 规则引擎 + 审查台账。

## SOP Upgrade Applied
1. 将三优结论写入 Principle Compliance Declaration 与 Three-Optimal Decision。
2. 绑定风险-证据矩阵、Kill Switch、双轨指标与自动降级门禁。
3. 生成 L0/L1 检索层并写回 Links。
