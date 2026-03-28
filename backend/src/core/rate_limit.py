"""Limiteur de débit partagé — utilisé par tous les routers sensibles."""

from slowapi import Limiter  # type: ignore[import-untyped]
from slowapi.util import get_remote_address  # type: ignore[import-untyped]

limiter = Limiter(key_func=get_remote_address, default_limits=["1000/day"])
