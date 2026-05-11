# Optimization Report: Lightweight Multi-turn Memory

Date: 2026-05-11  
Project: AIA RAG Case Study Service  
Report Type: PRD Gap Closure / Feature Enhancement  
Optimization Area: Multi-turn RAG QA  
Related Components: `app/core/session_memory.py`, `app/api/chat.py`, `app/rag/generator.py`, `configs/app.yaml`

---

## 1. Purpose

This report documents the implementation of lightweight multi-turn memory.

The goal was to address the PRD requirement for a multi-turn RAG QA + generative service.

---

## 2. Initial Gap

Before this change, the `/chat` API accepted and logged `session_id`, but each request was answered independently.

The system did not use previous conversation turns when generating a follow-up answer.

This meant the service was closer to single-turn RAG QA, even though the PRD expected multi-turn RAG QA.

---

## 3. Change

Added a lightweight in-memory session memory implementation.

New component:

    app/core/session_memory.py

Behavior:

- stores recent conversation turns by `session_id`
- keeps only the latest N turns
- default max_turns = 3
- resets when the service restarts
- does not require database or external storage

Updated generation flow:

1. `/chat` receives the current question and optional `session_id`.
2. The current question is still used as the retrieval query.
3. Recent conversation history is loaded by `session_id`.
4. The generator prompt includes conversation history.
5. The generator is instructed to use conversation history only for understanding follow-up references.
6. The retrieved context remains the only source of policy truth.
7. After generation, the current question and answer are stored back into session memory.

---

## 4. Design Principle

The implementation intentionally keeps retrieval grounded in the current question and keeps retrieved context as the source of truth.

Conversation history is used for follow-up understanding, not as authoritative policy context.

This reduces the risk of hallucination from previous answers while still supporting basic multi-turn behavior.

---

## 5. Validation

Manual two-turn test was performed with the same session ID:

    session_id = multi-turn-demo-001

Turn 1:

    What are the audit logging requirements?

Turn 2:

    How long should they be retained?

Observed result:

    Operational logs should be retained for at least 90 days,
    while audit logs for privileged operations should be retained for at least one year.

This shows that the second question was handled as a follow-up question.

Structured logs also confirmed both requests were written with the same session ID:

    session_id = multi-turn-demo-001

---

## 6. Known Limitations

This is a lightweight MVP memory implementation.

Current limitations:

- memory is in-process only
- service restart clears memory
- memory is not shared across multiple service instances
- retrieval query still primarily uses the current question
- no history-aware query rewriting
- no conversation summarization
- no persistent session storage

---

## 7. Future Enhancement

A more advanced memory system should be implemented later.

Future options:

- persistent session storage
- conversation summarization
- history-aware query rewriting
- retrieval query expansion based on recent turns
- evaluation set for multi-turn QA
- production-grade shared memory store for multi-instance deployment

---

## 8. Conclusion

Lightweight multi-turn memory is implemented and validated.

This closes the basic PRD gap for multi-turn RAG QA at MVP level.

Final status:

    Completed
