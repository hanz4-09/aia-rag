# Issue Diagnosis Report: LLM Insufficient Context Answer Not Converted to Refusal

Date: 2026-05-09  
Project: AIA RAG Case Study Service  
Report Type: Issue Diagnosis  
Issue Category: Answer Compliance / Refusal Appropriateness  
Related Component: `app/rag/generator.py`  
Related Evaluation Report: `reports/evaluations/2026-05-09_answer_quality_baseline.md`  
Supporting CSV: `reports/evaluations/2026-05-09_answer_quality_baseline.csv`

---

## 1. Purpose

This report documents a refusal appropriateness issue found during the Phase 3 answer-level baseline evaluation.

After integrating the LLM-based generator, the system correctly generated an answer stating that the internal knowledge base did not contain enough information for an out-of-scope question.

However, the system did not convert this answer into a standardized refusal response.

This report records:

1. The observed issue.
2. The evaluation evidence.
3. The root cause.
4. The implemented fix.
5. The expected post-fix validation result.

---

## 2. Issue Summary

### User Question

    How to configure Kubernetes ingress?

This question is out of scope for the current internal knowledge base.

The expected system behavior is:

    refused = true
    refusal_reason = NO_RETRIEVED_CONTEXT

However, before the fix, the actual result was:

    refused = false
    refusal_reason = empty

The LLM answer itself was:

    The provided internal knowledge base does not contain information about Kubernetes ingress configuration.

This means the model recognized that the context was insufficient, but the application layer did not convert that into a structured refusal.

---

## 3. Before Fix: Observed Behavior

From the answer evaluation result:

| Field | Value |
|---|---|
| Question | How to configure Kubernetes ingress? |
| Category | out_of_scope |
| Expected Refused | true |
| Actual Refused | false |
| Expected Refusal Reason | NO_RETRIEVED_CONTEXT |
| Actual Refusal Reason | empty |
| Rule-based Pass | false |
| Expected Keywords Hit Rate | 0.0 |
| Model Name | qwen-plus |
| Generator Type | llm |
| Total Tokens | 1103 |
| Answer Preview | The provided internal knowledge base does not contain information about Kubernetes ingress configuration. |

---

## 4. Evidence

The failed evaluation row showed:

    expected_refused = True
    actual_refused = False
    expected_refusal_reason = NO_RETRIEVED_CONTEXT
    actual_refusal_reason = empty
    rule_based_pass = False

The answer preview showed:

    The provided internal knowledge base does not contain information about Kubernetes ingress configuration.

This proves that the LLM already expressed insufficient context, but the system-level response metadata was incorrect.

---

## 5. Root Cause

The root cause was in the LLM generator behavior.

Before the fix:

1. The retriever returned some loosely related chunks.
2. The LLM received those chunks as context.
3. The LLM correctly stated that the context did not contain enough information.
4. The generator returned the answer with:

       refused = false
       refusal_reason = None

The issue was:

    The application did not detect insufficient-context answers from the LLM and did not standardize them into NO_RETRIEVED_CONTEXT refusals.

This created a mismatch between the natural language answer and the structured response fields.

---

## 6. Why This Matters

This issue affects refusal appropriateness and answer compliance.

For an enterprise RAG system, it is not enough for the answer text to say:

    I do not have enough information.

The structured response should also reflect the refusal state:

    refused = true
    refusal_reason = NO_RETRIEVED_CONTEXT

Without this, downstream metrics and reports become inaccurate:

- refusal_rate is undercounted
- answer evaluation marks the case as failed
- product behavior becomes inconsistent
- out-of-scope questions may appear as successfully answered

---

## 7. Fix

The LLM generator was updated in:

    app/rag/generator.py

The fix added a standardized insufficient-context answer:

    I could not find enough relevant information in the internal knowledge base to answer this question.

The LLM system prompt was updated to instruct the model:

    If the context does not contain enough information, respond exactly with the standardized insufficient-context answer.

The generator also added a post-processing check:

    _is_insufficient_context_answer(answer)

If the LLM answer indicates insufficient context, the generator now returns:

    refused = true
    refusal_reason = NO_RETRIEVED_CONTEXT
    answer = standardized insufficient-context answer

---

## 8. Before / After Behavior

| Item | Before Fix | After Fix |
|---|---|---|
| Question | How to configure Kubernetes ingress? | How to configure Kubernetes ingress? |
| LLM recognizes insufficient context | Yes | Yes |
| System-level refused | false | true |
| refusal_reason | empty | NO_RETRIEVED_CONTEXT |
| Evaluation pass | false | expected to pass |
| Refusal tracking | inaccurate | accurate |

---

## 9. Expected Post-fix Validation

After the fix, rerun:

    python scripts/evaluate_answers.py

Expected improvement:

    rule_based_pass_rate: 0.9 -> 1.0
    expected_refusal_match_rate: 0.9 -> 1.0
    refusal_reason_match_rate: 0.9 -> 1.0

For the specific out-of-scope question:

    How to configure Kubernetes ingress?

Expected result:

    actual_refused = true
    actual_refusal_reason = NO_RETRIEVED_CONTEXT
    rule_based_pass = true

---

## 10. Impact

This fix improves:

- Refusal appropriateness
- Answer compliance
- Operations metrics accuracy
- Evaluation reliability
- Consistency between answer text and structured response metadata

It also makes the LLM-based generator safer because out-of-scope questions are now handled consistently.

---

## 11. Lessons Learned

### 11.1 LLM uncertainty should be converted into structured system state

If the model says the context is insufficient, the application should not treat it as a normal answer.

It should convert that response into a structured refusal.

### 11.2 Natural language answer and API metadata must be consistent

The answer text and response fields should agree.

If the answer says there is not enough information, then:

    refused = true

should be set.

### 11.3 Answer evaluation can reveal issues that retrieval evaluation cannot

Retrieval evaluation only checks whether relevant sources are retrieved.

Answer evaluation checks whether the final system behavior is correct.

This issue was only visible after running answer-level evaluation.

---

## 12. Remaining Risks

This fix is still rule-based.

Remaining risks:

1. The LLM may express insufficient context in wording not covered by current patterns.
2. Some legitimate cautious answers may be over-converted to refusals.
3. The current insufficient-context detection is not semantic.
4. A future LLM-as-judge evaluation may provide more robust classification.

---

## 13. Next Actions

Recommended next actions:

1. Rerun answer evaluation after the fix.
2. Save the new CSV and Markdown report as a new version.
3. Add more out-of-scope questions to the answer evaluation set.
4. Track refusal appropriateness as a dedicated metric.
5. Consider a more robust refusal classifier in a future version.

---

## 14. Conclusion

The issue was successfully diagnosed.

The LLM correctly identified that the knowledge base did not contain Kubernetes ingress configuration information, but the system failed to convert that into a standardized refusal.

The fix updates the LLM generator so insufficient-context answers are converted into:

    refused = true
    refusal_reason = NO_RETRIEVED_CONTEXT

This improves answer compliance and refusal appropriateness in the Phase 3 LLM-based RAG pipeline.
