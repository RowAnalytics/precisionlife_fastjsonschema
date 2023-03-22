import pytest

from precisionlife_fastjsonschema import JsonSchemaValidationException


@pytest.mark.parametrize('const, value, expected', [
    ('foo', 'foo', 'foo'),
    (42, 42, 42),
    (False, False, False),
    ([1, 2, 3], [1, 2, 3], [1, 2, 3]),

    ('foo', 0, JsonSchemaValidationException('must be const "foo" but is: 0', value='{data}', _rendered_path='data', definition='{definition}', rule='const')),
    (42, 0, JsonSchemaValidationException('must be const 42 but is: 0', value='{data}', _rendered_path='data', definition='{definition}', rule='const')),
    (42, 'foo', JsonSchemaValidationException('must be const 42 but is: foo', value='{data}', _rendered_path='data', definition='{definition}', rule='const')),
    ('x', 'xz', JsonSchemaValidationException('must be const "x" but is: xz', value='{data}', _rendered_path='data', definition='{definition}', rule='const')),
    (True, False, JsonSchemaValidationException('must be const True but is: False', value='{data}', _rendered_path='data', definition='{definition}', rule='const')),
])
def test_const(asserter, const, value, expected):
    asserter({
        '$schema': 'http://json-schema.org/draft-06/schema',
        'const': const,
    }, value, expected)
