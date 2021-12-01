import subprocess
from datetime import datetime
from inspect import isclass
from typing import Union, Any, Type, Iterable, Optional

import typing
from dateutil import tz

from cattleman.constants import UNDEFINED
from cattleman.exceptions import TypeMismatchException
from cpk.constants import CANONICAL_ARCH


def now() -> datetime:
    return datetime.now(tz=tz.tzlocal())


def is_undefined(value: Any) -> bool:
    return id(value) is UNDEFINED


def run_cmd(cmd):
    cmd = " ".join(cmd)
    lines = subprocess.check_output(cmd, shell=True).decode("utf-8").split("\n")
    return list(filter(lambda line: len(line) > 0, lines))


def assert_canonical_arch(arch):
    if arch not in CANONICAL_ARCH.values():
        raise ValueError(
            f"The given architecture '{arch}' is not supported. "
            f"Valid choices are: {', '.join(list(set(CANONICAL_ARCH.values())))}"
        )


def canonical_arch(arch):
    if arch not in CANONICAL_ARCH:
        raise ValueError(
            f"Given architecture {arch} is not supported. "
            f"Valid choices are: {', '.join(list(set(CANONICAL_ARCH.values())))}"
        )
    # ---
    return CANONICAL_ARCH[arch]


def human_size(value: Union[int, float], suffix: str = "B", precision: int = 2):
    fmt = f"%3.{precision}f %s%s"
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if abs(value) < 1024.0:
            return fmt % (value, unit, suffix)
        value /= 1024.0
    return fmt.format(value, "Yi", suffix)


def human_time(time_secs: Union[int, float], compact: bool = False):
    label = lambda s: s[0] if compact else " " + s
    days = int(time_secs // 86400)
    hours = int(time_secs // 3600 % 24)
    minutes = int(time_secs // 60 % 60)
    seconds = int(time_secs % 60)
    parts = []
    if days > 0:
        parts.append("{}{}".format(days, label("days")))
    if days > 0 or hours > 0:
        parts.append("{}{}".format(hours, label("hours")))
    if days > 0 or hours > 0 or minutes > 0:
        parts.append("{}{}".format(minutes, label("minutes")))
    parts.append("{}{}".format(seconds, label("seconds")))
    return ", ".join(parts)


def ask_confirmation(logger, message, default="y", question="Do you confirm?", choices=None):
    binary_question = False
    if choices is None:
        choices = {"y": "Yes", "n": "No"}
        binary_question = True
    choices_str = " ({})".format(", ".join([f"{k}={v}" for k, v in choices.items()]))
    default_str = f" [{default}]" if default else ""
    while True:
        logger.warn(f"{message.rstrip('.')}.")
        r = input(f"{question}{choices_str}{default_str}: ")
        if r.strip() == "":
            r = default
        r = r.strip().lower()
        if binary_question:
            if r in ["y", "yes", "yup", "yep", "si", "aye"]:
                return True
            elif r in ["n", "no", "nope", "nay"]:
                return False
        else:
            if r in choices:
                return r


def typing_type(type) -> type:
    # noinspection PyProtectedMember,PyUnresolvedReferences
    if isinstance(type, typing._GenericAlias):
        return type.__dict__["__origin__"]
    return type


def typing_content_type(type) -> type:
    # noinspection PyProtectedMember,PyUnresolvedReferences
    if isinstance(type, typing._GenericAlias):
        return type.__dict__["__args__"][0]
    return type


def assert_type(value: Any, klass: Union[Type, Iterable[Type]], nullable: bool = False,
                field: Optional[str] = None):
    if value is None and nullable:
        return


    # typing
    # noinspection PyProtectedMember,PyUnresolvedReferences
    # if isinstance(klass, typing._GenericAlias):
    #     print(klass)
    #     print(value)
    #     print(field)
    #
    #     container = klass.__dict__["__origin__"]
    #     content = klass.__dict__["__args__"]
    #
    #     if container is typing.Union:
    #         if type(None) in content and value is None:
    #             return
    #         for ctype in content:
    #             if isclass(ctype) and isinstance(value, ctype):
    #                 return
    #         TypeMismatchException(klass, value, field=field)
    #     if not isinstance(value, container):
    #         raise TypeMismatchException(container, value, field=field)
    #     if container in [list, set, tuple]:
    #         for i, elem in enumerate(value):
    #             assert_type(elem, content[0], field=f"{field}[{i}]")
    # else:


    if not isinstance(value, klass):
        raise TypeMismatchException(klass, value, field=field)
