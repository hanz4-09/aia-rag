# All Evaluations Summary

Date: 2026-05-12  
Project: AIA RAG Case Study Service  
Mode: `all`  

---

## 1. Summary

- Total tasks: 13
- Successful tasks: 0
- Failed or missing tasks: 13

---

## 2. Task Results

| Task | Status | Duration sec | Report | Key Metrics |
|---|---:|---:|---|---|
| operations_report | skipped | 0 | `reports\operations_report.csv` | total_requests=9; p50_latency_ms=751; p95_latency_ms=3355; avg_latency_ms=885.56; avg_total_tokens=792.25; reference_cost_per_1000_calls=0.320711; estimated_billable_cost_per_1000_calls=0.0; answer_compliance_rate=1.0 |
| answer_compliance | skipped | 0 | `reports\evaluations\2026-05-11_answer_compliance_eval.csv` | total_questions=30; answer_compliance_rate=1.0; rule_based_pass_rate=1.0; answer_not_empty_rate=1.0; expected_refusal_match_rate=1.0; refusal_reason_match_rate=1.0; source_hit_rate=1.0; forbidden_keywords_clean_rate=1.0; avg_expected_keywords_hit_rate=0.9417 |
| refusal_appropriateness | skipped | 0 | `reports\evaluations\2026-05-09_refusal_appropriateness.csv` | total_questions=14; pass_rate=1.0; refusal_decision_match_rate=1.0; refusal_reason_match_rate=1.0; false_positive_rate=0.0; false_negative_rate=0.0 |
| context_precision | skipped | 0 | `reports\evaluations\2026-05-11_context_precision_eval.csv` | avg_context_precision=0.9807; avg_source_accuracy=1.0; avg_keyword_coverage=0.9613; passing_count=28; passing_rate=1.0; prd_target=0.7; prd_pass=True |
| faithfulness_llm_judge | skipped | 0 | `reports\evaluations\2026-05-11_faithfulness_eval.csv` | avg_faithfulness=1.0; overall_statements=76; passing_count=28; prd_target=0.85; prd_pass=True |
| style_consistency | skipped | 0 | `reports\evaluations\2026-05-11_style_consistency_eval.csv` | total_answerable=28; total_evaluated=28; avg_style_consistency=0.994; avg_language_consistency=1.0; avg_format_consistency=0.9821; avg_tone_professionalism=1.0; passing_count=27; passing_rate=0.9643; prd_target=0.85; prd_pass=True |
| pii_redaction | skipped | 0 | `reports\evaluations\2026-05-11_pii_redaction_eval.csv` | total_cases=7; passing_count=7; pass_rate=1.0; forbidden_clean_rate=1.0; placeholder_present_rate=1.0; prd_pass=True |
| multiturn_qa | skipped | 0 | `reports\evaluations\2026-05-11_multiturn_eval.csv` | total_cases=3; passing_count=3; pass_rate=1.0; history_used_rate=1.0; source_hit_rate=1.0; avg_keyword_hit_rate=1.0; prd_pass=True |
| cache | skipped | 0 | `reports\evaluations\2026-05-11_cache_eval.csv` | total_cases=2; passing_count=2; pass_rate=1.0; first_cache_miss_rate=1.0; second_cache_hit_rate=1.0; latency_improved_rate=1.0; avg_keyword_hit_rate=1.0; prd_pass=True |
| pdf_ingestion | skipped | 0 | `reports\evaluations\2026-05-11_pdf_ingestion_eval.csv` | total_cases=2; passing_count=2; pass_rate=1.0; pdf_files_checked=2; scanned_pdf_candidates=1; pdfs_with_ocr_performed=1; pdfs_with_ocr_succeeded=1; retrieval_hit_rate=1.0; loaded_documents=10; skipped_empty_documents=0; prd_pass=True |
| advanced_memory | skipped | 0 | `reports\evaluations\2026-05-11_advanced_memory_eval.csv` | total_cases=2; passing_count=2; pass_rate=1.0; persistent_memory_pass_rate=1.0; query_rewrite_applied_rate=1.0; retrieval_query_resolution_rate=1.0; source_hit_rate=1.0; avg_keyword_hit_rate=1.0; prd_pass=True |
| latency | skipped | 0 | `reports\evaluations\2026-05-11_latency_eval.csv` | total_requests=30; successful_requests=30; failed_requests=0; success_rate=1.0; within_10s_rate=0.9667; avg_latency_ms=3102; p50_latency_ms=2545.0; p90_latency_ms=5248.0; p95_latency_ms=7153.7; max_latency_ms=10591; prd_pass=True |
| concurrency | skipped | 0 | `reports\evaluations\2026-05-11_concurrency_eval.csv` | total_requests=5; concurrency_level=5; successful_requests=5; failed_requests=0; success_rate=1.0; within_10s_rate=1.0; avg_latency_ms=3157.6; p95_latency_ms=5915.6; max_latency_ms=6373; wall_clock_latency_ms=6377; prd_pass=True |

---

## 3. Notes

- This script orchestrates existing evaluation scripts.
- It does not replace the individual detailed evaluation reports.
- LLM-based evaluations may consume model quota.
- Performance evaluations may be skipped by running `--mode core`.
