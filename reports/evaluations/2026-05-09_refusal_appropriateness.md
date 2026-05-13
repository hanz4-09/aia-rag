# Refusal Appropriateness Evaluation Report

Date: 2026-05-09  
Project: AIA RAG Case Study Service  
Evaluation Type: Refusal Appropriateness Evaluation  
Supporting CSV: reports/evaluations/2026-05-09_refusal_appropriateness.csv

---

## 1. Objective

This evaluation checks whether the system refuses the right requests and answers the right requests.

The goal is to verify:

- Unsafe prompt injection attempts are refused.
- Secret extraction attempts are refused.
- Out-of-scope questions are refused with NO_RETRIEVED_CONTEXT.
- Normal security policy questions are not falsely refused.
- Normal HR, compliance, and technical questions are answered.

---

## 2. Dataset

Evaluation set:

    eval/refusal_eval_set.jsonl

Total questions:

    14

The dataset contains both refusal-positive and refusal-negative cases.

---

## 3. Metrics

Metrics:

- pass_rate
- refusal_decision_match_rate
- refusal_reason_match_rate
- false_positive_rate
- false_negative_rate
- answer_allowed_rate
- actual_refusal_rate
- avg_total_latency_ms
- avg_total_tokens

False positive means:

    The system refused a question that should have been answered.

False negative means:

    The system answered a question that should have been refused.

---

## 4. Summary Results

| Metric | Value |
|---|---:|
| Total Questions | 14 |
| Pass Rate | 1.0 |
| Refusal Decision Match Rate | 1.0 |
| Refusal Reason Match Rate | 1.0 |
| False Positive Rate | 0.0 |
| False Negative Rate | 0.0 |
| Answer Allowed Rate | 0.4286 |
| Actual Refusal Rate | 0.5714 |
| Avg Total Latency ms | 1560.79 |
| Avg Total Tokens | 1019.33 |

---

## 5. Interpretation

This evaluation directly validates refusal appropriateness.

A good result should show:

- high pass_rate
- high refusal_decision_match_rate
- high refusal_reason_match_rate
- low false_positive_rate
- low false_negative_rate

This evaluation is especially important because previous diagnosis reports found two refusal-related issues:

1. Normal API key policy questions were incorrectly refused.
2. LLM insufficient-context answers were not converted into structured refusals.

---

## 6. Limitations

Current limitations:

1. This is a small evaluation set.
2. It uses rule-based expectations.
3. It does not use LLM-as-judge.
4. It does not cover all possible prompt injection styles.
5. It does not cover multi-turn attacks.

---

## 7. Next Steps

Recommended next steps:

1. Expand refusal test cases.
2. Add multilingual adversarial prompts.
3. Add more normal security policy questions to detect false positives.
4. Add multi-turn refusal tests.
5. Track refusal appropriateness in future answer evaluations.
