from pathlib import Path
from orion_engine import ToolManager


tm = ToolManager()

@tm.tool()
class FileSystem:
    """
    Tools for reading, writing, or creating files and directories.
    """
    def __init__(self):
        self.root = Path.home()

    def _resolve(self, path: str) -> Path:
        target = (self.root / path).resolve()

        if self.root != target and self.root not in target.parents:
            raise PermissionError(
                f'Access outside filesystem root is not allowed: {path}'
            )

        return target

    def list_directory(self, path: str = '.') -> list[str]:
        """
        Lists the content of the directory, path is relative to the home directory.
        """
        target = self._resolve(path)

        if not target.is_dir():
            raise NotADirectoryError(path)

        return [
            item.name
            for item in target.iterdir()
        ]

    def read_file(self, path: str) -> str:
        """
        Reads the content of a text file, path is relative to the home directory.
        """
        target = self._resolve(path)

        if not target.is_file():
            raise FileNotFoundError(path)

        return target.read_text(encoding= 'utf-8')

    def write_file(self, path: str, content: str) -> str:
        """
        Writes text to the given file, also creates the directory if it doesn't exists.
        """
        target = self._resolve(path)

        target.parent.mkdir(parents= True, exist_ok= True)
        target.write_text(content, encoding= 'utf-8')

        return f'File written successfully: {path}'

    def create_directory(self, path: str) -> str:
        """
        Creates a single directory or nested directories, path is relative to the home directory.
        """
        target = self._resolve(path)

        target.mkdir(parents= True, exist_ok= True)

        return f'Directory created successfully: {path}'

    def get_root_directory(self) -> str:
        """
        Returns the root directory in which LLM has access for file & directory related tasks.
        """
        return str(self.root)


FileSystem()     # this is required
