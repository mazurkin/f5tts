"""
F5-TTS Voice Cloner
====================
Clone any voice from a short audio sample and generate new speech from text.

Uses F5-TTS for synthesis, with Whisper transcription of the pre-processed
(clipped) reference audio to ensure perfect audio/text alignment.

Usage:
    python voice_clone.py --ref_audio speaker.wav --text "Hello, this is my cloned voice."
    python voice_clone.py --ref_audio speaker.wav --text_file script.txt
    python voice_clone.py --ref_audio speaker.wav --text "Hello" --ref_text "manual transcript"
"""

import argparse
import os
import time
from pathlib import Path

from f5_tts.api import F5TTS


def clone_voice(
    ref_audio: str,
    gen_text: str,
    output_path: str = "output.wav",
    model: str = "F5TTS_v1_Base",
    speed: float = 1.0,
    ref_text: str = "",
    nfe_step: int = 32,
    cfg_strength: float = 2.0,
) -> str:
    """
    Clone a voice: generate new speech in the style of the reference audio.

    F5-TTS internally clips the reference to <=12s. If ref_text is empty,
    it transcribes the clipped audio with Whisper to ensure alignment.

    Args:
        ref_audio:     Path to reference voice audio file.
        gen_text:      Text to speak in the cloned voice.
        output_path:   Where to save the generated audio.
        model:         F5-TTS model name.
        speed:         Speech speed multiplier (1.0 = normal, lower = slower).
        ref_text:      Manual transcript. Leave empty for auto-transcription.
        nfe_step:      Number of ODE solver steps (more = higher quality, slower).
        cfg_strength:  Classifier-free guidance strength (higher = more text-faithful).

    Returns:
        Path to the generated audio file.
    """
    if not os.path.exists(ref_audio):
        raise FileNotFoundError(f"Reference audio not found: {ref_audio}")

    output_path = os.path.abspath(output_path)

    print(f"[F5-TTS] Loading {model} model...")
    tts = F5TTS(model=model)

    print(f"[F5-TTS] Generating speech ({len(gen_text)} chars, speed={speed}, nfe_step={nfe_step}, cfg={cfg_strength})...")
    start = time.time()

    wav, sr, _ = tts.infer(
        ref_file=ref_audio,
        ref_text=ref_text,
        gen_text=gen_text,
        file_wave=output_path,
        speed=speed,
        nfe_step=nfe_step,
        cfg_strength=cfg_strength,
    )

    elapsed = time.time() - start
    duration = len(wav) / sr if sr > 0 else 0
    print(f"[F5-TTS] Done in {elapsed:.1f}s -> {output_path} ({duration:.2f}s audio)")

    return output_path


def clone_voice_batch(
    ref_audio: str,
    text_file: str,
    output_dir: str = "outputs",
    model: str = "F5TTS_v1_Base",
    speed: float = 1.0,
    ref_text: str = "",
    nfe_step: int = 32,
    cfg_strength: float = 2.0,
) -> list[str]:
    """Generate one WAV per non-empty line in text_file."""
    lines = [line.strip() for line in Path(text_file).read_text().splitlines() if line.strip()]
    if not lines:
        print("No text lines found in file.")
        return []

    output_dir = os.path.abspath(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    print(f"[F5-TTS] Loading {model} model...")
    tts = F5TTS(model=model)

    print(f"\n[Batch] Generating {len(lines)} clips...")
    outputs = []
    for i, line in enumerate(lines, 1):
        out_path = os.path.join(output_dir, f"clip_{i:03d}.wav")
        label = f"\"{line[:80]}...\"" if len(line) > 80 else f"\"{line}\""
        print(f"\n[Batch {i}/{len(lines)}] {label}")

        tts.infer(
            ref_file=ref_audio,
            ref_text=ref_text,
            gen_text=line,
            file_wave=out_path,
            speed=speed,
            nfe_step=nfe_step,
            cfg_strength=cfg_strength,
        )
        outputs.append(out_path)

    print(f"\n[Batch] All done! {len(outputs)} files in '{output_dir}/'")
    return outputs


def main():
    parser = argparse.ArgumentParser(description="Clone a voice with F5-TTS")
    parser.add_argument("--ref_audio", required=True, help="Path to reference voice audio")
    parser.add_argument("--text", default=None, help="Text to speak in cloned voice")
    parser.add_argument("--text_file", default=None, help="Text file (one utterance per line) for batch mode")
    parser.add_argument("--ref_text", default="",
                        help="Manual transcript of reference audio (default: auto-transcribe)")
    parser.add_argument("--output", default="output.wav", help="Output WAV path (default: output.wav)")
    parser.add_argument("--output_dir", default="outputs", help="Output dir for batch mode (default: outputs/)")
    parser.add_argument("--model", default="F5TTS_v1_Base",
                        choices=["F5TTS_v1_Base", "F5TTS_Base", "E2TTS_Base", "F5TTS_Small", "E2TTS_Small"],
                        help="TTS model name (default: F5TTS_v1_Base)")
    parser.add_argument("--speed", type=float, default=1.0, help="Speech speed multiplier (default: 1.0)")
    parser.add_argument("--nfe_step", type=int, default=32,
                        help="Number of ODE solver steps; more = better quality, slower (default: 32)")
    parser.add_argument("--cfg_strength", type=float, default=2.0,
                        help="Classifier-free guidance strength (default: 2.0)")

    args = parser.parse_args()

    if not args.text and not args.text_file:
        parser.error("Provide either --text or --text_file")

    if args.text_file:
        clone_voice_batch(
            ref_audio=args.ref_audio,
            text_file=args.text_file,
            output_dir=args.output_dir,
            model=args.model,
            speed=args.speed,
            ref_text=args.ref_text,
            nfe_step=args.nfe_step,
            cfg_strength=args.cfg_strength,
        )
    else:
        clone_voice(
            ref_audio=args.ref_audio,
            gen_text=args.text,
            output_path=args.output,
            model=args.model,
            speed=args.speed,
            ref_text=args.ref_text,
            nfe_step=args.nfe_step,
            cfg_strength=args.cfg_strength,
        )


if __name__ == "__main__":
    main()
