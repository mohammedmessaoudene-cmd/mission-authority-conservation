# AIGP federated enforcement — research profile 0.2.0

**Documentation snapshot, 26 September 2026.** This specification describes the locally tested research implementation. Its executable source has not been uploaded to this directory: platform checks blocked software-transfer calls. This documentation publication is not a complete executable software release. Implementation statements below refer to the local research artifact, not to code available in this GitHub directory.

## 1. Scope and terms

This is a complete *architectural scope* with a software-test implementation. It is
not a completed hardware-backed, legally operational federation. The four original
pillars remain requirements rather than being replaced by the budget subsystem.
Words MUST and MUST NOT express this research profile's requirements, not adoption
by a standards organization.

A principal delegates a mission. An issuer signs an Agent Binding Certificate (ABC).
A registry identifies that principal. A verifier signs an appraisal result. A
guarantor describes exposure terms. A log records the ABC/kernel commitment. Each
relying party (RP) independently selects roots and acceptance rules. The RP's PEP
checks every admitted request. A shared ledger accounts for both mission resources
and guarantee exposure. A resource applies the effect and creates a durable receipt.
These roles are distinct keys and software objects; only selected boundaries are
isolated as processes. The fixture must not be called a secure OS sandbox.

## 2. Federation and roots

Each RP has separate accepted sets for operational issuers, identity registries,
guarantors, appraisal verifiers, logs, approvers and reputation reporters. No key is
accepted merely because its signature is valid. Root provisioning is a trusted local
administrative act, outside messages received from an agent. Neither federation
membership nor a logged certificate automatically overrides RP policy.

The registry statement binds principal and permitted operational issuer. The ABC
binds that identity reference, the principal, the agent's public key, the workload
TLS SPKI digest, the approved PEP digest, the discovered tool-manifest digest, the
exact root-capability digest, the bond reference and a bounded validity period.

## 3. Encoding and signatures

The implemented profile is `aigp-json-ed25519/0.1`: an exact five-field envelope
(profile, kind, kid, body, sig). `kid` is SHA-256 of the raw Ed25519 public key. A
signature covers `AIGP-REFERENCE\0` followed by canonical bytes of the other four
fields. The canonical domain is restricted ASCII JSON, unique keys, bounded nesting,
bounded item counts and safe integers; floating point is rejected. This is not COSE,
Biscuit, a generic VC, or general RFC 8785. Untrusted inputs cannot select algorithms
or expand the set of acceptable roots.

Kinds include ABC, IDENTITY, BOND, ATTESTATION_RESULT, LOG, REVOCATION, CAPABILITY,
POP, SESSION, ACTION, APPROVAL, ADMISSION, PERMIT, RECEIPT and REPUTATION.
Different kinds are different signature domains. The code enforces exact body
schemas at receiving boundaries.

## 4. Session and attestation-result binding

The actual TLS fixture requires mutually authenticated TLS 1.3, pins each expected
URI identity after chain validation and obtains 32 bytes from the real TLS exporter.
Its label is `EXPORTER-AIGP-REFERENCE`; its context is `aigp/0.2.0`. The server issues
a fresh nonce. The signed appraisal binds nonce, exporter, workload SPKI, ABC hash,
kernel and manifest. A separate proof of possession is signed with the agent key
and binds the same context. Reusing the challenge is rejected persistently.

An appraisal verifier has an allowed set of assurance modes in RP policy. The
fixture verifier is authorized only for `software-test`. Declaring `hardware` in a
newly signed fixture appraisal does not enlarge that set. The high-assurance profile
requires a real approved evidence backend; no fallback is allowed. No claim that
source hashing proves remote execution is made.

The session ticket binds RP, ABC, channel, exact policy digest and current revocation
sequences. Its expiry is no later than 20 logical seconds and no later than the
expiry of any required credential/checkpoint. All relevant documents are rechecked
at action admission and before dispatch. A changed policy or epoch requires a new
session rather than silently extending old authority.

## 5. Delegation and policy

The native research engine is `aigp-static-v1`; selecting an unavailable engine is
an error. Each capability is signed, names a principal and subject key, and limits
operations, destinations, RPs, expiry and a three-component allocation. A child
commits to the exact parent token, narrows its sets and expiry, and is signed by the
parent subject. The root token must exactly match the ABC's committed digest and
operational issuer. The ledger compares the exact leaf-token hash with its installed
copy: a same-name substitute is not sufficient authority. The principal's revocation
snapshot can revoke any capability identifier in the submitted chain.

Delegation is not just portable token creation. Installing a delegated capability
moves its allocation out of the parent's available resources. A token that was not
installed obtains no budget. The trusted administrator provisions a mission root;
this is not an agent-controlled method of manufacturing an unlimited treasury.

Each action binds id, cap, RP, resource, operation, destination, arguments, discovered
manifest, session and validity. Cost is recomputed from the defined fixture operation,
not trusted from an LLM. The resource independently recomputes that cost.

Approvals are required for an experimental money threshold or for send/export. The
approval key has a separate role and signs the exact action and session. Two arbitrary
software signatures cannot substitute for it. This tests role separation, not human
presence. A production ceremony needs its own verified authentication and consent UX.

## 6. Revocation, transparency and reputation

Each credential issuer publishes a signed, time-bounded snapshot with an increasing
sequence and explicit revoked identifiers. Required snapshots cover operational
issuer, identity registry, guarantor and appraisal verifier. Missing or expired
snapshots cause refusal. The RP persists the last sequence and hash, rejects lower
sequences or same-sequence equivocation, and rejects removal of already revoked
identifiers. This profile makes revocation terminal; renewal requires new objects.
It does not enforce a universal global update latency.

The transparency fixture signs a Merkle root plus its bounded full leaf list. The RP
verifies membership, root and append-only prefix continuity against its local state.
This deliberately simple O(n) fixture is not a deployment of Rekor, SCITT or an
Internet-scale consistency/gossip service. A hash in a log does not make code benign.
An independent approved-kernel set is still required.

Reputation uses signed evidence-reference events from locally approved reporters,
deduplicated by event id. The test policy degrades consequential actions after three
unexpired events concerning the same principal. Another RP may make a different
decision. Events do not prove semantic truth, prompt injection, fraud or legal fault.

## 7. Guarantee and settlement representation

A bond binds principal, beneficiaries, covered operations, currency, per-action
limit, aggregate exposure, terms hash, assurance profile and expiry. RP acceptance
checks these fields and trusts the guarantor separately from the operational issuer.
The executed profile uses currency `TEST` and `test-exposure` terms. The registry and
bond fixtures must never be labeled qualified identity or real insurance.

A shared ledger atomically reserves mission resources and aggregate bond exposure.
Two RPs presenting the same bond cannot each consume its whole remaining capacity
inside this serialization domain. The amount reserved is a test exposure allocation,
not an actuarial risk model. Exposure remains consumed after a committed effect,
conservatively avoiding an unsupported claim-tail release policy. Real instruments,
claims, runoff and settlement require a separate provider contract.

A dispute is a separate administrative record. Opening it neither establishes fault
nor seizes collateral, revokes access or changes an execution receipt. Automatic
slashing is not implemented or claimed as a legal remedy.

## 8. Effects and uncertainty

The action states are RESERVED, DISPATCHED, UNKNOWN, COMMITTED and ABORTED. An
unemitted reservation may be canceled and returned. A dispatched action with no
response becomes UNKNOWN, not ABORTED. Both resources and exposure remain reserved.

The permit commits to the admission, action, RP, manifest, cost and effective expiry.
The resource validates it, then atomically records a fixture effect and its receipt.
A repeated permit returns the same receipt. A precondition failure is recorded as a
permanent NOT_APPLIED tombstone, so a delayed replay cannot execute after refund.
A missing lookup result is not a proof of non-application. Only an authenticated,
exactly linked terminal receipt permits reconciliation.

For capability c and component j, the invariant is:

`allocation[c,j] = free[c,j] + pending[c,j] + spent[c,j] + children[c,j]`.

For each bond: `held + used <= total`. These are conditional on a single honest,
non-cloned serialization domain, correct storage and trusted resource behavior.
A cloned ledger with its key violates the global invariant; the negative experiment
is preserved. Issuer, RP or resource collusion is not repaired by signatures.

## 9. Binding coverage

MCP: actual subprocess stdin/stdout initialize, initialized notification, tools/list
and tools/call. The tool exposes the integrated local research transaction. No official
SDK/TCK or HTTP OAuth profile was run. Experimental raw TLS framing is not mislabeled
as an MCP transport. Production OAuth audiences and token-passthrough prohibitions
must be maintained by the native integration.

A2A: a limited SendMessage JSON-RPC/data-part path is exercised over local HTTP and
returns a Message. It reaches the same TLS/PEP/ledger pipeline; the two bindings can
share mission state in a single gateway. This is not full A2A implementation or TCK
conformance. It does not claim a deployed fleet of autonomous LLMs.

AP2: architectural mapping to verified checkout/payment authorization and a separate
rail adapter, not an executed native AP2 mandate verifier or actual payment provider.
SPIFFE: real certificate URI identity pins under a local test CA, not a running SPIRE
control plane. RATS/EAT: role and evidence-binding contracts; the JSON appraisal is
not a native EAT or proof that real vendor evidence was verified. Biscuit/Cedar are
native backend targets rather than names applied to the custom engine.

## 10. Qualification boundaries

A research release may be qualified when its complete coverage ledger, executable
fixtures, failures, limitations, source, paper and reproducibility checks are public.
Operational qualification additionally requires native engines/protocols, verified
hardware evidence, workload isolation, guarded side effects, non-cloned authority,
identity/bond providers and external review. A signed assertion or a successful
software mock is never allowed to silently satisfy those operational requirements.

**Current publication boundary:** this documentation snapshot does not satisfy the complete-source-public condition. The local artifact and test evidence exist, but software upload was blocked. This limitation does not remove any architectural requirement above or turn a fixture into a production integration.

License: CC BY 4.0. Project initiative and direction: Mohammed Messaoudene; AI assistance disclosed in README.md.
