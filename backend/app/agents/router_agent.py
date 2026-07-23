import json
from typing import Any

from app.core.config import settings
from app.core.logging import get_logger
from app.services.llm_service import LLMService
from app.services.providers.base import LLMProviderError, LLMResult
from app.tools import tool_manager

logger = get_logger(__name__)

class RouterAgent:
    """Routes the incoming request to the appropriate LLM provider and handles tool calls."""

    def __init__(self) -> None:
        self.llm_service = LLMService()

    def _inject_tools_prompt(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Injects tool descriptions into the system prompt."""
        tools_prompt = tool_manager.get_tools_prompt()
        if tools_prompt == "No tools available.":
            return messages

        system_instruction = (
            "You are FRIDAY, an advanced AI assistant. "
            "You have access to the following tools:\n\n"
            f"{tools_prompt}\n\n"
            "If you need to use a tool to answer the user's request, you MUST reply with ONLY a JSON object in the following format:\n"
            "{\n"
            '  "tool": "tool_name",\n'
            '  "kwargs": {"param1": "value1"}\n'
            "}\n"
            "Do not include any other text if you are calling a tool. "
            "If you do not need a tool, just answer normally as text."
        )

        # Check if the first message is a system message
        new_messages = list(messages)
        if new_messages and new_messages[0]["role"] == "system":
            new_messages[0]["content"] = system_instruction + "\n\n" + str(new_messages[0]["content"])
        else:
            new_messages.insert(0, {"role": "system", "content": system_instruction})

        return new_messages

    async def route_and_execute(self, messages: list[dict[str, Any]]) -> LLMResult:
        """
        Selects a provider, executes it, and handles any tool calls in a loop.
        """
        active_providers = self.llm_service.available_providers
        if not active_providers:
            return LLMResult(
                content=(
                    "I saved your message to this conversation. Configure at least one "
                    "provider (GROQ_API_KEY, GEMINI_API_KEY, OPENROUTER_API_KEY, or NVIDIA_API_KEY) "
                    "in backend/.env to enable AI-generated replies."
                ),
                provider="local-fallback",
                model="offline-storage",
                latency_ms=0,
                finish_reason="offline",
            )

        current_messages = self._inject_tools_prompt(messages)
        
        # Max tool iterations to prevent infinite loops
        max_iterations = 3
        total_latency = 0
        last_provider = "unknown"
        last_model = "unknown"

        for _ in range(max_iterations):
            # Attempt LLM inference
            result = await self._call_providers(current_messages)
            total_latency += result.latency_ms
            last_provider = result.provider
            last_model = result.model
            
            content = result.content.strip()
            
            # Check if it's a JSON tool call
            if content.startswith("{") and content.endswith("}") and '"tool"' in content:
                try:
                    tool_call = json.loads(content)
                    tool_name = tool_call.get("tool")
                    tool_kwargs = tool_call.get("kwargs", {})
                    
                    if tool_name:
                        # Append the LLM's tool call message
                        current_messages.append({"role": "assistant", "content": content})
                        
                        # Execute the tool
                        tool_result = await tool_manager.execute_tool(tool_name, tool_kwargs)
                        
                        # Append the tool observation
                        observation = f"Tool '{tool_name}' result:\n{tool_result}"
                        current_messages.append({"role": "system", "content": observation})
                        continue  # Loop again with the new context
                except json.JSONDecodeError:
                    pass # Not a valid tool JSON, fall through and return as normal response

            # If we reach here, it's not a tool call, or we failed to parse it, so return the final answer
            return LLMResult(
                content=content,
                provider=last_provider,
                model=last_model,
                latency_ms=total_latency,
                finish_reason=result.finish_reason
            )

        # Fallback if max iterations reached
        return LLMResult(
            content="I used too many tools and had to stop. Please try asking in a different way.",
            provider=last_provider,
            model=last_model,
            latency_ms=total_latency,
            finish_reason="max_iterations"
        )

    def _contains_images(self, messages: list[dict[str, Any]]) -> bool:
        """Check if any message in history contains an image_url element."""
        for msg in messages:
            content = msg.get("content")
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "image_url":
                        return True
        return False

    def _sanitize_for_text_only(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Converts multimodal image payloads to text descriptions for text-only LLMs."""
        sanitized = []
        for msg in messages:
            content = msg.get("content")
            if isinstance(content, list):
                text_parts = []
                for item in content:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            text_parts.append(item.get("text", ""))
                        elif item.get("type") == "image_url":
                            text_parts.append("[Attached Image]")
                sanitized.append({"role": msg.get("role", "user"), "content": " ".join(text_parts).strip()})
            else:
                sanitized.append(msg)
        return sanitized

    async def _call_providers(self, messages: list[dict[str, Any]]) -> LLMResult:
        chain = []
        for p in settings.fallback_chain:
            if p not in chain:
                chain.append(p)
                
        errors = []
        has_images = self._contains_images(messages)

        # 1. If images are present, prioritize vision-capable providers
        if has_images:
            for provider_name in chain:
                provider = self.llm_service.get_provider(provider_name)
                if provider and provider.supports_vision:
                    try:
                        return await provider.generate_response(messages)
                    except Exception as exc:
                        logger.error(f"Vision provider {provider_name} failed: {exc}")
                        errors.append(f"{provider_name} (vision): {exc}")
            
            for provider_name, provider in self.llm_service.available_providers.items():
                if provider.supports_vision and provider_name not in chain:
                    try:
                        return await provider.generate_response(messages)
                    except Exception as exc:
                        errors.append(f"{provider_name} (vision): {exc}")

            # Degrade to text-sanitized payload for text-only providers
            logger.warning("No vision provider succeeded. Degrading payload for text-only LLMs.")
            messages = self._sanitize_for_text_only(messages)

        # 2. Standard text execution chain
        for provider_name in chain:
            provider = self.llm_service.get_provider(provider_name)
            if not provider:
                continue
            try:
                return await provider.generate_response(messages)
            except Exception as exc:
                logger.error(f"Provider {provider_name} failed: {exc}")
                errors.append(f"{provider_name}: {exc}")
                
        active_providers = self.llm_service.available_providers
        for provider_name, provider in active_providers.items():
            if provider_name in chain:
                continue
            try:
                return await provider.generate_response(messages)
            except Exception as exc:
                errors.append(f"{provider_name}: {exc}")
                
        raise LLMProviderError(f"All providers failed. Details: {' | '.join(errors)}")

    async def _call_providers_stream(self, messages: list[dict[str, Any]]) -> Any:
        chain = []
        for p in settings.fallback_chain:
            if p not in chain:
                chain.append(p)
                
        errors = []
        has_images = self._contains_images(messages)

        if has_images:
            for provider_name in chain:
                provider = self.llm_service.get_provider(provider_name)
                if provider and provider.supports_vision:
                    try:
                        return provider.stream_response(messages)
                    except Exception as exc:
                        logger.error(f"Vision provider {provider_name} stream failed: {exc}")
                        errors.append(f"{provider_name} (vision): {exc}")
            
            for provider_name, provider in self.llm_service.available_providers.items():
                if provider.supports_vision and provider_name not in chain:
                    try:
                        return provider.stream_response(messages)
                    except Exception as exc:
                        errors.append(f"{provider_name} (vision): {exc}")

            logger.warning("No vision provider succeeded. Degrading payload for text-only LLMs.")
            messages = self._sanitize_for_text_only(messages)

        for provider_name in chain:
            provider = self.llm_service.get_provider(provider_name)
            if not provider:
                continue
            try:
                return provider.stream_response(messages)
            except Exception as exc:
                logger.error(f"Provider {provider_name} stream failed: {exc}")
                errors.append(f"{provider_name}: {exc}")
                
        active_providers = self.llm_service.available_providers
        for provider_name, provider in active_providers.items():
            if provider_name in chain:
                continue
            try:
                return provider.stream_response(messages)
            except Exception as exc:
                errors.append(f"{provider_name}: {exc}")
                
        raise LLMProviderError(f"All stream providers failed. Details: {' | '.join(errors)}")

    async def route_and_stream(self, messages: list[dict[str, Any]]) -> Any:
        """
        Selects a provider, streams the response, and handles any tool calls in a loop.
        Yields text chunks.
        """
        active_providers = self.llm_service.available_providers
        if not active_providers:
            yield (
                "I saved your message to this conversation. Configure at least one "
                "provider in backend/.env to enable AI-generated replies."
            )
            return

        current_messages = self._inject_tools_prompt(messages)
        max_iterations = 3

        for _ in range(max_iterations):
            try:
                stream_generator = await self._call_providers_stream(current_messages)
            except LLMProviderError as exc:
                yield f"Error: {exc}"
                return

            is_tool_call = False
            buffer = ""
            first_chunk_processed = False

            async for chunk in stream_generator:
                if not first_chunk_processed:
                    first_chunk_processed = True
                    if chunk.strip().startswith("{"):
                        is_tool_call = True
                
                if is_tool_call:
                    buffer += chunk
                else:
                    buffer += chunk
                    yield chunk
            
            if is_tool_call:
                content = buffer.strip()
                try:
                    tool_call = json.loads(content)
                    tool_name = tool_call.get("tool")
                    tool_kwargs = tool_call.get("kwargs", {})
                    
                    if tool_name:
                        current_messages.append({"role": "assistant", "content": content})
                        tool_result = await tool_manager.execute_tool(tool_name, tool_kwargs)
                        observation = f"Tool '{tool_name}' result:\n{tool_result}"
                        current_messages.append({"role": "system", "content": observation})
                        continue
                except json.JSONDecodeError:
                    yield content
                    return
            
            # If not a tool call, we streamed the response successfully
            return
            
        yield "I used too many tools and had to stop. Please try asking in a different way."
