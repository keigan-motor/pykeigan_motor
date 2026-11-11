# -*- coding: utf-8 -*-
"""
Entry point of the pykeigan-mcp command. Checks that the MCP SDK is installed before loading the server,
so that a plain 'pip install pykeigan-motor' (without the [mcp] extra) gets a clear message instead of a traceback.
"""
import sys

INSTALL_MESSAGE = """\
pykeigan-mcp needs the MCP SDK (mcp >= 2, Python >= 3.10), which is not installed.
Install it with:

    pip install pykeigan-motor[mcp]        (BLE too: pip install pykeigan-motor[mcp,ble])
"""


def main(argv=None):
    if sys.version_info < (3, 10):
        sys.exit('pykeigan-mcp requires Python 3.10 or later (this is Python {}.{}).'.format(*sys.version_info[:2]))
    try:
        import mcp.server.mcpserver  # noqa: F401  (mcp >= 2)
    except ImportError:
        sys.exit(INSTALL_MESSAGE)
    from pykeigan import mcp_server
    mcp_server.main(argv)


if __name__ == '__main__':
    main()
