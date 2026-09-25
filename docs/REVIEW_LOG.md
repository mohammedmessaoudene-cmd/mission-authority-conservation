# Review and correction record

This record first describes historical reviews in the originating ChatGPT workflow.
Those initial analytical roles were perspectives of the same assistant, not independent human
committees or institutional peer review. The four parallel workers used for mutation
experiments execute Python tests; they are not four independent AI reviewers.

## Evidence and engineering

The original 99,185-byte archive was checked against its supplied SHA-256 and
replayed before extension. Its 83 unit tests were retained. The authorization core
`lab/core.py` remains byte-identical to the admitted original. Six tests add spawned
resource processes and actual process termination after a committed SQLite effect.
They do not establish operating-system isolation or distributed deployment safety.

The first process-fixture run exposed a fixture clock problem: after recording a
later time, the resource restarted with the earlier default time. The core correctly
rejected that rollback. The fixture now passes its current clock at construction;
the first failing log remains in `evidence/history/`. This correction is not counted
as a newly discovered core vulnerability.

The experiment scripts use explicit exception checks rather than optimization-
disabled Python assertions. Unit results, test identifiers, source hashes and
execution environment are recorded. The aggregate runner refuses a nonempty output
directory and derives its reported test count from the unittest result.

## Adversarial and scientific review

Four separate mutations modify one unique line in disposable copies of the actual
core. Each control requires direct unsafe behavior, execution of the changed line,
a failed safety assertion without an import/runtime error, and successful baseline
and restored tests. The original source is rehashed after the experiment. Exact
patches, observations, line traces and test results are retained.

The finite state model remains a separate abstraction, not a proof that Python
implements that model. The generated cases are predefined families, not a statistical
sample of real attacks or LLM behavior. The conventional SQL/uniqueness baseline is
retained as equally safe in the selected comparison. Privileged cloning of the
authority register remains an executed counterexample, not a corrected feature.

The related-work review explicitly credits hierarchical resource conservation in
Agent Contracts, invocation-bound delegation in AIP, external authorization in
aiAuthZ, the cited individual Internet-Draft, and the author's AUEC and AOR releases.
The new artifact is not a new version or an integration of AUEC or AOR. No global
novelty, universal exactly-once execution, human-presence proof, production security,
or institutional endorsement is claimed.

## Editorial and typesetting review

The paper uses a two-column research-report layout without naming a journal or
claiming journal acceptance. The author footnote includes the requested MCB title,
ORCID, institutional e-mail, and non-endorsement statement. Results are generated
from the selected evidence through `tools/paper_metrics.py`.

An initial lifecycle drawing had crowded connectors and labels. It was replaced
with a vertical state diagram and a clearly distinguished receipt-verification
step. Compilation errors encountered during drafting were corrected. A resolved
bibliography accompanies the BibTeX database so the distributed source builds
without requiring the BibTeX executable. Final PDF rendering and build checks are
recorded in the delivery's local validation record.

## Rights, packaging and publication boundary

Only the allowlisted public projection is released. Raw input proposals, private
correspondence, unpublished work-control prompts, credentials and font files are
excluded. Executable material is Apache-2.0; the paper and narrative specification
are CC BY 4.0. Existing AUEC and AOR licences and records are not modified. Licence
texts are reproduced unmodified. These assignments concern rights held by the
releaser and are not a warranty about patent rights or generated-material ownership.

The public software partition and report-source partition have distinct manifests
and licences. Local preparation and a reserved DOI are not evidence of publication.
Actual GitHub/Zenodo publication requires the authorized publisher to verify the
public records and downloadable bytes. No such remote publication is asserted by
this local review record.

## Final Codex reconciliation and reproduction

The supplied 89-method extension was compared with the authenticated earlier
local candidate (92 methods). The unchanged original core and 83 contract methods
were retained, together with the six new process methods. Nine evidence regressions
were reconciled, yielding 98 methods. A faulty reserve/cancel exception boundary
could hide a wrong acceptance when cancellation failed. The correction records
the admission decision before cleanup and preserves failure evidence. Partial-batch
counts and failed generated-case persistence were also restored. These findings
concern the evidence runner; they do not establish a new core vulnerability.

Windows packaging now uses POSIX paths for inventory and licence partitioning.
The mutation harness writes exact bytes and verifies the core hashes actually
loaded in baseline, mutant and restored probes, avoiding newline translation.

Three actual Codex subagents reviewed isolated engineering, scientific and
editorial copies under one coordinating agent. Their shared origin is disclosed;
this is not independent human peer review. A storage-full optimized attempt and
a subsequent interrupted retry remain private failed/incomplete evidence. They
are not counted as successful runs. The selected public evidence identifies its
actual execution environment and tested sources.
