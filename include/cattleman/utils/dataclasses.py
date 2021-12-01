import dataclasses
from typing import Union, Any, Iterable

from cattleman.constants import UNDEFINED, NoneType


def make_field(type: Union[type, Iterable[Union[type, NoneType]]],
               default: Any = UNDEFINED,
               content: Union[type, Iterable[Union[type, NoneType]]] = UNDEFINED,
               factory: Any = UNDEFINED) -> dataclasses.Field:
    args = {
        'metadata': {
            'type': type,
            'content': content
        }
    }
    # default
    if default is not UNDEFINED:
        if not callable(default):
            args['default'] = default
        else:
            args['default_factory'] = default
    # default factory
    if factory is not UNDEFINED:
        args['default_factory'] = factory if callable(factory) else (lambda: factory)
    # one or the other
    if 'default_factory' not in args and 'default' not in args:
        args['default'] = UNDEFINED
    # ---
    return dataclasses.field(**args)
