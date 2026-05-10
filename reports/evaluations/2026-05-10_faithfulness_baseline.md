# Faithfulness Evaluation Report: Baseline

Date: 2026-05-10  
Project: AIA RAG Case Study Service  
Evaluation Type: Faithfulness Evaluation  
Version: v1  
Supporting CSV: reports/evaluations/2026-05-10_faithfulness_baseline.csv

---

## 1. Objective

This evaluation checks whether generated answers are supported by retrieved context.

The goal is to detect whether the LLM answer:

- covers expected supported claims
- avoids known unsupported claims
- uses retrieved context rather than external knowledge
- handles out-of-scope questions as refusals

---

## 2. Evaluation Dataset

Evaluation set:

    eval/faithfulness_eval_set.jsonl

Total questions:

    9

The dataset covers:

- compliance
- data security
- technical specification
- HR policy
- architecture
- out-of-scope refusal

---

## 3. Metrics

Metrics:

- faithfulness_pass_rate
- answer_not_empty_rate
- expected_refusal_match_rate
- source_hit_rate
- unsupported_claims_clean_rate
- avg_answer_claim_coverage_rate
- avg_context_claim_support_rate
- avg_total_latency_ms
- avg_total_tokens

This is a rule-based baseline faithfulness evaluation.

---

## 4. Summary Results

| Metric | Value |
|---|---:|
| Total Questions | 9 |
| Faithfulness Pass Rate | 1.0 |
| Answer Not Empty Rate | 1.0 |
| Expected Refusal Match Rate | 1.0 |
| Source Hit Rate | 1.0 |
| Unsupported Claims Clean Rate | 1.0 |
| Avg Answer Claim Coverage Rate | 1.0 |
| Avg Context Claim Support Rate | 0.8889 |
| Avg Total Latency ms | 2136.56 |
| Avg Total Tokens | 935.56 |

---

## 5. Interpretation

This baseline checks whether expected claims appear in the answer and whether those claims are supported by the selected context chunks.

A high faithfulness pass rate means the answer is likely grounded in the retrieved context under the current rule-based criteria.

---

## 6. Limitations

Current limitations:

1. This is rule-based, not semantic.
2. Claim matching is based on text containment.
3. Correct paraphrases may be missed.
4. Some unsupported claims may not be detected unless they are listed.
5. Future work should add LLM-as-judge faithfulness evaluation.

---

## 7. Next Steps

Recommended next steps:

1. Review failed cases in the CSV.
2. Improve prompts or context assembly if unsupported claims appear.
3. Expand the faithfulness evaluation set.
4. Add semantic or LLM-as-judge faithfulness scoring.
