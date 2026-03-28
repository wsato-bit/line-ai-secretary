"""Agent orchestrator unit tests.

Tests agent loop, tool dispatch, approval flow, and max_turns limit.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.ai.agent_orchestrator import run_agent, run_agent_collect, MAX_TURNS
from src.ai.tool_dispatcher import ApprovalRequest, dispatch


# ─── Helper ───────────────────────────────────────────────────

def _make_text_block(text: str):
    """Create a mock Anthropic text content block."""
    block = MagicMock()
    block.type = "text"
    block.text = text
    return block


def _make_tool_use_block(tool_id: str, name: str, input_data: dict):
    """Create a mock Anthropic tool_use content block."""
    block = MagicMock()
    block.type = "tool_use"
    block.id = tool_id
    block.name = name
    block.input = input_data
    return block


def _make_response(content_blocks, stop_reason="end_turn"):
    """Create a mock Anthropic messages response."""
    resp = MagicMock()
    resp.content = content_blocks
    resp.stop_reason = stop_reason
    return resp


# ─── Agent Loop Tests ─────────────────────────────────────────

class TestAgentLoop:
    """Agent orchestrator loop tests."""

    @pytest.mark.asyncio
    async def test_simple_text_response(self):
        """Agent should yield text SSE events for a simple text response."""
        mock_response = _make_response([_make_text_block("Hello, how can I help?")])

        with patch("src.ai.agent_orchestrator.anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.Anthropic.return_value = mock_client

            events = []
            async for event in run_agent("Hi", "U_test", [], MagicMock()):
                events.append(event)

        # Should have text event and done event
        assert any('"type": "text"' in e for e in events)
        assert any('"type": "done"' in e for e in events)

    @pytest.mark.asyncio
    async def test_tool_use_emits_tool_events(self):
        """Agent should emit tool_start and tool_end SSE events for tool use."""
        # First call: tool use
        tool_block = _make_tool_use_block("tu_1", "get_schedule", {"date": "2026-03-28"})
        resp1 = _make_response([tool_block], stop_reason="tool_use")

        # Second call: final text
        text_block = _make_text_block("Here is your schedule.")
        resp2 = _make_response([text_block], stop_reason="end_turn")

        with patch("src.ai.agent_orchestrator.anthropic") as mock_anthropic, \
             patch("src.ai.agent_orchestrator.dispatch", new_callable=AsyncMock) as mock_dispatch:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = [resp1, resp2]
            mock_anthropic.Anthropic.return_value = mock_client

            mock_dispatch.return_value = {
                "status": "ok",
                "events": [],
                "message": "No events today.",
            }

            events = []
            async for event in run_agent("Show my schedule", "U_test", [], MagicMock()):
                events.append(event)

        event_text = "".join(events)
        assert '"type": "tool_start"' in event_text
        assert '"type": "tool_end"' in event_text
        assert '"type": "done"' in event_text

    @pytest.mark.asyncio
    async def test_max_turns_limit(self):
        """Agent should stop after MAX_TURNS iterations."""
        # Always return tool use to force looping
        tool_block = _make_tool_use_block("tu_1", "get_schedule", {})
        resp = _make_response([tool_block], stop_reason="tool_use")

        with patch("src.ai.agent_orchestrator.anthropic") as mock_anthropic, \
             patch("src.ai.agent_orchestrator.dispatch", new_callable=AsyncMock) as mock_dispatch:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = resp
            mock_anthropic.Anthropic.return_value = mock_client
            mock_dispatch.return_value = {"status": "ok"}

            events = []
            async for event in run_agent("Loop test", "U_test", [], MagicMock()):
                events.append(event)

        # Should have called create exactly MAX_TURNS times
        assert mock_client.messages.create.call_count == MAX_TURNS

    @pytest.mark.asyncio
    async def test_api_error_emits_error_event(self):
        """Anthropic API error should emit an error SSE event."""
        import anthropic

        with patch("src.ai.agent_orchestrator.anthropic") as mock_anthropic_mod:
            mock_client = MagicMock()
            # Simulate APIError
            mock_error = anthropic.APIError(
                message="Rate limited",
                request=MagicMock(),
                body=None,
            )
            mock_client.messages.create.side_effect = mock_error
            mock_anthropic_mod.Anthropic.return_value = mock_client
            mock_anthropic_mod.APIError = anthropic.APIError

            events = []
            async for event in run_agent("Error test", "U_test", [], MagicMock()):
                events.append(event)

        event_text = "".join(events)
        assert '"type": "error"' in event_text
        assert '"type": "done"' in event_text


class TestAgentCollect:
    """run_agent_collect tests (non-SSE mode)."""

    @pytest.mark.asyncio
    async def test_collect_returns_text(self):
        """run_agent_collect should return concatenated text."""
        mock_response = _make_response([_make_text_block("Collected response")])

        with patch("src.ai.agent_orchestrator.anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.Anthropic.return_value = mock_client

            text, approvals = await run_agent_collect(
                "Collect test", "U_test", [], MagicMock()
            )

        assert "Collected response" in text
        assert approvals == []


# ─── Tool Dispatch Tests ──────────────────────────────────────

class TestToolDispatch:
    """Tool dispatcher routing tests."""

    @pytest.mark.asyncio
    async def test_dispatch_known_tool(self):
        """Dispatching a known tool should return a result dict."""
        db = MagicMock()
        result = await dispatch(
            tool_name="get_schedule",
            tool_input={"date": "2026-03-28"},
            user_id="U_test",
            db=db,
        )
        assert isinstance(result, dict)
        assert result.get("status") == "ok"

    @pytest.mark.asyncio
    async def test_dispatch_unknown_tool(self):
        """Dispatching an unknown tool should return an error dict."""
        db = MagicMock()
        result = await dispatch(
            tool_name="nonexistent_tool",
            tool_input={},
            user_id="U_test",
            db=db,
        )
        assert isinstance(result, dict)
        assert "error" in result


# ─── Approval Flow Tests ─────────────────────────────────────

class TestApprovalFlow:
    """Approval request tests."""

    @pytest.mark.asyncio
    async def test_approval_required_tool_returns_request(self):
        """Tools requiring approval should return ApprovalRequest."""
        db = MagicMock()
        result = await dispatch(
            tool_name="create_event",
            tool_input={
                "title": "Test Meeting",
                "date": "2026-03-28",
                "start_time": "10:00",
                "end_time": "11:00",
            },
            user_id="U_test",
            db=db,
        )
        assert isinstance(result, ApprovalRequest)
        assert result.tool_name == "create_event"

    @pytest.mark.asyncio
    async def test_force_execute_skips_approval(self):
        """force_execute=True should bypass approval check."""
        db = MagicMock()
        result = await dispatch(
            tool_name="create_event",
            tool_input={
                "title": "Test",
                "date": "2026-03-28",
                "start_time": "10:00",
                "end_time": "11:00",
            },
            user_id="U_test",
            db=db,
            force_execute=True,
        )
        assert isinstance(result, dict)
        assert result.get("status") == "ok"

    @pytest.mark.asyncio
    async def test_approval_request_emitted_in_agent(self):
        """Agent should emit approval_request SSE event for approval-required tools."""
        tool_block = _make_tool_use_block("tu_1", "create_event", {
            "title": "Meeting",
            "date": "2026-03-28",
            "start_time": "10:00",
            "end_time": "11:00",
        })
        resp1 = _make_response([tool_block], stop_reason="tool_use")
        resp2 = _make_response(
            [_make_text_block("Waiting for approval.")],
            stop_reason="end_turn",
        )

        with patch("src.ai.agent_orchestrator.anthropic") as mock_anthropic, \
             patch("src.ai.agent_orchestrator.dispatch", new_callable=AsyncMock) as mock_dispatch:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = [resp1, resp2]
            mock_anthropic.Anthropic.return_value = mock_client

            mock_dispatch.return_value = ApprovalRequest(
                tool_name="create_event",
                tool_input={"title": "Meeting"},
                description="Create meeting event",
            )

            events = []
            async for event in run_agent("Schedule meeting", "U_test", [], MagicMock()):
                events.append(event)

        event_text = "".join(events)
        assert '"type": "approval_request"' in event_text
