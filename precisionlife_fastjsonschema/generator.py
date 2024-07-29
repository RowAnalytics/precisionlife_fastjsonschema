import collections
from collections import OrderedDict
import re
import inspect
from typing import Optional, Any

from .exceptions import JsonSchemaValidationException, JsonSchemaDefinitionException
from .indent import indent
from .ref_resolver import RefResolver


def enforce_list(variable):
    if isinstance(variable, list):
        return variable
    return [variable]


def prepare_path(path):
    """
    Returns path as a string that can be evaluated.
    So for this input: ['1', 'data_x', '"text"']
    returns: '[1, data_x, "text"]'
    :param path:    List of strings, that are code fragments.
                    Those should be stringified array indexes ('1'), variable names ('data_x') and field names in quotes ('"text"').
    :return: String.
    """
    result = "["
    for element in path:
        result += element
        result += ", "
    result += "]"
    return result


def is_any_field_error(path, error):
    """
    Returns True if given error is related to any field.
    :param path:    Path to current element.
    :param error:   JsonSchemaValidationException from validating schema of that element.
    """
    if len(error.path) > len(path):
        return True
    if error.rule == 'required-additionalProperties':
        return True
    #if error.rule == 'required':
    #    return True
    #if error.rule == 'additionalProperties':
    #    return True
    if error.rule == 'propertyNames':
        return True
    return False


def is_specific_field_error(path, error, field, *, existence_only):
    """
    Returns True if given error is related to given field.
    :param existence_only: If True errors about the value of the field are ignored, only errors about existence of given field are taken into account.
    """
    if not existence_only:
        if (len(error.path) > len(path)) and (error.path[len(path)] == field):
            return True

    if error.rule == 'required-additionalProperties':
        if field in error.missing_fields:
            return True
        if field in error.extra_fields:
            return True

    #if (error.rule == 'required') and (re.search(f'is missing required properties: {escaped_field}', error.message)):
    #    return True

    #if error.rule == 'additionalProperties':
    #    if re.search(f'additional properties are not allowed: {escaped_field}', error.message):
    #        return True

    if error.rule == 'propertyNames':
        raise Exception('@todo Figure out what check should be here.')

    return False


def is_fundamental_error(path, error):
    """
    Returns True if error is not field related. (So type related, for example.)
    """
    return not is_any_field_error(path, error)


def raise_best_anyof_error(data, root_object, root_path, errors, special_fields_extractor, definition):
    """
    If any tag or discriminator fields are present:
      First schema that:
      - passed type check,
      - did not fail on any discriminator fields
      - allowed all tag fields
      will be assumed to be the right schema, and therefore exception from it will be returned.
      Additionally, if object did not validate an error is returned that says those tag/discriminator fields have invalid values.

    @note Tag and discriminator fields should only contain fields that should be present in the data object (unless optional).
          Both can contain optional fields.

    It is assumed that tag/discriminator fields are first fields in the schema (this is very week as well, because order of elements in JSON is not preserved...).
    If this is not the case validation will still work, but error messages won't be improved.
    """
    assert len(errors) > 0

    if (special_fields_extractor is None) or not isinstance(data, dict):
        best_error = max(errors, key=lambda exc: len(exc.path))
        raise best_error

    tag_fields, discriminator_fields, identification_fields = special_fields_extractor(data)
    if len(tag_fields) + len(discriminator_fields) == 0:
        best_error = max(errors, key=lambda exc: len(exc.path))
        raise best_error

    for error in errors:
        if is_fundamental_error(root_path, error):
            continue

        # If object has tag fields, and tag fields are allowed by schema, we raise this error.
        # @note This doesn't work tool well, because we get only first error from subschema, not all of errors.
        #       Will try to improve if needed.
        if len(tag_fields) > 0:
            allowed_fields = [not is_specific_field_error(root_path, error, tag_field, existence_only=True) for tag_field in tag_fields]
            if all(allowed_fields):
                raise error

        # If object has discriminator fields, and there were no errors on discriminator fields, we raise this error.
        if len(discriminator_fields) > 0:
            allowed_fields = [not is_specific_field_error(root_path, error, discriminator_field, existence_only=False) for discriminator_field in discriminator_fields]
            if all(allowed_fields):
                raise error

    # If object has tag fields, we know those were not accepted by any schema, so we raise an error for a tag field.
    if len(tag_fields) > 0:
        raise JsonSchemaValidationException('tag fields not recognized', data, definition, 'unknownTags', root_path, root_object, special_fields_extractor)

    # If object has any discriminator fields, we know those were not accepted by any schema, so complain that discriminators were not matched.
    if len(discriminator_fields) > 0:
        raise JsonSchemaValidationException('discriminator fields not recognized', data, definition, 'badDiscriminators', root_path, root_object, special_fields_extractor)

    best_error = max(errors, key=lambda exc: len(exc.path))
    raise best_error


common_functions_lines = [
    *inspect.getsourcelines(is_any_field_error)[0],
    '',
    '',
    *inspect.getsourcelines(is_specific_field_error)[0],
    '',
    '',
    *inspect.getsourcelines(is_fundamental_error)[0],
    '',
    '',
    *inspect.getsourcelines(raise_best_anyof_error)[0],
]


# pylint: disable=too-many-instance-attributes,too-many-public-methods
class CodeGenerator:
    """
    This class is not supposed to be used directly. Anything
    inside of this class can be changed without noticing.

    This class generates code of validation function from JSON
    schema object as string. Example:

    .. code-block:: python

        CodeGenerator(json_schema_definition).func_code
    """

    INDENT = 4  # spaces

    def __init__(self, definition, resolver=None):
        self._code = []
        self._compile_regexps = {}

        # Any extra library should be here to be imported only once.
        # Lines are imports to be printed in the file and objects
        # key-value pair to pass to compile function directly.
        self._extra_imports_lines = []
        self._extra_imports_objects = {}

        self._variables = set()
        self._indent = 0
        self._indent_last_line = None
        # Name of the variable in generated code, that holds object that is being validated.
        self._variable = None
        # Path to this object (list of field names and array indices that were traversed to reach it).
        # Each element in this list is a piece of code, that evaluated will give the actual path element.
        # Please note that this path will evaluate successfully only in the scope it is created in (as it may use local variable names).
        self._variable_path = []
        self._root_definition = definition
        self._definition = None

        # map schema URIs to validation function names for functions
        # that are not yet generated, but need to be generated
        self._needed_validation_functions = {}
        # validation function names that are already done
        self._validation_functions_done = set()

        if resolver is None:
            resolver = RefResolver.from_schema(definition)
        self._resolver = resolver

        # add main function to `self._needed_validation_functions`
        self._needed_validation_functions[self._resolver.get_uri()] = self._resolver.get_scope_name()

        self._json_keywords_to_function = OrderedDict()

    @property
    def func_code(self):
        """
        Returns generated code of whole validation function as string.
        """
        self._generate_func_code()

        return '\n'.join(self._code)

    @property
    def global_state(self):
        """
        Returns global variables for generating function from ``func_code``. Includes
        compiled regular expressions and imports, so it does not have to do it every
        time when validation function is called.
        """
        self._generate_func_code()

        return dict(
            **self._extra_imports_objects,
            REGEX_PATTERNS=self._compile_regexps,
            collections=collections,
            re=re,
            JsonSchemaValidationException=JsonSchemaValidationException,
            is_any_field_error=is_any_field_error,
            is_specific_field_error=is_specific_field_error,
            is_fundamental_error=is_fundamental_error,
            raise_best_anyof_error=raise_best_anyof_error,
        )

    @property
    def global_state_code(self):
        """
        Returns global variables for generating function from ``func_code`` as code.
        Includes compiled regular expressions and imports.
        """
        self._generate_func_code()

        if not self._compile_regexps:
            return '\n'.join(self._extra_imports_lines + [
                'import collections',
                'from precisionlife_fastjsonschema import JsonSchemaValidationException',
                '',
                '',
                '',
                *common_functions_lines,
                '',
            ])
        regexs = ['"{}": re.compile(r"{}")'.format(key, value.pattern) for key, value in self._compile_regexps.items()]
        return '\n'.join(self._extra_imports_lines + [
            'import re',
            'import collections',
            'from precisionlife_fastjsonschema import JsonSchemaValidationException',
            '',
            '',
            'REGEX_PATTERNS = {',
            '    ' + ',\n    '.join(regexs),
            '}',
            '',
            '',
            *common_functions_lines,
            '',
        ])


    def _generate_func_code(self):
        if not self._code:
            self.generate_func_code()

    def generate_func_code(self):
        """
        Creates base code of validation function and calls helper
        for creating code by definition.
        """
        self.l('NoneType = type(None)')
        # Generate parts that are referenced and not yet generated
        while self._needed_validation_functions:
            # During generation of validation function, could be needed to generate
            # new one that is added again to `_needed_validation_functions`.
            # Therefore usage of while instead of for loop.
            uri, name = self._needed_validation_functions.popitem()
            self.generate_validation_function(uri, name)

    def generate_validation_function(self, uri, name):
        """
        Generate validation function for given uri with given name
        """
        self._validation_functions_done.add(uri)
        self.l('')
        with self._resolver.resolving(uri) as definition:
            with self.l('def {}(data, *, root_object=None, root_path=[], special_fields_extractor=None):', name):
                self.l(f'""" Validation function for: base_uri={self._resolver.base_uri} uri={uri} """')
                self.l('root_object = (data if root_object is None else root_object)')
                self.generate_func_code_block(definition, 'data', [], clear_variables=True)
                self.l('return data')

    def generate_func_code_block(self, definition, variable, variable_path, clear_variables=False):
        """
        Creates validation rules for current definition.
        """
        backup = self._definition, self._variable, self._variable_path
        self._definition, self._variable, self._variable_path = definition, variable, variable_path
        if clear_variables:
            backup_variables = self._variables
            self._variables = set()

        self._generate_func_code_block(definition)

        self._definition, self._variable, self._variable_path = backup
        if clear_variables:
            self._variables = backup_variables

    def _generate_func_code_block(self, definition):
        if not isinstance(definition, dict):
            raise JsonSchemaDefinitionException("definition must be an object")
        if '$ref' in definition:
            # needed because ref overrides any sibling keywords
            self.generate_ref()
        else:
            self.run_generate_functions(definition)

    def run_generate_functions(self, definition):
        for key, func in self._json_keywords_to_function.items():
            if key in definition:
                func()

    def generate_ref(self):
        """
        Ref can be link to remote or local definition.

        .. code-block:: python

            {'$ref': 'http://json-schema.org/draft-04/schema#'}
            {
                'properties': {
                    'foo': {'type': 'integer'},
                    'bar': {'$ref': '#/properties/foo'}
                }
            }
        """
        with self._resolver.in_scope(self._definition['$ref']):
            name = self._resolver.get_scope_name()
            uri = self._resolver.get_uri()
            if uri not in self._validation_functions_done:
                self._needed_validation_functions[uri] = name
            # call validation function, with current full name as a root_path
            self.l('{}({variable}, root_object=root_object, root_path=root_path + {path}, special_fields_extractor=special_fields_extractor)', name, path=prepare_path(self._variable_path))


    # pylint: disable=invalid-name
    @indent
    def l(self, line, *args, **kwds):
        """
        Short-cut of line. Used for inserting line. It's formated with parameters
        ``variable``, ``variable_path`` (as ``name`` for short-cut), all keys from
        current JSON schema ``definition`` and also passed arguments in ``args``
        and named ``kwds``.

        .. code-block:: python

            self.l('if {variable} not in {enum}: raise JsonSchemaValidationException("Wrong!")')

        When you want to indent block, use it as context manager. For example:

        .. code-block:: python

            with self.l('if {variable} not in {enum}:'):
                self.l('raise JsonSchemaValidationException("Wrong!")')
        """
        spaces = ' ' * self.INDENT * self._indent

        context = dict(
            self._definition or {},
            variable=self._variable,
            **kwds
        )
        line = line.format(*args, **context)
        line = line.replace('\n', '\\n').replace('\r', '\\r')
        self._code.append(spaces + line)
        return line

    def e(self, string):
        """
        Short-cut of escape. Used for inserting user values into a string message.

        .. code-block:: python

            self.l('raise JsonSchemaValidationException("Variable: {}")', self.e(variable))
        """
        return str(string).replace('"', '\\"')

    def exc(self, msg, *args, rule=None, missing_fields: Optional[list[str]] = None, extra_fields: Optional[list[str]] = None):
        """
        """
        name_path = prepare_path(self._variable_path)
        msg = 'raise JsonSchemaValidationException("'+msg+'", value={variable}, definition={definition}, rule={rule}, path=root_path + ' + name_path + ', root_object=root_object, special_fields_extractor=special_fields_extractor'
        if missing_fields is not None:
            msg += f', missing_fields={missing_fields}'
        if extra_fields is not None:
            msg += f', extra_fields={extra_fields}'
        msg += ')'
        self.l(msg, *args, definition=repr(self._definition), rule=repr(rule))

    def create_variable_with_length(self):
        """
        Append code for creating variable with length of that variable
        (for example length of list or dictionary) with name ``{variable}_len``.
        It can be called several times and always it's done only when that variable
        still does not exists.
        """
        variable_name = '{}_len'.format(self._variable)
        if variable_name in self._variables:
            return
        self._variables.add(variable_name)
        self.l('{variable}_len = len({variable})')

    def create_variable_keys(self):
        """
        Append code for creating variable with keys of that variable (dictionary)
        with a name ``{variable}_keys``. Similar to `create_variable_with_length`.
        """
        variable_name = '{}_keys'.format(self._variable)
        if variable_name in self._variables:
            return
        self._variables.add(variable_name)
        self.l('{variable}_keys = set({variable}.keys())')

    def create_variable_is_list(self):
        """
        Append code for creating variable with bool if it's instance of list
        with a name ``{variable}_is_list``. Similar to `create_variable_with_length`.
        """
        variable_name = '{}_is_list'.format(self._variable)
        if variable_name in self._variables:
            return
        self._variables.add(variable_name)
        self.l('{variable}_is_list = isinstance({variable}, collections.abc.Sequence) and not isinstance({variable}, str)')

    def create_variable_is_dict(self):
        """
        Append code for creating variable with bool if it's instance of list
        with a name ``{variable}_is_dict``. Similar to `create_variable_with_length`.
        """
        variable_name = '{}_is_dict'.format(self._variable)
        if variable_name in self._variables:
            return
        self._variables.add(variable_name)
        self.l('{variable}_is_dict = isinstance({variable}, collections.abc.Mapping)')

    def can_emit_required_and_additional(self):
        variable_name = '{}_required_and_additional'.format(self._variable)
        if variable_name in self._variables:
            return False
        self._variables.add(variable_name)
        return True
