# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Test organization-name normalization from CLI input.

These tests guard against incomplete URL substring sanitization: the
``github.com`` prefix must only be stripped when it is the actual host
of the supplied value, not when it merely appears somewhere in the
string.
"""

import pytest

from markdown_table_fixer.cli import _normalize_org_name


@pytest.mark.parametrize(
    ("supplied", "expected"),
    [
        # Bare organization names are returned unchanged.
        ("myorg", "myorg"),
        ("  myorg  ", "myorg"),
        # Genuine GitHub URLs/hosts have their prefix stripped.
        ("github.com/myorg", "myorg"),
        ("//github.com/myorg", "myorg"),
        ("https://github.com/myorg", "myorg"),
        ("http://github.com/myorg", "myorg"),
        ("https://www.github.com/myorg", "myorg"),
        ("https://github.com/myorg/", "myorg"),
        ("https://github.com/myorg/repo", "myorg"),
    ],
)
def test_normalize_org_name_valid(supplied: str, expected: str) -> None:
    """Legitimate org values resolve to the bare organization name."""
    assert _normalize_org_name(supplied) == expected


@pytest.mark.parametrize(
    "supplied",
    [
        # ``github.com`` appears in the value but is not the host; the
        # value must not be treated as a GitHub URL.
        "evil-github.com.example/payload",
        "notgithub.com/foo",
        "github.com.attacker.test/victim",
        # Surrounding whitespace is stripped before the host check.
        "  notgithub.com/foo  ",
        # Path-based attacks: ``github.com`` appears in the path rather
        # than the host, so it must not trigger prefix stripping.
        "attacker.com/github.com/fake-org",
        "example.com/github.com/org",
    ],
)
def test_normalize_org_name_rejects_lookalike_hosts(supplied: str) -> None:
    """Look-alike hosts are not mistaken for github.com."""
    # No GitHub prefix stripping is applied: the value is returned with
    # only surrounding whitespace and leading/trailing slashes stripped
    # (whitespace is stripped first by the helper).
    assert _normalize_org_name(supplied) == supplied.strip().strip("/")


@pytest.mark.parametrize(
    "supplied",
    [
        "https://github.com",
        "https://github.com/",
        "github.com",
        "//www.github.com/",
    ],
)
def test_normalize_org_name_requires_org_segment(supplied: str) -> None:
    """A GitHub host without an org segment fails fast."""
    with pytest.raises(ValueError, match="No organization found"):
        _normalize_org_name(supplied)


@pytest.mark.parametrize(
    ("supplied", "expected"),
    [
        # Empty and whitespace-only input parses to an empty hostname,
        # so no prefix stripping applies and the result is empty.
        ("", ""),
        ("   ", ""),
        # Slash-only input also yields an empty hostname and an empty
        # result after stripping.
        ("/", ""),
        ("//", ""),
        ("///", ""),
    ],
)
def test_normalize_org_name_empty_or_malformed(
    supplied: str, expected: str
) -> None:
    """Empty or malformed input yields an empty org name, not an error.

    These inputs cause ``urlparse`` to return an empty hostname, which
    must be handled gracefully (the github.com branch is skipped) rather
    than raising or mis-detecting a GitHub URL.
    """
    assert _normalize_org_name(supplied) == expected
