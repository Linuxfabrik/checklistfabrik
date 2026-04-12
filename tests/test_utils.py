"""Tests for checklistfabrik.core.utils."""

from checklistfabrik.core.utils import (
    eval_all_conditionals,
    eval_conditional,
    eval_when,
    validate_dict_keys,
)

# --- eval_conditional ---


class TestEvalConditional:
    def test_true_condition(self):
        assert eval_conditional({'x': 1}, 'x == 1') is True

    def test_false_condition(self):
        assert eval_conditional({'x': 1}, 'x == 2') is False

    def test_string_comparison(self):
        assert eval_conditional({'os': 'linux'}, "os == 'linux'") is True

    def test_undefined_variable_is_falsy(self):
        assert eval_conditional({}, 'x') is False

    def test_boolean_fact(self):
        assert eval_conditional({'enabled': True}, 'enabled') is True

    def test_complex_expression(self):
        assert eval_conditional({'a': 5, 'b': 10}, 'a < b and b == 10') is True


# --- eval_all_conditionals ---


class TestEvalAllConditionals:
    def test_all_true(self):
        facts = {'a': 1, 'b': 2}
        assert eval_all_conditionals(facts, ['a == 1', 'b == 2']) is True

    def test_one_false(self):
        facts = {'a': 1, 'b': 2}
        assert eval_all_conditionals(facts, ['a == 1', 'b == 99']) is False

    def test_empty_list(self):
        assert eval_all_conditionals({}, []) is True


# --- eval_when ---


class TestEvalWhen:
    def test_none_is_truthy(self):
        result = eval_when({}, None)
        assert result == (True, None)

    def test_single_true_condition(self):
        result = eval_when({'x': 1}, 'x == 1')
        assert result is True

    def test_single_false_condition(self):
        result = eval_when({'x': 1}, 'x == 2')
        assert result is False

    def test_list_all_true(self):
        result = eval_when({'a': 1, 'b': 2}, ['a == 1', 'b == 2'])
        assert result is True

    def test_list_one_false(self):
        result = eval_when({'a': 1, 'b': 2}, ['a == 1', 'b == 99'])
        assert result is False


# --- validate_dict_keys ---


class TestValidateDictKeys:
    def test_all_required_present(self):
        ok, _ = validate_dict_keys({'a': 1, 'b': 2}, {'a', 'b'})
        assert ok is True

    def test_missing_required_key(self):
        ok, msg = validate_dict_keys({'a': 1}, {'a', 'b'})
        assert ok is False
        assert 'b' in msg

    def test_extra_keys_allowed_by_default(self):
        ok, _ = validate_dict_keys({'a': 1, 'extra': 2}, {'a'})
        assert ok is True

    def test_extra_keys_disallowed(self):
        ok, msg = validate_dict_keys(
            {'a': 1, 'extra': 2},
            {'a'},
            disallow_extra_keys=True,
        )
        assert ok is False
        assert 'extra' in msg

    def test_optional_keys_not_flagged(self):
        ok, _ = validate_dict_keys(
            {'a': 1, 'opt': 2},
            {'a'},
            optional_keys={'opt'},
            disallow_extra_keys=True,
        )
        assert ok is True

    def test_none_required_keys(self):
        ok, _ = validate_dict_keys({'any': 1}, None)
        assert ok is True
