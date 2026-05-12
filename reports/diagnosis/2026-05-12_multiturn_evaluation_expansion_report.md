# Optimization Report: Multi-turn Evaluation Set Expansion

Date: 2026-05-12  
Project: AIA RAG Case Study Service  
Report Type: Multi-turn QA Evaluation Enhancement  
Optimization Area: Multi-turn RAG / Advanced Memory Evaluation  
Related Components: `scripts/evaluate_multiturn.py`, `app/core/session_memory.py`, `app/rag/query_rewriter.py`

---

## 1. Purpose

This report documents the expansion of the multi-turn evaluation set.

The project already supported lightweight multi-turn QA and Advanced Memory v1. The original multi-turn evaluation validated basic follow-up behavior with 3 cases. This enhancement expands the evaluation set to cover additional follow-up patterns.

---

## 2. Change

Enhanced:

    scripts/evaluate_multiturn.py

The evaluation set was expanded from 3 cases to 6 cases.

Added new multi-turn cases covering:

- audit log required fields follow-up
- Chinese API Key incident report recipient follow-up
- OCR scanned PDF API Key incident reporting window follow-up

---

## 3. Expanded Evaluation Scope

The expanded multi-turn evaluation now covers:

1. English audit log retention follow-up
2. Chinese API Key incident reporting window follow-up
3. HR / annual leave manager approval follow-up
4. audit log required fields follow-up
5. Chinese API Key incident report recipient follow-up
6. OCR scanned PDF reporting window follow-up

---

## 4. Issue Found During Expansion

The first expanded run exposed two evaluation issues:

1. Newly added cases initially used an incompatible schema with `first_question` and `follow_up_question`, while the evaluator expected a `turns` list.
2. One Chinese API Key recipient case expected the exact keyword `Security Operations Team`, while the generated answer correctly used `Security Operations 团队`.

Both issues were fixed by:

- converting new cases to the existing `turns` list schema
- adjusting the expected keyword to `Security Operations`, which matches bilingual answer wording

---

## 5. Final Evaluation Result

Final command:

    python scripts/evaluate_multiturn.py

Final result:

    total_cases = 6
    passing_count = 6
    pass_rate = 1.0
    history_used_rate = 1.0
    source_hit_rate = 1.0
    avg_keyword_hit_rate = 1.0
    PRD Status = PASS

Output reports:

    reports/evaluations/2026-05-12_multiturn_eval.csv
    reports/evaluations/2026-05-12_multiturn_eval.md

---

## 6. PRD Impact

The PRD requires a multi-turn RAG QA service.

This enhancement strengthens that requirement by validating more follow-up scenarios, including English, Chinese, and OCR-based follow-up questions.

The expanded evaluation confirms that:

- conversation history is used
- expected sources are retrieved
- follow-up answers contain expected evidence
- multi-turn QA remains stable after the BAAI/bge-m3 embedding model switch

---

## 7. Limitations

Current limitations:

- The expanded evaluation set is still relatively small.
- It does not yet cover long conversations with more than 2 turns.
- It does not test topic switching.
- It does not test conflicting memory.
- It does not test session expiration or memory cleanup.
- It does not test concurrent multi-session memory writes.

---

## 8. Future Work

Future improvements may include:

- 10+ multi-turn cases
- 3-turn and 5-turn conversation chains
- topic-shift handling evaluation
- memory conflict evaluation
- session TTL evaluation
- distributed memory validation
- concurrent memory write tests

---

## 9. Conclusion

Multi-turn Evaluation Set Expansion is completed.

Final status:

    PASS

The multi-turn evaluation set now includes 6 cases and all cases pass.
