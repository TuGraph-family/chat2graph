"""Compatibility helpers for MCP type changes.

This module provides a `ContentBlock` type that works across different
versions of the `mcp` package. Newer versions removed the `ContentBlock`
export in favor of more specific content types like `TextContent`.

Import `ContentBlock` from here instead of `mcp.types` directly.
"""

from __future__ import annotations

from typing import Any


try:  # Prefer the old unified type if available
    from mcp.types import ContentBlock as _ContentBlock  # type: ignore

    ContentBlock = _ContentBlock  # noqa: N816 (keep alias name)
except Exception:  # Fallbacks for newer releases without ContentBlock
    try:
        # Attempt to build a reasonable union from known content types
        from typing import Union

        from mcp.types import (  # type: ignore
            EmbeddedResource,
            ImageContent,
            TextContent,
        )

        ContentBlock = Union[TextContent, ImageContent, EmbeddedResource]  # type: ignore
    except Exception:
        # Last resort: use Any to avoid import-time failures
        ContentBlock = Any  # type: ignore

