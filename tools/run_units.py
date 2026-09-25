"""Structured unittest runner: measured counts, no hardcoded PASS summary."""
from pathlib import Path
import json, sys, unittest

def run(out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    suite = unittest.defaultTestLoader.discover('tests')
    def ids(suite):
        for item in suite:
            if isinstance(item,unittest.TestSuite): yield from ids(item)
            else: yield item.id()
    test_ids=list(ids(suite))
    with (out/'unit_tests.log').open('w', encoding='utf-8') as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    data = {'tests_run': result.testsRun, 'failures': len(result.failures),
            'errors': len(result.errors), 'skipped':len(result.skipped),
            'expected_failures':len(result.expectedFailures),
            'unexpected_successes':len(result.unexpectedSuccesses),
            'successful': result.wasSuccessful(), 'test_ids':test_ids,
            'process_test_methods':sum(x.startswith('test_process_boundary.') for x in test_ids)}
    (out/'unit_tests.json').write_text(json.dumps(data,indent=2)+'\n')
    if not result.wasSuccessful() or result.testsRun == 0 or result.skipped or result.expectedFailures:
        raise RuntimeError('Release suite is not wholly green; inspect unit_tests.log')
    return data
if __name__ == '__main__':
    print(json.dumps(run(Path(sys.argv[1])),indent=2))
