#!/usr/bin/env python3
"""Reproduce bounded research evidence, without network or consequential effects."""
from __future__ import annotations
import argparse,datetime,hashlib,json,os,platform,sqlite3,sys
from pathlib import Path

def main(argv=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',default='local-results',help='new or empty result directory')
    args=parser.parse_args(argv);root=Path(__file__).resolve().parent;os.chdir(root)
    out=Path(args.out).resolve()
    if out.exists() and any(out.iterdir()):
        parser.error('Refusing to overwrite evidence. Choose a new output directory.')
    out.mkdir(parents=True,exist_ok=True)
    import cryptography
    from tools.run_units import run as units
    from tools.mutations import run as mutations
    from lab.evaluate import run as evaluate
    from lab.demo import run as demo
    try:
        unit=units(out)
        results=evaluate(out)
        mutation=mutations(out/'source_mutations')
        demo(out)
        env={'python':sys.version,'platform':platform.platform(),'sqlite':sqlite3.sqlite_version,
             'cryptography':cryptography.__version__,'optimization':sys.flags.optimize}
        (out/'environment.json').write_text(json.dumps(env,indent=2)+'\n')
        code={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
              for base in ('lab','tests','tools') for p in sorted((root/base).glob('*.py'))}
        code.update({name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in ('run_all.py','requirements.txt')})
        (out/'executed_sources.json').write_text(json.dumps(code,indent=2)+'\n')
        summary={'verdict':'PASS_BOUNDED_RESEARCH_WITH_REPRODUCED_LIMITATIONS',
            'unit':unit,'source_mutations':mutation,'finite_states':results['model_check']['none']['states_discovered'],
            'finite_transitions':results['model_check']['none']['edges_examined'],
            'generated_cases':results['generated_cases']['requests'],
            'generated_mismatches':len(results['generated_cases']['unexpected']),
            'cloning_limit_reproduced':results['cloning_limitation']['expected_limitation_reproduced'],
            'local_process_test_methods':unit['process_test_methods'],'network_protocol_integration':False,
            'independent_validation':False,'production_ready':False,'formal_code_refinement_proof':False}
        (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
        print(json.dumps(summary,indent=2));return 0
    except Exception as exc:
        failure={'verdict':'FAIL','type':type(exc).__name__,'message':str(exc)}
        (out/'FAILED.json').write_text(json.dumps(failure,indent=2)+'\n')
        (out/'summary.json').write_text(json.dumps(failure,indent=2)+'\n')
        raise
if __name__=='__main__': raise SystemExit(main())
