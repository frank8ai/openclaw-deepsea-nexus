# SOP三优研究记录

- Date: 2026-02-17
- SOP: `resources/sop/2026-02/2026-02-17-web3-onchain-monitoring-alerting-sop.md`
- SOP Name: 链上数据监控与告警
- Search SOP Tool: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP Tool: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- External evidence pack: `resources/sop/2026-02/2026-02-17-internet-web3-sop-toolchain-research-pack.md`
- Scorecard: `resources/sop/2026-02/2026-02-17-web3-onchain-monitoring-alerting-scorecard.md`

## External Sources Used
- OpenZeppelin Defender Monitor: https://docs.openzeppelin.com/defender/monitor
- Chainlink Data Feeds: https://docs.chain.link/data-feeds
- NIST Incident Handling: https://csrc.nist.gov/pubs/sp/800/61/r2/final

## Internal Evidence Used
- SOP Factory standard: `agent/patterns/sop-factory.md`
- Strict validator: `scripts/validate_sop_factory.py`
- Scorecard weighted selection: Winner A=4.55, runner-up=3.70, margin=0.85

## Three-Optimal Conclusion
- 最佳实践: 监控阈值必须可量化并绑定响应动作。
- 最佳方法: 指标分层 -> 阈值设置 -> 告警分级 -> 周期调优。
- 最佳工具: 链上索引平台 + 告警编排 + 值班SOP。

## SOP Upgrade Applied
1. 将三优结论写入 Principle Compliance Declaration 与 Three-Optimal Decision。
2. 绑定风险-证据矩阵、Kill Switch、双轨指标与自动降级门禁。
3. 生成 L0/L1 检索层并写回 Links。
