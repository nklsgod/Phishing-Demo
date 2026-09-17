"""
================================================================================
 AI-Phishing-Awareness-Demo  |  Management-Konferenz
================================================================================
Zweck (DEFENSIV / EDUKATIV):
    Zeigt Live, wie ueberzeugend eine KI eine personalisierte Spear-Phishing-
    Mail aus (a) oeffentlichen Firmendaten und (b) manuell eingegebenen
    Profildaten erzeugen kann -- um das Management fuer dieses Risiko zu
    sensibilisieren.

Verantwortungsvoller Einsatz -- fest eingebaut:
    1. Einwilligungs-Gate: ohne ausdrueckliche Einwilligung laeuft nichts.
    2. Die Mail wird NUR am Bildschirm angezeigt, NIE versendet.
    3. Keine dauerhafte Speicherung personenbezogener Daten.
    4. Deutlich sichtbares "SIMULATION / TRAINING"-Banner.
    5. Automatische Awareness-Analyse: benennt Manipulationstechniken +
       Warnsignale (der eigentliche Lerneffekt).

Auth + Aufruf angelehnt an deine bestehenden Skripte:
    Entra ID (DefaultAzureCredential) + Bearer-Token, direkter requests.post
    auf das GPT-5-Deployment in Azure AI Foundry. KEIN API-Key noetig.
================================================================================
"""

import os
import sys
import json
import datetime

try:
    import requests
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider
except ImportError:
    sys.exit("Fehlende Pakete. Installiere sie mit:  pip install -r requirements.txt")


# --------------------------------------------------------------------------- #
# 1) KONFIGURATION  (genau wie in deinen bestehenden Skripten)
# --------------------------------------------------------------------------- #
ENDPOINT = os.environ.get(
    "AZURE_OPENAI_ENDPOINT",
    "https://aif-bdai-prod-0075.cognitiveservices.azure.com/openai/deployments/gpt-5/chat/completions?api-version=2025-01-01-preview",
)

COMPANY_FILE = os.environ.get("COMPANY_DATA_FILE", "beispiel_firmendaten.json")

# Token-Provider: liefert bei JEDEM Aufruf ein frisches (gecachtes/erneuertes)
# Entra-ID-Token -> kein Ablauf mitten in der Demo (Verbesserung ggue. token einmal beim Import).
_token_provider = get_bearer_token_provider(
    DefaultAzureCredential(),
    "https://cognitiveservices.azure.com/.default",
)


# --------------------------------------------------------------------------- #
# 2) MODELL-AUFRUF
# --------------------------------------------------------------------------- #
def chat(messages):
    """POST an das GPT-5-Deployment -- gleiches Muster wie deine anderen Skripte."""
    headers = {
        "Authorization": f"Bearer {_token_provider()}",
        "Content-Type": "application/json",
    }
    body = {"messages": messages}   # GPT-5 (Reasoning): minimaler Body, keine temperature -> laeuft zuverlaessig
    r = requests.post(ENDPOINT, headers=headers, json=body, timeout=90)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


# --------------------------------------------------------------------------- #
# 3) HILFSFUNKTIONEN
# --------------------------------------------------------------------------- #
def banner(text, zeichen="="):
    line = zeichen * 78
    print("\n" + line)
    print(text.center(78))
    print(line)


def load_companies(pfad):
    if not os.path.exists(pfad):
        sys.exit(f"Firmendaten-Datei nicht gefunden: {pfad}\n"
                 f"Setze COMPANY_DATA_FILE oder lege {pfad} an (siehe beispiel_firmendaten.json).")
    with open(pfad, encoding="utf-8") as f:
        data = json.load(f)
    firmen = data.get("companies", data if isinstance(data, list) else [])
    if not firmen:
        sys.exit("Keine Firmen in der JSON gefunden (erwartet: Schluessel 'companies').")
    return firmen


def choose(prompt, optionen):
    for i, o in enumerate(optionen, 1):
        print(f"  [{i}] {o.get('name', o)}")
    while True:
        wahl = input(prompt).strip()
        if wahl.isdigit() and 1 <= int(wahl) <= len(optionen):
            return optionen[int(wahl) - 1]
        print("  Bitte eine gueltige Nummer eingeben.")


def log_consent():
    """Protokolliert NUR Zeitstempel + Einwilligung -- keine personenbezogenen Daten."""
    try:
        with open("consent_log.txt", "a", encoding="utf-8") as f:
            f.write(f"{datetime.datetime.now().isoformat(timespec='seconds')}\tEinwilligung erteilt (Demo)\n")
    except Exception:
        pass  # darf die Demo nie blockieren


# --------------------------------------------------------------------------- #
# 4) PROMPTS  (Muster: SYSTEM_PROMPT + USER_PROMPT_TEMPLATE.format(...))
# --------------------------------------------------------------------------- #
SYSTEM_PROMPT = (
    "Du unterstuetzt eine autorisierte Security-Awareness-Schulung fuer ein "
    "Unternehmen. Deine Aufgabe ist es, zu Demonstrationszwecken und mit "
    "ausdruecklicher Einwilligung der betroffenen Person eine realistische, "
    "deutschsprachige Spear-Phishing-Beispielmail zu erstellen. Sie wird "
    "ausschliesslich am Bildschirm gezeigt, um Mitarbeitende fuer Angriffe zu "
    "sensibilisieren -- niemals versendet. Erstelle KEINE echten funktionierenden "
    "Schadlinks; nutze klar erkennbare Platzhalter-URLs (z.B. "
    "https://[gefaelschte-domain]/login). Erfinde keine echten Zugangsdaten."
)

USER_PROMPT_TEMPLATE = """Erstelle eine ueberzeugende Spear-Phishing-BEISPIELMAIL fuer eine Awareness-Demo.

ZIELPERSON (mit Einwilligung, aus oeffentlichem Profil):
- Name: {name}
- Titel/Position: {position}

OEFFENTLICHE FIRMENDATEN:
- Firma: {firma_name}
- Branche: {branche}
- Standort: {standort}
- Eingesetzte Tools: {tools}
- Aktueller Anlass/Nachricht: {anlass}
- Vorgetaeuschter Absender: {absender}

ANFORDERUNGEN:
- Nutze Position und aktuellen Anlass, um die Mail glaubwuerdig und personalisiert
  zu machen (Pretext, Autoritaet, Dringlichkeit).
- Baue einen klaren Handlungsaufruf ein (Klick / Login) mit einer OFFENSICHTLICH
  gefaelschten Platzhalter-URL.
- Gib die Mail strukturiert aus: Von, An (nur Rolle/Vorname), Betreff, Text, Signatur.
- Deutsch, professioneller Ton."""

ANALYSIS_PROMPT_TEMPLATE = """Analysiere die folgende Phishing-Beispielmail fuer eine Awareness-Schulung. Erklaere sachlich und knapp:
1. Welche psychologischen Manipulationstechniken werden genutzt (z.B. Autoritaet, Dringlichkeit, Personalisierung)?
2. An welchen konkreten WARNSIGNALEN haetten Mitarbeitende die Mail erkennen koennen (Absenderadresse, URL, Ton, Kontext)?
3. Ein Satz Handlungsempfehlung fuer Empfaenger.

Nutze kurze Aufzaehlungen.

--- MAIL ---
{mailtext}
--- ENDE ---"""


# --------------------------------------------------------------------------- #
# 5) ABLAUF
# --------------------------------------------------------------------------- #
def main():
    banner("AI-PHISHING-AWARENESS-DEMO  --  SIMULATION / TRAINING")
    print("Diese Demo erzeugt eine Beispiel-Phishing-Mail zu Schulungszwecken.")
    print("Die Mail wird NUR angezeigt und NICHT versendet. Es werden keine")
    print("personenbezogenen Daten gespeichert.\n")

    firmen = load_companies(COMPANY_FILE)

    # 5.1 Einwilligung
    banner("EINWILLIGUNG", "-")
    print("Bitte die Einwilligung der Person einholen. Ohne Einwilligung wird nichts erstellt.")
    if input('Hat die Person ausdruecklich eingewilligt? Tippe "JA" zum Fortfahren: ').strip().upper() != "JA":
        print("\nKeine Einwilligung -> Abbruch. (Korrektes Verhalten.)")
        return
    log_consent()

    # 5.2 Firma waehlen
    banner("FIRMA WAEHLEN", "-")
    firma = choose("Nummer der Firma: ", firmen)

    # 5.3 Profildaten manuell eingeben (aus LinkedIn kopiert)
    banner("PROFILDATEN (manuell aus dem Profil kopieren)", "-")
    name     = input("Name: ").strip() or "Unbekannt"
    position = input("Titel / Position: ").strip() or "Mitarbeiter/in"

    # 5.4 Mail generieren
    banner("GENERIERE MAIL ...", "-")
    user_prompt = USER_PROMPT_TEMPLATE.format(
        name=name,
        position=position,
        firma_name=firma.get("name", "-"),
        branche=firma.get("branche", "-"),
        standort=firma.get("standort", "-"),
        tools=", ".join(firma.get("eingesetzte_tools", [])) or "-",
        anlass=firma.get("aktuelle_nachricht", "-"),
        absender=firma.get("gespoofter_absender", "IT-Support"),
    )
    mail = chat([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user_prompt},
    ])

    banner(">>> SIMULIERTE PHISHING-MAIL (TRAINING -- NICHT VERSENDEN) <<<")
    print(mail)

    # 5.5 Awareness-Analyse
    banner("AWARENESS-ANALYSE  --  Warum haette man das erkennen koennen?", "-")
    analyse = chat([
        {"role": "system", "content": "Du bist Security-Awareness-Trainer."},
        {"role": "user",   "content": ANALYSIS_PROMPT_TEMPLATE.format(mailtext=mail)},
    ])
    print(analyse)

    banner("ENDE DER DEMO  --  keine Daten gespeichert, nichts versendet")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAbgebrochen.")
    except requests.HTTPError as e:
        print(f"\nHTTP-Fehler vom Endpoint: {e}\nPruefe ENDPOINT, Deployment-Name und deine Azure-Anmeldung (az login / DefaultAzureCredential).")
