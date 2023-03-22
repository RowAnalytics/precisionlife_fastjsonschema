import pytest

from precisionlife_fastjsonschema import JsonSchemaValidationException


@pytest.mark.parametrize('const, value, expected', [
    ('foo', 'foo', 'foo'),
    (42, 42, 42),
    (False, False, False),
    ([1, 2, 3], [1, 2, 3], [1, 2, 3]),

    (42, 0, JsonSchemaValidationException('must be const 42 but is: 0', value='{data}', _rendered_path='data', definition='{definition}', rule='const')),
])
def test_const(asserter, const, value, expected):
    asserter({
        '$schema': 'http://json-schema.org/draft-06/schema',
        'const': const,
    }, value, expected)
