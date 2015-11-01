import copy
import tempfile

from hypothesis import given
from hypothesis.strategies import lists, text, booleans, choices

import pycco.main as p

PYTHON = p.languages['.py']


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
    source = """
# -*- coding: utf-8 -*-
def foo():
    return True
"""
    parsed = p.parse(source, PYTHON)
    for section in parsed:
        assert "coding" not in section['code_text']
