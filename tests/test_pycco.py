import copy
import tempfile
import pytest
from hypothesis import given
from hypothesis.strategies import lists, text, booleans, choices, none

import pycco.main as p

PYTHON = p.languages['.py']

FOO_FUNCTION = """def foo():\n    return True"""


@given(lists(text()), text())
def test_shift(fragments, default):
    if fragments == []:
        assert p.shift(fragments, default) == default
    else:
        fragments2 = copy.copy(fragments)
        head = p.shift(fragments, default)
        assert [head] + fragments == fragments2


@given(text(), booleans(), text(min_size=1))
def test_destination(filepath, preserve_paths, outdir):
    dest = p.destination(filepath, preserve_paths=preserve_paths, outdir=outdir)
    assert dest.startswith(outdir)
    assert dest.endswith(".html")


@given(choices(), text())
def test_parse(choice, source):
    l = choice(p.languages.values())
    parsed = p.parse(source, l)
    assert [{"code_text", "docs_text"} == set(s.keys()) for s in parsed]


def test_generate_documentation():
    p.generate_documentation('pycco/main.py', outdir=tempfile.gettempdir())


def test_skip_coding_directive():
    source = "# -*- coding: utf-8 -*-\n" + FOO_FUNCTION
    parsed = p.parse(source, PYTHON)
    for section in parsed:
        assert "coding" not in section['code_text']


def test_multi_line_leading_spaces():
    source = "# This is a\n# comment that\n# is indented\n"
    source += FOO_FUNCTION
    parsed = p.parse(source, PYTHON)
    # The resulting comment has leading spaces stripped out.
    assert parsed[0]["docs_text"] == "This is a\ncomment that\nis indented\n"


@given(text(), text())
def test_get_language_specify_language(source, code):
    assert p.get_language(source, code, language="python") == p.languages['.py']

    with pytest.raises(ValueError):
        p.get_language(source, code, language="non-existent")


@given(text() | none())
def test_get_language_bad_source(source):
    code = "#!/usr/bin/python\n"
    code += FOO_FUNCTION
    assert p.get_language(source, code) == PYTHON
    with pytest.raises(ValueError):
        assert p.get_language(source, "badlang")


@given(text() | none())
def test_get_language_bad_code(code):
    source = "test.py"
    assert p.get_language(source, code) == PYTHON
