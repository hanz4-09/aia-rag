# Answer Quality Evaluation Report: Baseline

Date: 2026-05-09  
Project: AIA RAG Case Study Service  
Evaluation Type: Answer Quality Evaluation  
Version: v1  
Supporting CSV: reports/evaluations/2026-05-09_answer_quality_baseline.csv

---

## 1. Objective

This evaluation validates the first LLM-based answer generation pipeline.

The goal is to verify that the system can:

- Generate non-empty answers
- Respect expected refusal behavior
- Return sources for answerable questions
- Include expected answer keywords
- Avoid forbidden answer keywords
- Record token usage and latency

---

## 2. Evaluation Dataset

Evaluation set:

    eval/answer_eval_set.jsonl

The dataset covers:

- Compliance questions
- Data security questions
- Technical specification questions
- HR policy questions
- Architecture questions
- Safety refusal
- Out-of-scope refusal

Total questions:

    10

---

## 3. Metrics

Metrics used in this baseline evaluation:

- rule_based_pass_rate
- answer_not_empty_rate
- expected_refusal_match_rate
- refusal_reason_match_rate
- source_hit_rate
- forbidden_keywords_clean_rate
- avg_expected_keywords_hit_rate
- avg_total_latency_ms
- avg_generation_latency_ms
- avg_total_tokens

This is a rule-based baseline evaluation, not an LLM-as-judge evaluation.

---

## 4. Summary Results

| Metric | Value |
|---|---:|
| Total Questions | 10 |
| Rule-based Pass Rate | 1.0 |
| Answer Not Empty Rate | 1.0 |
| Expected Refusal Match Rate | 1.0 |
| Refusal Reason Match Rate | 1.0 |
| Source Hit Rate | 1.0 |
| Forbidden Keywords Clean Rate | 1.0 |
| Avg Expected Keywords Hit Rate | 0.95 |
| Avg Total Latency ms | 1737.0 |
| Avg Generation Latency ms | 1725.7 |
| Avg Total Tokens | 926.89 |

---

## 5. Interpretation

This report establishes the first answer-level evaluation baseline after replacing the extractive generator with an LLM-based generator.

The current evaluation is intentionally simple and reproducible.

It checks rule-based properties such as:

- Whether the answer exists
- Whether refusal behavior matches expectation
- Whether expected sources are present
- Whether expected keywords appear
- Whether forbidden keywords are avoided

---

## 6. Limitations

Current limitations:

1. This is not a semantic faithfulness evaluation.
2. This does not yet measure context precision.
3. This does not use LLM-as-judge.
4. Keyword matching may be too strict or too loose.
5. Some correct answers may fail if they use different wording.
6. Some incorrect answers may pass if they contain expected keywords.

---

## 7. Next Steps

Recommended next steps:

1. Review failed cases in the CSV.
2. Improve prompts or context assembly if needed.
3. Add faithfulness evaluation.
4. Add context precision evaluation.
5. Add refusal appropriateness evaluation set.
6. Add LLM-as-judge evaluation when stable.
