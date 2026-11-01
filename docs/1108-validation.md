# Release 1108 validation

Run from the repository root:

```sh
python3 tests/test_finance.py
```

Requires Python Playwright and Chromium at `/usr/bin/chromium`. The test starts an ephemeral loopback HTTP server and uses an isolated browser. Financial data and Supabase responses are synthetic; no production writes are made.

Covered: partial/full payment, excess payment rejection, local persistence failure rollback, payment history and legacy paid balance, supplier statement and print document, purchase filters, expense suggestions, project details, three-way record reconciliation and deletion, stale conditional writes, upload failure status, complete simulated sync round trip, backup read-back and corruption, and inclusion of accounting records.

Cloud synchronization uses the existing `updated_at` column and conditional update with returned rows. Authenticated access and deployed RLS policies must support update/insert/select. This has not been tested against the live Supabase project. The batch across tables is not a database transaction: successful earlier groups remain saved when a later group fails, and the UI must keep the failure visible. Same-record concurrent edits stop synchronization for review; export a local backup before reconciliation. Every active device must update to 1108: older clients still use unconditional writes. First synchronization of differing legacy records without timestamps stops instead of choosing a version silently.

Existing project accounting formulas are retained; the new breakdown makes their inputs visible and does not certify tax treatment. Backup file read-back verifies persisted JSON, not a full disaster recovery exercise. Missing or oversized referenced attachments prevent an automatic backup from being reported complete. Manual export can contain attachment warnings. Cloud-only data not downloaded to the device cannot be included.
