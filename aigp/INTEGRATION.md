# Native integration and operational activation contracts

The full architecture is retained. Missing upstream engines and external services
are not renamed simulations and are not removed from the target.

This is a documentation publication. The research implementation described here was tested locally but is not uploaded in this directory. These contracts describe work needed for operational backends; none is evidence that those backends have been deployed.

## Native Biscuit scope backend

Replace the experimental capability wire only in a separately versioned profile.
Use the upstream Biscuit library with a pinned actual wire/library version. Validate
the authoritative signature, attenuation semantics, block trust, revocation ids,
resource/audience binding, expiry and delegation key possession. Pin the exact token
digest from ABC through the ledger. Datalog ambient facts must come from authenticated
resource/RP state; token facts cannot self-assert an arbitrary budget, trust root,
human approval or evidence mode. Raw token construction and negative attenuation
vectors must run against the actual library. Merely translating fields into a JSON
object called 'Biscuit' is not an integration.

## Native Cedar local policy backend

Use an upstream Cedar authorizer and schema, exact engine version and validated
entities/context. Root selection, deny precedence, assurance mode, principal/bond
binding, local thresholds and expiry must preserve the published rejection corpus.
An unavailable engine or schema/validation error denies; no silent permissive
fallback is permitted. A differential runner must compare all agreed policy cases,
including false facts supplied in the request, unknown entities, policy updates and
conflicting permit/forbid rules. Do not let a remotely provided policy overwrite
trusted RP policy. The native-engine result must be separately labeled from the
existing `aigp-static-v1` result.

## MCP and A2A native gateways

The current harness paths are real protocol-subset exchanges, not SDK or TCK results.
Connect unchanged upstream SDKs and conformance tools in a new integration profile.
Preserve normal clients that did not negotiate the extension. Transport metadata
must not widen authority. For MCP HTTP, retain its native authorization/audience
requirements and do not treat an AIGP scope token as arbitrary OAuth token passthrough.
For A2A, bind discovered tool/agent metadata to the action without confusing a signed
Agent Card with runtime attestation. Report all official failures and skips unchanged.
Maintain the shared ledger when a mission crosses bindings; do not reset it per tool.

## SPIFFE/SPIRE and real TLS endpoint identity

Keep the verified TLS 1.3 exporter and proof-of-possession tests. Obtain real workload
credentials through the authorized Workload API/SPIRE configuration and test rotation,
trust-domain federation, workload selectors, stale trust bundles and URI mismatch.
A self-issued test certificate with a `spiffe://` URI remains a fixture. The attested
key and the endpoint actually emitting the action must be bound; a quote borrowed
from another enclave or session must not suffice.

## RATS/EAT and hardware evidence

Introduce a concrete Evidence -> Verifier -> Attestation Result adapter. Use a pinned
vendor/evidence profile, manufacturer collateral, revocation/freshness validation,
nonce and report-data binding, reference values and allowed assurance modes. Require
an exact mapping from hardware evidence to the workload/session/PEP identity.
Recorded vendor test vectors may qualify the verifier parser and cryptographic
checks, but do not demonstrate a live measured deployment. Report such results as
VERIFIER_VECTORS, separately from LIVE_HARDWARE_ATTESTATION. CPU-only attestation does
not silently cover a GPU. Hashing a prompt does not prove reasoning correctness.
No amount of software votes may authorize a software-test key to assert hardware.
When no device/provider is available, run all parser/adversarial tests that are
possible and preserve this external activation gate; do not substitute an unconditional
success response.

## Legal identity, bond and AP2/payment adapters

A qualified identity backend must verify the actual selected credential ecosystem
and authorization chain, including principal-to-issuer delegation and its validity.
The current test registry is not vLEI/eIDAS/KYC evidence. A guarantee backend must
verify approved issuer identity, beneficiary, covered actions, instrument/currency,
validity, exclusions, aggregate reserved exposure and claim/runoff rules. Signatures
do not decide enforceability or ensure an insurer will compensate a loss.

An AP2 adapter should consume natively verified checkout/payment mandates, bind the
final action/amount/merchant/currency to the AIGP admission and preserve exact mandate
references in the receipt. Only an authorized provider can attest the corresponding
reservation and final settlement. A sandbox provider is not production money.
Retain UNKNOWN for ambiguous outcomes, permanent terminal non-application evidence
before release, and cross-RP aggregate exposure. Never send real money or sign an
insurance contract under the research automation mandate.

## Transparency and global deployment

Replace the bounded full-leaf fixture with a reviewed transparency implementation
and verified inclusion/consistency proofs. Add independent checkpoint witnesses or
gossip to investigate split views. Such logs do not repair a malicious PEP by merely
recording its hash. Protect the serialization domain against key/storage cloning or
partition its consumable authority into demonstrably disjoint allocations. Measure
revocation propagation on the actual topology; specify both availability cost and
in-flight expiry. A synthetic 1,000-domain simulation is not that measurement.

## Activation decision

The research-profile gate and operational gate are separate. Software-test publication
can proceed with explicit gaps. Deployment involving real consequences cannot pass
until the actual required backend receipts exist. Additional stages do not shrink
the architecture or redefine earlier unexecuted properties as optional successes.

License: CC BY 4.0. Project initiative and direction: Mohammed Messaoudene; AI assistance disclosed.
