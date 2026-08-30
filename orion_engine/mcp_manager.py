from mcp import ClientSession, Tool
from mcp.client.stdio import StdioServerParameters, stdio_client


class MCPServerConnector:
    def __init__(
        self,
        name: str,
        command: str,
        args: list[str],
    ) -> None:
        self.name = name
        self.command = command
        self.args = args

        self._stdio = None
        self.session = None

    async def initialize_session(self):
        server_params = StdioServerParameters(
            command=self.command,
            args=self.args,
        )

        self._stdio = stdio_client(server_params)

        read, write = await self._stdio.__aenter__()

        self.session = ClientSession(read, write)

        await self.session.__aenter__()
        await self.session.initialize()

    async def disconnect(self):
        if self.session:
            await self.session.__aexit__(None, None, None)

        if self._stdio:
            await self._stdio.__aexit__(None, None, None)

    async def list_tools(self) -> list[Tool]:
        result = await self.session.list_tools()

        return result.tools

    async def call_tool(
        self,
        name: str,
        arguments: dict,
    ):
        return await self.session.call_tool(
            name,
            arguments,
        )
