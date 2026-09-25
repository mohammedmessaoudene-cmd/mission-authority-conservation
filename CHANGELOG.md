# 0.1.0-research — initial standalone publication candidate

Original prototype core is unchanged (SHA-256 recorded in provenance.json).
The original 83 tests are preserved. This publication pass adds six local
spawned-process tests and four source-level causal mutation controls. The runner
now records actual unittest counts, rejects nonempty output directories, and
uses explicit experiment failure conditions that are not removed by Python -O.

A restarted-process fixture initially reset its virtual clock. The core rejected
that backward time; the fixture now initializes from the controller's current
clock and does not reset it between commands. The first failed run is preserved.

The release includes an English LaTeX research report, a narrative profile,
licence mapping, public claim–evidence records and reproducible release builders.
No production or protocol-integration claim is added.

Final Codex reconciliation restored nine targeted evidence regressions from the
authenticated earlier local candidate. The resulting suite has 98 methods:
83 contract, six process and nine evidence tests. Admission is recorded before
cancellation so a cleanup refusal cannot mask an incorrect acceptance; generated
failure records and partial-batch counts are preserved. Mutation probes verify
the hashes of the bytes actually executed, including on Windows. The release
builder normalizes paths and checks complete per-file licence assignments.

The selected final run uses Windows/Python 3.11.9. The paper's tables are generated
from that run, with historical Linux evidence distinguished. Actual Codex review
subagents are disclosed without implying independent human peer review.
