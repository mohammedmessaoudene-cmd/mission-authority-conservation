# Security scope

Research software only. No production deployment or security certification is
claimed. The gate and resource must be honest, their keys protected, clocks
trusted, and each root allocation managed in a single non-cloned serialization
domain. The actual resource must enforce every effect on the governed path.

## Reproduced limitation

Cloning the gate's storage and keys allows independent spending from both
histories. Two budgets of 100 created by copying one authorized state produce
200 units of effects. Both local audits pass. This is an explicit counterexample
to an anti-cloning claim, not an expected safe production behavior.

## Other limitations

An in-flight permit can still execute before expiry after local revocation.
Unknown results can permanently immobilize allocation. A software approval key
is not evidence of human presence. A valid request can carry false content.
Internal Python methods and multiprocessing pipes are trusted test interfaces.
No untrusted API deployment, root isolation, hardware TEE, TLS/DPoP binding,
provider integration or general exactly-once guarantee is implemented.

Potential issues in this research artifact may be reported to
mohammed.messaoudene@univ-temouchent.edu.dz. No response time, bounty, contractual
warranty, or production incident support is promised.
