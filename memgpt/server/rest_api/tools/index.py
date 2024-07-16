import uuid
from functools import partial
from typing import List, Literal, Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel, Field

from memgpt.models.pydantic_models import ToolModel
from memgpt.server.rest_api.auth_token import get_current_user
from memgpt.server.rest_api.interface import QueuingInterface
from memgpt.server.server import SyncServer

router = APIRouter()

def setup_user_tools_index_router(server: SyncServer, interface: QueuingInterface, password: str):
    get_current_user_with_server = partial(partial(get_current_user, server), password)

    @router.delete("/tools/{tool_name}", tags=["tools"])
    async def delete_tool(
        tool_name: str,
        user_id: uuid.UUID = Depends(get_current_user_with_server),
    ):
        """
        Delete a tool by name
        """
        # Clear the interface
        interface.clear()
        # tool = server.ms.delete_tool(user_id=user_id, tool_name=tool_name) TODO: add back when user-specific
        server.ms.delete_tool(name=tool_name, user_id=user_id)

    @router.get("/tools/{tool_name}", tags=["tools"], response_model=ToolModel)
    async def get_tool(
        tool_name: str,
        user_id: uuid.UUID = Depends(get_current_user_with_server),
    ):
        """
        Get a tool by name
        """
        # Clear the interface
        interface.clear()
        tool = server.ms.get_tool(tool_name=tool_name, user_id=user_id)
        if tool is None:
            # return 404 error
            raise HTTPException(status_code=404, detail=f"Tool with name {tool_name} not found.")
        return tool

    @router.get("/tools", tags=["tools"], response_model=ListToolsResponse)
    async def list_all_tools(
        user_id: uuid.UUID = Depends(get_current_user_with_server),
    ):
        """
        Get a list of all tools available to agents created by a user
        """
        # Clear the interface
        interface.clear()
        tools = server.ms.list_tools(user_id=user_id)
        return ListToolsResponse(tools=tools)

    @router.post("/tools", tags=["tools"], response_model=ToolModel)
    async def create_tool(
        request: CreateToolRequest = Body(...),
        user_id: uuid.UUID = Depends(get_current_user_with_server),
    ):
        """
        Create a new tool
        """
        try:
            return server.create_tool(
                json_schema=request.json_schema,
                source_code=request.source_code,
                source_type=request.source_type,
                tags=request.tags,
                user_id=user_id,
                exists_ok=request.update,
            )
        except Exception as e:
            print(e)
            raise HTTPException(status_code=500, detail=f"Failed to create tool: {e}, exists_ok={request.update}")

    return router
