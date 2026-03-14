# SOP三优研究记录

- Date: 2026-02-17
- SOP: `resources/sop/2026-02/2026-02-17-search-recall-sop.md`
- SOP Name: Search Recall Execution
- Search SOP Tool: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP Tool: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- External evidence pack: `resources/sop/2026-02/2026-02-17-sop-toolchain-research-pack.md`
- Scorecard: `resources/sop/2026-02/2026-02-17-search-recall-scorecard.md`

## External Sources Used
- PRISMA 2020: https://www.bmj.com/content/372/bmj.n71
- PRISMA-S: https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z
- NIST Information Quality: https://www.nist.gov/director/nist-information-quality-standards
- CEBM levels: https://www.cebm.ox.ac.uk/resources/levels-of-evidence/explanation-of-the-2011-ocebm-levels-of-evidence
- Stanford lateral reading: https://ed.stanford.edu/news/stanford-scholars-observe-experts-see-how-they-evaluate-credibility-information-online

## Internal Evidence Used
- Best Practice evidence rows: Relevance-ranked semantic recall <- `nexus_core.py` search_recall path；Trigger-aware search mode <- `nexus_core.py` smart_search；Cache-backed recall <- `_cached_search` in `nexus_core.py`
- Best Method score: Winner B=4.40, Runner-up=3.80, Margin=0.60, Hard constraints=passed
- Best Tool evidence: gain[`nexus_recall`:consistent baseline retrieval；`smart_search`:improved first relevant hit rate；`rg`:fast local evidence validation], rollback[`nexus_recall`->fallback to single-pass only；`smart_search`->disable expansion path；`rg`->manual source check]

## Three-Optimal Conclusion
- 最佳实践: evidence-linked semantic recall with threshold gates and fallback.
- 最佳方法: two-pass recall (original query, then expansion if gate fails).
- 最佳工具: `nexus_recall` for primary recall, `smart_search` for trigger-aware expansion, `rg` for source validation.

## SOP Upgrade Applied
1. 三优结论回写到 Principle Compliance Declaration。
2. 三优研究段落写入 SOP 主体并挂研究记录路径。
3. 绑定 Search/Research 工具SOP与外部证据包，形成可追溯闭环。
