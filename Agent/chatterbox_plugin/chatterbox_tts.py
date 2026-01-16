"""
Chatterbox TTS Plugin for LiveKit Agents

This module provides a custom TTS class that integrates with LiveKit agents
and calls your deployed Chatterbox TTS API on Modal.

Modal URL Format:
    After `modal deploy main.py`, you get a single base URL:
    https://<workspace>--chatterbox-tts-web-app.modal.run
    
    With routes:
    - POST /speak      - Generate speech
    - GET  /voices     - List voices
    - GET  /languages  - List languages
    - GET  /health     - Health check
    - GET  /docs       - API documentation

Usage in LiveKit agent:
    from chatterbox_tts import ChatterboxTTS
    
    tts = ChatterboxTTS(
        api_url="https://your-workspace--chatterbox-tts-web-app.modal.run",
        voice="priya_hi_female",
        language="en"
    )
    
    # Use in AgentSession
    session = AgentSession(tts=tts, ...)
    
    # Or standalone
    tts_stream = tts.stream()
    tts_stream.push_text("Hello world")
    tts_stream.end_input()
    async for audio in tts_stream:
        await audio_source.capture_frame(audio.frame)
"""

import re
import asyncio
import aiohttp
import struct
import io
import uuid
import logging
from dataclasses import dataclass
from typing import AsyncIterable, Optional
from livekit import rtc
from livekit.agents.tts import TTS, TTSCapabilities, SynthesizedAudio


logger = logging.getLogger("chatterbox_tts")


class ChatterboxTTS(TTS):
    """
    Chatterbox TTS plugin for LiveKit Agents.
    Connects to your deployed Chatterbox TTS API (on Modal).
    """
    
    def __init__(
        self,
        api_url: str,
        voice: str = "default",
        language: str = "en",
        exaggeration: float = 0.5,
        cfg_weight: float = 0.5,
        temperature: float = 0.8,
        sample_rate: int = 24000,
    ):
        super().__init__(
            capabilities=TTSCapabilities(streaming=True),
            sample_rate=sample_rate,
            num_channels=1
        )
        self.api_url = api_url.rstrip("/")
        self.voice = voice
        self.language = language
        self.exaggeration = exaggeration
        self.cfg_weight = cfg_weight
        self.temperature = temperature
        self._session: Optional[aiohttp.ClientSession] = None

    def _ensure_session(self) -> aiohttp.ClientSession:
        if not self._session:
            self._session = aiohttp.ClientSession()
        return self._session
    
    def stream(self, **kwargs) -> "ChatterboxTTSStream":
        logger.info(f"ChatterboxTTS: stream() initialized")
        return ChatterboxTTSStream(self)
    
    async def synthesize(self, text: str) -> bytes:
        """Synthesize speech from text (non-streaming)."""
        url = f"{self.api_url}/speak"
        params = {
            "text": text,
            "language": self.language,
            "exaggeration": self.exaggeration,
        }
        if self.voice and self.voice != "default":
            params["voice"] = self.voice
        
        session = self._ensure_session()
        async with session.post(url, params=params) as response:
            if response.status != 200:
                error = await response.text()
                raise Exception(f"TTS API error: {response.status} - {error}")
            return await response.read()

    async def aclose(self) -> None:
        if self._session:
            await self._session.close()
            self._session = None


class ChatterboxTTSStream:
    """Streaming TTS that yields audio frames for LiveKit."""
    
    def __init__(self, tts: ChatterboxTTS):
        self._tts = tts
        self._text_queue: asyncio.Queue[Optional[str]] = asyncio.Queue()
        self._closed = False
        self._request_id = str(uuid.uuid4())
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._closed = True
        self._text_queue.put_nowait(None)
    
    def push_text(self, text: str) -> None:
        if not self._closed:
            self._text_queue.put_nowait(text)
    
    def end_input(self) -> None:
        self._text_queue.put_nowait(None)
        self._closed = True
    
    async def __aiter__(self) -> AsyncIterable[SynthesizedAudio]:
        buffer = ""
        # Split sentences on standard punctuation to buffer reasonable chunks
        sentence_pattern = re.compile(r'(.*?[.!?]+(?:\s+|$))', re.DOTALL)

        while True:
            text = await self._text_queue.get()
            
            if text is None:
                if buffer.strip():
                    async for audio in self._synthesize_streaming(buffer, self._request_id, is_final_chunk=True):
                        yield audio
                break
            
            buffer += text
            
            while True:
                match = sentence_pattern.search(buffer)
                if not match:
                    break
                
                sentence = match.group(1)
                buffer = buffer[match.end():]
                
                if sentence.strip():
                    async for audio in self._synthesize_streaming(sentence, self._request_id):
                        yield audio

    async def _synthesize_streaming(self, text: str, request_id: str, is_final_chunk: bool = False) -> AsyncIterable[SynthesizedAudio]:
        """Synthesize text and yield audio frames via the /stream endpoint."""
        url = f"{self._tts.api_url}/stream"
        params = {
            "text": text,
            "language": self._tts.language,
            "exaggeration": self._tts.exaggeration,
            "chunk_size": 200
        }
        if self._tts.voice and self._tts.voice != "default":
            params["voice"] = self._tts.voice
        
        session = self._tts._ensure_session()
        
        try:
            async with session.post(url, params=params) as response:
                if response.status != 200:
                    error = await response.text()
                    logger.error(f"ChatterboxTTS: API Error {response.status}: {error}")
                    return

                # Streaming WAV parsing state
                header_buffer = b""
                header_parsed = False
                residual_bytes = b""
                
                # Default WAV properties (will be overwritten by header)
                sample_rate = 24000
                num_channels = 1
                bytes_per_sample = 2
                
                # request_id passed from caller
                frame_duration_ms = 20
                
                frame_count = 0

                async for chunk in response.content.iter_chunked(2048):
                    current_data = chunk
                    
                    # 1. Parse Header (first 44 bytes)
                    if not header_parsed:
                        header_buffer += current_data
                        if len(header_buffer) >= 44:
                            # Extract header and parse
                            header = header_buffer[:44]
                            residual = header_buffer[44:]
                            
                            try:
                                # Parse relevant fields from WAV header
                                # Offsets: NumChannels(22), SampleRate(24), BitsPerSample(34)
                                num_channels = struct.unpack('<H', header[22:24])[0]
                                sample_rate = struct.unpack('<I', header[24:28])[0]
                                bits_per_sample = struct.unpack('<H', header[34:36])[0]
                                bytes_per_sample = bits_per_sample // 8
                            except Exception as e:
                                logger.error(f"Failed to parse WAV header: {e}")
                            
                            header_parsed = True
                            current_data = residual
                        else:
                            continue # Need more data for header

                    # 2. Process PCM Data
                    data_to_process = residual_bytes + current_data
                    
                    # Calculate frame size
                    samples_per_frame = int(sample_rate * frame_duration_ms / 1000)
                    bytes_per_frame = samples_per_frame * bytes_per_sample * num_channels
                    
                    offset = 0
                    while offset + bytes_per_frame <= len(data_to_process):
                        frame_data = data_to_process[offset:offset + bytes_per_frame]
                        offset += bytes_per_frame
                        
                        # Create AudioFrame from raw PCM
                        frame = rtc.AudioFrame(
                            data=frame_data,
                            sample_rate=sample_rate,
                            num_channels=num_channels,
                            samples_per_channel=samples_per_frame,
                        )
                        
                        frame_count += 1
                        yield SynthesizedAudio(
                            frame=frame,
                            request_id=request_id,
                            is_final=False, # is_final will be handled by the last frame of the entire input
                            delta_text=""
                        )
                    
                    # Store incomplete frame for next chunk
                    residual_bytes = data_to_process[offset:]
                
                # After the loop, if there's any residual data, it means the stream ended
                # with an incomplete frame. Pad it and yield as the final frame for this chunk.
                if residual_bytes:
                    # Pad last frame if needed
                    if len(residual_bytes) < bytes_per_frame:
                        residual_bytes = residual_bytes + b'\x00' * (bytes_per_frame - len(residual_bytes))
                    
                    frame = rtc.AudioFrame(
                        data=residual_bytes,
                        sample_rate=sample_rate,
                        num_channels=num_channels,
                        samples_per_channel=samples_per_frame,
                    )
                    frame_count += 1
                    yield SynthesizedAudio(
                        frame=frame,
                        request_id=request_id,
                        is_final=is_final_chunk, # Only mark as final if this is the last chunk of the entire input
                        delta_text=text if is_final_chunk else ""
                    )

        except Exception as e:
            logger.error(f"Streaming failed: {e}")


# =============================================================================
# Helper function to list available voices
# =============================================================================

async def list_voices(api_url: str) -> list:
    """Get list of available voices from the API."""
    url = f"{api_url.rstrip('/')}/voices"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("voices", [])
            return []


async def list_languages(api_url: str) -> list:
    """Get list of supported languages from the API."""
    url = f"{api_url.rstrip('/')}/languages"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("languages", [])
            return []
