"""Shared fixtures. The default enterprise is generated once per process;
tests must treat it as read-only (the injector deep-copies on its own)."""

from functools import lru_cache

from enterprise import generator
from enterprise.config import GenConfig


@lru_cache(maxsize=None)
def default_config():
    return GenConfig()


@lru_cache(maxsize=None)
def default_enterprise():
    return generator.generate(default_config())
