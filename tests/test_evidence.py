"""Regression tests for evidence integrity, not a new agent benchmark."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import run_all
from lab import evaluate
from lab.checks import CheckFailed
from lab.core import Denied, Gate
from lab.scenario import Scenario

ROOT=Path(__file__).resolve().parents[1]


class EvidenceTests(unittest.TestCase):
    def test_cancellation_failure_cannot_hide_bad_acceptance(self):
        original_reserve,original_cancel=Gate.reserve,Gate.cancel
        def reserve(gate,signed,preview,approval=None):
            if signed['payload']['iid']=='fuzz-1':return 'RESERVED'
            return original_reserve(gate,signed,preview,approval)
        def cancel(gate,iid):
            if iid=='fuzz-1':raise Denied('INJECTED_CANCEL_FAILURE')
            return original_cancel(gate,iid)
        with patch.object(Gate,'reserve',reserve),patch.object(Gate,'cancel',cancel):
            with self.assertRaises(CheckFailed) as ctx:evaluate.generated(2)
        record=ctx.exception.result
        self.assertFalse(record['complete'])
        self.assertEqual(record['cancellation_error'],'INJECTED_CANCEL_FAILURE')
        self.assertEqual(record['unexpected'],[{'i':1,'case':1,'expected_allow':False,'actual_allow':True}])
        self.assertTrue(record['cases'][1]['actual_allow'])

    def test_observed_count_and_failure_are_recorded(self):
        from tools.run_units import run
        class Count(unittest.TestCase):
            def test_pass(self): self.assertTrue(True)
            def test_fail(self): self.fail('injected')
        suite=unittest.defaultTestLoader.loadTestsFromTestCase(Count)
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)
            with patch('tools.run_units.unittest.defaultTestLoader.discover',return_value=suite):
                with self.assertRaises(RuntimeError):run(out)
            record=json.loads((out/'unit_tests.json').read_text())
            self.assertEqual(record['tests_run'],2)
            self.assertEqual(record['failures'],1)
            self.assertFalse(record['successful'])

    def test_zero_test_success_is_rejected(self):
        from tools.run_units import run
        with tempfile.TemporaryDirectory() as d:
            with patch('tools.run_units.unittest.defaultTestLoader.discover',return_value=unittest.TestSuite()):
                with self.assertRaises(RuntimeError):run(Path(d))
            self.assertEqual(json.loads((Path(d)/'unit_tests.json').read_text())['tests_run'],0)

    def test_generated_mismatch_evidence_survives_failure(self):
        evidence={'unexpected':[{'case':0,'expected_allow':True,'actual_allow':False}]}
        with tempfile.TemporaryDirectory() as d:
            with patch('lab.evaluate.run_model',return_value={}), patch('lab.evaluate.generated',side_effect=CheckFailed('injected mismatch',evidence)):
                with self.assertRaises(CheckFailed):evaluate.run(Path(d))
            self.assertEqual(json.loads((Path(d)/'generated_cases.json').read_text()),evidence)

    def test_runner_error_is_nonzero_and_never_pass(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'out'
            code='import run_all,sys,tools.run_units; tools.run_units.run=lambda out: (_ for _ in ()).throw(RuntimeError("injected unit error")); raise SystemExit(run_all.main(["--out",sys.argv[1]]))'
            cp=subprocess.run([sys.executable,'-B','-c',code,str(out)],cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(cp.returncode,1)
            self.assertEqual(json.loads((out/'summary.json').read_text())['verdict'],'FAIL')
            self.assertIn('injected unit error',(out/'FAILED.json').read_text())

    def test_existing_evidence_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/'summary.json';file.write_text('preserved')
            with self.assertRaises(SystemExit):run_all.main(['--out',d])
            self.assertEqual(file.read_text(),'preserved')

    def test_negative_controls_fail_even_under_optimization(self):
        code="from lab import modelcheck as m; m.explore=lambda variant: {'safe_in_finite_model':True}; m.run()"
        for flags in ([],['-O']):
            with self.subTest(flags=flags):
                cp=subprocess.run([sys.executable,'-B',*flags,'-c',code],cwd=ROOT,capture_output=True,text=True)
                self.assertNotEqual(cp.returncode,0)
                self.assertIn('Model negative control escaped detection',cp.stderr)

    def test_partial_generated_batch_has_exact_expected_count(self):
        result=evaluate.generated(1)
        self.assertEqual(result['expected_accepted'],1)
        self.assertEqual(result['counts']['case_0_accepted'],1)

    def test_nonterminal_receipt_never_refunds(self):
        s=Scenario()
        try:
            p=s.make();pr,_=s.reserve(p);permit=s.gate.begin(p['iid'])
            receipt=s.resource.apply(p,pr,permit)
            s.gate.mark_unknown(p['iid'])
            receipt['payload']['result']='PENDING'
            signed=s.rkey.sign('RECEIPT',receipt['payload'])
            before=s.gate.balance()
            with self.assertRaises(Denied) as ctx:s.gate.settle(signed)
            self.assertEqual(ctx.exception.code,'RESULT')
            self.assertEqual(s.gate.balance(),before)
            self.assertEqual(s.gate.state(p['iid']),'UNKNOWN')
        finally:s.close()
