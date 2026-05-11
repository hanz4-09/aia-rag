# Multi-turn Evaluation Report

Date: 2026-05-11
Project: AIA RAG Case Study Service
Evaluation Type: Multi-turn QA Evaluation

## Summary

- Total cases: 3
- Passing cases: 3
- Pass rate: 1.0
- History used rate: 1.0
- Source hit rate: 1.0
- Avg keyword hit rate: 1.0
- PRD pass: True

## Method

Each case contains two turns with the same session_id.
The second turn is a follow-up question.
The evaluator checks whether conversation history was used,
whether the answer was not refused, whether expected source was hit,
and whether expected keywords appeared in the second-turn answer.

## Case Results

### mt_audit_log_retention

- Category: compliance
- Turn 1: What are the audit logging requirements?
- Turn 2: How long should they be retained?
- History turns used: 1
- Source hit: True
- Keyword hit rate: 1.0
- Pass: True
- Answer preview: Audit logs for privileged operations should be retained for at least one year. Operational logs should be retained for at least 90 days, unless a longer retention period is required by legal, security, or business requirements.

### mt_api_key_incident_report

- Category: security_cn
- Turn 1: API Key 泄露后应该怎么处理？
- Turn 2: 多久内要报告？
- History turns used: 1
- Source hit: True
- Keyword hit rate: 1.0
- Pass: True
- Answer preview: 如果员工怀疑 API Key 已经泄露，必须在 24 小时内向 Security Operations 团队报告。

### mt_annual_leave_approval

- Category: hr_policy
- Turn 1: What is the annual leave policy?
- Turn 2: How long does the manager have to review it?
- History turns used: 1
- Source hit: True
- Keyword hit rate: 1.0
- Pass: True
- Answer preview: Managers should review leave requests within three working days.
