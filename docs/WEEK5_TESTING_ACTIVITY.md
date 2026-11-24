# Week 5 activity: unit tests for our validation

Our equivalent of `validation.py` is `services/input_validation.py`. Its `validate_record(table, values)`
returns a list of readable problems (an empty list means the record is valid) instead of raising
`ValueError`, because the Streamlit form shows every problem at once. The tests are in
`tests/test_input_validation.py`.

## Activity items and the tests that cover them

| Activity item | Test |
|---|---|
| Valid entity passes | `test_valid_brand_returns_cleaned_values_without_errors`, `test_optional_values_and_valid_job_dates_pass` |
| Blank title is rejected | `test_blank_or_whitespace_brand_name_is_rejected[""]` |
| Spaces-only value is rejected | `test_blank_or_whitespace_brand_name_is_rejected["   "]` and `["\t  "]` |
| Negative quantity is rejected | `test_negative_cargo_quantity_is_rejected[-1]` and `[-0.25]` |
| Boundary value (0) | `test_zero_weight_is_the_allowed_boundary` (new) |
| Advanced: parametrized invalid types | `test_invalid_cargo_quantity_types_are_rejected`, `test_invalid_cargo_weight_types_are_rejected` (new: `True`, `"3"`, `2.5`) |

The new tests follow the Arrange, Act, Assert pattern, and their expected results come from the
requirement ("WeightKg must be a whole, non-negative number"), not from what the code returned.

## Red: the new test exposed a logical bug

```
pytest tests/test_input_validation.py -q

E       AssertionError: True was accepted as a cargo weight
E       AssertionError: '3' was accepted as a cargo weight
FAILED tests/test_input_validation.py::test_invalid_cargo_weight_types_are_rejected[True]
FAILED tests/test_input_validation.py::test_invalid_cargo_weight_types_are_rejected[3]
2 failed, 19 passed
```

**Why it failed (explained before editing the code):** the validator converted every value with
`float(value)`. `float(True)` is `1.0` because `bool` is a subclass of `int`, and `float("3")` is
`3.0`, so both passed as valid numbers. There was no exception and no traceback: a logical error,
not a runtime error. `2.5` was already rejected by the whole-number rule.

## Fix

In `services/input_validation.py`, before converting a numeric field:

```python
if isinstance(value, (bool, str)):
    problems.append(f"{name} must be a number.")
    continue
```

## Green: the same tests pass

```
pytest tests/test_input_validation.py -q
21 passed

pytest -q
107 passed (64 test functions; parametrize expands them into 107 cases)
```

The tests stay in Git as regression tests: if someone removes the type check later, the
`[True]` and `["3"]` cases fail again.

## How to run

```
.venv\Scripts\activate
pytest -v tests/test_input_validation.py
pytest tests/test_input_validation.py::test_invalid_cargo_weight_types_are_rejected -v
pytest -q
```
