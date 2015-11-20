import os
import tempfile
import time

import pytest
from hypothesis import given, example
from hypothesis.strategies import text, booleans, choices, none

import pycco.main as p


PYTHON = p.languages['.py']
PYCCO_SOURCE = 'pycco/main.py'
FOO_FUNCTION = """def foo():\n    return True"""


def get_language(choice):
    return choice(list(p.languages.values()))


@given(text(), booleans(), text(min_size=1))
@example("/foo", True, "0")
def test_destination(filepath, preserve_paths, outdir):
    dest = p.destination(filepath, preserve_paths=preserve_paths, outdir=outdir)
    assert dest.startswith(outdir)
    assert dest.endswith(".html")


@given(choices(), text())
def test_parse(choice, source):
    l = get_language(choice)
    parsed = p.parse(source, l)
    for s in parsed:
        assert {"code_text", "docs_text"} == set(s.keys())


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


def test_comment_with_only_cross_ref():
    source = '''# ==Link Target==\n\ndef test_link():\n    """[[testing.py#link-target]]"""\n    pass'''
    sections = p.parse(source, PYTHON)
    highlighted = p.highlight(sections, PYTHON, outdir=tempfile.gettempdir())
    assert highlighted[1]['docs_html'] == '<p><a href="testing.html#link-target">testing.py</a></p>'


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
    with pytest.raises(ValueError) as e:
        assert p.get_language(source, "badlang")

    msg = "Can't figure out the language!"
    try:
        assert e.value.message == msg
    except AttributeError:
        assert e.value.args[0] == msg


@given(text() | none())
def test_get_language_bad_code(code):
    source = "test.py"
    assert p.get_language(source, code) == PYTHON


@given(text(max_size=64))
def test_ensure_directory(dir_name):
    tempdir = os.path.join(tempfile.gettempdir(), str(int(time.time())), dir_name)

    # Use sanitization from function, but only for housekeeping. We
    # pass in the unsanitized string to the function.
    safe_name = p.remove_control_chars(dir_name)

    if not os.path.isdir(safe_name) and os.access(safe_name, os.W_OK):
        p.ensure_directory(tempdir)
        assert os.path.isdir(safe_name)

# The following functions get good test coverage, but effort should be put into
# decomposing the functions they test and actually testing their output.


def test_generate_documentation():
    p.generate_documentation(PYCCO_SOURCE, outdir=tempfile.gettempdir())


@given(booleans(), choices())
def test_process(preserve_paths, choice):
    lang_name = choice([l["name"] for l in p.languages.values()])
    p.process([PYCCO_SOURCE], preserve_paths=preserve_paths, outdir=tempfile.gettempdir(), language=lang_name)


def test_ensure_multiline_string_support():
    code = '''x = """
multi-line-string
"""

y = z  # comment

# *comment with formatting*

def x():
    """multi-line-string
    """'''

    docs_code_tuple_list = p.parse(code, PYTHON)

    assert docs_code_tuple_list[0]['docs_text'] == ''
    assert "#" not in docs_code_tuple_list[1]['docs_text']


def test_pre_indent():
    lines = [
        'def foo():',
        '    """',
        '    Normal text',
        '       indented_text',
        '       second_line',
        '    """',
        '    pass'
    ]
    source = '\n'.join(lines)
    parsed = p.parse(source, PYTHON)
    highlighted = p.highlight(parsed, PYTHON, outdir="/")
