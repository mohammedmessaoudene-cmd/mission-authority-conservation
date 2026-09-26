# Security boundary

This document describes a locally tested research fixture. Its executable implementation is not uploaded in this directory; see README.md for the documentation-only publication status.

Research software only. Do not place this fixture on the public Internet or give it
real banking, messaging, confidential-data or physical-actuator credentials.

The adversary may submit malformed or altered documents, replay evidence on another
connection, use an untrusted issuer, present stale revocation information, widen a
delegation, replace a capability with the same identifier, exceed a shared allocation,
or repeat an effect after a lost response. The RP policy and its initial roots,
cryptographic implementations, clocks, verifier decisions, principal provisioning,
ledger and resource implementations are trusted. Endpoint keys are software keys.

All administrative Python methods are trusted internal interfaces. They are NOT
ready-to-expose unauthenticated RPC methods. The ledger accepts only pinned RP
admissions; a malicious RP is outside the current adversary model. Resource effects
are local rows atomically committed with a receipt. No analogous atomicity is
established for an external bank, SMTP service or actuator.

The `software-test` appraisal hashes actual source bytes but does not prove that
an uncompromised measured runtime executed them. No TEE, TPM, GPU attestation,
non-exportable key, WebAuthn ceremony, signed manufacturer quote, remote QVI or
licensed insurer was exercised. Hardware requirements deny the test appraisal.

Local revocation checkpoints prevent a sequential rollback while that RP's storage
is intact. They cannot defeat simultaneous privileged rollback of clock, database
and keys, nor a global split view without witnesses. An issuer can cause denial of
service. Freshness enforcement trades availability for safety during partitions.
In-flight permits are bounded by their effective expiry; they are not globally
recalled. The logical clock is injected in deterministic tests.

Reputation events are signed observations with local policy. A trusted dishonest
reporter can still lie; a threshold is not an adjudication of fault or an injection
detector. Content provenance/taint is not a complete semantic-information-flow
system. Explicitly allowed false content is preserved as a negative limitation.

A simulated bond limits an exposure allocation; it is not a solvency, insurance,
financial settlement or enforceable compensation guarantee. Completed exposure is
conservatively retained; no automatic release or slashing occurs. Disputes are
separate administrative records. No law is encoded by the fixture.

Known critical production limit: cloning the ledger with its signing key allows
independent copies to over-allocate while each local accounting invariant holds.
The reproduced test produces 200 units from two copies of an allocation of 100.
No anti-cloning claim is permitted.

There is no external audit, independent implementation of the full engine, official
MCP/A2A conformance run, multi-platform campaign, network DoS qualification or global
latency measurement. The JavaScript verifier checks signatures and selected links
only. Public issues must not contain secrets, real credentials or uncoordinated disclosures about unrelated live systems.

License: CC BY 4.0. Project initiative and direction: Mohammed Messaoudene; AI assistance disclosed.
