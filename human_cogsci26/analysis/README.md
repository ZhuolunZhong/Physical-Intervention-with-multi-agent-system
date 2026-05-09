# Analysis Scripts

This directory contains statistical analysis scripts for the CogSci 2026 paper.

## Q-Value × Intervention Frequency Analysis

### Quick Start

```bash
cd /path/to/human_cogsci26
python analysis/reproduce_qvalue_frequency_analysis.py
```

### What This Analysis Shows

High-frequency teachers (>15 interventions/round) target significantly lower 
expected Q-value states than low-frequency teachers:

| Group | n | M (normalized) | SD |
|-------|---|----------------|----|
| High-frequency | 39 | 0.247 | 0.025 |
| Low-frequency | 43 | 0.260 | 0.022 |

**Test statistics**: t(80) = -2.58, p = .012, d = -0.57

### Required Data Files

1. `study_data/user_data_q.csv` - Timestep-level Q-values (every 0.5s)
   - Columns: agent_id, time, user_id, round, ExpectedQvalue
   
2. `study_data/user_data_action.csv` - Intervention records
   - Used for counting intervention frequency per user

### Critical Note on Data Sources

**Use the correct Q-value source!**

| File | Column | Use For |
|------|--------|---------|
| `user_data_q.csv` | `ExpectedQvalue` | ✅ This analysis (full trajectory) |
| `user_data_action.csv` | `expected_q_value` | ❌ Different construct (intervention moments only) |

The paper's claim is about what **states** users are in across their entire session, 
not just what states they intervene on. Using `user_data_action.csv` instead of 
`user_data_q.csv` will produce non-significant results.

### Dependencies

```bash
pip install pandas numpy scipy
```

### Output

The script prints:
1. Sample sizes and intervention frequencies
2. Raw and normalized expected Q-values
3. t-test statistics with effect size
4. LaTeX-formatted text for the paper

---

## Other Analysis Scripts

- `statistical_analysis.py` - Comprehensive analysis covering all paper claims
- `frequency_analysis_investigation.md` - Investigation log for reproducing this finding

---

*Last updated: 2026-02-01*
