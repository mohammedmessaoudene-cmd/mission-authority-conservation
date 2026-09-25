"""Generate paper numbers from the selected executed evidence, never from prose."""
from pathlib import Path
import argparse,json

def build(evidence:Path,target:Path):
    def read(name):return json.loads((evidence/name).read_text())
    s=read('summary.json');b=read('local_benchmark.json')
    if s['unit']['failures'] or s['unit']['errors'] or s['generated_mismatches']:
        raise RuntimeError('Cannot build positive result macros from a failed run')
    metrics={'UnitCount':s['unit']['tests_run'],'ProcessCount':s['local_process_test_methods'],
       'CaseCount':f"{s['generated_cases']:,}", 'StateCount':f"{s['finite_states']:,}",
       'TransitionCount':f"{s['finite_transitions']:,}",
       'MutationCount':s['source_mutations']['passed'],
       'SigMedian':b['signature_verification']['median_ms'],
       'SigTail':b['signature_verification']['p99_ms'],
       'ReserveMedian':b['reserve_including_checks_and_sqlite']['median_ms'],
       'ReserveTail':b['reserve_including_checks_and_sqlite']['p99_ms'],
       'CycleMedian':b['reserve_dispatch_effect_settle_toy']['median_ms'],
       'CycleTail':b['reserve_dispatch_effect_settle_toy']['p99_ms']}
    target.write_text('% Generated from evidence/reproduced; do not edit counts by hand.\n'+
       '\n'.join('\\newcommand{\\'+k+'}{'+str(v)+'}' for k,v in metrics.items())+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--evidence',default='evidence/reproduced');p.add_argument('--target',default='paper/metrics.tex');a=p.parse_args()
    build(Path(a.evidence),Path(a.target))
