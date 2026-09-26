# Mission Authority Conservation

**0.1.0-research — executable research profile, not a production security system.**

Software archive: [10.5281/zenodo.22967206](https://doi.org/10.5281/zenodo.22967206).
Companion research report: [10.5281/zenodo.22967208](https://doi.org/10.5281/zenodo.22967208).
The software archive is Apache-2.0; the report and narrative specification are
CC BY 4.0. The GitHub release contains both, with file-level licensing.

This laboratory studies one question: when agents delegate, approvals expire,
or an action loses its reply, how can the original mission allocation remain
conserved until the resource's effect is known?

The gate transfers (rather than copies) delegated budgets, binds approvals to
exact actions and resource-derived costs, and keeps an uncertain action's
reservation until a terminal resource receipt justifies settlement. The resource
atomically records fictional effects and receipts under unique invocation IDs.

## Reproduce

Python 3.11 or later is the intended environment; the included execution used
Python 3.11.9 on Windows. Install the pinned dependency and run from this directory:

```sh
python -m pip install -r requirements.txt
python -B run_all.py --out local-results
```

The command refuses to overwrite a non-empty result directory. It runs 98 test
methods (83 original, six spawned-process cases and nine evidence regressions), 10,000 generated admission
requests in ten authored families, a 1,638-state finite model, four selected
source mutations, a conventional transactional baseline, and a privileged-clone
counterexample. Counts are measured by the runner; no test may be skipped for a
positive release result. Four expected failing mutants are separate experiments,
not expected failures inside the ordinary test suite.

The fixture launches local Python processes and creates temporary SQLite rows.
No LLM API, bank, real mail service, TEE, MCP server, or A2A peer is invoked.
The pipe interface is trusted test infrastructure, not an authenticated public API.

## What the evidence says

* All 98 test methods pass in the recorded environment, with no skips.
* Each of four source mutants exposes a directly observed unsafe outcome,
  fails a focused assertion, and returns to safe behavior after restoration.
* The conventional SQL baseline is equally safe for its tested budget and
  deduplication objective; the new profile is not claimed to invent those guarantees.
* Two privileged copies of a gate with a budget of 100 produce 200 units of
  fictional effects. Anti-cloning and hardware rollback resistance are NOT provided.

There is no general exactly-once guarantee for arbitrary providers, truth
verification of model output, independent security review, or production readiness.
A live permit can outlast local revocation until it expires at an unaware resource.
UNKNOWN can remain unresolved and block budget indefinitely.

## Contents

`lab/`: reference core and experimental fixtures. `tests/`: 98 ordinary tests.
`tools/`: reproducible runners, source mutations, packaging and document checks.
`evidence/reproduced/`: selected execution records and exact source hashes.
`evidence/history/`: historical failed development checks, explicitly separated.
`docs/SPEC.md`: narrative profile. `docs/CLAIMS.json`: claim–evidence ledger.
`paper/`: English research report, editable LaTeX, bibliography and generated numbers.

The original private input archive has SHA-256
`38073bd5d0661b8bd624ef19f12b09ea0c5ed4b3c75a9b961551599c55499b03`.
It is not redistributed because it includes working prompts and third-party
proposal texts. `provenance.json` identifies the unchanged original core.

## Related work and attribution

Agent Contracts (Ye and Tan, arXiv:2601.08815) is direct prior art for hierarchical
resource conservation. AIP, aiAuthZ, OAuth RAR, and the individual IETF draft
`draft-das-rats-frontier-model-extraction-02` address adjacent authority boundaries.
AUEC (DOI 10.5281/zenodo.21815335) and AOR (DOI 10.5281/zenodo.22866138) are
previous artifacts by the author; this laboratory does not claim code integration
or inherit their protocol-conformance results. See the report for exact citations.

Project initiative and direction: **Mohammed Messaoudene**. Research synthesis,
implementation, testing and manuscript preparation used disclosed ChatGPT
and Codex assistance. Three Codex subagents reviewed engineering, science and
editorial evidence in isolated copies; the coordinating agent handled integration
and publication. Shared AI origin is disclosed; these are not independent human reviews.
AI review roles are not independent human or institutional committees.

Academic appointment: Maître de conférences B (MCB), Belhadj Bouchaib University
of Ain Temouchent, Algeria. This affiliation does not imply university sponsorship,
collaboration, or endorsement. ORCID: 0009-0007-4665-2548.

## Licences

New software, tests, schemas, executable evidence, root project metadata, and this
README: **Apache-2.0**. Paper and narrative documents under `docs/`: **CC BY 4.0**,
except machine-readable claims and source indexes explicitly mapped as Apache-2.0.
See `LICENSE` and `LICENSE-MAP.json`. Dependencies retain their own licences.
Previous AUEC/AOR releases are not modified or relicensed. No implied trademark,
legal-priority, insurance or certification claim accompanies this research release.

## Separate AIGP architecture documentation

[AIGP: Federated Acceptance and Evidence-Bound Enforcement](aigp/)
is a broader research architecture covering identity, recipient-local trust,
session-bound appraisal, delegation, revocation, guarantees and effects.
The supplement publishes documentation and the manuscript under its own
[CC BY 4.0 notice](aigp/LICENSE). **Its executable implementation is not
uploaded**; local software results are identified as such.

This addition does not replace the MAC 0.1.0 software or research report.
The two Zenodo DOIs above identify MAC, not the AIGP supplement. No new AIGP
Zenodo record or production qualification is asserted here.
