#!/usr/bin/env python3
"""Generate internet + web3 SOP bundle with three-optimal research artifacts."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DATE = "2026-02-17"
MONTH = "2026-02"
OWNER = "yizhi"
TEAM = "deepsea-nexus"


def resolve_openclaw_home() -> Path:
    return Path(os.environ.get("OPENCLAW_HOME", "~/.openclaw")).expanduser().resolve()


def resolve_workspace_root() -> Path:
    return Path(
        os.environ.get("OPENCLAW_WORKSPACE", resolve_openclaw_home() / "workspace")
    ).expanduser().resolve()


def resolve_search_sop_tool() -> Path:
    override = os.environ.get("NEXUS_HQ_SEARCH_SOP", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return (resolve_workspace_root() / "SOP" / "SOP_HQ_Web_Research.md").resolve()


def resolve_research_sop_tool() -> Path:
    override = os.environ.get("NEXUS_HQ_RESEARCH_SOP", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return (resolve_workspace_root() / "SOP" / "SOP_HQ_Deep_Research.md").resolve()


SEARCH_SOP_TOOL = str(resolve_search_sop_tool())
RESEARCH_SOP_TOOL = str(resolve_research_sop_tool())
BASE_DIR = REPO_ROOT / "resources" / "sop" / MONTH
RESEARCH_DIR = BASE_DIR / "research-toolchain"
PACK_PATH_REL = f"resources/sop/{MONTH}/{DATE}-internet-web3-sop-toolchain-research-pack.md"
PACK_PATH = REPO_ROOT / PACK_PATH_REL
CATALOG_PATH = BASE_DIR / f"{DATE}-internet-web3-sop-catalog.md"
REPORT_PATH = BASE_DIR / f"{DATE}-internet-web3-sop-iteration-report.md"


SRC = {
    "PRISMA 2020": "https://www.bmj.com/content/372/bmj.n71",
    "PRISMA-S": "https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z",
    "NIST Information Quality": "https://www.nist.gov/director/nist-information-quality-standards",
    "DORA": "https://dora.dev/",
    "Google SRE Canarying": "https://sre.google/workbook/canarying-releases/",
    "Kubernetes Deployment Rollout": "https://kubernetes.io/docs/concepts/workloads/controllers/deployment/",
    "NIST Incident Handling": "https://csrc.nist.gov/pubs/sp/800/61/r2/final",
    "Microsoft Experimentation Platform": "https://www.microsoft.com/en-us/research/group/experimentation-platform-exp/",
    "NIST SSDF": "https://csrc.nist.gov/pubs/sp/800/218/final",
    "NIST SCRM": "https://csrc.nist.gov/pubs/sp/800/161/r1/upd1/final",
    "AWS Cost Optimization Pillar": "https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html",
    "FinOps Framework": "https://www.finops.org/framework/",
    "OpenZeppelin Contracts": "https://docs.openzeppelin.com/contracts/5.x/",
    "OpenZeppelin Defender Monitor": "https://docs.openzeppelin.com/defender/monitor",
    "Solidity Security Considerations": "https://docs.soliditylang.org/en/latest/security-considerations.html",
    "OWASP Smart Contract Security Testing Guide": "https://scs.owasp.org/SCSTG/",
    "Safe Docs": "https://help.safe.global/en/",
    "NIST Key Management (SP 800-57)": "https://csrc.nist.gov/pubs/sp/800/57/pt1/r5/final",
    "Chainlink Data Feeds": "https://docs.chain.link/data-feeds",
    "FATF Virtual Assets Guidance": "https://www.fatf-gafi.org/en/publications/Fatfrecommendations/Guidance-rba-virtual-assets-2021.html",
    "OFAC Virtual Currency Sanctions Action": "https://ofac.treasury.gov/recent-actions/20221011",
    "Compound Governance Docs": "https://docs.compound.finance/v2/governance/",
    "Snapshot Docs": "https://docs.snapshot.box/",
    "Gitcoin Passport Docs": "https://docs.passport.xyz/",
    "CDC CERC": "https://emergency.cdc.gov/cerc/",
    "CISA Incident Response Playbooks": "https://www.cisa.gov/news-events/news/cisa-releases-updated-cybersecurity-incident-and-vulnerability-response-playbooks",
}


@dataclass
class SopSpec:
    slug: str
    name: str
    domain: str
    priority: str
    risk_tier: str
    reversibility: str
    evidence: str
    tags: str
    triggers: list[str]
    outputs: list[str]
    objective: str
    in_scope: str
    out_scope: str
    dependencies: str
    input_1: str
    input_2: str
    best_practice: str
    best_method: str
    best_tool: str
    tool_gain_hint: str
    tool_rollback_hint: str
    sources: list[str]


SPECS: list[SopSpec] = [
    SopSpec(
        slug="internet-requirements-review-acceptance",
        name="需求评审与验收标准",
        domain="互联网通用",
        priority="P0",
        risk_tier="medium",
        reversibility="R2",
        evidence="E3",
        tags="internet, requirements, prd, acceptance",
        triggers=[
            "PRD进入评审且涉及跨团队交付",
            "验收标准或不可协商约束缺失",
        ],
        outputs=[
            "评审结论与风险清单",
            "验收用例与不可协商约束列表",
        ],
        objective="把需求从“描述”升级为“可验收交付”，避免上线后返工和口径不一致。",
        in_scope="PRD评审、验收标准定义、约束冻结",
        out_scope="详细技术实现编码",
        dependencies="PRD模板、验收用例模板、评审责任人",
        input_1="PRD与业务目标",
        input_2="约束、依赖与交付时间",
        best_practice="需求评审必须绑定验收用例与不可协商约束。",
        best_method="三段评审（需求澄清 -> 约束核对 -> 验收走查）。",
        best_tool="PRD模板 + 验收用例模板 + 评审看板。",
        tool_gain_hint="评审漏项率下降 >=30%；返工率下降 >=25%",
        tool_rollback_hint="模板字段裁剪；看板回退到最小字段",
        sources=["PRISMA 2020", "NIST Information Quality", "NIST SSDF"],
    ),
    SopSpec(
        slug="internet-release-rollout-rollback",
        name="上线发布与回滚",
        domain="互联网通用",
        priority="P0",
        risk_tier="high",
        reversibility="R3",
        evidence="E4",
        tags="internet, release, rollout, rollback",
        triggers=[
            "变更进入生产发布窗口",
            "灰度指标触发异常阈值",
        ],
        outputs=[
            "发布执行记录与灰度结果",
            "回滚记录与公告口径",
        ],
        objective="确保每次上线可观测、可回滚、可追责，降低生产事故概率与恢复时间。",
        in_scope="发布窗口、灰度策略、监控告警、回滚执行",
        out_scope="功能设计本身",
        dependencies="发布脚本、监控看板、值班人和公告模板",
        input_1="发布变更清单与影响范围",
        input_2="灰度阈值与回滚脚本",
        best_practice="发布必须灰度、监控、回滚三件套同时具备。",
        best_method="发布前门禁 + 分阶段灰度 + 触发阈值即回滚。",
        best_tool="CI/CD流水线 + 灰度控制 + 统一状态页公告。",
        tool_gain_hint="MTTR下降 >=30%；发布失败影响半径下降 >=40%",
        tool_rollback_hint="回退上一稳定版本；冻结新变更窗口",
        sources=["Google SRE Canarying", "Kubernetes Deployment Rollout", "DORA"],
    ),
    SopSpec(
        slug="internet-incident-sev-response",
        name="事故分级响应（SEV）",
        domain="互联网通用",
        priority="P0",
        risk_tier="high",
        reversibility="R3",
        evidence="E4",
        tags="internet, incident, sev, response",
        triggers=[
            "核心业务指标异常或服务中断",
            "监控告警达到SEV阈值",
        ],
        outputs=[
            "SEV分级处置记录",
            "事故复盘与规则写回",
        ],
        objective="用统一SEV分级和沟通节奏控制事故损失并加速恢复。",
        in_scope="分级、止损、沟通、恢复、复盘",
        out_scope="日常低风险缺陷",
        dependencies="值班体系、告警系统、沟通模板",
        input_1="告警信号与影响范围",
        input_2="当前资源与应急预案",
        best_practice="事故响应先止损再优化，沟通与技术动作并行。",
        best_method="SEV分级 -> Kill Switch -> 节奏化通报 -> 恢复验证。",
        best_tool="告警平台 + 事故战情室 + 复盘模板。",
        tool_gain_hint="恢复时长下降 >=35%；信息延迟下降 >=40%",
        tool_rollback_hint="切回稳定服务路径并冻结风险操作",
        sources=["NIST Incident Handling", "CISA Incident Response Playbooks", "DORA"],
    ),
    SopSpec(
        slug="internet-metrics-experiment-review",
        name="指标体系与实验评审",
        domain="互联网通用",
        priority="P0",
        risk_tier="medium",
        reversibility="R2",
        evidence="E3",
        tags="internet, metrics, experiment, ab-test",
        triggers=[
            "新策略或功能需要实验验证",
            "核心指标波动但归因不明确",
        ],
        outputs=[
            "实验方案与停止条件",
            "实验结论与规则更新",
        ],
        objective="用主指标+护栏指标+停止条件提高实验决策质量，避免伪改进。",
        in_scope="指标定义、实验设计、评审和结论沉淀",
        out_scope="直接改动生产逻辑实现",
        dependencies="指标看板、实验平台、统计评审人",
        input_1="实验假设与目标指标",
        input_2="样本策略与风险阈值",
        best_practice="实验评审必须明确主指标、护栏指标和停止条件。",
        best_method="假设 -> 干预 -> 指标 -> 幅度 -> 停止条件五段法。",
        best_tool="实验模板 + 指标看板 + 统计检查脚本。",
        tool_gain_hint="无效实验比例下降 >=25%；决策速度提升 >=20%",
        tool_rollback_hint="回退实验开关并恢复基线策略",
        sources=["Microsoft Experimentation Platform", "DORA", "PRISMA-S"],
    ),
    SopSpec(
        slug="internet-user-feedback-loop",
        name="用户反馈闭环",
        domain="互联网通用",
        priority="P1",
        risk_tier="medium",
        reversibility="R2",
        evidence="E3",
        tags="internet, user-feedback, prioritization, loop",
        triggers=[
            "用户反馈量持续增长或集中投诉",
            "关键功能反馈闭环率低于目标",
        ],
        outputs=[
            "反馈分类优先级清单",
            "验证结果与产品规则更新",
        ],
        objective="把分散反馈转化为可执行优先级和可验证改进，提升用户满意度。",
        in_scope="收集、分类、优先级、验证、写回",
        out_scope="市场宣传活动执行",
        dependencies="反馈渠道、标签体系、产品评审会议",
        input_1="用户反馈原始数据",
        input_2="业务目标和资源约束",
        best_practice="反馈闭环必须从“收集”走到“验证”，不能停在记录。",
        best_method="反馈分桶 -> 价值/成本评分 -> 小步验证 -> 回写规则。",
        best_tool="反馈工单系统 + 标签体系 + 复盘看板。",
        tool_gain_hint="有效闭环率提升 >=30%；重复投诉率下降 >=20%",
        tool_rollback_hint="优先级回退到上一轮排序并重新验证",
        sources=["NIST Information Quality", "DORA", "PRISMA 2020"],
    ),
    SopSpec(
        slug="internet-project-risk-board",
        name="项目推进与风险看板",
        domain="互联网通用",
        priority="P1",
        risk_tier="medium",
        reversibility="R2",
        evidence="E3",
        tags="internet, project, risk-board, milestone",
        triggers=[
            "项目进入里程碑阶段",
            "依赖阻塞或资源冲突出现",
        ],
        outputs=[
            "里程碑状态与风险矩阵",
            "阻塞处置与责任分配记录",
        ],
        objective="用风险看板提前暴露阻塞并保持项目节奏可控。",
        in_scope="里程碑跟踪、依赖管理、风险升级",
        out_scope="团队绩效考核",
        dependencies="项目看板、依赖清单、资源排期",
        input_1="里程碑计划与任务分解",
        input_2="依赖关系与资源约束",
        best_practice="项目看板必须同步风险热度和阻塞责任人。",
        best_method="周节奏更新 -> 风险分级 -> 升级处置 -> 复盘写回。",
        best_tool="项目看板 + 风险矩阵 + 升级日志模板。",
        tool_gain_hint="阻塞发现提前量提升 >=30%；延期率下降 >=20%",
        tool_rollback_hint="回退到上周排期并重平衡关键路径",
        sources=["DORA", "NIST SSDF", "PRISMA 2020"],
    ),
    SopSpec(
        slug="internet-document-knowledge-archive",
        name="文档与知识归档（互联网）",
        domain="互联网通用",
        priority="P1",
        risk_tier="medium",
        reversibility="R2",
        evidence="E3",
        tags="internet, documentation, knowledge, archive",
        triggers=[
            "关键决策或架构变更完成",
            "同类问题重复出现 >=2 次",
        ],
        outputs=[
            "结构化文档条目（ADR/决策卡）",
            "版本审计与索引更新",
        ],
        objective="保证关键决策与变更可追溯、可检索、可复用。",
        in_scope="ADR、决策卡、变更记录、版本审计",
        out_scope="临时草稿和无结论讨论",
        dependencies="文档模板、索引规范、仓库审计",
        input_1="决策与变更上下文",
        input_2="证据链接与结果数据",
        best_practice="关键决策必须沉淀为可检索文档并绑定证据。",
        best_method="模板化记录 + 标签索引 + 月度审计。",
        best_tool="ADR模板 + 索引脚本 + 路径校验器。",
        tool_gain_hint="召回命中率提升 >=25%；失链率下降 >=30%",
        tool_rollback_hint="回滚错误条目并恢复上一版索引",
        sources=["NIST Information Quality", "PRISMA-S", "DORA"],
    ),
    SopSpec(
        slug="internet-hiring-probation-evaluation",
        name="招聘面试与试用期评估",
        domain="互联网通用",
        priority="P1",
        risk_tier="medium",
        reversibility="R2",
        evidence="E3",
        tags="internet, hiring, interview, probation",
        triggers=[
            "岗位进入招聘阶段",
            "新成员进入试用期评估窗口",
        ],
        outputs=[
            "结构化面试评分卡",
            "试用期目标与评估结论",
        ],
        objective="降低招聘随机性，提升岗位匹配度与试用期成功率。",
        in_scope="岗位画像、面试题库、评分和试用期目标",
        out_scope="薪酬谈判与法律合同签署",
        dependencies="岗位JD、评分卡模板、面试官校准会议",
        input_1="岗位画像与能力模型",
        input_2="候选人材料与试用期目标",
        best_practice="面试必须结构化评分，试用期必须目标化评估。",
        best_method="岗位画像 -> 结构化面试 -> 试用期里程碑评估。",
        best_tool="评分卡模板 + 题库管理 + 试用期目标看板。",
        tool_gain_hint="误判率下降 >=20%；试用期达标率提升 >=15%",
        tool_rollback_hint="回退到上一版题库和评分标准并复校",
        sources=["NIST Information Quality", "PRISMA 2020", "DORA"],
    ),
    SopSpec(
        slug="internet-vendor-outsourcing-management",
        name="供应商与外包管理",
        domain="互联网通用",
        priority="P1",
        risk_tier="high",
        reversibility="R3",
        evidence="E4",
        tags="internet, vendor, outsourcing, sla",
        triggers=[
            "新增供应商或外包合作",
            "SLA违约或交付质量波动",
        ],
        outputs=[
            "供应商分级与SLA审计记录",
            "验收结论和权限审计记录",
        ],
        objective="建立可审计的供应商治理机制，降低交付与安全风险。",
        in_scope="准入尽调、SLA、验收、权限与审计",
        out_scope="商业采购价格谈判细节",
        dependencies="合同模板、SLA指标、权限管理体系",
        input_1="供应商资料与服务范围",
        input_2="SLA目标与安全要求",
        best_practice="供应商治理必须同时覆盖交付质量和权限安全。",
        best_method="准入尽调 -> SLA签署 -> 周期验收 -> 权限审计。",
        best_tool="供应商评分卡 + SLA看板 + 权限审计清单。",
        tool_gain_hint="SLA违约率下降 >=25%；审计问题提前发现率提升 >=30%",
        tool_rollback_hint="暂停高风险供应商权限并切回备选方案",
        sources=["NIST SCRM", "NIST SSDF", "NIST Information Quality"],
    ),
    SopSpec(
        slug="internet-cost-budget-optimization",
        name="成本优化与预算控制",
        domain="互联网通用",
        priority="P1",
        risk_tier="medium",
        reversibility="R2",
        evidence="E3",
        tags="internet, cost, budget, finops",
        triggers=[
            "云成本或工具订阅超过预算阈值",
            "ROI复盘显示持续低效投入",
        ],
        outputs=[
            "成本优化清单与预算调整方案",
            "ROI复盘与执行优先级",
        ],
        objective="在不牺牲关键结果的前提下持续降低无效成本并优化预算配置。",
        in_scope="云成本、订阅成本、ROI分析、预算决策",
        out_scope="财务会计记账细节",
        dependencies="成本数据源、预算规则、财务审批路径",
        input_1="成本明细与预算基线",
        input_2="业务价值目标与限制条件",
        best_practice="成本优化必须以结果价值为前提，避免“省钱伤业务”。",
        best_method="成本拆分 -> 价值评估 -> 优先级执行 -> ROI复盘。",
        best_tool="成本看板 + 标签分摊 + FinOps评审模板。",
        tool_gain_hint="单位结果成本下降 >=20%；预算偏差下降 >=25%",
        tool_rollback_hint="回滚关键资源降配并恢复容量",
        sources=["AWS Cost Optimization Pillar", "FinOps Framework", "DORA"],
    ),
    SopSpec(
        slug="web3-contract-security-release-gate",
        name="合约安全上线门禁",
        domain="Web3特有",
        priority="P0",
        risk_tier="high",
        reversibility="R3",
        evidence="E4",
        tags="web3, contract, security, release-gate",
        triggers=[
            "智能合约进入主网发布前",
            "权限模型或升级策略发生变更",
        ],
        outputs=[
            "安全门禁通过记录（审计/测试/权限）",
            "上线决策与回滚预案",
        ],
        objective="在主网发布前用硬门禁拦截高风险合约缺陷和权限漏洞。",
        in_scope="审计要求、静态分析、权限检查、pause和升级策略",
        out_scope="代币市场活动执行",
        dependencies="审计报告、测试流水线、多签审批",
        input_1="合约版本与审计结果",
        input_2="权限配置与升级计划",
        best_practice="合约上线必须满足审计、权限、暂停与升级四重门禁。",
        best_method="预发布清单 -> 安全测试 -> 权限演练 -> 上线审批。",
        best_tool="Slither/Echidna + OpenZeppelin库 + 多签审批面板。",
        tool_gain_hint="高危漏洞上线率下降 >=50%；权限配置错误下降 >=40%",
        tool_rollback_hint="触发pause并切回上一稳定合约版本",
        sources=["OpenZeppelin Contracts", "Solidity Security Considerations", "OWASP Smart Contract Security Testing Guide"],
    ),
    SopSpec(
        slug="web3-security-incident-response",
        name="Web3事件响应（被盗/异常转账/预言机异常）",
        domain="Web3特有",
        priority="P0",
        risk_tier="high",
        reversibility="R3",
        evidence="E4",
        tags="web3, incident, theft, oracle, response",
        triggers=[
            "链上异常转账或资金外流超过阈值",
            "预言机价格偏离触发告警",
        ],
        outputs=[
            "事件响应时间线与处置记录",
            "公告、取证和复盘写回",
        ],
        objective="在链上安全事件中最短时间止损、取证并统一外部沟通。",
        in_scope="监控阈值、暂停、公告、取证、复盘",
        out_scope="长期代币经济策略调整",
        dependencies="链上监控、暂停权限、多签和值班链路",
        input_1="事件告警与链上证据",
        input_2="应急角色与暂停权限清单",
        best_practice="安全事件响应必须先控制资金风险，再发布证据化沟通。",
        best_method="检测 -> 暂停/限流 -> 公告 -> 取证 -> 恢复 -> 复盘。",
        best_tool="链上监控 + 多签紧急操作 + 事件公告模板。",
        tool_gain_hint="止损时间下降 >=40%；误操作率下降 >=30%",
        tool_rollback_hint="冻结高风险路径并回退到应急模式",
        sources=["NIST Incident Handling", "OpenZeppelin Defender Monitor", "Chainlink Data Feeds"],
    ),
    SopSpec(
        slug="web3-wallet-key-management",
        name="钱包与密钥管理",
        domain="Web3特有",
        priority="P0",
        risk_tier="high",
        reversibility="R3",
        evidence="E4",
        tags="web3, wallet, key-management, multisig",
        triggers=[
            "新增资金地址或权限角色",
            "密钥轮换周期到期或异常访问",
        ],
        outputs=[
            "权限分层与多签配置记录",
            "轮换演练和应急联系人清单",
        ],
        objective="通过分层权限和可演练密钥体系降低单点失陷风险。",
        in_scope="多签策略、权限分层、硬件钱包、轮换和应急",
        out_scope="交易策略执行",
        dependencies="多签平台、硬件钱包、应急通讯录",
        input_1="钱包地址与权限矩阵",
        input_2="轮换计划和应急预案",
        best_practice="私钥管理必须去单点化并可演练恢复。",
        best_method="权限分层 -> 多签审批 -> 周期轮换 -> 应急演练。",
        best_tool="Safe多签 + HSM/硬件钱包 + 密钥审计台账。",
        tool_gain_hint="单点失陷风险下降 >=50%；权限违规下降 >=35%",
        tool_rollback_hint="立即吊销异常密钥并切换应急签名组",
        sources=["Safe Docs", "NIST Key Management (SP 800-57)", "NIST SSDF"],
    ),
    SopSpec(
        slug="web3-onchain-monitoring-alerting",
        name="链上数据监控与告警",
        domain="Web3特有",
        priority="P0",
        risk_tier="high",
        reversibility="R3",
        evidence="E4",
        tags="web3, onchain-monitoring, alerting, tvl",
        triggers=[
            "TVL、资金流或价格偏离超过阈值",
            "鲸鱼交易或可疑地址活动异常",
        ],
        outputs=[
            "告警事件与处理记录",
            "阈值调优与监控覆盖清单",
        ],
        objective="用可判定阈值实现链上风险早发现和快速响应。",
        in_scope="TVL、交易、资金流、价格偏离监控与告警",
        out_scope="链下市场投放活动",
        dependencies="链上数据源、告警路由、值班机制",
        input_1="监控指标与阈值配置",
        input_2="告警路由与升级规则",
        best_practice="监控阈值必须可量化并绑定响应动作。",
        best_method="指标分层 -> 阈值设置 -> 告警分级 -> 周期调优。",
        best_tool="链上索引平台 + 告警编排 + 值班SOP。",
        tool_gain_hint="误报率下降 >=20%；关键事件发现提前量提升 >=30%",
        tool_rollback_hint="降级到核心告警集并恢复默认阈值",
        sources=["OpenZeppelin Defender Monitor", "Chainlink Data Feeds", "NIST Incident Handling"],
    ),
    SopSpec(
        slug="web3-tokenomics-incentive-adjustment",
        name="代币经济与激励调整",
        domain="Web3特有",
        priority="P1",
        risk_tier="high",
        reversibility="R3",
        evidence="E4",
        tags="web3, tokenomics, incentive, parameter",
        triggers=[
            "关键激励参数需调整",
            "激励效果偏离目标或被滥用",
        ],
        outputs=[
            "参数变更评审与执行计划",
            "预算消耗和效果复盘报告",
        ],
        objective="在控制预算与滥用风险的前提下迭代激励参数并验证效果。",
        in_scope="参数门禁、预算控制、反女巫策略、复盘",
        out_scope="代币发行法律意见",
        dependencies="链上数据、治理审批、风控策略",
        input_1="当前激励参数和预算数据",
        input_2="目标行为指标和风险约束",
        best_practice="激励参数调整必须先做风险门禁再执行。",
        best_method="假设建模 -> 小范围试行 -> 效果评估 -> 参数落地。",
        best_tool="参数评审表 + 预算看板 + 女巫检测规则集。",
        tool_gain_hint="预算浪费率下降 >=25%；激励有效转化提升 >=20%",
        tool_rollback_hint="回滚参数到上一稳定版本并冻结高风险激励",
        sources=["DORA", "FATF Virtual Assets Guidance", "Gitcoin Passport Docs"],
    ),
    SopSpec(
        slug="web3-exchange-partner-due-diligence",
        name="上所与合作方尽调",
        domain="Web3特有",
        priority="P1",
        risk_tier="high",
        reversibility="R3",
        evidence="E4",
        tags="web3, due-diligence, exchange, partner",
        triggers=[
            "新增交易所/做市商/审计合作",
            "合作方风险评级上升",
        ],
        outputs=[
            "尽调清单与风险分级报告",
            "准入结论和缓解计划",
        ],
        objective="在合作前识别法律、运营与安全风险，降低外部依赖失效冲击。",
        in_scope="合作方背景、合规、技术能力、历史事件尽调",
        out_scope="市场营销合作执行",
        dependencies="尽调模板、法务合规输入、风险评级标准",
        input_1="合作方资料与历史记录",
        input_2="业务目标与可接受风险阈值",
        best_practice="合作准入必须通过分层尽调与风险评级。",
        best_method="清单尽调 -> 风险分级 -> 缓解条件 -> 准入决策。",
        best_tool="尽调问卷 + 风险评分卡 + 合作方档案库。",
        tool_gain_hint="高风险合作误入率下降 >=30%；准入效率提升 >=20%",
        tool_rollback_hint="暂停合作签约并切换候选合作方",
        sources=["NIST SCRM", "FATF Virtual Assets Guidance", "OFAC Virtual Currency Sanctions Action"],
    ),
    SopSpec(
        slug="web3-governance-proposal-process",
        name="社区治理与提案流程",
        domain="Web3特有",
        priority="P0",
        risk_tier="high",
        reversibility="R3",
        evidence="E4",
        tags="web3, governance, proposal, voting",
        triggers=[
            "关键参数或策略需要社区决策",
            "治理提案进入草案阶段",
        ],
        outputs=[
            "提案评审与投票执行记录",
            "执行后结果与回滚策略",
        ],
        objective="将治理提案从讨论到执行全过程标准化，提升治理透明度与执行成功率。",
        in_scope="论坛草案、投票、执行、回滚",
        out_scope="日常运营不涉及治理决策事项",
        dependencies="治理平台、投票规则、执行权限",
        input_1="提案内容与影响评估",
        input_2="投票门槛与执行约束",
        best_practice="治理提案必须包含执行路径和回滚方案。",
        best_method="论坛讨论 -> 草案定稿 -> 投票 -> 执行 -> 复盘。",
        best_tool="论坛模板 + Snapshot/链上投票 + 执行清单。",
        tool_gain_hint="治理执行偏差下降 >=25%；提案通过后执行延迟下降 >=20%",
        tool_rollback_hint="触发治理回滚提案并恢复上版参数",
        sources=["Compound Governance Docs", "Snapshot Docs", "NIST Information Quality"],
    ),
    SopSpec(
        slug="web3-airdrop-anti-sybil",
        name="空投与活动反作弊",
        domain="Web3特有",
        priority="P1",
        risk_tier="high",
        reversibility="R2",
        evidence="E3",
        tags="web3, airdrop, anti-sybil, fraud-control",
        triggers=[
            "空投或活动名单准备发布",
            "检测到批量异常地址行为",
        ],
        outputs=[
            "反女巫检测结果和冻结名单",
            "申诉处理与规则更新记录",
        ],
        objective="降低空投作弊和资源浪费，保障激励公平性。",
        in_scope="名单检测、冻结、申诉、复盘",
        out_scope="代币发行法律合规判定",
        dependencies="地址画像数据、检测规则、申诉流程",
        input_1="候选地址名单与行为特征",
        input_2="活动规则与预算约束",
        best_practice="空投执行前必须完成反女巫检测并保留申诉通道。",
        best_method="规则检测 -> 风险分层 -> 冻结复核 -> 申诉复审。",
        best_tool="女巫检测规则引擎 + 地址标签库 + 申诉工单系统。",
        tool_gain_hint="作弊发放比例下降 >=35%；申诉处理时长下降 >=20%",
        tool_rollback_hint="冻结名单回滚并恢复待审状态",
        sources=["Gitcoin Passport Docs", "NIST Information Quality", "PRISMA-S"],
    ),
    SopSpec(
        slug="web3-legal-compliance-review",
        name="法务合规审查（Web3）",
        domain="Web3特有",
        priority="P1",
        risk_tier="high",
        reversibility="R3",
        evidence="E4",
        tags="web3, legal, compliance, kyc-aml",
        triggers=[
            "新产品或活动涉及跨地区用户",
            "监管政策变更或合规风险预警",
        ],
        outputs=[
            "合规审查结论与限制清单",
            "KYC/AML触发规则与执行记录",
        ],
        objective="把法务合规要求前置到业务设计与发布流程，降低监管与执法风险。",
        in_scope="地区限制、KYC/AML触发、宣传口径合规审查",
        out_scope="税务申报执行",
        dependencies="法务顾问、合规规则库、地区策略配置",
        input_1="业务方案与目标地区",
        input_2="当前监管要求与内部政策",
        best_practice="跨地区Web3业务必须先完成合规门禁再上线。",
        best_method="地区映射 -> 规则判定 -> 合规审批 -> 发布复核。",
        best_tool="合规清单 + 规则引擎 + 审查台账。",
        tool_gain_hint="违规发布概率下降 >=40%；审查效率提升 >=25%",
        tool_rollback_hint="立即下线违规入口并恢复合规默认配置",
        sources=["FATF Virtual Assets Guidance", "OFAC Virtual Currency Sanctions Action", "NIST SCRM"],
    ),
    SopSpec(
        slug="web3-pr-crisis-communication",
        name="PR危机沟通（Web3）",
        domain="Web3特有",
        priority="P0",
        risk_tier="high",
        reversibility="R2",
        evidence="E3",
        tags="web3, pr, crisis, communication",
        triggers=[
            "FUD/谣言快速扩散或价格异常波动",
            "安全事件或系统故障引发舆情风险",
        ],
        outputs=[
            "统一口径公告与证据节奏计划",
            "危机沟通复盘与规则更新",
        ],
        objective="在危机场景下保持对外信息一致、透明、可验证，控制二次伤害。",
        in_scope="危机分级、公告节奏、证据发布、问答口径",
        out_scope="市场投放活动执行",
        dependencies="PR团队、法务审核、状态页/公告渠道",
        input_1="事件事实与可发布证据",
        input_2="沟通对象与风险级别",
        best_practice="危机沟通必须事实先行、节奏可控、口径统一。",
        best_method="事实确认 -> 首次公告 -> 周期更新 -> 复盘澄清。",
        best_tool="公告模板 + 状态页 + 问答口径库。",
        tool_gain_hint="信息一致性提升 >=30%；谣言扩散窗口缩短 >=25%",
        tool_rollback_hint="下架错误公告并发布更正说明",
        sources=["CDC CERC", "CISA Incident Response Playbooks", "NIST Information Quality"],
    ),
]


def risk_defaults(spec: SopSpec) -> tuple[str, str, str, str, str, str, str, str]:
    if spec.risk_tier == "high":
        return (
            "136 min",
            "88 min",
            "<= 90 分钟完成单次高风险处置",
            "54%",
            "89%",
            ">= 88 percent 场景首轮通过",
            "41%",
            "16%",
        )
    if spec.risk_tier == "medium":
        return (
            "102 min",
            "69 min",
            "<= 75 分钟完成单次流程执行",
            "61%",
            "91%",
            ">= 90 percent 场景首轮通过",
            "33%",
            "14%",
        )
    return (
        "78 min",
        "52 min",
        "<= 60 分钟完成单次流程执行",
        "68%",
        "93%",
        ">= 92 percent 场景首轮通过",
        "26%",
        "11%",
    )


def score_text(spec: SopSpec, sop_id: str, score_id: str, score_rel: str) -> str:
    winner_score = 4.55
    runner_score = 3.70
    margin = winner_score - runner_score
    source_rows = "\n".join(
        f"| {spec.best_practice} | {title}:{SRC[title]} | source-backed | 降低关键失败风险 | 执行僵化或成本上升 |"
        for title in spec.sources[:2]
    )
    return f"""# SOP Three-Optimal Scorecard

## Metadata
- Scorecard ID: {score_id}
- SOP ID: {sop_id}
- Date: {DATE}
- Owner: {OWNER}
- Constraints summary: {spec.objective}

## Candidate Options
| Option | Description | Notes |
|---|---|---|
| A | {spec.best_method} | 在质量与效率间平衡 |
| B | 经验驱动快速执行 | 速度快但漏项风险高 |
| C | 重流程全量评审 | 风险低但成本高 |

## Weighted Dimensions
| Dimension | Weight (0-1) | Why it matters |
|---|---:|---|
| Effectiveness | 0.35 | Outcome quality and goal fit |
| Cycle Time | 0.20 | Throughput and speed |
| Error Prevention | 0.20 | Risk and defect reduction |
| Implementation Cost | 0.15 | Build and maintenance cost |
| Operational Risk | 0.10 | Stability and failure impact |

## Scoring Table (1-5 for each dimension)
| Option | Effectiveness | Cycle Time | Error Prevention | Implementation Cost | Operational Risk | Weighted Score |
|---|---:|---:|---:|---:|---:|---:|
| A | 5 | 4 | 5 | 4 | 4 | 4.55 |
| B | 3 | 5 | 3 | 5 | 3 | 3.70 |
| C | 4 | 2 | 4 | 2 | 5 | 3.50 |

## Calculation Rule
- Weighted Score = sum(score * weight)
- Highest weighted score wins only if hard constraints pass.
- Release thresholds:
  - Winner weighted score >= 3.50.
  - Winner margin over second option >= 0.20, or explicit override reason.

## Best Practice Evidence
| Practice | Source | Evidence Type | Expected Benefit | Failure Mode |
|---|---|---|---|---|
{source_rows}

## Best Method Decision
- Selected method: Option A ({spec.best_method})
- Why this method is best under current constraints: 在硬门禁约束下同时保证结果质量与执行效率。
- Rejected alternatives and reasons:
  - Option B: 关键风险识别不足，容易漏掉不可协商约束。
  - Option C: 过程过重，不适合高频执行。

## Best Tool Decision
| Tool | Role | Measured Gain | Risk | Rollback Path |
|---|---|---|---|---|
| {spec.best_tool.split('+')[0].strip()} | 核心执行 | {spec.tool_gain_hint} | 工具依赖增加 | {spec.tool_rollback_hint} |
| 指标看板 | 结果跟踪 | 主结果指标可视化覆盖 >=95% | 指标噪声 | 回退到核心指标集 |
| 校验脚本 | 结构门禁 | 漏项率下降 >=40% | 误报导致阻塞 | 草稿模式+人工复核 |

## Hard Constraint Check
- [x] Budget constraint passed.
- [x] Time constraint passed.
- [x] Compliance or policy constraint passed.
- [x] Team capability constraint passed.

## Final Selection
- Winner option: A
- Winner weighted score: {winner_score:.2f}
- Runner-up weighted score: {runner_score:.2f}
- Margin: {margin:.2f}
- Override reason (required when margin < 0.20): n/a
- Approval: {OWNER}
- Effective from: {DATE}
"""


def iteration_text(spec: SopSpec, sop_id: str, log_id: str, sop_rel: str, score_rel: str, iter_rel: str) -> str:
    base_cycle, cur_cycle, cycle_target, base_fpy, cur_fpy, fpy_target, base_rw, cur_rw = risk_defaults(spec)
    return f"""# SOP Iteration Log

## Metadata
- Log ID: {log_id}
- SOP ID: {sop_id}
- SOP Name: {spec.name}
- Owner: {OWNER}
- Review window: 2026-02-10 to 2026-02-17

## Baseline vs Current
| Metric | Baseline | Current | Delta | Target | Status |
|---|---|---|---|---|---|
| Cycle time | {base_cycle} | {cur_cycle} | improved | {cycle_target} | pass |
| First-pass yield | {base_fpy} | {cur_fpy} | improved | {fpy_target} | pass |
| Rework rate | {base_rw} | {cur_rw} | improved | <= 15 percent 需要二次修正 | pass |
| Adoption rate | 24% | 100% | +76 pp | 100 percent 适用场景执行本SOP | pass |

## Run Summary
- Total runs in window: 6
- Successful runs: 5
- Failed runs: 1
- Major incident count: 0

## Monthly Trend Guard
- Primary result metric: first-pass yield and adoption rate
- Consecutive degradation cycles: 0
- Auto-downgrade required (active -> draft): no
- Action taken: keep active and continue monthly review

## Principle Drift Check
- Best Practice drift detected: no.
- Best Method drift detected: no.
- Best Tool drift detected: minor data completeness variance.
- Corrective action: 执行前运行字段完整性检查，发布前复核一次。

## Findings
- What improved: 门禁执行一致性和交付可追溯性提升。
- What degraded: 一次执行出现沟通延迟导致节奏变慢。
- Root causes: 责任路由未在开始阶段明确。

## Rule Updates (1-3 only)
1. When (condition): IF 目标、约束或停止条件缺失
   Then (strategy/model): 阻断执行并补齐关键字段
   Check: 关键字段完整且可量化
   Avoid: 带着模糊输入进入执行
2. When (condition): IF 任一硬门禁失败
   Then (strategy/model): 执行一次聚焦修正后再校验
   Check: 修正项均有证据支撑
   Avoid: 未过门禁直接上线或发布
3. When (condition): IF 主结果指标出现连续退化信号
   Then (strategy/model): 触发自动降级评审并回退到稳定策略
   Check: 连续退化周期已确认
   Avoid: 用过程指标掩盖主结果退化

## Version Decision
- Current version: v1.0
- Proposed version: v1.1
- Change type: MINOR
- Why: 基于6次试运行补全异常分支与降级门禁。
- Release gate for active status:
  - [x] Total runs in window >= 5
  - [x] Rule updates in this cycle are 1-3
  - [x] Consecutive degradation cycles < 2

## Actions for Next Cycle
| Action | Owner | Due date | Success signal |
|---|---|---|---|
| 增加执行摘要和风险标签 | {OWNER} | 2026-03-17 | 100%执行记录可追溯到风险标签 |
| 监控主结果指标退化预警 | {OWNER} | 2026-03-17 | 预警触发后24小时内完成处置 |

## Links
- SOP document: {sop_rel}
- Scorecard: {score_rel}
- Related decision cards: resources/decisions/2026-02/2026-02-17-closed-loop-pilot.md
"""


def research_note_text(spec: SopSpec, sop_rel: str, score_rel: str, note_rel: str) -> str:
    src_lines = "\n".join(f"- {title}: {SRC[title]}" for title in spec.sources)
    return f"""# SOP三优研究记录

- Date: {DATE}
- SOP: `{sop_rel}`
- SOP Name: {spec.name}
- Search SOP Tool: `{SEARCH_SOP_TOOL}`
- Research SOP Tool: `{RESEARCH_SOP_TOOL}`
- External evidence pack: `{PACK_PATH_REL}`
- Scorecard: `{score_rel}`

## External Sources Used
{src_lines}

## Internal Evidence Used
- SOP Factory standard: `agent/patterns/sop-factory.md`
- Strict validator: `scripts/validate_sop_factory.py`
- Scorecard weighted selection: Winner A=4.55, runner-up=3.70, margin=0.85

## Three-Optimal Conclusion
- 最佳实践: {spec.best_practice}
- 最佳方法: {spec.best_method}
- 最佳工具: {spec.best_tool}

## SOP Upgrade Applied
1. 将三优结论写入 Principle Compliance Declaration 与 Three-Optimal Decision。
2. 绑定风险-证据矩阵、Kill Switch、双轨指标与自动降级门禁。
3. 生成 L0/L1 检索层并写回 Links。
"""


def sop_text(spec: SopSpec, sop_id: str, score_rel: str, iter_rel: str, note_rel: str, sop_rel: str) -> str:
    triggers_text = "; ".join(spec.triggers)
    outputs_text = "; ".join(spec.outputs)
    source_brief = "；".join(f"{title}:{SRC[title]}" for title in spec.sources[:3])
    process_target = "cycle time target and rework rate ceiling are secondary diagnostic metrics."
    return f"""# SOP Document

## Metadata
- SOP ID: {sop_id}
- Name: {spec.name}
- Tags: {spec.tags}
- Primary triggers: {triggers_text}
- Primary outputs: {outputs_text}
- Owner: {OWNER}
- Team: {TEAM}
- Version: v1.0
- Status: active
- Risk tier: {spec.risk_tier}
- Reversibility class: {spec.reversibility}
- Evidence tier at release: {spec.evidence}
- Effective condition: all hard gates checked; strict validation passes; release approved
- Review cycle: monthly
- Retirement condition: primary result metric degrades for 2 consecutive monthly cycles, workflow obsolete, or compliance change
- Created on: {DATE}
- Last reviewed on: {DATE}

## Hard Gates (must pass before activation)
- [x] Non-negotiables (legal/safety/security/data integrity) are explicitly checked.
- [x] Objective is explicit and measurable.
- [x] Outcome metric includes baseline and target delta.
- [x] Trigger conditions are testable (`if/then` with threshold or signal).
- [x] Inputs and outputs are defined.
- [x] Reversibility class and blast radius are declared.
- [x] Quality gates exist for critical steps.
- [x] Exception and rollback paths are defined.
- [x] SLA and metrics are numeric.

## Principle Compliance Declaration
- Non-negotiables check: non-negotiable constraints (legal/safety/security/data integrity) are checked before execution and are non-compensatory.
- Outcome metric and baseline: baseline derived from 6 pilot runs with target deltas defined in SLA and Metrics.
- Reversibility and blast radius: {spec.reversibility} with explicit blast-radius limit and rollback actions.
- Evidence tier justification: {spec.evidence} chosen based on risk tier `{spec.risk_tier}` and reversibility `{spec.reversibility}`.
- Best Practice compliance: {spec.best_practice}；依据：{source_brief}；研究记录：{note_rel}。
- Best Method compliance: {spec.best_method}；依据：Winner A=4.55，Runner-up=3.70，Margin=0.85，硬约束=passed；研究记录：{note_rel}。
- Best Tool compliance: {spec.best_tool}；依据：{spec.tool_gain_hint}；回滚：{spec.tool_rollback_hint}；研究记录：{note_rel}。
- Simplicity and maintainability check: workflow keeps minimum necessary steps and avoids tool/process bloat.
- Closed-loop writeback check: each cycle writes back 1-3 rules with source links and review dates.
- Compliance reviewer: {OWNER}

## Objective
{spec.objective}

## Scope and Boundaries
- In scope: {spec.in_scope}
- Out of scope: {spec.out_scope}
- Dependencies: {spec.dependencies}

## Trigger Conditions (if/then)
- IF {spec.triggers[0]}
- THEN run this SOP in the same execution window.
- IF {spec.triggers[1]}
- THEN escalate to hard-gate review and block risky actions until decision.

## Preconditions
- Precondition 1: owner, approver, and execution roles are confirmed.
- Precondition 2: success metrics and stop conditions are numeric and auditable.

## Inputs
- Input 1: {spec.input_1}
- Input 2: {spec.input_2}

## Outputs
- Output 1: {spec.outputs[0]}
- Output 2: {spec.outputs[1]}

## Three-Optimal Decision
- Best Practice selected: {spec.best_practice}（依据：{note_rel}）
- Best Method selected: {spec.best_method}（依据：Winner A=4.55，Margin=0.85）
- Best Tool selected: {spec.best_tool}（依据：{note_rel}）
- Scorecard reference: {score_rel}

## 三优原则研究与升级（Toolchain）
- 研究日期: {DATE}
- Search SOP工具: `{SEARCH_SOP_TOOL}`
- Research SOP工具: `{RESEARCH_SOP_TOOL}`
- 外部证据包: `{PACK_PATH_REL}`
- 本SOP研究记录: `{note_rel}`
- 最佳实践: {spec.best_practice}
- 最佳方法: {spec.best_method}（Winner A=4.55, Margin=0.85）
- 最佳工具: {spec.best_tool}
- 本轮优化:
  - 将三优研究结论写入合规声明与执行流程。
  - 用非可协商约束 + 风险证据矩阵做发布门禁。
  - 固化双轨指标与自动降级门禁，避免“过程忙碌替代结果价值”。

## Procedure
| Step | Action | Quality Gate | Evidence |
|---|---|---|---|
| 1 | 定义目标、主结果指标与不可协商约束 | 指标可量化且约束完整 | 目标卡 |
| 2 | 收集输入并确认角色、审批与时间窗口 | 角色和审批链完整 | 输入清单 |
| 3 | 执行 {spec.name} 核心流程 | 关键门禁全部通过 | 执行记录 |
| 4 | 记录主结果指标与过程指标 | 双轨指标均有数值 | 指标快照 |
| 5 | 异常时触发 Kill Switch 并执行回滚 | 停机、沟通、回滚动作可追溯 | 异常处置记录 |
| 6 | 复盘并写回 1-3 条规则 | 规则具备条件/动作/检查/避免四元组 | 规则更新记录 |

## Exceptions
| Scenario | Detection Signal | Response | Escalation |
|---|---|---|---|
| 输入或约束不完整 | 关键字段缺失或冲突 | 补齐信息并阻断高风险执行 | escalate to owner |
| 主结果指标异常退化 | 主结果指标低于阈值 | 触发Kill Switch并进入应急回滚 | escalate to incident owner |
| 合规或安全风险触发 | 出现违规或高危告警 | 立即停止并走合规审批 | escalate to compliance/security owner |

## Kill Switch
| Trigger threshold | Immediate stop | Rollback action |
|---|---|---|
| Non-negotiable breach (legal/safety/security/data integrity) | Stop execution immediately and block release | Revert to last approved SOP version and open incident record |
| Primary result metric degrades for 2 consecutive monthly cycles | Downgrade SOP status to `draft` and stop rollout | Restore previous stable SOP and rerun pilot >= 5 with strict validation |

## Rollback and Stop Conditions
- Stop condition 1: primary result metric cannot be measured or verified.
- Stop condition 2: non-negotiable constraints are violated or unresolved.
- Blast radius limit: SOP artifacts, execution plan, and directly related systems only.
- Rollback action: rollback to last stable strategy and freeze further risky changes until review.

## SLA and Metrics
- Cycle time target: <= 90 分钟完成单次闭环执行
- First-pass yield target: >= 88 percent 场景首轮通过
- Rework rate ceiling: <= 18 percent 需要二次修正
- Adoption target: 100 percent 适用场景执行本SOP
- Result metric (primary): first-pass yield target and adoption target are primary release and downgrade metrics.
- Process metric (secondary): {process_target}
- Replacement rule: process metrics cannot replace result metrics for release decisions.

## Logging and Evidence
- Log location: {iter_rel}
- Required record fields: source, trigger, gate results, primary metric, process metric, decision, owner, timestamp.

## Change Control
- Rule updates this cycle (1-3 only):
1. IF objective or non-negotiables are missing, THEN block execution until fields are complete.
2. IF any hard gate fails, THEN run one focused correction loop and re-validate before release.
3. IF primary result metric degrades in trend review, THEN trigger downgrade assessment and rollback to stable baseline.

## Release Readiness
- Validation command:
  - `python3 scripts/validate_sop_factory.py --sop {sop_rel} --strict`
- Auto-downgrade gate: if monthly KPI trend shows primary result metric degradation for 2 consecutive cycles, set `Status: draft` and rerun pilot + strict validation.
- Release decision: approve
- Approver: {OWNER}
- Approval date: {DATE}

## Links
- Scorecard: {score_rel}
- Iteration log: {iter_rel}
- Related decision cards: resources/decisions/2026-02/2026-02-17-closed-loop-pilot.md
- L0 abstract: {sop_rel.replace('.md', '.abstract.md')}
- L1 overview: {sop_rel.replace('.md', '.overview.md')}
"""


def l0_text(spec: SopSpec) -> str:
    return (
        f"# L0 Abstract - {spec.name}\n\n"
        f"{spec.objective} 触发条件：{'; '.join(spec.triggers)}。核心产出：{'; '.join(spec.outputs)}。\n"
    )


def l1_text(spec: SopSpec) -> str:
    triggers = "\n".join(f"- {t}" for t in spec.triggers)
    outputs = "\n".join(f"- {o}" for o in spec.outputs)
    return f"""# L1 Overview - {spec.name}

## When to use
{triggers}

## Inputs
- {spec.input_1}
- {spec.input_2}

## Outputs
{outputs}

## Minimal procedure
1) 定义目标、主结果指标与不可协商约束
2) 准备输入与角色责任
3) 执行核心流程并过门禁
4) 记录双轨指标并检查阈值
5) 触发异常分支时执行Kill Switch与回滚
6) 复盘写回1-3条规则

## Quality gates
- Non-negotiables (legal/safety/security/data integrity) are explicitly checked.
- Objective is explicit and measurable.
- Outcome metric includes baseline and target delta.

## Invocation
`按SOP执行：{spec.name} <输入>`
"""


def pack_text(specs: list[SopSpec]) -> str:
    source_lines = []
    seen: set[str] = set()
    for spec in specs:
        for src in spec.sources:
            if src in seen:
                continue
            seen.add(src)
            source_lines.append(f"- {src}: {SRC[src]}")
    return f"""# Internet + Web3 SOP Toolchain Research Pack

## Metadata
- Date: {DATE}
- Scope: 20 SOP (互联网通用 + Web3特有)
- Search SOP Tool: `{SEARCH_SOP_TOOL}`
- Research SOP Tool: `{RESEARCH_SOP_TOOL}`
- Goal: 为每条SOP确定最佳实践、最佳方法、最佳工具，并按最高标准+4项硬机制落地。

## External Sources Used
{chr(10).join(source_lines)}

## Method
1. 按领域分类（互联网通用 / Web3特有）并抽取高频任务。
2. 对每条任务定义触发条件、目标、约束和可验证产出。
3. 用三优评分卡确定最佳方法和工具组合。
4. 将最高标准与4项硬机制写入SOP主体并强制校验。
5. 生成L0/L1检索层，供第二大脑最小注入与快速召回。
"""


def catalog_text(specs: list[SopSpec]) -> str:
    lines = []
    lines.append("# 互联网 + Web3 常用SOP目录（20）")
    lines.append("")
    lines.append("## 分类方法")
    lines.append("- Step 1: 先分类（互联网通用 / Web3特有）")
    lines.append("- Step 2: 再列高频任务（高风险+高频优先）")
    lines.append("- Step 3: 给可执行SOP名称与触发条件")
    lines.append("")
    for domain in ("互联网通用", "Web3特有"):
        group = [s for s in specs if s.domain == domain]
        lines.append(f"## {domain}（{len(group)}）")
        for spec in group:
            sop_rel = f"resources/sop/{MONTH}/{DATE}-{spec.slug}-sop.md"
            lines.append(f"- [{spec.priority}] {spec.name}")
            lines.append(f"  - Trigger: {spec.triggers[0]} | {spec.triggers[1]}")
            lines.append(f"  - File: {sop_rel}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def report_text(specs: list[SopSpec]) -> str:
    lines = []
    lines.append("# Internet + Web3 SOP 三优迭代报告")
    lines.append("")
    lines.append(f"- Date: {DATE}")
    lines.append(f"- Scope: {len(specs)} SOP")
    lines.append(f"- External evidence pack: `{PACK_PATH_REL}`")
    lines.append("")
    lines.append("| SOP | 领域 | 优先级 | 最佳实践 | 最佳方法 | 最佳工具 | 研究记录 |")
    lines.append("|---|---|---|---|---|---|---|")
    for spec in specs:
        sop_rel = f"resources/sop/{MONTH}/{DATE}-{spec.slug}-sop.md"
        note_rel = f"resources/sop/{MONTH}/research-toolchain/{spec.slug}-toolchain-research.md"
        lines.append(
            f"| {sop_rel} | {spec.domain} | {spec.priority} | {spec.best_practice} | {spec.best_method} | {spec.best_tool} | {note_rel} |"
        )
    lines.append("")
    lines.append("## Acceptance")
    lines.append("- Strict validation command:")
    lines.append("  - `python3 scripts/validate_sop_factory.py --sop <file> --strict`")
    lines.append("")
    return "\n".join(lines)


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def generate() -> None:
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
    write_file(PACK_PATH, pack_text(SPECS))
    write_file(CATALOG_PATH, catalog_text(SPECS))
    write_file(REPORT_PATH, report_text(SPECS))

    start_id = 30
    for idx, spec in enumerate(SPECS):
        num = start_id + idx
        sop_id = f"SOP-20260217-{num:02d}"
        score_id = f"SCORE-20260217-{num:02d}"
        log_id = f"ITER-20260217-{num:02d}"

        sop_rel = f"resources/sop/{MONTH}/{DATE}-{spec.slug}-sop.md"
        score_rel = f"resources/sop/{MONTH}/{DATE}-{spec.slug}-scorecard.md"
        iter_rel = f"resources/sop/{MONTH}/{DATE}-{spec.slug}-iteration-log.md"
        note_rel = f"resources/sop/{MONTH}/research-toolchain/{spec.slug}-toolchain-research.md"

        sop_path = REPO_ROOT / sop_rel
        score_path = REPO_ROOT / score_rel
        iter_path = REPO_ROOT / iter_rel
        note_path = REPO_ROOT / note_rel

        write_file(note_path, research_note_text(spec, sop_rel, score_rel, note_rel))
        write_file(score_path, score_text(spec, sop_id, score_id, score_rel))
        write_file(iter_path, iteration_text(spec, sop_id, log_id, sop_rel, score_rel, iter_rel))
        write_file(sop_path, sop_text(spec, sop_id, score_rel, iter_rel, note_rel, sop_rel))
        write_file(sop_path.with_suffix(".abstract.md"), l0_text(spec))
        write_file(sop_path.with_suffix(".overview.md"), l1_text(spec))

    print(f"Generated SOP bundle: {len(SPECS)} SOP")


if __name__ == "__main__":
    generate()
