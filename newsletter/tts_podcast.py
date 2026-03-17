"""
Titanair Executive Brief — Module Google Cloud TTS
Génère le fichier audio MP3 du podcast à partir du script texte.
"""

import os
import re
from pathlib import Path

from google.cloud import texttospeech


def strip_stage_directions(script: str) -> str:
    """Retire les indications scéniques [entre crochets] et les marqueurs PRÉSENTATEUR."""
    text = re.sub(r"\[.*?\]", "", script)
    text = re.sub(r"PRÉSENTATEUR\s*:", "", text)
    text = re.sub(r"[«»]", "", text)
    # Nettoyer les lignes vides multiples
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def generate_podcast_audio(
    script_path: str,
    output_path: str,
    voice_name: str = "fr-FR-Wavenet-B",
    speaking_rate: float = 0.95,
) -> str:
    """
    Génère un fichier MP3 à partir du script podcast.

    Args:
        script_path: Chemin vers le fichier script .txt
        output_path: Chemin de sortie pour le fichier .mp3
        voice_name: Voix Google Cloud TTS (fr-FR-Wavenet-B = voix masculine posée)
        speaking_rate: Vitesse de parole (0.95 = légèrement plus lent, style France Inter)

    Returns:
        Chemin du fichier MP3 généré
    """
    script_text = Path(script_path).read_text(encoding="utf-8")
    clean_text = strip_stage_directions(script_text)

    client = texttospeech.TextToSpeechClient()

    # Construire le SSML pour un rendu plus naturel
    ssml = build_ssml(clean_text)

    synthesis_input = texttospeech.SynthesisInput(ssml=ssml)

    voice = texttospeech.VoiceSelectionParams(
        language_code="fr-FR",
        name=voice_name,
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=speaking_rate,
        pitch=-1.0,  # Voix légèrement plus grave
        effects_profile_id=["headphone-class-device"],
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config,
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as out:
        out.write(response.audio_content)

    print(f"Audio généré : {output_path} ({len(response.audio_content)} octets)")
    return output_path


def build_ssml(text: str) -> str:
    """Construit du SSML à partir du texte nettoyé pour un rendu naturel."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    ssml_parts = ["<speak>"]
    for paragraph in paragraphs:
        ssml_parts.append(f'  <p><s>{paragraph}</s></p>')
        ssml_parts.append('  <break time="800ms"/>')
    ssml_parts.append("</speak>")

    return "\n".join(ssml_parts)


if __name__ == "__main__":
    import sys

    script = sys.argv[1] if len(sys.argv) > 1 else "output/podcast-script.txt"
    output = sys.argv[2] if len(sys.argv) > 2 else "output/podcast.mp3"
    generate_podcast_audio(script, output)
