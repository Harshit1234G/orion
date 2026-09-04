from pathlib import Path
from orion_engine import GLOBAL_TOOL_MANAGER


@GLOBAL_TOOL_MANAGER.tool
class FileSystem:
    def __init__(self, root: str | Path):
        self.root = Path(root).expanduser().resolve()

    def _resolve(self, path: str) -> Path:
        target = (self.root / path).resolve()

        if self.root != target and self.root not in target.parents:
            raise PermissionError(
                f'Access outside filesystem root is not allowed: {path}'
            )

        return target

    def list_directory(self, path: str = '.') -> list[str]:
        target = self._resolve(path)

        if not target.is_dir():
            raise NotADirectoryError(path)

        return [
            item.name
            for item in target.iterdir()
        ]

    def read_file(self, path: str) -> str:
        target = self._resolve(path)

        if not target.is_file():
            raise FileNotFoundError(path)

        return target.read_text(encoding= 'utf-8')

    def write_file(self, path: str, content: str) -> str:
        target = self._resolve(path)

        target.parent.mkdir(parents= True, exist_ok= True)
        target.write_text(content, encoding= 'utf-8')

        return f'File written successfully: {path}'

    def create_directory(self, path: str) -> str:
        target = self._resolve(path)

        target.mkdir(parents= True, exist_ok= True)

        return f'Directory created successfully: {path}'
