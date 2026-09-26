# AIGP: Federated Acceptance and Evidence-Bound Enforcement

**Documentation snapshot 0.2.0-docs, describing research profile 0.2.0. Not peer reviewed. Not a production trust network or an accepted standard.**

AIGP retains the full architectural scope: operational agent identity, principal identity, recipient-local acceptance, policy enforcement, session-bound attestation results, transparency, delegation, revocation, reputation, approvals, guarantee exposure, and effect accounting and recovery. It is not just a mission-budget counter and does not replace TLS, MCP, A2A, or their authorization mechanisms.

## Read the architecture

- [Research paper — PDF](paper/main.pdf) and [editable LaTeX](paper/main.tex)
- [Complete research specification](SPEC.md)
- [Native integration and operational activation contracts](INTEGRATION.md)
- [Trust assumptions and unresolved security limits](SECURITY.md)
- [Local validation record and its limitations](VALIDATION.md)
- [Provenance and AI assistance](PROVENANCE.md)
- [License](LICENSE) and [citation metadata](CITATION.cff)

The paper was compiled successfully on GitHub from the published LaTeX source. Its [build record](paper/BUILD_RECORD.txt) and [checksums](paper/SHA256SUMS.txt) are available. This document build does not execute or transfer the AIGP reference implementation.

## Publication status

This directory publishes the architecture documentation and manuscript. **The complete executable implementation is not uploaded here.** The originating assistant reproduced the software locally, but the platform blocked its code-transfer tool calls. A passing local test result is not evidence that source files are present in this repository. The former Mission Authority Conservation 0.1.0 release and its Zenodo DOIs do not identify the broader AIGP architecture.

No new Zenodo DOI, institutional endorsement, patent, or exclusive worldwide priority is claimed. The current publication documents only the material actually accessible in this directory.

## What the architecture connects

An agent presents evidence about its issuer, principal, delegated scope and execution environment. Each relying party independently selects its accepted issuers, identity registries, appraisal verifiers, guarantors, approvers and reputation reporters. Evidence is bound to the recipient, the session and the exact action. An admission remains separate from an execution permit: a shared ledger first reserves mission resources and simulated guarantee exposure. The resource records its local effect and terminal receipt atomically. An unknown result retains its reservation until a suitable receipt resolves it.

The local research implementation exercises real signatures, mutually authenticated TLS 1.3 with exporter binding, limited MCP and A2A harness paths, persistent revocation checkpoints, cross-recipient budgets, crash recovery and replay rejection. Its identity registry, hardware appraisal and guarantee provider are **software fixtures**, not qualified institutions. Native Biscuit/Cedar, live hardware attestation, qualified identities, real insurance, AP2 settlement and official protocol conformance remain unexecuted integrations.

## Bounded local evidence

The recorded local checks comprise 105 ordinary tests, 256 combinations of eight fixture faults, four selected source mutations, a 17-object JavaScript signature/link check, and concurrency/crash experiments. Re-execution on 26 September 2026 reproduced all five runner stages. These are same-project software experiments, not independent human or production validation.

The known privileged-cloning limit remains: two copies of an authority funded with 100 can produce 200 units of fictional effects. An authorized message may still contain false content. The architecture does not guarantee truth, universal exactly-once effects, worldwide instantaneous revocation, or legal compensation.

## Attribution and licensing

Project initiative and direction: **Mohammed Messaoudene**. Design synthesis, implementation, tests and writing used disclosed AI assistance. Requester-supplied reports attributed to Grok, Claude and DeepSeek informed the architecture. AI review perspectives are not independent institutional committees.

This documentation and the paper: **CC BY 4.0**. The separately prepared software is designated Apache-2.0, but is not distributed through this directory. Existing AUEC and AOR licenses and releases are unchanged.

M. Messaoudene is a Maître de conférences B (MCB) at Belhadj Bouchaib University of Ain Temouchent, Ain Temouchent, Algeria (e-mail: mohammed.messaoudene@univ-temouchent.edu.dz; ORCID: 0009-0007-4665-2548). This affiliation identifies the author's academic appointment only and does not imply sponsorship, collaboration, or endorsement by the university.
