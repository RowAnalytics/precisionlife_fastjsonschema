import collections


class JsonSchemaException(Exception):
    """
    Common class for exceptions from this library.
    """
    pass


class JsonSchemaDefinitionException(JsonSchemaException):
    """
    Exception raised by generator of validation function.
    """
    pass


class JsonSchemaValidationException(JsonSchemaException):
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

    def __init__(self, message, value, definition, rule, path=None, root_object=None, special_fields_extractor=None, *, _rendered_path=None, missing_fields=[], extra_fields=[]):
        # @todo path, root_object and special_fields_extractor are mandatory, but for tests they are ignored. It should be fixed somehow.
        # @todo Pre-assigned _rendered_path is used only for tests. It should be fixed somehow.
        super().__init__(message)
        self.message = message          # Error message. For 'required-additionalProperties' rule this is not used by __str__.
        self.value = value              # Value with error.
        self.definition = definition    # Schema that value failed on.
        self.rule = rule                # Name of the rule in the schema that was violated.
        self.path = path                # List of ints (array indices) and strings (field names) on the path from root object to the item with error.
        self.root_object = root_object  # Root object that was being validated. Used for rendering paths
        self.special_fields_extractor = special_fields_extractor  # Special fields extractor. Used for rendering paths
        self._rendered_path = _rendered_path  # Cache for rendered path. Used to limit rendering only to errors that will actually need that.
        self.missing_fields = missing_fields   # For 'required-additionalProperties' rule: fields that were required but are not present.
        self.extra_fields = extra_fields        # For 'required-additionalProperties' rule: fields that were present but not expected.

    def __repr__(self):
        if self.rule == 'required-additionalProperties':
            return f'JsonSchemaValidationException({self.message}, {self.rule}, {self.path}, {self.missing_fields}, {self.extra_fields})'
        return f'JsonSchemaValidationException({self.message}, {self.rule}, {self.path})'

    def __str__(self):
        if self.rule == 'required-additionalProperties':
            message = self.rendered_path
            if self.missing_fields:
                fields = ', '.join(f'[{v}]' for v in self.missing_fields)
                message += f' is missing required properties: {fields}'
            if self.extra_fields and self.missing_fields:
                message += '; '
            if self.extra_fields:
                fields = ', '.join(f'[{v}]' for v in self.extra_fields)
                message += f' additional properties are not allowed: {fields}'
            return message
        return f'{self.rendered_path} {self.message}'

    @property
    def rendered_path(self):
        if self._rendered_path is None:
            self._rendered_path = render_path(self.root_object, self.path, self.special_fields_extractor)
        return self._rendered_path

    @property
    def rule_definition(self):
        if not self.rule or not self.definition:
            return None
        return self.definition.get(self.rule)


def render_path(obj, path, special_fields_extractor):
    """
    Returns path as a string that can be displayed to the user.
    So for this input: [1, 'data', 'text']
    returns: data[1].data.text
    :param obj:     Object the path is in.
    :param path:    List of strings or ints (actual runtime values, not code fragments).
                    Ints are array indexes, strings are field names.
    :param special_fields_extractor: Function that given a Mapping returns (tag_fields, discriminator_fields, identification_fields) - lists of fields in given category.
    :return: String.
    """
    result = "data"

    def add_context(o):
        nonlocal result

        if special_fields_extractor is None:
            return

        if not isinstance(o, collections.abc.Mapping):
            return

        tag_fields, discriminator_fields, identification_fields = special_fields_extractor(o)
        if len(tag_fields) + len(discriminator_fields) + len(identification_fields) == 0:
            return

        id_fields = discriminator_fields + identification_fields
        id_data = ["{}={}".format(field, o[field]) for field in id_fields]
        result += "<"
        result += ",".join(tag_fields + id_data)
        result += ">"

    cur_obj = obj
    add_context(cur_obj)
    for element in path:
        cur_obj = cur_obj[element]
        result += ("[{}]" if isinstance(element, int) else ".{}").format(element)
        add_context(cur_obj)
    return result
