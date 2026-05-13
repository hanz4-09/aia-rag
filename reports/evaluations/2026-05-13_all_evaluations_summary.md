# All Evaluations Summary

Date: 2026-05-13
Project: AIA RAG Case Study Service
Mode: `all`

---

## 1. Summary

- Total tasks: 13
- Successful tasks: 0
- Skipped tasks: 13
- Tasks with available reports: 13
- Failed or missing tasks: 0

---

## 2. Task Results

| Task | Status | Duration sec | Report | Key Metrics |
|---|---:|---:|---|---|
| operations_report | skipped | 0.0 | `reports\operations_report.csv` | total_requests=60; p50_latency_ms=1958; p95_latency_ms=8221; avg_latency_ms=2780.85; avg_retrieval_latency_ms=130.58; avg_generation_latency_ms=2648.95; cache_hit_rate=0.2833; refusal_rate=0.1333; llm_request_count=59; extractive_request_count=1; generator_types=extractive|llm; model_names=qwen-max; total_input_tokens=48060; total_output_tokens=3629; total_tokens=51689; avg_input_tokens=906.79; avg_output_tokens=68.47; avg_total_tokens=975.26; cost_enabled=True; currency=USD; input_price_per_1m_tokens=0.4; output_price_per_1m_tokens=1.2; free_quota_enabled=True; reference_total_cost=0.023579; reference_cost_per_request=0.000393; reference_cost_per_1000_calls=0.39298; estimated_billable_total_cost=0.0; estimated_billable_cost_per_1000_calls=0.0; answer_compliance_rate=1.0; answer_compliance_report=C:\Users\dx\OneDrive\aia-rag\reports\evaluations\2026-05-11_answer_compliance_eval.csv |
| answer_compliance | skipped | 0.0 | `reports\evaluations\2026-05-11_answer_compliance_eval.csv` | total_questions=30; answer_compliance_rate=1.0; rule_based_pass_rate=1.0; answer_not_empty_rate=1.0; expected_refusal_match_rate=1.0; refusal_reason_match_rate=1.0; source_hit_rate=1.0; forbidden_keywords_clean_rate=1.0; avg_expected_keywords_hit_rate=0.9417; avg_total_latency_ms=2269.0; avg_generation_latency_ms=2221.63; avg_total_tokens=990.86 |
| refusal_appropriateness | skipped | 0.0 | `reports\evaluations\2026-05-09_refusal_appropriateness.csv` | total_questions=14; pass_rate=1.0; refusal_decision_match_rate=1.0; refusal_reason_match_rate=1.0; false_positive_rate=0.0; false_negative_rate=0.0; answer_allowed_rate=0.4286; actual_refusal_rate=0.5714; avg_total_latency_ms=1560.79; avg_total_tokens=1019.33 |
| context_precision | skipped | 0.0 | `reports\evaluations\2026-05-13_context_precision_eval.csv` | total_answerable=28; total_evaluated=28; avg_context_precision=0.9807; avg_source_accuracy=1.0; avg_keyword_coverage=0.9613; passing_count=28; passing_rate=1.0; prd_target=0.7; prd_pass=True |
| faithfulness_llm_judge | skipped | 0.0 | `reports\evaluations\2026-05-13_faithfulness_eval.csv` | total_answerable=28; total_evaluated=28; avg_faithfulness=1.0; overall_statements=84; overall_faithful=84; overall_faithfulness_rate=1.0; passing_count=28; passing_rate=1.0; prd_target=0.85; prd_pass=True |
| style_consistency | skipped | 0.0 | `reports\evaluations\2026-05-13_style_consistency_eval.csv` | total_answerable=28; total_evaluated=28; avg_style_consistency=0.9762; avg_language_consistency=0.9821; avg_format_consistency=0.9464; avg_tone_professionalism=1.0; passing_count=24; passing_rate=0.8571; prd_target=0.85; prd_pass=True |
| pii_redaction | skipped | 0.0 | `reports\evaluations\2026-05-13_pii_redaction_eval.csv` | total_cases=13; passing_count=13; pass_rate=1.0; true_positive_cases=7; true_positive_passing=7; true_positive_pass_rate=1.0; false_positive_cases=6; false_positive_passing=6; false_positive_clean_rate=1.0; forbidden_clean_count=13; forbidden_clean_rate=1.0; placeholder_present_count=7; placeholder_present_rate=1.0; unexpected_placeholder_clean_count=6; unexpected_placeholder_clean_rate=1.0; prd_pass=True |
| multiturn_qa | skipped | 0.0 | `reports\evaluations\2026-05-13_multiturn_eval.csv` | total_cases=6; passing_count=6; pass_rate=1.0; history_used_count=6; history_used_rate=1.0; source_hit_count=6; source_hit_rate=1.0; avg_keyword_hit_rate=1.0; prd_pass=True |
| cache | skipped | 0.0 | `reports\evaluations\2026-05-13_cache_eval.csv` | total_cases=2; passing_count=0; pass_rate=0.0; first_cache_miss_count=2; first_cache_miss_rate=1.0; second_cache_hit_count=0; second_cache_hit_rate=0.0; latency_improved_count=0; latency_improved_rate=0.0; avg_keyword_hit_rate=1.0; prd_pass=False |
| pdf_ingestion | skipped | 0.0 | `reports\evaluations\2026-05-13_pdf_ingestion_eval.csv` | total_cases=4; passing_count=4; pass_rate=1.0; pdf_files_checked=2; scanned_pdf_candidates=1; pdfs_with_ocr_performed=1; pdfs_with_ocr_succeeded=1; retrieval_hit_count=4; retrieval_hit_rate=1.0; loaded_documents=10; skipped_empty_documents=0; prd_pass=True |
| advanced_memory | skipped | 0.0 | `reports\evaluations\2026-05-13_advanced_memory_eval.csv` | total_cases=2; passing_count=2; pass_rate=1.0; persistent_memory_pass_count=2; persistent_memory_pass_rate=1.0; query_rewrite_applied_count=2; query_rewrite_applied_rate=1.0; retrieval_query_resolution_count=2; retrieval_query_resolution_rate=1.0; source_hit_count=2; source_hit_rate=1.0; avg_keyword_hit_rate=1.0; prd_pass=True |
| latency | skipped | 0.0 | `reports\evaluations\2026-05-11_latency_eval.csv` | total_requests=30; successful_requests=30; failed_requests=0; success_rate=1.0; within_10s_count=30; within_10s_rate=1.0; avg_latency_ms=2323.73; p50_latency_ms=1737.5; p90_latency_ms=4375.0; p95_latency_ms=5677.05; max_latency_ms=8806; avg_retrieval_latency_ms=45; avg_generation_latency_ms=2277.93; prd_latency_threshold_ms=10000; prd_required_within_threshold_rate=0.9; prd_pass=True |
| concurrency | skipped | 0.0 | `reports\evaluations\2026-05-11_concurrency_eval.csv` | total_requests=5; concurrency_level=5; successful_requests=5; failed_requests=0; success_rate=1.0; within_10s_count=5; within_10s_rate=1.0; avg_latency_ms=2804.6; p50_latency_ms=2596.0; p90_latency_ms=4141.2; p95_latency_ms=4422.6; max_latency_ms=4704; wall_clock_latency_ms=4706; prebuild_latency_ms=48011; avg_retrieval_latency_ms=560; avg_generation_latency_ms=2243.6; prd_required_success_rate=1.0; prd_required_within_10s_rate=0.9; prd_pass=True |

---

## 3. Notes

- This script orchestrates existing evaluation scripts.
- It does not replace the individual detailed evaluation reports.
- LLM-based evaluations may consume model quota.
- Performance evaluations may take longer than rule-based checks.
- `--skip-run` summarizes existing reports without rerunning evaluations.
- If a task has no runnable script but has an existing report, the report is reused and the task is marked as skipped.
