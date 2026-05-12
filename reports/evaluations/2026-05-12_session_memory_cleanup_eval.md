# Session Memory TTL and Cleanup Evaluation Report

Date: 2026-05-12
Project: AIA RAG Case Study Service
Evaluation Type: Session Memory TTL / Cleanup / Capacity Guard

## Summary

- Total cases: 5
- Passing cases: 5
- Pass rate: 1.0
- TTL cleanup pass: True
- Max sessions pass: True
- Max turns pass: True
- PRD pass: True

## Case Results

### max_turns_retains_recent_turns

- Expected: Only the latest 2 turns are retained.
- Actual: [{'question': 'q2', 'answer': 'a2'}, {'question': 'q3', 'answer': 'a3'}]
- Pass: True

### ttl_cleanup_removes_expired_sessions

- Expected: Expired session is removed and active session is retained.
- Actual: removed_count=1; sessions=['active']
- Pass: True

### cleanup_disabled_keeps_expired_sessions

- Expected: Expired session is retained when cleanup is disabled.
- Actual: removed_count=0; sessions=['expired']
- Pass: True

### max_sessions_evicts_oldest_session

- Expected: Only 2 newest sessions remain and oldest session is evicted.
- Actual: sessions=['s2', 's3']
- Pass: True

### memory_state_export_import_compatible

- Expected: Memory can export and import state with TTL metadata.
- Actual: [{'question': 'q1', 'answer': 'a1'}]
- Pass: True
