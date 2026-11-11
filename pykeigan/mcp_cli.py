# -*- coding: utf-8 -*-
"""
Entry point of the pykeigan-mcp command. Checks that the MCP SDK is installed before loading the server,
so that a plain 'pip install pykeigan-motor' (without the [mcp] extra) gets a clear message instead of a traceback.
"""
import sys

from pykeigan._deps import MissingDependencyError, require_mcp


def main(argv=None):
    try:
        require_mcp()
    except MissingDependencyError as e:
        sys.exit(str(e))
    from pykeigan import mcp_server
    mcp_server.main(argv)


if __name__ == '__main__':
    main()
