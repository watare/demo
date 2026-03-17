"""
Titanair Executive Brief — Module d'envoi via Brevo (ex-Sendinblue)
Envoie la newsletter HTML avec le fichier podcast MP3 en pièce jointe.
"""

import base64
import os
from pathlib import Path

import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException


def send_newsletter(
    html_content: str,
    subject: str,
    recipients: list[str],
    sender_email: str,
    sender_name: str,
    attachment_path: str | None = None,
    api_key: str | None = None,
) -> dict:
    """
    Envoie la newsletter via l'API Brevo.

    Args:
        html_content: Contenu HTML de la newsletter
        subject: Objet de l'e-mail
        recipients: Liste d'adresses e-mail des destinataires
        sender_email: Adresse e-mail de l'expéditeur
        sender_name: Nom de l'expéditeur
        attachment_path: Chemin vers le fichier MP3 (optionnel)
        api_key: Clé API Brevo (si None, lue depuis BREVO_API_KEY)

    Returns:
        Réponse de l'API Brevo
    """
    api_key = api_key or os.environ["BREVO_API_KEY"]

    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key["api-key"] = api_key

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
        sib_api_v3_sdk.ApiClient(configuration)
    )

    to_list = [{"email": email.strip()} for email in recipients]

    send_params = {
        "sender": {"name": sender_name, "email": sender_email},
        "to": to_list,
        "subject": subject,
        "html_content": html_content,
    }

    # Ajouter la pièce jointe MP3 si disponible
    if attachment_path and os.path.exists(attachment_path):
        mp3_data = Path(attachment_path).read_bytes()
        b64_content = base64.b64encode(mp3_data).decode("utf-8")
        filename = os.path.basename(attachment_path)

        send_params["attachment"] = [
            {"content": b64_content, "name": filename}
        ]
        print(f"Pièce jointe : {filename} ({len(mp3_data)} octets)")

    send_email = sib_api_v3_sdk.SendSmtpEmail(**send_params)

    try:
        response = api_instance.send_transac_email(send_email)
        print(f"Newsletter envoyée ! Message ID : {response.message_id}")
        return {"success": True, "message_id": response.message_id}
    except ApiException as e:
        print(f"Erreur d'envoi Brevo : {e}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    test_html = "<h1>Test Titanair Newsletter</h1><p>Ceci est un test.</p>"
    result = send_newsletter(
        html_content=test_html,
        subject="[TEST] Titanair Executive Brief",
        recipients=[os.environ["RECIPIENTS"].split(",")[0]],
        sender_email=os.environ["SENDER_EMAIL"],
        sender_name=os.environ["SENDER_NAME"],
    )
    print(result)
