import pytest

from precisionlife_fastjsonschema import JsonSchemaValidationException


exc = JsonSchemaValidationException('must be boolean, but is a: {value_type}', value='{data}', _rendered_path='data', definition='{definition}', rule='type')
@pytest.mark.parametrize('value, expected', [
    (0, exc),
    (None, exc),
    (True, True),
    (False, False),
    ('abc', exc),
    ([], exc),
    ({}, exc),
])
def test_boolean(asserter, value, expected):
    asserter({'type': 'boolean'}, value, expected, value_type=type(value).__name__)
