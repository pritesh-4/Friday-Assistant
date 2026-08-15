"""OpenRouter Unified Audio Client for STT and TTS API interactions."""

import logging
import time
from typing import AsyncGenerator
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

OPENROUTER_TRANSCRIPTION_URL = "https://openrouter.ai/api/v1/audio/transcriptions"
OPENROUTER_SPEECH_URL = "https://openrouter.ai/api/v1/audio/speech"


class OpenRouterAudioError(RuntimeError):
    """Raised when an OpenRouter audio request fails."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class OpenRouterAudioClient:
    """
    Centralized server-side client for OpenRouter Audio APIs (STT & TTS).

    Handles authentication, headers, connection pooling, retries, timeouts,
    error parsing, and observability metrics.
    """

    _client: httpx.AsyncClient | None = None

    @classmethod
    def get_client(cls) -> httpx.AsyncClient:
        """Return a singleton AsyncClient with connection pooling."""
        if cls._client is None or cls._client.is_closed:
            timeout = httpx.Timeout(settings.llm_request_timeout_seconds)
            limits = httpx.Limits(max_keepalive_connections=10, max_connections=20)
            cls._client = httpx.AsyncClient(timeout=timeout, limits=limits)
        return cls._client

    @classmethod
    def _get_headers(cls) -> dict[str, str]:
        """Return standardized request headers for OpenRouter."""
        if not settings.openrouter_api_key:
            raise OpenRouterAudioError(
                "OPENROUTER_API_KEY is missing from environment."
            )
        return {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "HTTP-Referer": settings.frontend_url,
            "X-Title": settings.app_name,
        }

    async def transcribe_audio(
        self,
        audio_bytes: bytes,
        filename: str = "audio.webm",
        mime_type: str = "audio/webm",
        model: str = "openai/whisper-large-v3-turbo",
    ) -> dict:
        """
        Transcribe audio bytes using OpenRouter STT (/api/v1/audio/transcriptions).
        """
        headers = self._get_headers()
        client = self.get_client()

        files = {"file": (filename, audio_bytes, mime_type)}
        data = {"model": model}

        start_time = time.monotonic()
        max_retries = 2

        for attempt in range(max_retries):
            try:
                response = await client.post(
                    OPENROUTER_TRANSCRIPTION_URL,
                    headers=headers,
                    files=files,
                    data=data,
                )

                if response.status_code == 402:
                    logger.warning(
                        "[OPENROUTER-AUDIO] HTTP 402 Payment Required: Credit balance too low for OpenRouter STT."
                    )
                    raise OpenRouterAudioError(
                        "OpenRouter STT requires credit balance ($0.50 minimum).",
                        status_code=402,
                    )

                response.raise_for_status()
                res_data = response.json()
                elapsed = time.monotonic() - start_time
                logger.info(
                    "[OPENROUTER-STT] Transcribed %d bytes audio via '%s' in %.2fs.",
                    len(audio_bytes),
                    model,
                    elapsed,
                )
                return res_data

            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code
                error_body = exc.response.text
                if (
                    status_code in (429, 500, 502, 503, 504)
                    and attempt < max_retries - 1
                ):
                    logger.warning(
                        "[OPENROUTER-STT] HTTP %d on attempt %d, retrying...",
                        status_code,
                        attempt + 1,
                    )
                    import asyncio

                    await asyncio.sleep(1)
                    continue

                logger.error(
                    "[OPENROUTER-STT] HTTP error %d: %s", status_code, error_body
                )
                raise OpenRouterAudioError(
                    f"OpenRouter STT HTTP {status_code}: {error_body}",
                    status_code=status_code,
                ) from exc

            except httpx.RequestError as exc:
                if attempt < max_retries - 1:
                    logger.warning(
                        "[OPENROUTER-STT] Connection error on attempt %d, retrying...",
                        attempt + 1,
                    )
                    import asyncio

                    await asyncio.sleep(1)
                    continue

                logger.error("[OPENROUTER-STT] Connection failure: %s", exc)
                raise OpenRouterAudioError(
                    f"OpenRouter STT connection failed: {exc}"
                ) from exc

        raise OpenRouterAudioError("OpenRouter STT transcription failed after retries.")

    async def synthesize_speech(
        self,
        text: str,
        voice: str = "nova",
        response_format: str = "mp3",
        model: str = "fish-audio/s2.1-pro-free:free",
    ) -> bytes:
        """
        Synthesize text to speech using OpenRouter TTS (/api/v1/audio/speech).
        """
        headers = self._get_headers()
        headers["Content-Type"] = "application/json"
        client = self.get_client()

        payload = {
            "model": model,
            "input": text,
            "voice": voice,
            "response_format": response_format,
        }

        start_time = time.monotonic()
        max_retries = 2

        for attempt in range(max_retries):
            try:
                response = await client.post(
                    OPENROUTER_SPEECH_URL, headers=headers, json=payload
                )
                response.raise_for_status()
                audio_bytes = response.content
                elapsed = time.monotonic() - start_time
                logger.info(
                    "[OPENROUTER-TTS] Synthesized %d chars via '%s' in %.2fs -> %d bytes.",
                    len(text),
                    model,
                    elapsed,
                    len(audio_bytes),
                )
                return audio_bytes

            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code
                error_body = exc.response.text
                if (
                    status_code in (429, 500, 502, 503, 504)
                    and attempt < max_retries - 1
                ):
                    logger.warning(
                        "[OPENROUTER-TTS] HTTP %d on attempt %d, retrying...",
                        status_code,
                        attempt + 1,
                    )
                    import asyncio

                    await asyncio.sleep(1)
                    continue

                logger.error(
                    "[OPENROUTER-TTS] HTTP error %d: %s", status_code, error_body
                )
                raise OpenRouterAudioError(
                    f"OpenRouter TTS HTTP {status_code}: {error_body}",
                    status_code=status_code,
                ) from exc

            except httpx.RequestError as exc:
                if attempt < max_retries - 1:
                    logger.warning(
                        "[OPENROUTER-TTS] Connection error on attempt %d, retrying...",
                        attempt + 1,
                    )
                    import asyncio

                    await asyncio.sleep(1)
                    continue

                logger.error("[OPENROUTER-TTS] Connection failure: %s", exc)
                raise OpenRouterAudioError(
                    f"OpenRouter TTS connection failed: {exc}"
                ) from exc

        raise OpenRouterAudioError("OpenRouter TTS synthesis failed after retries.")

    async def stream_speech(
        self,
        text: str,
        voice: str = "nova",
        response_format: str = "mp3",
        model: str = "fish-audio/s2.1-pro-free:free",
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream synthesized audio bytes from OpenRouter TTS (/api/v1/audio/speech).
        """
        headers = self._get_headers()
        headers["Content-Type"] = "application/json"
        client = self.get_client()

        payload = {
            "model": model,
            "input": text,
            "voice": voice,
            "response_format": response_format,
            "stream": True,
        }

        try:
            async with client.stream(
                "POST", OPENROUTER_SPEECH_URL, headers=headers, json=payload
            ) as response:
                response.raise_for_status()
                async for chunk in response.aiter_bytes():
                    if chunk:
                        yield chunk

        except httpx.HTTPStatusError as exc:
            logger.error(
                "[OPENROUTER-TTS-STREAM] HTTP error %d: %s",
                exc.response.status_code,
                exc.response.text,
            )
            raise OpenRouterAudioError(
                f"OpenRouter TTS streaming HTTP {exc.response.status_code}",
                status_code=exc.response.status_code,
            ) from exc
        except httpx.RequestError as exc:
            logger.error("[OPENROUTER-TTS-STREAM] Connection error: %s", exc)
            raise OpenRouterAudioError(
                f"OpenRouter TTS streaming connection failed: {exc}"
            ) from exc
