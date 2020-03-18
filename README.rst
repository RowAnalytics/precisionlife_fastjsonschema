===========================
Fast JSON schema for Python
===========================

This is a modification of fastjsonschema done for the following purposes:

* Add support for validating documents that are composed from any Sequences and Mappings, not only lists and dicts.
* Include full path to validated field in error messages.
  (see: https://github.com/horejsek/python-fastjsonschema/issues/63)
* Improve error messages for anyOf and oneOf rules by:

  * introducing concept of "discriminator fields",
  * if object is a Mapping, and has any of the discriminator fields,
    then it is assumed it must match first schema that does not return any error
    on any of the discriminator fields,
  * introducing concept of "tag fields",
  * if object is a Mapping, and has any of the tag fields,
    then it is assumed it must match first schema that allows this field to exist,
  * if object is a Mapping, and has any tag or discriminator fields, and failed validation,
    then an error is returned that says those tag/discriminator fields have invalid values,
    all more specific errors are dropped.
    (see: https://github.com/horejsek/python-fastjsonschema/issues/72)

* When unexpected additional fields are present those should be enumerated in error message.
  (see: https://github.com/horejsek/python-fastjsonschema/issues/84)
* Make the store for cached documents overridable.
* Improve handling of '$' character (see DOLLAR_FINDER).


Please note that tag and discriminator fields must be hand-picked for any given schema,
as there is no logic that automatically figures them out.
Also if those fields are specified incorrectly some correct documents might be rejected.

About tag and discriminator fields
==================================

Existence of a tag field on an object determines which schema out of anyOf or oneOf
should be chosen.
Existence of a discriminator field with a specific value determines which schema out of anyOf or oneOf
should be chosen.

Example where 'type' is a discriminator field.
From the value of this field we know which schema must be used.
::

    {
       type: square
       width: 5
    }
    {
       type: circle
       radius: 5
    }

Example where '$add' and '$log' are tag fields.
From existence of any of those fields we know which schema must be used.
::

    {
       $add: 5
       other: 2
    }
    {
       $log: 3
       base: 10
    }


Status of original fastjsonschema package
=========================================

|PyPI| |Pythons|

.. |PyPI| image:: https://img.shields.io/pypi/v/fastjsonschema.svg
   :alt: PyPI version
   :target: https://pypi.python.org/pypi/fastjsonschema

.. |Pythons| image:: https://img.shields.io/pypi/pyversions/fastjsonschema.svg
   :alt: Supported Python versions
   :target: https://pypi.python.org/pypi/fastjsonschema

See `documentation <https://horejsek.github.io/python-fastjsonschema/>`_.
