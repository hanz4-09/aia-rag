# Evaluation Report: Qwen-Max Full Evaluation Revalidation

Date: 2026-05-11  
Project: AIA RAG Case Study Service  
Report Type: Full PRD Evaluation Revalidation  
Evaluation Area: Phase 3 / Full Evaluation Suite  
Model: `qwen-max`  
Related Components: `scripts/run_all_evaluations.py`, `reports/evaluations/2026-05-11_all_evaluations_summary.csv`

---

## 1. Purpose

This report documents the full Phase 3 evaluation revalidation after switching the LLM model to `qwen-max`.

The goal was to verify whether all core quality and performance evaluations still pass under the stronger model configuration.

---

## 2. Validation Command

The full evaluation suite was executed with:

    python scripts/run_all_evaluations.py --mode all

This command reran both core and performance evaluations, including:

- operations report generation
- answer compliance evaluation
- refusal appropriateness evaluation
- context precision evaluation
- faithfulness LLM-as-Judge evaluation
- style consistency LLM-as-Judge evaluation
- latency evaluation
- concurrency evaluation

---

## 3. Overall Result

All 8 evaluation tasks completed successfully.

| Task | Status |
|---|---|
| operations_report | success |
| answer_compliance | success |
| refusal_appropriateness | success |
| context_precision | success |
| faithfulness_llm_judge | success |
| style_consistency | success |
| latency | success |
| concurrency | success |

Overall status:

    PASS

---

## 4. Key Metrics

| Area | Metric | Result |
|---|---|---:|
| Answer Compliance | answer_compliance_rate | 1.0 |
| Refusal Appropriateness | pass_rate | 1.0 |
| Context Precision | avg_context_precision | 0.9717 |
| Context Precision | passing_rate | 0.9643 |
| Context Precision | prd_pass | True |
| Faithfulness | avg_faithfulness | 1.0 |
| Faithfulness | prd_pass | True |
| Style Consistency | avg_style_consistency | 0.994 |
| Style Consistency | passing_rate | 0.9643 |
| Style Consistency | prd_pass | True |
| Latency | within_10s_rate | 0.9667 |
| Latency | max_latency_ms | 10591 |
| Latency | prd_pass | True |
| Concurrency | concurrency_level | 5 |
| Concurrency | success_rate | 1.0 |
| Concurrency | within_10s_rate | 1.0 |
| Concurrency | prd_pass | True |

---

## 5. Detailed Results

### 5.1 Operations Report

Result:

- status = success
- total_requests = 1
- avg_latency_ms = 3352
- avg_total_tokens = 1061
- reference_cost_per_1000_calls = 0.5188
- estimated_billable_cost_per_1000_calls = 0.0
- answer_compliance_rate = 1.0

Observation:

The operations report now correctly includes `answer_compliance_rate = 1.0`.

### 5.2 Answer Compliance

Result:

- total_questions = 30
- answer_compliance_rate = 1.0
- rule_based_pass_rate = 1.0
- answer_not_empty_rate = 1.0
- expected_refusal_match_rate = 1.0
- refusal_reason_match_rate = 1.0
- source_hit_rate = 1.0
- forbidden_keywords_clean_rate = 1.0
- avg_expected_keywords_hit_rate = 0.9694

Status:

    PASS

### 5.3 Refusal Appropriateness

Result:

- total_questions = 14
- pass_rate = 1.0
- refusal_decision_match_rate = 1.0
- refusal_reason_match_rate = 1.0
- false_positive_rate = 0.0
- false_negative_rate = 0.0

Status:

    PASS

### 5.4 Context Precision

Result:

- avg_context_precision = 0.9717
- avg_source_accuracy = 1.0
- avg_keyword_coverage = 0.9435
- passing_count = 27
- passing_rate = 0.9643
- prd_target = 0.7
- prd_pass = True

Status:

    PASS

Observation:

Context Precision still passes the PRD target by a large margin.

However, the passing count dropped from a previous 28/28 run to 27/28 in this full qwen-max revalidation. This should be reviewed later as a minor evaluation stability or keyword-alignment issue.

### 5.5 Faithfulness

Result:

- avg_faithfulness = 1.0
- overall_statements = 76
- passing_count = 28
- prd_target = 0.85
- prd_pass = True

Status:

    PASS

### 5.6 Style Consistency

Result:

- total_answerable = 28
- total_evaluated = 28
- avg_style_consistency = 0.994
- avg_language_consistency = 1.0
- avg_format_consistency = 0.9821
- avg_tone_professionalism = 1.0
- passing_count = 27
- passing_rate = 0.9643
- prd_target = 0.85
- prd_pass = True

Status:

    PASS

Observation:

Style Consistency improved compared with the earlier run.

### 5.7 Latency

Result:

- total_requests = 30
- successful_requests = 30
- failed_requests = 0
- success_rate = 1.0
- within_10s_rate = 0.9667
- avg_latency_ms = 3102
- p50_latency_ms = 2545.0
- p90_latency_ms = 5248.0
- p95_latency_ms = 7153.7
- max_latency_ms = 10591
- prd_pass = True

Status:

    PASS

Observation:

Latency still passes the PRD requirement because 29/30 requests completed within 10 seconds.

However, one request exceeded the 10-second threshold. This should be tracked as a follow-up performance caveat, especially because `qwen-max` has higher latency than the earlier qwen-plus baseline.

### 5.8 Concurrency

Result:

- total_requests = 5
- concurrency_level = 5
- successful_requests = 5
- failed_requests = 0
- success_rate = 1.0
- within_10s_rate = 1.0
- avg_latency_ms = 3157.6
- p95_latency_ms = 5915.6
- max_latency_ms = 6373
- wall_clock_latency_ms = 6377
- prd_pass = True

Status:

    PASS

---

## 6. Issues / Follow-up Items Identified

The full qwen-max run passed, but several follow-up items should be reviewed later.

### 6.1 Context Precision Local Regression

Observed:

    passing_count = 27 / 28
    passing_rate = 0.9643

Previous best run:

    passing_count = 28 / 28

Impact:

    Not a PRD blocker. Overall avg_context_precision remains 0.9717, far above the 0.70 target.

Follow-up:

    Identify the one failed context precision case and determine whether it is an evaluation keyword-alignment issue or a real retrieval precision issue.

### 6.2 Latency Outlier

Observed:

    within_10s_rate = 0.9667
    max_latency_ms = 10591

Impact:

    Not a PRD blocker. PRD requires within_10s_rate >= 0.90, and the current result is 0.9667.

Follow-up:

    Identify the slow request and check whether the latency came from qwen-max generation, temporary provider latency, or answer length.

### 6.3 Operations Report Log Sample Limitation

Observed:

    operations_report total_requests = 1
    model_names may reflect the available structured log sample rather than the full qwen-max evaluation suite

Impact:

    Not a PRD blocker.

Follow-up:

    Decide whether evaluation scripts should also write structured runtime logs, or whether operations_report should remain limited to service runtime logs.

### 6.4 Model Cost / Latency Trade-off

Observed:

    qwen-max passes all PRD metrics but has higher latency than the earlier qwen-plus baseline.

Impact:

    Not a PRD blocker.

Follow-up:

    Document model selection guidance:
    - qwen-max for final quality validation or demo
    - qwen-plus / qwen-turbo / qwen-flash for cost-sensitive repeated evaluations

---

## 7. Conclusion

The full Phase 3 evaluation suite was successfully rerun under `qwen-max`.

All core and performance evaluations completed successfully and passed PRD targets.

Final status:

    PASS

This result can be used as the qwen-max full evaluation revalidation baseline for Phase 3.
