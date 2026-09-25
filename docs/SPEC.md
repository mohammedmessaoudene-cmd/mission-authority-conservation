# Mission Authority Conservation — executable research profile 0.1.0

Status: narrative specification of a software-only laboratory; not an adopted
standard, legal contract, insurance agreement, or production security profile.
The key words below state the behavior of this profile, not an external RFC.

## 1. Roles and assumptions

A principal creates a root allocation; an actor proposes actions and delegates;
a distinct approval key authorizes exact high-cost/export actions; a gate
serializes the allocation; a resource produces fictional effects and terminal
receipts. The actor cannot establish authority by declaring a cost or policy.

The gate, resource, principal, storage and clocks are trusted within the positive
claim. One root allocation MUST have one non-cloned serialization domain. Key
material is software-only; the process fixture is not adversarial isolation.
Root allocations are per mission, not a shared cap on all principal activity.

## 2. Value and signature domain

The value profile is ASCII JSON with sorted object keys, compact separators,
integers bounded by abs(x)<=2**53-1, no floats or duplicate keys, at most 65,536
canonical bytes, depth at most 16, strings at most 16,384 characters, lists at
most 1,024 items and objects at most 64 entries. It is NOT general RFC 8785.
Exact message schemas reject unknown fields at their designated boundary.

An envelope has exactly kind, kid, payload, signature. The key identifier is the
lowercase SHA-256 hex digest of the pinned raw Ed25519 public key. The signature
is 64 bytes encoded as 128 lowercase hexadecimal characters. The signed preimage:

    ASCII('ATLAB/0.1') || 0x00 || ASCII(kind) || 0x00 ||
    Canon({"kid": kid, "payload": payload})

This retains the original laboratory domain prefix; the project name is not a
new wire revision. Signatures do not certify truth or runtime integrity.

## 3. Payloads (exact field sets)

| Kind | Required payload fields | Signer |
|---|---|---|
| MISSION | id subject aud ops dest expires budget | principal |
| DELEGATE | parent id subject aud ops dest expires budget | parent's actor |
| INVOKE | iid mission cap actor aud op target params deadline policy | actor |
| PREPARED | action_hash cost resource_version expires aud | resource |
| APPROVE | action_hash preview_hash cap epoch expires decision | approval role |
| DISPATCH | iid action_hash preview_hash cost aud cap epoch expires resource_version | gate |
| RECEIPT | iid action_hash preview_hash cost result epoch aud | resource |
| REVOKE | cap epoch | principal |

Identifiers on INVOKE are nonempty ASCII strings at most 128 characters. An
operation is pay, send or export. Pay takes exactly amount_minor, a positive
integer (not bool). Send takes exactly message, an ASCII string. Export takes
exactly dataset: dataset-a (80 bytes) or dataset-b (240 bytes). All are fixtures.

PREPARED binds the exact canonical action hash. Its expiry equals the action
deadline and its audience equals the action audience. The gate checks the
resource signature and version, then independently verifies subject, mission,
audience, scope, policy and capability chain. Cost is a three-component
nonnegative integer vector, not an actor-trusted estimate.

## 4. Allocation and delegation

For each capability v and each component:

    B[v] = F[v] + P[v] + C[v] + sum(B[child] for child of v)

P includes RESERVED, DISPATCHED and UNKNOWN. A child allocation is removed
atomically from F[parent]. Child operations/destinations are subsets of the
parent's; audience is unchanged; expiry does not exceed the parent's. Revoked
or expired ancestors invalidate new covered dispatches. Child budget reclamation
is deliberately absent. All conservation checks are componentwise.

## 5. Approval and temporal revalidation

Approval is required for export or a fictional monetary amount >=50. This is a
test threshold, not advice for real transactions. The dedicated key MUST bind
action_hash, preview_hash, capability, current epoch, decision='approve', and
expiry. Another actor/principal signature cannot substitute for this role.

At reservation the effective expiry is min(action deadline, capability expiry,
approval expiry when required). At dispatch the gate rechecks chain, epoch,
expiry, resource version and stored policy version. Persist DISPATCHED before
returning a permit. The resource checks expiry/version/cost before a new effect.
A correct repeat of an already terminal identifier returns its old receipt.

## 6. Outcome and refund

RESERVED -> DISPATCHED -> COMMITTED (bound APPLIED receipt).
DISPATCHED -> UNKNOWN -> COMMITTED or ABORTED (bound terminal receipt).
RESERVED -> ABORTED (trusted cancellation before permit release).
DISPATCHED -> ABORTED (bound durable NOT_APPLIED receipt).

A missing reply or absent lookup MUST NOT free P. NOT_APPLIED MUST be a durable
terminal resource record that prevents later application under the same iid.
A duplicate receipt does not re-account the cost. An identifier reused with
other action parameters is rejected. DISPATCHED/UNKNOWN cannot generate another
permit through begin(); a previously retained permit can be replayed to the
idempotent resource. Lost permits and absent receipts can therefore leave budget
permanently pending.

## 7. Revocation scope

Revocation is serialized at the gate and advances a global generation. It
blocks new covered dispatches after that local point. It does not recall an
in-flight permit at an unaware resource before expiry. The global generation
also invalidates older unstarted reservations in other missions; this is a
known availability cost. No propagation SLO or distributed consensus is provided.

## 8. Observable guarantees and limits

Ordinary test suite, model, source mutations, conventional baseline and cloned
state counterexample are separate evidence categories. Their execution is not
independent human validation. Actual fictional resource effect <= root budget
is conditional on unique resource execution, correct measured costs, no unsafe
refund, and the non-cloned trusted domain. Cloning the gate defeats the bound.

Detailed model, conditional proof and experimental methods appear in paper/main.pdf.
The JSON schemas are documentation aids; passing them does not establish semantic
conformance, signature validity, rights, freshness, or safe deployment.
