# SOP Toolchain Research Pack

## Metadata
- Date: 2026-02-17
- Toolchain:
  - Search SOP: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
  - Research SOP: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- Scope: `resources/sop/2026-02/*-sop.md` 全量SOP
- Goal: 为每个SOP确定最佳实践、最佳方法、最佳工具，并据此升级SOP。

## External Evidence Base

### Research Quality and Evidence
- PRISMA 2020 statement: https://www.bmj.com/content/372/bmj.n71
- PRISMA-S extension: https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z
- Oxford CEBM levels: https://www.cebm.ox.ac.uk/resources/levels-of-evidence/explanation-of-the-2011-ocebm-levels-of-evidence
- Cochrane Handbook (certainty context): https://training.cochrane.org/handbook/current/chapter-14

### Risk and Governance
- NIST Information Quality Standards: https://www.nist.gov/director/nist-information-quality-standards
- NIST AI Risk Management Framework: https://www.nist.gov/itl/ai-risk-management-framework
- NIST CSF 2.0: https://www.nist.gov/cyberframework

### Software and Execution Practice
- Scrum Guide 2020: https://scrumguides.org/scrum-guide.html
- DORA quick check: https://dora.dev/
- NIST Computer Security Incident Handling (SP 800-61 r2 landing): https://csrc.nist.gov/pubs/sp/800/61/r2/final

### Source Evaluation and Documentation
- Stanford lateral reading (experts evaluate online credibility): https://ed.stanford.edu/news/stanford-scholars-observe-experts-see-how-they-evaluate-credibility-information-online
- Stanford lateral reading training effect: https://ed.stanford.edu/news/it-doesn-t-take-long-learn-how-spot-misinformation-online-stanford-study-finds
- Diataxis documentation framework: https://diataxis.fr/

### Learning Science
- Retrieval practice paper: https://pubmed.ncbi.nlm.nih.gov/16719566/
- Spacing effect review: https://pubmed.ncbi.nlm.nih.gov/16507066/
- Effective learning techniques review: https://pubmed.ncbi.nlm.nih.gov/26173288/

### Life Ops (Health/Finance/Emergency/Travel)
- CDC physical activity basics: https://www.cdc.gov/physical-activity-basics/guidelines/index.html
- CDC sleep overview: https://www.cdc.gov/sleep/about/index.html
- CFPB toolkit: https://www.consumerfinance.gov/consumer-tools/educator-tools/your-money-your-goals/toolkit/
- IRS recordkeeping: https://www.irs.gov/tax-professionals/eitc-central/recordkeeping
- Ready.gov emergency kit: https://www.ready.gov/kit
- U.S. State Department travel checklist: https://travel.state.gov/content/travel/en/international-travel/before-you-go/travelers-checklist.html

## Method Used
1. Use Search SOP to collect candidate authoritative sources by topic.
2. Use Deep Research SOP to classify evidence strength and resolve conflicts.
3. Map each SOP to domain-specific evidence set.
4. For each SOP, derive:
   - Best Practice from evidence + scorecard practice rows
   - Best Method from scorecard winner + constraints
   - Best Tool from tool gain/rollback + minimum toolchain principle
5. Write research note and push upgrades back into SOP file.

## Acceptance Gates
- Every SOP has:
  - one research note file
  - one upgraded research section in SOP body
  - clear best practice/method/tool statements
- Strict validator passes after update:
  - `python3 scripts/validate_sop_factory.py --sop <file> --strict`
