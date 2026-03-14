# SOP三优研究记录

- Date: 2026-02-17
- SOP: `resources/sop/2026-02/2026-02-17-web3-wallet-key-management-sop.md`
- SOP Name: 钱包与密钥管理
- Search SOP Tool: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP Tool: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- External evidence pack: `resources/sop/2026-02/2026-02-17-internet-web3-sop-toolchain-research-pack.md`
- Scorecard: `resources/sop/2026-02/2026-02-17-web3-wallet-key-management-scorecard.md`

## External Sources Used
- Safe Docs: https://help.safe.global/en/
- NIST Key Management (SP 800-57): https://csrc.nist.gov/pubs/sp/800/57/pt1/r5/final
- NIST SSDF: https://csrc.nist.gov/pubs/sp/800/218/final

## Internal Evidence Used
- SOP Factory standard: `agent/patterns/sop-factory.md`
- Strict validator: `scripts/validate_sop_factory.py`
- Scorecard weighted selection: Winner A=4.55, runner-up=3.70, margin=0.85

## Three-Optimal Conclusion
- 最佳实践: 私钥管理必须去单点化并可演练恢复。
- 最佳方法: 权限分层 -> 多签审批 -> 周期轮换 -> 应急演练。
- 最佳工具: Safe多签 + HSM/硬件钱包 + 密钥审计台账。

## SOP Upgrade Applied
1. 将三优结论写入 Principle Compliance Declaration 与 Three-Optimal Decision。
2. 绑定风险-证据矩阵、Kill Switch、双轨指标与自动降级门禁。
3. 生成 L0/L1 检索层并写回 Links。
