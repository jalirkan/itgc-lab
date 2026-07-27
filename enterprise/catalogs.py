"""Loaders for the committed enterprise data files (matrix, roles, SoD, org)."""

import json
import os
from functools import lru_cache

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


@lru_cache(maxsize=None)
def _load(name: str):
    with open(os.path.join(_DATA_DIR, name), "r", encoding="utf-8") as fh:
        return json.load(fh)


def org():
    return _load("org.json")


def roles():
    """system -> role -> {privileged: bool}"""
    return _load("roles.json")


def authorization_matrix():
    """job_function -> sorted list of 'system:role' strings"""
    return _load("authorization_matrix.json")


def sod_matrix():
    """{'pairs': [{'a': 'system:role', 'b': 'system:role', 'conflict': str}]}"""
    return _load("sod_matrix.json")


def is_privileged(system: str, role: str) -> bool:
    return roles()[system][role]["privileged"]


def all_system_roles():
    """Sorted list of every 'system:role' in the role catalog."""
    out = []
    for system, rmap in sorted(roles().items()):
        for role in sorted(rmap):
            out.append("{0}:{1}".format(system, role))
    return out
