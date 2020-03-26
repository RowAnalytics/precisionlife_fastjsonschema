import re


class JsonSchemaException(ValueError):
    """
    Exception raised by validation function. Available properties:

     * ``message`` containing human-readable information what is wrong (e.g. ``data.property[index] must be smaller than or equal to 42``),
     * invalid ``value`` (e.g. ``60``),
     * ``name`` of a path in the data structure (e.g. ``data.property[0]``),
     * ``path`` as an array in the data structure (e.g. ``['data', 'property', 0]``),
     * the whole ``definition`` which the ``value`` has to fulfil (e.g. ``{'type': 'number', 'maximum': 42}``),
     * ``rule`` which the ``value`` is breaking (e.g. ``maximum``)
     * and ``rule_definition`` (e.g. ``42``).

    .. versionchanged:: 2.14.0
        Added all extra properties.
    """

    def __init__(self, message, value, name, definition, rule, path=None): # @todo path should be required. Will fix after tests are updated.
        super().__init__(message)
        self.message = message          # Error message.
        self.value = value              # Value with error.
        self.name = name                # Human readable path from root object to the item with error.
        self.definition = definition    # Schema that value failed on.
        self.rule = rule                # Name of the rule in the schema that was violated.
        self.path = path                # List of ints (array indices) and strings (field names) on the path from root object to the item with error.

    @property
    def rule_definition(self):
        if not self.rule or not self.definition:
            return None
        return self.definition.get(self.rule)


class JsonSchemaDefinitionException(JsonSchemaException):
    """
    Exception raised by generator of validation function.
    """
    def __init__(self, message):
        # @todo It doesn't make sense for JsonSchemaDefinitionException to inherit from JsonSchemaException.
        super().__init__(message, None, None, None, None, None)
