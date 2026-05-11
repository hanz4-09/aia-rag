# Optimization Report: Cross-lingual Evaluation Keyword Alignment

Date: 2026-05-11  
Project: AIA RAG Case Study Service  
Report Type: Evaluation Set Optimization Summary  
Optimization Area: Context Precision / Answer Compliance Evaluation  
Related Components: `eval/answer_eval_set.jsonl`, `scripts/evaluate_context_precision.py`, `scripts/evaluate_answers.py`

---

## 1. Purpose

This report documents a small evaluation-set alignment fix discovered after the qwen-max full evaluation revalidation.

The goal was to investigate why Context Precision dropped from a previous 28/28 passing result to 27/28, even though the overall PRD target was still passed.

---

## 2. Initial Issue

After the qwen-max full evaluation run, Context Precision still passed the PRD target, but one case failed the single-case threshold.

Failed case:

    运营日志至少需要保留多少天？

Observed result:

    context_precision = 0.5
    source_accuracy = 1.0
    keyword_coverage = 0.0
    expected_source = 03_compliance_guide_en.txt

The important signal was:

    source_accuracy = 1.0

This showed that retrieval had found the correct source document.

---

## 3. Diagnosis

The failure was caused by keyword coverage rather than source retrieval.

The evaluation set originally used Chinese expected keywords:

    运营日志
    90天

However, the expected source document was English:

    03_compliance_guide_en.txt

The retrieved context therefore contained English wording such as:

    operational logs
    90 days

This caused keyword coverage to be 0.0 even though the correct source was retrieved.

Conclusion:

    This was a cross-lingual evaluation keyword alignment issue, not a retrieval failure.

---

## 4. Change

Updated the expected keywords for the affected case in:

    eval/answer_eval_set.jsonl

The keyword list was expanded from Chinese-only keywords to bilingual keywords:

    运营日志
    90天
    operational logs
    90 days

This keeps the evaluation semantically strict while allowing both Chinese answer wording and English source-context wording to be matched.

---

## 5. Validation

Context Precision was rerun.

Final result:

    Answerable questions: 28
    Evaluated questions: 28
    Avg Context Precision: 0.9807
    Avg Source Accuracy: 1.0
    Avg Keyword Coverage: 0.9613
    Passing: 28/28
    PRD Target: >= 0.7
    PRD Status: PASS

The affected case improved to:

    context_precision = 0.75
    source_accuracy = 1.0
    keyword_coverage = 0.5

Answer Compliance was also rerun to ensure the evaluation-set change did not break answer-level compliance.

Final Answer Compliance result:

    total_questions = 30
    answer_compliance_rate = 1.0
    rule_based_pass_rate = 1.0
    expected_refusal_match_rate = 1.0
    refusal_reason_match_rate = 1.0
    source_hit_rate = 1.0
    forbidden_keywords_clean_rate = 1.0

---

## 6. Conclusion

The Context Precision local regression was resolved.

Final status:

    PASS

This optimization confirms that the issue was caused by cross-lingual keyword alignment in the evaluation set, not by retrieval quality regression.
