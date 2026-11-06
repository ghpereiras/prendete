"""Thin wrapper around AWS Bedrock's Converse API for one job: make the model call a tool and return its arguments.

Forcing a tool call gives structured output without parsing free text. Everything that talks to the network lives
here, so tests (and the eval harness) swap exactly one function: `call_tool`.
"""
import logging
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.config import settings

logger = logging.getLogger(__name__)


class LlmError(Exception):
    """The model call failed or came back unusable. The message is for logs, never shown to users."""


@dataclass
class ToolResult:
    arguments: dict[str, Any]
    input_tokens: int
    output_tokens: int
    latency_ms: int


@lru_cache
def _client():
    credentials = {}
    if settings.aws_access_key_id and settings.aws_secret_access_key:
        credentials = {
            "aws_access_key_id": settings.aws_access_key_id,
            "aws_secret_access_key": settings.aws_secret_access_key,
        }
    return boto3.client(
        "bedrock-runtime",
        region_name=settings.aws_region,
        # Short timeouts: a request that hangs holds one of the few workers of a free instance.
        config=Config(
            connect_timeout=5,
            read_timeout=settings.ai_timeout_seconds,
            retries={"max_attempts": 2, "mode": "standard"},
        ),
        **credentials,
    )


def call_tool(
    *,
    system: str,
    user_text: str,
    tool_name: str,
    tool_description: str,
    schema: dict[str, Any],
    max_tokens: int = 700,
) -> ToolResult:
    started = time.monotonic()
    try:
        response = _client().converse(
            modelId=settings.bedrock_model_id,
            system=[{"text": system}],
            messages=[{"role": "user", "content": [{"text": user_text}]}],
            # Deterministic extraction: the same sentence should give the same draft.
            inferenceConfig={"maxTokens": max_tokens, "temperature": 0},
            toolConfig={
                "tools": [{"toolSpec": {"name": tool_name, "description": tool_description, "inputSchema": {"json": schema}}}],
                "toolChoice": {"tool": {"name": tool_name}},
            },
        )
    except (BotoCoreError, ClientError) as exc:
        raise LlmError(f"bedrock request failed: {type(exc).__name__}: {exc}") from exc

    if response.get("stopReason") == "max_tokens":
        raise LlmError("the model ran out of tokens before finishing the tool call")

    arguments = None
    for block in response.get("output", {}).get("message", {}).get("content", []):
        if "toolUse" in block and block["toolUse"].get("name") == tool_name:
            arguments = block["toolUse"].get("input")
            break
    if not isinstance(arguments, dict):
        raise LlmError("the model did not return the expected tool call")

    usage = response.get("usage", {})
    return ToolResult(
        arguments=arguments,
        input_tokens=int(usage.get("inputTokens", 0)),
        output_tokens=int(usage.get("outputTokens", 0)),
        latency_ms=int((time.monotonic() - started) * 1000),
    )
