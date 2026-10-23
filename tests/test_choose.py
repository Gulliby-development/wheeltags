from dataclasses import FrozenInstanceError, fields
from inspect import Parameter, signature

import pytest

from wheeltags.choose import Ranked, choose
from wheeltags.listing import Entry, Loaded
from wheeltags.names import parse_name


@pytest.mark.parametrize(
    ("entries", "tags", "expected"),
    [
        ([], ["py3-none-any"], []),
        (
            [Entry(1, parse_name("pkg-1-cp311-cp311-win32.whl", True))],
            ["py3-none-any"],
            [],
        ),
        ([Entry(1, parse_name("pkg-1.tar.gz", True))], [], [(1, None, None)]),
        (
            [Entry(1, parse_name("pkg-1-py2.py3-none-win32.any.whl", True))],
            ["py3-none-any", "py2-none-win32"],
            [(1, 0, "py3-none-any")],
        ),
        (
            [
                Entry(1, parse_name("pkg-2.9-py3-none-any.whl", True)),
                Entry(2, parse_name("pkg-2.10.tar.gz", True)),
            ],
            ["py3-none-any"],
            [(2, None, None), (1, 0, "py3-none-any")],
        ),
        (
            [
                Entry(1, parse_name("pkg-2.1.0.tar.gz", True)),
                Entry(2, parse_name("pkg-2.1-py3-none-any.whl", True)),
            ],
            ["py3-none-any"],
            [(2, 0, "py3-none-any"), (1, None, None)],
        ),
        (
            [
                Entry(1, parse_name("pkg-1-9-py3-none-any.whl", True)),
                Entry(2, parse_name("pkg-1-py2-none-any.whl", True)),
            ],
            ["py2-none-any", "py3-none-any"],
            [(2, 0, "py2-none-any"), (1, 1, "py3-none-any")],
        ),
        (
            [
                Entry(1, parse_name("pkg-1-9-py3-none-any.whl", True)),
                Entry(2, parse_name("pkg-1-10-py3-none-any.whl", True)),
            ],
            ["py3-none-any"],
            [(2, 0, "py3-none-any"), (1, 0, "py3-none-any")],
        ),
        (
            [
                Entry(1, parse_name("pkg-1-py3-none-any.whl", True)),
                Entry(2, parse_name("pkg-1-0-py3-none-any.whl", True)),
            ],
            ["py3-none-any"],
            [(2, 0, "py3-none-any"), (1, 0, "py3-none-any")],
        ),
        (
            [
                Entry(5, parse_name("aaa-1-py3-none-any.whl", True)),
                Entry(2, parse_name("zzz-1-py3-none-any.whl", True)),
            ],
            ["py3-none-any"],
            [(2, 0, "py3-none-any"), (5, 0, "py3-none-any")],
        ),
        (
            [
                Entry(4, parse_name("pkg-1.0.tar.gz", True)),
                Entry(2, parse_name("other-1.tar.gz", True)),
            ],
            [],
            [(2, None, None), (4, None, None)],
        ),
    ],
)
def test_choose_candidate_ordering(entries, tags, expected):
    ranked = choose(entries, tags)
    assert [
        (candidate.entry.line, candidate.rank, candidate.via) for candidate in ranked
    ] == expected


def test_ranked_contract():
    assert [(field.name, field.type) for field in fields(Ranked)] == [
        ("entry", Entry),
        ("rank", int | None),
        ("via", str | None),
    ]
    ranked_signature = signature(Ranked)
    assert [
        (parameter.name, parameter.annotation, parameter.default)
        for parameter in ranked_signature.parameters.values()
    ] == [
        ("entry", Entry, Parameter.empty),
        ("rank", int | None, Parameter.empty),
        ("via", str | None, Parameter.empty),
    ]
    choose_signature = signature(choose)
    assert [
        (parameter.name, parameter.annotation, parameter.default)
        for parameter in choose_signature.parameters.values()
    ] == [
        ("entries", list[Entry], Parameter.empty),
        ("tags", list[str], Parameter.empty),
    ]
    assert choose_signature.return_annotation == list[Ranked]


def test_complete_ties_preserve_input_order():
    first = Entry(7, parse_name("zzz-1.tar.gz", True))
    second = Entry(7, parse_name("aaa-1.tar.gz", True))

    ranked = choose([first, second], [])

    assert [candidate.entry for candidate in ranked] == [first, second]
    assert [(candidate.rank, candidate.via) for candidate in ranked] == [
        (None, None),
        (None, None),
    ]


@pytest.mark.parametrize(
    ("record", "attribute", "replacement"),
    [
        (parse_name("pkg-1-py3-none-any.whl", True), "kind", "sdist"),
        (Entry(1, parse_name("pkg-1.tar.gz", True)), "line", 2),
        (Loaded("listing", []), "display", "other"),
        (Ranked(Entry(1, parse_name("pkg-1.tar.gz", True)), None, None), "rank", 0),
    ],
)
def test_records_reject_field_reassignment(record, attribute, replacement):
    with pytest.raises(FrozenInstanceError):
        setattr(record, attribute, replacement)
