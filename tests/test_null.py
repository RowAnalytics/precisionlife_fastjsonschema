import pytest

from precisionlife_fastjsonschema import JsonSchemaValidationException


exc = JsonSchemaValidationException('must be null, but is a: {value_type}', value='{data}', _rendered_path='data', definition='{definition}', rule='type')
@pytest.mark.parametrize('value, expected', [
    (0, exc),
    (None, None),
    (True, exc),
    ('abc', exc),
    ([], exc),
    ({}, exc),
])
def test_null(asserter, value, expected):
    asserter({'type': 'null'}, value, expected, value_type=type(value).__name__)
