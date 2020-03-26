import pytest

from fastjsonschema import JsonSchemaException


@pytest.mark.parametrize('definition, rule, expected_rule_definition', [
    (None, None, None),
    ({}, None, None),
    ({'type': 'string'}, None, None),
    ({'type': 'string'}, 'unique', None),
    ({'type': 'string'}, 'type', 'string'),
    (None, 'type', None),
])
def test_exception_rule_definition(definition, rule, expected_rule_definition):
    exc = JsonSchemaException('msg', None, None, definition=definition, rule=rule)
    assert exc.rule_definition == expected_rule_definition
