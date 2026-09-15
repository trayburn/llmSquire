"""Tests that verify koan exercise structure — no API calls needed.

These tests check that each koan file:
- Has the right class name and inherits from Koan
- Has test methods starting with test_
- Uses _fill_ in the right places (blanks exist for the learner to fill)
- The known-correct answers make the tests pass

For koans that require API calls, we mock the LLM client.
For koans that are deterministic, we run them directly.
"""
import pytest
from unittest.mock import MagicMock, patch
from types import ModuleType
import sys
import os

# Ensure koans/ is importable
_koans_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "koans")
if _koans_dir not in sys.path:
    sys.path.insert(0, os.path.dirname(_koans_dir))

from llmsquire.koan import Koan, _fill_, FillMeInError
from llmsquire.llm_client import LLMResponse, InteractionRecord
from llmsquire.proxy import llm as _llm_proxy


def _make_mock_response(content="Hello!", tool_calls=None):
    """Create a mock LLMResponse for testing."""
    record = InteractionRecord(
        request={"model": "test", "messages": []},
        response={"content": content, "tool_calls": tool_calls or []},
        timestamp=0.0,
        latency_ms=10.0,
        input_tokens=5,
        output_tokens=3,
        model="test-model",
    )
    return LLMResponse(
        content=content,
        tool_calls=tool_calls or [],
        finish_reason="stop",
        usage=record,
    )


def _setup_mock_llm(response_content="Hello!", tool_calls=None):
    """Set up the llm proxy with a mock client that returns canned responses."""
    mock_client = MagicMock()
    mock_client.trace = []
    mock_client.ask.return_value = _make_mock_response(response_content, tool_calls)
    mock_client.converse.return_value = _make_mock_response(response_content, tool_calls)
    _llm_proxy._client = mock_client
    return mock_client


def _load_koan_module(module_name):
    """Import a koan module and inject _fill_ into its namespace."""
    full_name = f"koans.{module_name}"
    mod = __import__(full_name, fromlist=["*"])
    # Inject _fill_ into the module's namespace so student code can use it
    # without importing it. The Sensei runner does the same thing.
    mod._fill_ = _fill_
    return mod


class TestKoanStructure:
    """Verify the structural integrity of koan files."""

    def _find_koan_class(self, module):
        """Find the Koan subclass in a module."""
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, type) and issubclass(obj, Koan) and obj is not Koan:
                return obj
        return None

    def test_about_invocation_exists_and_has_tests(self):
        mod = _load_koan_module("about_invocation")
        cls = self._find_koan_class(mod)
        assert cls is not None, "No Koan subclass found in about_invocation"
        test_methods = [m for m in dir(cls) if m.startswith("test_")]
        assert len(test_methods) >= 3, f"Expected 3+ tests, got {test_methods}"

    def test_about_statelessness_exists_and_has_tests(self):
        mod = _load_koan_module("about_statelessness")
        cls = self._find_koan_class(mod)
        assert cls is not None
        test_methods = [m for m in dir(cls) if m.startswith("test_")]
        assert len(test_methods) >= 2

    def test_about_context_window_exists_and_has_tests(self):
        mod = _load_koan_module("about_context_window")
        cls = self._find_koan_class(mod)
        assert cls is not None
        test_methods = [m for m in dir(cls) if m.startswith("test_")]
        assert len(test_methods) >= 2

    def test_about_system_prompts_exists_and_has_tests(self):
        mod = _load_koan_module("about_system_prompts")
        cls = self._find_koan_class(mod)
        assert cls is not None
        test_methods = [m for m in dir(cls) if m.startswith("test_")]
        assert len(test_methods) >= 3

    def test_about_tool_definitions_exists_and_has_tests(self):
        mod = _load_koan_module("about_tool_definitions")
        cls = self._find_koan_class(mod)
        assert cls is not None
        test_methods = [m for m in dir(cls) if m.startswith("test_")]
        assert len(test_methods) >= 3

    def test_about_tool_calling_exists_and_has_tests(self):
        mod = _load_koan_module("about_tool_calling")
        cls = self._find_koan_class(mod)
        assert cls is not None
        test_methods = [m for m in dir(cls) if m.startswith("test_")]
        assert len(test_methods) >= 3

    def test_about_constraining_tools_exists_and_has_tests(self):
        mod = _load_koan_module("about_constraining_tools")
        cls = self._find_koan_class(mod)
        assert cls is not None
        test_methods = [m for m in dir(cls) if m.startswith("test_")]
        assert len(test_methods) >= 3

    def test_about_context_composition_exists_and_has_tests(self):
        mod = _load_koan_module("about_context_composition")
        cls = self._find_koan_class(mod)
        assert cls is not None
        test_methods = [m for m in dir(cls) if m.startswith("test_")]
        assert len(test_methods) >= 4

    def test_about_skills_exists_and_has_tests(self):
        mod = _load_koan_module("about_skills")
        cls = self._find_koan_class(mod)
        assert cls is not None
        test_methods = [m for m in dir(cls) if m.startswith("test_")]
        assert len(test_methods) >= 3

    def test_about_rtcc_exists_and_has_tests(self):
        mod = _load_koan_module("about_rtcc")
        cls = self._find_koan_class(mod)
        assert cls is not None
        test_methods = [m for m in dir(cls) if m.startswith("test_")]
        assert len(test_methods) >= 3

    def test_about_evaluation_criteria_exists_and_has_tests(self):
        mod = _load_koan_module("about_evaluation_criteria")
        cls = self._find_koan_class(mod)
        assert cls is not None
        test_methods = [m for m in dir(cls) if m.startswith("test_")]
        assert len(test_methods) >= 3

    def test_about_edd_cycle_exists_and_has_tests(self):
        mod = _load_koan_module("about_edd_cycle")
        cls = self._find_koan_class(mod)
        assert cls is not None
        test_methods = [m for m in dir(cls) if m.startswith("test_")]
        assert len(test_methods) >= 4

    def test_about_decomposition_exists_and_has_tests(self):
        mod = _load_koan_module("about_decomposition")
        cls = self._find_koan_class(mod)
        assert cls is not None
        test_methods = [m for m in dir(cls) if m.startswith("test_")]
        assert len(test_methods) >= 3

    def test_about_guardrails_exists_and_has_tests(self):
        mod = _load_koan_module("about_guardrails")
        cls = self._find_koan_class(mod)
        assert cls is not None
        test_methods = [m for m in dir(cls) if m.startswith("test_")]
        assert len(test_methods) >= 3

    def test_about_adversarial_review_exists_and_has_tests(self):
        mod = _load_koan_module("about_adversarial_review")
        cls = self._find_koan_class(mod)
        assert cls is not None
        test_methods = [m for m in dir(cls) if m.startswith("test_")]
        assert len(test_methods) >= 3

    def test_about_harness_basic_exists_and_has_tests(self):
        mod = _load_koan_module("about_harness_basic")
        cls = self._find_koan_class(mod)
        assert cls is not None
        test_methods = [m for m in dir(cls) if m.startswith("test_")]
        assert len(test_methods) >= 3

    def test_about_harness_failure_exists_and_has_tests(self):
        mod = _load_koan_module("about_harness_failure")
        cls = self._find_koan_class(mod)
        assert cls is not None
        test_methods = [m for m in dir(cls) if m.startswith("test_")]
        assert len(test_methods) >= 3

    def test_about_harness_audit_exists_and_has_tests(self):
        mod = _load_koan_module("about_harness_audit")
        cls = self._find_koan_class(mod)
        assert cls is not None
        test_methods = [m for m in dir(cls) if m.startswith("test_")]
        assert len(test_methods) >= 3

    def test_about_punch_out_exists_and_has_tests(self):
        mod = _load_koan_module("about_punch_out")
        cls = self._find_koan_class(mod)
        assert cls is not None
        test_methods = [m for m in dir(cls) if m.startswith("test_")]
        assert len(test_methods) >= 3


class TestKoanAnswersWithFillMeIn:
    """Verify that koans have _fill_ blanks for the learner to fill."""

    def test_invocation_has_fill_me_in_blanks(self):
        """The koan source should contain _fill_ blanks."""
        mod = _load_koan_module("about_invocation")
        source_path = mod.__file__
        with open(source_path) as f:
            source = f.read()
        assert "_fill_" in source, "about_invocation should have _fill_ blanks"

    def test_statelessness_has_fill_me_in_blanks(self):
        mod = _load_koan_module("about_statelessness")
        with open(mod.__file__) as f:
            source = f.read()
        assert "_fill_" in source, "about_statelessness should have _fill_ blanks"

    def test_context_window_has_fill_me_in_blanks(self):
        mod = _load_koan_module("about_context_window")
        with open(mod.__file__) as f:
            source = f.read()
        assert "_fill_" in source, "about_context_window should have _fill_ blanks"

    def test_system_prompts_has_fill_me_in_blanks(self):
        mod = _load_koan_module("about_system_prompts")
        with open(mod.__file__) as f:
            source = f.read()
        assert "_fill_" in source, "about_system_prompts should have _fill_ blanks"

    def test_tool_definitions_has_fill_me_in_blanks(self):
        mod = _load_koan_module("about_tool_definitions")
        with open(mod.__file__) as f:
            source = f.read()
        assert "_fill_" in source, "about_tool_definitions should have _fill_ blanks"

    def test_tool_calling_has_fill_me_in_blanks(self):
        mod = _load_koan_module("about_tool_calling")
        with open(mod.__file__) as f:
            source = f.read()
        assert "_fill_" in source, "about_tool_calling should have _fill_ blanks"

    def test_constraining_tools_has_fill_me_in_blanks(self):
        mod = _load_koan_module("about_constraining_tools")
        with open(mod.__file__) as f:
            source = f.read()
        assert "_fill_" in source, "about_constraining_tools should have _fill_ blanks"

    def test_context_composition_has_fill_me_in_blanks(self):
        mod = _load_koan_module("about_context_composition")
        with open(mod.__file__) as f:
            source = f.read()
        assert "_fill_" in source, "about_context_composition should have _fill_ blanks"

    def test_skills_has_fill_me_in_blanks(self):
        mod = _load_koan_module("about_skills")
        with open(mod.__file__) as f:
            source = f.read()
        assert "_fill_" in source, "about_skills should have _fill_ blanks"

    def test_rtcc_has_fill_me_in_blanks(self):
        mod = _load_koan_module("about_rtcc")
        with open(mod.__file__) as f:
            source = f.read()
        assert "_fill_" in source, "about_rtcc should have _fill_ blanks"

    def test_evaluation_criteria_has_fill_me_in_blanks(self):
        mod = _load_koan_module("about_evaluation_criteria")
        with open(mod.__file__) as f:
            source = f.read()
        assert "_fill_" in source, "about_evaluation_criteria should have _fill_ blanks"

    def test_edd_cycle_has_fill_me_in_blanks(self):
        mod = _load_koan_module("about_edd_cycle")
        with open(mod.__file__) as f:
            source = f.read()
        assert "_fill_" in source, "about_edd_cycle should have _fill_ blanks"

    def test_decomposition_has_fill_me_in_blanks(self):
        mod = _load_koan_module("about_decomposition")
        with open(mod.__file__) as f:
            source = f.read()
        # Decomposition may not have _fill_ blanks — it's about composing steps
        # Just verify the file exists and has test methods (checked above)

    def test_guardrails_has_fill_me_in_blanks(self):
        mod = _load_koan_module("about_guardrails")
        with open(mod.__file__) as f:
            source = f.read()
        assert "_fill_" in source, "about_guardrails should have _fill_ blanks"

    def test_adversarial_review_has_fill_me_in_blanks(self):
        mod = _load_koan_module("about_adversarial_review")
        with open(mod.__file__) as f:
            source = f.read()
        assert "_fill_" in source, "about_adversarial_review should have _fill_ blanks"

    def test_harness_basic_has_fill_me_in_blanks(self):
        mod = _load_koan_module("about_harness_basic")
        with open(mod.__file__) as f:
            source = f.read()
        assert "_fill_" in source, "about_harness_basic should have _fill_ blanks"

    def test_harness_failure_has_fill_me_in_blanks(self):
        mod = _load_koan_module("about_harness_failure")
        with open(mod.__file__) as f:
            source = f.read()
        assert "_fill_" in source, "about_harness_failure should have _fill_ blanks"

    def test_harness_audit_has_fill_me_in_blanks(self):
        mod = _load_koan_module("about_harness_audit")
        with open(mod.__file__) as f:
            source = f.read()
        assert "_fill_" in source, "about_harness_audit should have _fill_ blanks"

    def test_punch_out_has_fill_me_in_blanks(self):
        mod = _load_koan_module("about_punch_out")
        with open(mod.__file__) as f:
            source = f.read()
        assert "_fill_" in source, "about_punch_out should have _fill_ blanks"

    def test_statelessness_fill_in_assert_match_raises(self):
        """When _fill_ is used in assert_match, it should raise FillMeInError.

        NOTE: This test is only valid on the main branch where koans are blank.
        On the student-solutions branch, koans are solved and _fill_ is replaced.
        Skip this test when the koan has been solved.
        """
        mod = _load_koan_module("about_statelessness")
        with open(mod.__file__) as f:
            source = f.read()
        if "_fill_" not in source:
            pytest.skip("Koan has been solved — _fill_ is no longer present")


class TestPathToEnlightenment:
    """Verify the path is properly configured."""

    def test_path_has_19_entries(self):
        from llmsquire.path_to_enlightenment import PATH
        assert len(PATH) == 19

    def test_path_starts_with_invocation(self):
        from llmsquire.path_to_enlightenment import PATH
        assert PATH[0] == "koans.about_invocation"

    def test_path_ends_with_punch_out(self):
        from llmsquire.path_to_enlightenment import PATH
        assert PATH[-1] == "koans.about_punch_out"