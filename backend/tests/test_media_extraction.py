import pytest
from typing import Optional, Dict, Any
from backend.app.services.document_ingestion.validator import FileValidator, InvalidFileFormatException
from backend.app.services.model_gateway import (
    ModelGateway, MockSpeechProvider, MockTranscriptionProvider,
    TranscriptionProvider, ModelResponse, UsageMetadata
)
from backend.app.services.content_extraction import MediaContentExtractor, TranscriptSegmentDTO

def test_media_file_validation_all_6_formats():
    # 1. MP4
    mp4_bytes = b"\x00\x00\x00\x1cftypmp42" + b"\x00" * 50
    name_mp4, mime_mp4 = FileValidator.validate(mp4_bytes, "lecture_video.mp4")
    assert mime_mp4 == "video/mp4"

    # 2. WebM
    webm_bytes = b"\x1a\x45\xdf\xa3" + b"\x00" * 50
    name_webm, mime_webm = FileValidator.validate(webm_bytes, "presentation.webm")
    assert mime_webm == "video/webm"

    # 3. MOV
    mov_bytes = b"\x00\x00\x00\x14ftypqt  " + b"\x00" * 50
    name_mov, mime_mov = FileValidator.validate(mov_bytes, "clip.mov")
    assert mime_mov == "video/quicktime"

    # 4. MP3
    mp3_bytes = b"ID3" + b"\x00" * 50
    name_mp3, mime_mp3 = FileValidator.validate(mp3_bytes, "audio_lecture.mp3")
    assert mime_mp3 == "audio/mpeg"

    # 5. WAV
    wav_bytes = b"RIFF\x00\x00\x00\x00WAVE" + b"\x00" * 50
    name_wav, mime_wav = FileValidator.validate(wav_bytes, "record.wav")
    assert mime_wav == "audio/wav"

    # 6. M4A
    m4a_bytes = b"\x00\x00\x00\x14ftypM4A " + b"\x00" * 50
    name_m4a, mime_m4a = FileValidator.validate(m4a_bytes, "podcast.m4a")
    assert mime_m4a == "audio/mp4"

@pytest.mark.asyncio
async def test_speech_to_text_segmentation_with_timestamps():
    speech_provider = MockSpeechProvider()
    gateway = ModelGateway(transcription_provider=speech_provider)
    extractor = MediaContentExtractor(
        gateway=gateway,
        segment_duration_sec=60.0,
        max_concurrency=2,
        low_confidence_threshold=0.70
    )

    fake_media_bytes = b"RIFF\x00\x00\x00\x00WAVE" + b"\x00" * 200
    segments = await extractor.extract_transcript_segments(
        file_bytes=fake_media_bytes,
        mime_type="audio/wav",
        total_duration_sec=180.0
    )

    # 180s duration / 60s per segment = 3 segments
    assert len(segments) == 3

    # Check timestamps
    assert segments[0].start_time == 0.0
    assert segments[0].end_time == 60.0
    assert segments[1].start_time == 60.0
    assert segments[1].end_time == 120.0
    assert segments[2].start_time == 120.0
    assert segments[2].end_time == 180.0

    for seg in segments:
        assert seg.text != ""
        assert seg.speaker is not None

@pytest.mark.asyncio
async def test_low_confidence_segment_flagging():
    class LowConfTranscriptionProvider(TranscriptionProvider):
        @property
        def provider_name(self) -> str:
            return "LowConfAI"

        async def transcribe_audio(
            self, audio_bytes: bytes, language: str = "vi", model_name: Optional[str] = None, timeout_sec: float = 60.0
        ) -> ModelResponse[Any]:
            return ModelResponse(
                content="Âm thanh nhiễu không rõ lời",
                usage=UsageMetadata(10, 10, 20, 0.0001),
                model_name="low-conf-v1",
                provider_name=self.provider_name
            )

    gateway = ModelGateway(transcription_provider=LowConfTranscriptionProvider())
    extractor = MediaContentExtractor(gateway=gateway, low_confidence_threshold=0.90)

    segments = await extractor.extract_transcript_segments(
        file_bytes=b"ID3" + b"\x00" * 100,
        mime_type="audio/mpeg",
        total_duration_sec=60.0
    )

    assert len(segments) == 1
    assert segments[0].confidence < 0.90
    assert segments[0].needs_review is True

def test_content_block_creation_with_timestamp_references():
    speech_provider = MockSpeechProvider()
    gateway = ModelGateway(transcription_provider=speech_provider)
    extractor = MediaContentExtractor(gateway=gateway)

    segments = [
        TranscriptSegmentDTO(start_time=0.0, end_time=60.0, text="Khái niệm Gradient Descent.", speaker="Giảng viên 1"),
        TranscriptSegmentDTO(start_time=60.0, end_time=120.0, text="Công thức tính Learning Rate.", speaker="Giảng viên 1")
    ]

    blocks = extractor.group_segments_into_content_blocks(
        document_id="doc-media-1",
        document_version_id="ver-media-1",
        segments=segments
    )

    assert len(blocks) == 2
    assert blocks[0].metadata["timestamp_start"] == 0.0
    assert blocks[0].metadata["timestamp_end"] == 60.0
    assert blocks[0].source_reference == "Timestamp: 0.0s - 60.0s"

    assert blocks[1].metadata["timestamp_start"] == 60.0
    assert blocks[1].metadata["timestamp_end"] == 120.0
    assert blocks[1].source_reference == "Timestamp: 60.0s - 120.0s"
