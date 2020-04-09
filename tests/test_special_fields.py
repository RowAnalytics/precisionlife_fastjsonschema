import pytest

import precisionlife_fastjsonschema as fastjsonschema
from precisionlife_fastjsonschema import JsonSchemaValidationException

validationTestTypesSchema = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "taggedType": {
      "$ref": "#/definitions/TaggedType"
    },
    "discriminatedType": {
      "$ref": "#/definitions/DiscriminatedType"
    },
    "namedTypeArray": {
      "$ref": "#/definitions/NamedTypeArray"
    }
  },
  "additionalProperties": False,
  "definitions": {
    "TaggedType": {
      "anyOf": [
        {
          "type": "object",
          "properties": {
            "$tagOne": {
              "type": "number"
            },
            "value": {
              "type": "number"
            }
          },
          "required": [
            "$tagOne",
            "value"
          ],
          "additionalProperties": False
        },
        {
          "type": "object",
          "properties": {
            "$tagTwo": {
              "type": "number"
            },
            "value": {
              "type": "number"
            }
          },
          "required": [
            "$tagTwo",
            "value"
          ],
          "additionalProperties": False
        },
        {
          "type": "object",
          "properties": {
            "$tagThree": {
              "type": "number"
            },
            "value": {
              "type": "number"
            }
          },
          "required": [
            "$tagThree",
            "value"
          ],
          "additionalProperties": False
        }
      ]
    },
    "DiscriminatedType": {
      "anyOf": [
        {
          "type": "object",
          "properties": {
            "kind": {
              "type": "string",
              "enum": [
                "one"
              ]
            },
            "value": {
              "type": "number"
            }
          },
          "required": [
            "kind",
            "value"
          ],
          "additionalProperties": False
        },
        {
          "type": "object",
          "properties": {
            "kind": {
              "type": "string",
              "enum": [
                "two"
              ]
            },
            "value": {
              "type": "number"
            }
          },
          "required": [
            "kind",
            "value"
          ],
          "additionalProperties": False
        },
        {
          "type": "object",
          "properties": {
            "kind": {
              "type": "string",
              "enum": [
                "three"
              ]
            },
            "value": {
              "type": "number"
            }
          },
          "required": [
            "kind",
            "value"
          ],
          "additionalProperties": False
        }
      ]
    },
    "NamedTypeArray": {
      "type": "array",
      "items": {
        "$ref": "#/definitions/NamedType"
      }
    },
    "NamedType": {
      "type": "object",
      "properties": {
        "name": {
          "type": "string"
        },
        "content": {
          "type": "object",
          "properties": {
            "value": {
              "type": "number"
            }
          },
          "required": [
            "value"
          ],
          "additionalProperties": False
        }
      },
      "required": [
        "name",
        "content"
      ],
      "additionalProperties": False
    }
  }
}


def special_fields_extractor(instance):
    tag_fields = [field for field in instance.keys() if field.startswith('$')]
    discriminator_fields = [field for field in instance.keys() if field in ['type', 'kind']]
    identification_fields = [field for field in instance.keys() if field in ['name']]
    return tag_fields, discriminator_fields, identification_fields


@pytest.mark.parametrize('value, expected', [
    ({ "kind": "text", "prop1": { "$print": "a", "str": 1 } }, JsonSchemaValidationException('must be string, but is a: int', value=1, _rendered_path='data<kind=text>.prop1<$print>.str', definition={'type': 'string'}, rule='type')),
    ({ "kind": "text", "named": { "name": "obj", "str": 1 } }, JsonSchemaValidationException('must be string, but is a: int', value=1, _rendered_path='data<kind=text>.named<name=obj>.str', definition={'type': 'string'}, rule='type')),
])
def test_special_fields_reporting(asserter, value, expected):
    asserter({
        "definitions": {
            "SomeType": {
                "type": "object",
                "properties": {
                    "$print": {"type": "string"},
                    "str": {"type": "string"},
                },
            },
            "NamedType": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "str": {"type": "string"},
                },
            },
        },
        "type": "object",
        "properties": {
            "kind": {"type": "string"},
            "prop1": {"$ref": "#/definitions/SomeType"},
            "named": {"$ref": "#/definitions/NamedType"},
        }
    }, value, expected, special_fields_extractor=special_fields_extractor)


@pytest.mark.parametrize('value, expected', [
    ({ 'taggedType': { '$tagOne': 1 }}, JsonSchemaValidationException('missing/extra properties', missing_fields=['value'], value=None, _rendered_path='data.taggedType<$tagOne>', definition=None, rule='required-additionalProperties')),
    ({ 'taggedType': { '$tagOne': 'str' }}, JsonSchemaValidationException('must be number, but is a: str', value=None, _rendered_path='data.taggedType<$tagOne>.$tagOne', definition=None, rule='type')),
    ({ 'taggedType': { '$tagOne': 'str', 'value': 1 }}, JsonSchemaValidationException('must be number, but is a: str', value=None, _rendered_path='data.taggedType<$tagOne>.$tagOne', definition=None, rule='type')),
    ({ 'taggedType': { '$tagInvalid': 'str', 'value': 1 }}, JsonSchemaValidationException('tag fields not recognized', value=None, _rendered_path='data.taggedType<$tagInvalid>', definition=None, rule='unknownTags')),
    ({ 'taggedType': { '$tagOne': 1, 'value': 'str' }}, JsonSchemaValidationException('must be number, but is a: str', value=None, _rendered_path='data.taggedType<$tagOne>.value', definition=None, rule='type')),

    ({ 'discriminatedType': { 'kind': 'one' }}, JsonSchemaValidationException('missing/extra properties', missing_fields=['value'], value=None, _rendered_path='data.discriminatedType<kind=one>', definition=None, rule='required-additionalProperties')),
    ({ 'discriminatedType': { 'kind': 1, 'value': 1 }}, JsonSchemaValidationException('discriminator fields not recognized', value=None, _rendered_path='data.discriminatedType<kind=1>', definition=None, rule='badDiscriminators')),
    ({ 'discriminatedType': { 'kind': 'invalid', 'value': 1 }}, JsonSchemaValidationException('discriminator fields not recognized', value=None, _rendered_path='data.discriminatedType<kind=invalid>', definition=None, rule='badDiscriminators')),
    ({ 'discriminatedType': { 'kind': 'one', 'value': 'str' }}, JsonSchemaValidationException('must be number, but is a: str', value=None, _rendered_path='data.discriminatedType<kind=one>.value', definition=None, rule='type')),

    ({ 'namedTypeArray': [{ 'name': 'one', 'content': { 'value': 1 }}, { 'name': 'two', 'content': 'str' }, { 'name': 'three', 'content': { 'value': 1 }}]}, JsonSchemaValidationException('must be object, but is a: str', value=None, _rendered_path='data.namedTypeArray[1]<name=two>.content', definition=None, rule='type')),
    ({ 'namedTypeArray': [{ 'name': 'one', 'content': { 'value': 1 }}, { 'name': 'two', 'content': { 'value': 'str' } }, { 'name': 'three', 'content': { 'value': 1 }}]}, JsonSchemaValidationException('must be number, but is a: str', value=None, _rendered_path='data.namedTypeArray[1]<name=two>.content.value', definition=None, rule='type')),
])
def test_special_fields_function(asserter, value, expected):
    asserter(validationTestTypesSchema, value, expected, special_fields_extractor=special_fields_extractor, ignore_exc_fields=['value', 'definition'])
