from clue_eval.demos.stub_algorithm import StubClueAlgorithm
from clue_eval.suite import SuiteRunner, default_suite


def test_default_suite_has_fixture_tests():
    suite = default_suite()
    assert len(suite.tests) >= 1
    assert suite.tests[0].id.startswith("fixture-")


def test_suite_runner_smoke():
    results = SuiteRunner(StubClueAlgorithm()).run_suite(default_suite())
    assert len(results) == len(default_suite().tests)
    assert results[0]["test_id"] == default_suite().tests[0].id
    assert results[0]["generated_clue"] == "LINK"
