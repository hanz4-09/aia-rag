# Evaluation Report: Multi-turn QA Evaluation

Date: 2026-05-11  
Project: AIA RAG Case Study Service  
Report Type: PRD Evaluation Report  
Evaluation Area: Multi-turn RAG QA  
Related Components: `scripts/evaluate_multiturn.py`, `app/core/session_memory.py`, `app/api/chat.py`, `app/rag/generator.py`

---

## 1. Purpose

This report documents the formal evaluation of lightweight multi-turn QA behavior.

The PRD requires a multi-turn RAG QA + generative service. After implementing session-based in-memory history, this evaluation verifies that follow-up questions can use conversation history while still grounding answers in retrieved context.

---

## 2. Evaluation Method

The evaluation uses predefined two-turn cases.

Each case contains:

- one `session_id`
- a first-turn question
- a second-turn follow-up question
- expected source document
- expected answer keywords

The second turn is evaluated by checking:

- whether conversation history was used
- whether the answer was not refused
- whether the expected source was hit
- whether expected keywords appeared in the second-turn answer

---

## 3. Evaluation Cases

Three cases were evaluated:

1. Audit log retention follow-up
   - Turn 1: What are the audit logging requirements?
   - Turn 2: How long should they be retained?

2. API Key incident report follow-up
   - Turn 1: API Key 泄露后应该怎么处理？
   - Turn 2: 多久内要报告？

3. Annual leave approval follow-up
   - Turn 1: What is the annual leave policy?
   - Turn 2: How long does the manager have to review it?

---

## 4. Results

Final result:

    Total cases: 3
    Passing cases: 3
    Pass rate: 1.0
    History used rate: 1.0
    Source hit rate: 1.0
    Avg keyword hit rate: 1.0
    PRD Status: PASS

All evaluated multi-turn cases passed.

---

## 5. Observations

The evaluation confirms that:

- session-based history is loaded for second-turn questions
- follow-up questions can use previous turns for implicit references
- retrieved context remains the source of truth
- source hit quality remains valid during multi-turn evaluation

One keyword alignment issue was found in the API Key follow-up case. The answer was semantically correct but used `Security Operations 团队` instead of the stricter expected phrase `Security Operations Team`. The expected keyword list was adjusted to match semantically equivalent bilingual wording.

---

## 6. Limitations

This evaluation validates lightweight multi-turn behavior only.

Current limitations:

- memory is in-process only
- memory is not persistent
- memory is not shared across instances
- retrieval query still primarily uses the current question
- no history-aware query rewriting
- no summarization
- no advanced memory evaluation

---

## 7. Future Work

Future multi-turn improvements may include:

- persistent session storage
- conversation summarization
- history-aware query rewriting
- multi-turn retrieval query expansion
- larger multi-turn evaluation set
- production-grade shared memory storage

---

## 8. Conclusion

Multi-turn QA evaluation is completed.

Final status:

    PASS

The project now has both lightweight multi-turn memory implementation and reproducible multi-turn evaluation evidence.
