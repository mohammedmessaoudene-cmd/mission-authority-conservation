# Validation record — documentation snapshot

This document reports local experiments, not a GitHub-hosted reproduction of the AIGP software. The executable reference implementation could not be uploaded. Consequently this documentation snapshot alone does not enable an independent replay of its software experiments.

## Replay on 26 September 2026

The original research package was safely extracted and its 67-file manifest verified. Its five-stage runner finished at `2026-09-26T01:10:02Z`. Each stage returned exit status zero:

| Stage | Result |
|---|---|
| Ordinary test methods | 105 passed; no skipped tests or expected failures |
| Authored eight-fault composition corpus | 256 combinations; one clean acceptance, 255 refusals |
| Selected source mutation experiments | Four unsafe outcomes observed under mutation, focused red tests, safe restoration |
| Process, concurrency and counterexample experiments | Passed their declared assertions, including the known unsafe cloning case |
| Node.js public verification | 17 signatures and selected object links checked |

These are same-project tests of a software fixture, not human review, official MCP/A2A conformance, broad adversarial coverage or operational certification. The environmental replay used Python 3.13.5, Node.js 22.16.0, cryptography 46.0.4 and pyOpenSSL 25.3.0.

## Corrective history retained in the local artifact

The first 87 tests passed. Four added composition tests then failed because expected denials did not occur. Corrections bound the exact root capability into the ABC, checked the exact leaf token against the ledger, checked revocation throughout the capability chain, and prohibited removal of already revoked identifiers. The corrected suite passed 91 tests. Protocol-path, mutation-contract and second-language verification tests increased the ordinary total to 105.

The four subsequent source mutations concern assurance promotion, session binding, aggregate guarantee exposure and capability revocation. The exposure mutant permits 120 fictional units against a guarantee allocation of 100. Restoration rejects the unsafe case. Those intentionally failing mutants are separate experiments, not hidden failures inside the ordinary test suite.

## Limits preserved

Two privileged copies of a funded authority, including its signing key, produce 200 units of fictional effects from an original allocation of 100. A local invariant can hold in each copy while global conservation fails. There is no anti-cloning guarantee.

An authorized send action containing `2+2=5` passes authorization. Permissions do not establish truth. Real hardware evidence, qualified identity, real insurance, native Biscuit/Cedar and AP2 integrations, upstream protocol conformance and independent human validation remain unavailable.

A conventional SQL baseline preserves the tested budget as well. No exclusive invention of transactional accounting is claimed. Local benchmarks in the manuscript retain their historical run and scope; repeated-run timings are not silently substituted into that frozen table.

## Artifact identification

The following SHA-256 values identify the locally held replay evidence. A hash identifies bytes; it does not by itself prove that those bytes are publicly available.

| Local artifact | SHA-256 |
|---|---|
| `local-results/summary.json` | `0e4d015c0ec49d240268645922e8ca54a18624773d093dfca832b5b10d16a0e4` |
| `local-results/tests.log` | `b3a8ad71e6751e828c07a7d195321412ac0daf1f84d2ddc2acec9f91903edb63` |
| `local-results/mutations.json` | `fb66f13eb8eb6e18a89a6b684ca498c50f00b832870e22cc7f13edcff6ba68cc` |
| `local-results/experiments.json` | `057ac097274d3b92bf3eaab88feb5f40e42742b8cb59b4f4101990f159bcc46b` |
| `local-results/node-verifier.log` | `840f1e369c23e4c6a787b2b9f47152aa4c68922b2811d00c9e8ca650ed9ef0cc` |

The original six-page PDF rebuilt to SHA-256 `f4b02e001cd367066377dd88276b589dd60d4b849738cc264e1c3b235d2641f9`. The documentation edition changes availability wording and therefore has a different PDF. Its locally compiled source matches the GitHub source blob `478f06181d88d595dabdbfa8fc417fb17f6c898a`; compilation reported no undefined references or overfull lines.

License: CC BY 4.0. Project initiative and direction: Mohammed Messaoudene; AI assistance disclosed.
