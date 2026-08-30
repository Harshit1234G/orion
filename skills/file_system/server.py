from pathlib import Path
from mcp.server import MCPServer
from .file_system import FileSystem


mcp = MCPServer(
    name= 'ORION FileSystem',
    description= 'Provides controlled filesystem operations for ORION.',
    version= '0.1.0'
)

filesystem = FileSystem(
    root= Path.home()
)

@mcp.tool()
def list_directory(path: str = '.') -> list[str]:
    """
    List files and directories inside the specified directory.

    Args:
        path: path is relative to the home directory of user.

    Returns:
        List of all files and directories.
    """
    return filesystem.list_directory(path)


@mcp.tool()
def read_file(path: str = '.') -> str:
    """
    Read the UTF-8 text contents of a text file.

    Args:
        path: path is relative to the home directory of user.

    Returns:
        Text from the file.
    """
    return filesystem.read_file(path)


@mcp.tool()
def write_file(path: str, content: str) -> str:
    """
    Create or overwrite a UTF-8 text file.

    Args:
        path: path is relative to the home directory of user.
        content: Content to write in the file.

    Returns:
        Confirmation message that file has been created to the given path.
    """
    return filesystem.write_file(path, content)


@mcp.tool()
def create_directory(path: str = '.') -> str:
    """
    Create a directory and any missing parent directories.

    Args:
        path: path is relative to the home directory of user.

    Returns:
        Confirmation message that directory has been created.
    """
    return filesystem.create_directory(path)


if __name__ == '__main__':
    mcp.run()
