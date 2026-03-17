#!/usr/bin/env python3
"""
Titanair Executive Brief — Orchestrateur principal
Lance la génération de la newsletter, du podcast audio, et l'envoi via Brevo.

Usage:
    python main.py              # Génération complète + envoi
    python main.py --dry-run    # Génération sans envoi (prévisualisation)
    python main.py --no-audio   # Envoi sans génération audio TTS
"""

import argparse
import locale
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv


def get_date_info() -> dict:
    """Retourne les informations de date formatées en français."""
    try:
        locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
    except locale.Error:
        pass  # Fallback si la locale n'est pas disponible

    now = datetime.now()
    jours = [
        "Lundi", "Mardi", "Mercredi", "Jeudi",
        "Vendredi", "Samedi", "Dimanche",
    ]
    mois = [
        "janvier", "février", "mars", "avril", "mai", "juin",
        "juillet", "août", "septembre", "octobre", "novembre", "décembre",
    ]

    return {
        "date_full": f"{jours[now.weekday()]} {now.day} {mois[now.month - 1]} {now.year}",
        "date_short": now.strftime("%Y-%m-%d"),
        "year": now.year,
    }


def generate_podcast_script(date_info: dict, output_dir: str) -> str:
    """Génère le script podcast du jour à partir du template."""
    template_path = Path(__file__).parent / "podcast-script-2026-03-17.txt"
    script = template_path.read_text(encoding="utf-8")

    # Remplacer la date dans le script (pour un usage réel, le contenu serait
    # généré dynamiquement — ici on utilise le template statique)
    output_path = os.path.join(output_dir, f"podcast-script-{date_info['date_short']}.txt")
    Path(output_path).write_text(script, encoding="utf-8")
    print(f"Script podcast : {output_path}")
    return output_path


def generate_newsletter_html(date_info: dict, output_dir: str) -> str:
    """Génère le HTML de la newsletter du jour."""
    template_path = Path(__file__).parent / "newsletter-titanair-2026-03-17.html"
    html = template_path.read_text(encoding="utf-8")

    # Pour un usage réel, utiliser Jinja2 avec des données dynamiques
    output_path = os.path.join(output_dir, f"newsletter-{date_info['date_short']}.html")
    Path(output_path).write_text(html, encoding="utf-8")
    print(f"Newsletter HTML : {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Titanair Executive Brief — Envoi quotidien")
    parser.add_argument("--dry-run", action="store_true", help="Générer sans envoyer")
    parser.add_argument("--no-audio", action="store_true", help="Ne pas générer l'audio TTS")
    args = parser.parse_args()

    load_dotenv(Path(__file__).parent / ".env")

    date_info = get_date_info()
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    print(f"=== Titanair Executive Brief — {date_info['date_full']} ===\n")

    # 1. Générer le HTML
    html_path = generate_newsletter_html(date_info, str(output_dir))
    html_content = Path(html_path).read_text(encoding="utf-8")

    # 2. Générer le podcast audio (sauf si --no-audio)
    mp3_path = None
    if not args.no_audio:
        script_path = generate_podcast_script(date_info, str(output_dir))
        mp3_path = str(output_dir / f"brief-titanair-{date_info['date_short']}.mp3")
        try:
            from tts_podcast import generate_podcast_audio
            generate_podcast_audio(script_path, mp3_path)
        except Exception as e:
            print(f"Avertissement TTS : {e}")
            print("Envoi sans pièce jointe audio.")
            mp3_path = None
    else:
        print("Audio TTS : désactivé (--no-audio)")

    # 3. Envoyer via Brevo (sauf si --dry-run)
    if args.dry_run:
        print(f"\n[DRY RUN] Newsletter prête : {html_path}")
        print("Ouvrez ce fichier dans un navigateur pour prévisualiser.")
        return

    recipients_str = os.environ.get("RECIPIENTS", "")
    if not recipients_str:
        print("Erreur : variable RECIPIENTS non définie dans .env")
        sys.exit(1)

    recipients = [r.strip() for r in recipients_str.split(",") if r.strip()]
    sender_email = os.environ.get("SENDER_EMAIL", "newsletter@titanair.fr")
    sender_name = os.environ.get("SENDER_NAME", "Titanair Executive Brief")

    subject = f"Brief Titanair — {date_info['date_full']}"

    from send_brevo import send_newsletter
    result = send_newsletter(
        html_content=html_content,
        subject=subject,
        recipients=recipients,
        sender_email=sender_email,
        sender_name=sender_name,
        attachment_path=mp3_path,
    )

    if result["success"]:
        print(f"\nNewsletter envoyée à {len(recipients)} destinataire(s).")
    else:
        print(f"\nÉchec de l'envoi : {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
