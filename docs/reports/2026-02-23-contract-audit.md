# Contract Audit Report (2026-02-23)

## Scope
- Repository: `skills/deepsea-nexus`
- Script: `scripts/nexus_audit_contract.py`
- Sample size: `200`
- Vector DB: `/Users/yizhi/.openclaw/workspace/memory/.vector_db_restored`
- Collection: `deepsea_nexus_restored`

## Command

```bash
NEXUS_VECTOR_DB=/Users/yizhi/.openclaw/workspace/memory/.vector_db_restored \
NEXUS_COLLECTION=deepsea_nexus_restored \
/Users/yizhi/miniconda3/envs/openclaw-nexus/bin/python \
scripts/nexus_audit_contract.py --limit 200 --show-missing 12
```

## Result Summary
- Coverage:
  - `priority`: `0.0` (`0/200`)
  - `kind`: `0.0` (`0/200`)
  - `source`: `0.965` (`193/200`)
- Group coverage:
  - `legacy_source_file`: `191` samples
  - `legacy_unknown`: `9` samples
  - `new_contract`: `0` samples (in this sample window)

## Interpretation
1. 当前样本窗口主要被历史 legacy 数据占据，契约字段（priority/kind）尚未覆盖到该窗口。  
2. `source` 覆盖高，主要来自 legacy `source_file` 回退字段，不等价于新契约写入完整达标。  
3. 审计脚本已具备运营能力：可区分 new/legacy 并输出缺失样本，便于后续回填与追踪。  

## Next Actions
1. 继续执行 `CLAW-185/186/187`，增加“按新写入标记过滤”的审计窗口。  
2. 对 `legacy_*` 样本做轻量回填（优先补 `priority/kind`）。  
3. 将审计结果接入日报，持续观察 `new_contract` 组占比是否上升。  
