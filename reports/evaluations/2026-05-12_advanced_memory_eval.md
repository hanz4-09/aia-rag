# Advanced Memory Evaluation Report

Date: 2026-05-12
Project: AIA RAG Case Study Service
Evaluation Type: Advanced Memory v1 Evaluation

## Summary

- Total cases: 2
- Passing cases: 2
- Pass rate: 1.0
- Persistent memory pass rate: 1.0
- Query rewrite applied rate: 1.0
- Retrieval query resolution rate: 1.0
- Source hit rate: 1.0
- Avg keyword hit rate: 0.8334
- PRD pass: True

## Method

Each case contains two turns with the same session_id.
The evaluator validates persistent memory, history-aware retrieval query rewriting,
source hit, and keyword coverage on the second turn.

## Case Results

### am_audit_log_retention

- Category: compliance
- Turn 1: What are the audit logging requirements?
- Turn 2: How long should they be retained?
- First turn persisted: True
- Second turn persisted: True
- History turns used: 1
- Memory rewrite applied: True
- Rewrite strategy: previous_question_plus_current_follow_up
- Previous question in retrieval query: True
- Source hit: True
- Keyword hit rate: 1.0
- Pass: True
- Answer preview: Audit logs for privileged operations should be retained for at least one year.

### am_api_key_report_window

- Category: security_cn
- Turn 1: API Key 泄露后应该怎么处理？
- Turn 2: 多久内要报告？
- First turn persisted: True
- Second turn persisted: True
- History turns used: 1
- Memory rewrite applied: True
- Rewrite strategy: previous_question_plus_current_follow_up
- Previous question in retrieval query: True
- Source hit: True
- Keyword hit rate: 0.6667
- Pass: True
- Answer preview: 如果发现 API Key 泄露，必须在 24 小时内报告。
