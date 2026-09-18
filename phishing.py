#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
 AI-Phishing-Awareness-Demo  |  KfW Management-Konferenz
================================================================================
Zweck (DEFENSIV / EDUKATIV):
    Zeigt live, wie ueberzeugend und SCHNELL eine KI eine personalisierte
    Spear-Phishing-Mail erzeugt -- zur Sensibilisierung des Managements.

Ausgabe:
    HTML-Seite im Outlook-Web-Look (Ordner, Posteingang, Lesebereich) mit
    KfW-Branding. Die Mail wird beim Oeffnen Zeichen fuer Zeichen "getippt"
    (Live-Effekt) und zeigt die ECHTE KI-Generierungszeit. Danach per Klick
    die Awareness-Analyse mit markierten Warnsignalen.

Schutzmechanismen (fest eingebaut):
    - Einwilligungs-Gate  - rotes SIMULATION-Banner  - Links nicht klickbar
    - keine Speicherung personenbezogener Daten  - nichts wird versendet

Auth: Entra ID (DefaultAzureCredential) mit Fallback auf AzureCliCredential.
================================================================================
"""

import os
import re
import sys
import time
import html
import json
import datetime

try:
    import requests
    from azure.identity import (DefaultAzureCredential, AzureCliCredential,
                                get_bearer_token_provider)
except ImportError:
    sys.exit("Fehlende Pakete. Installiere sie mit:  pip install -r requirements.txt")


# --------------------------------------------------------------------------- #
# 1) KONFIGURATION
# --------------------------------------------------------------------------- #
ENDPOINT = os.environ.get(
    "AZURE_OPENAI_ENDPOINT",
    "https://aif-bdai-prod-0075.cognitiveservices.azure.com/openai/deployments/gpt-5/chat/completions?api-version=2025-01-01-preview",
)
COMPANY_FILE = os.environ.get("COMPANY_DATA_FILE", "beispiel_firmendaten.json")
HTML_OUT     = os.environ.get("HTML_OUT", "phishing_demo_ausgabe.html")
_SCOPE       = "https://cognitiveservices.azure.com/.default"

# --- Corporate Identity (KfW) ---
BRAND_COLOR   = os.environ.get("BRAND_COLOR", "#005a8c")
BRAND_NAME    = os.environ.get("BRAND_NAME", "KfW")
LOGO_DATA_URI = "data:image/png;base64,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"

_token_provider = None


def _make_token_provider():
    try:
        cred = DefaultAzureCredential()
        cred.get_token(_SCOPE)
        return get_bearer_token_provider(cred, _SCOPE)
    except Exception:
        print("\n[Hinweis] Compute-Instance-Identity nicht verfuegbar (SSO).")
        print("          Fallback auf AzureCliCredential -> ggf. 'az login --use-device-code'.")
        cred = AzureCliCredential()
        cred.get_token(_SCOPE)
        return get_bearer_token_provider(cred, _SCOPE)


def _auth_headers():
    global _token_provider
    if _token_provider is None:
        _token_provider = _make_token_provider()
    return {"Authorization": f"Bearer {_token_provider()}", "Content-Type": "application/json"}


# --------------------------------------------------------------------------- #
# 2) MODELL-AUFRUFE
# --------------------------------------------------------------------------- #
def chat(messages):
    r = requests.post(ENDPOINT, headers=_auth_headers(),
                      json={"messages": messages}, timeout=90)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


def chat_stream(messages, live_print=False):
    """
    Streamt die Antwort (SSE) -> liefert (text, sekunden).
    So ist die angezeigte Generierungszeit ECHT. Fallback auf chat() bei Fehler.
    """
    t0 = time.time()
    try:
        body = {"messages": messages, "stream": True}
        parts = []
        with requests.post(ENDPOINT, headers=_auth_headers(), json=body,
                           timeout=90, stream=True) as r:
            r.raise_for_status()
            for line in r.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    delta = json.loads(data)["choices"][0]["delta"].get("content")
                except Exception:
                    continue
                if delta:
                    parts.append(delta)
                    if live_print:
                        sys.stdout.write("."); sys.stdout.flush()
        if live_print:
            print()
        return "".join(parts).strip(), round(time.time() - t0, 1)
    except Exception:
        return chat(messages), round(time.time() - t0, 1)


def parse_json_block(text):
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z]*", "", t).strip().strip("`").strip()
    i, j = t.find("{"), t.rfind("}")
    if i != -1 and j != -1:
        t = t[i:j + 1]
    return json.loads(t)


# --------------------------------------------------------------------------- #
# 3) HILFSFUNKTIONEN
# --------------------------------------------------------------------------- #
class C:
    R = "\033[0m"; RED = "\033[91m"; YEL = "\033[93m"
    CY = "\033[96m"; GR = "\033[90m"; B = "\033[1m"


def banner(text, zeichen="="):
    line = zeichen * 78
    print("\n" + line); print(text.center(78)); print(line)


def load_companies(pfad):
    if not os.path.exists(pfad):
        sys.exit(f"Firmendaten-Datei nicht gefunden: {pfad}")
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
    try:
        with open("consent_log.txt", "a", encoding="utf-8") as f:
            f.write(f"{datetime.datetime.now().isoformat(timespec='seconds')}\tEinwilligung erteilt (Demo)\n")
    except Exception:
        pass


def read_profile():
    """Liest einen mehrzeiligen Profil-Text bis 'ENDE' (eigene Zeile) oder EOF (Strg-D)."""
    print("LinkedIn-Profil hier komplett einfuegen.")
    print("Abschluss: neue Zeile mit  ENDE  eingeben (oder Strg-D).")
    print("-" * 60)
    lines = []
    try:
        while True:
            line = input()
            if line.strip().upper() == "ENDE":
                break
            lines.append(line)
    except EOFError:
        pass
    return "\n".join(lines).strip()


def in_notebook():
    try:
        from IPython import get_ipython
        ip = get_ipython()
        return ip is not None and ip.__class__.__name__ == "ZMQInteractiveShell"
    except Exception:
        return False


# --------------------------------------------------------------------------- #
# 4) PROMPTS
# --------------------------------------------------------------------------- #
SYSTEM_PROMPT = (
    "Du unterstuetzt eine autorisierte Security-Awareness-Schulung. Erstelle zu "
    "Demonstrationszwecken und mit ausdruecklicher Einwilligung eine realistische, "
    "deutschsprachige Spear-Phishing-Beispielmail. Sie wird nur am Bildschirm "
    "gezeigt, niemals versendet. Erstelle KEINE echten Schadlinks; nutze eine klar "
    "erkennbare Platzhalter-URL. Erfinde keine echten Zugangsdaten. "
    "Antworte ausschliesslich mit gueltigem JSON, ohne Text davor oder danach."
)

USER_PROMPT_TEMPLATE = """Erstelle eine ueberzeugende Spear-Phishing-BEISPIELMAIL fuer eine Awareness-Demo.

ZIELPERSON (mit Einwilligung, oeffentliches LinkedIn-Profil, roh eingefuegt):
=== PROFIL ANFANG ===
{profil}
=== PROFIL ENDE ===

OEFFENTLICHE FIRMENDATEN:
- Firma: {firma_name}
- Branche: {branche}
- Standort: {standort}
- Eingesetzte Tools: {tools}
- Aktueller Anlass/Nachricht: {anlass}
- Vorgetaeuschter Absender: {absender}

Leite Name, Vorname, Rolle, Arbeitgeber und fachliche Schwerpunkte aus dem
Profil ab. Nutze konkrete Details (genutzte Technologien, Projekte, Team) fuer
maximale Personalisierung sowie den aktuellen Anlass fuer Glaubwuerdigkeit
(Pretext, Autoritaet, Dringlichkeit). Baue einen klaren Handlungsaufruf mit einer
OFFENSICHTLICH gefaelschten Platzhalter-URL ein.

Antworte EXAKT in diesem JSON-Schema (deutsche Inhalte):
{{
  "von_name": "Anzeigename des Absenders",
  "von_mail": "gefaelschte-absenderadresse@domain",
  "an": "Vorname der Zielperson",
  "betreff": "string",
  "preview": "kurzer Vorschautext (max 8 Woerter)",
  "text": "Mailtext mit \\n fuer Zeilenumbrueche, inkl. Anrede und Signatur",
  "cta": "Button-Text, z.B. 'Jetzt bestaetigen'",
  "fake_url": "https://[gefaelschte-domain]/..."
}}"""

ANALYSIS_PROMPT_TEMPLATE = """Analysiere diese Phishing-Beispielmail fuer eine Awareness-Schulung. Kurz und sachlich:
1. Genutzte psychologische Manipulationstechniken (Autoritaet, Dringlichkeit, Personalisierung ...).
2. Konkrete WARNSIGNALE, an denen man sie erkennt (Absenderadresse, URL, Ton, Kontext).
3. Ein Satz Handlungsempfehlung.

Nutze kurze Aufzaehlungen mit "- " am Zeilenanfang.

--- MAIL ---
Von: {von} <{mail}>
Betreff: {betreff}
{text}
Link: {fake_url}
--- ENDE ---"""


# --------------------------------------------------------------------------- #
# 5) HTML (Outlook-Look + Live-Typewriter)  -- statisches Template, Daten via JSON
# --------------------------------------------------------------------------- #
def _analysis_to_list(analyse):
    items = []
    for line in analyse.splitlines():
        s = line.strip()
        if not s:
            continue
        if s[0] in "-*•":
            items.append(s.lstrip("-*• ").strip())
        else:
            items.append(s)
    return items


PAGE_TEMPLATE = r"""<!DOCTYPE html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Awareness-Demo</title>
<style>
  :root { --accent:#005a8c; --bg:#f3f4f6; --ink:#201f1e; --muted:#605e5c;
          --line:#e1dfdd; --sel:#e8f0f6; --warn:#b91c1c; --caution:#fff4ce; }
  * { box-sizing:border-box; }
  html,body { margin:0; height:100%; }
  body { font-family:"Segoe UI",-apple-system,Roboto,Helvetica,Arial,sans-serif;
         color:var(--ink); background:var(--bg); }
  .sim { position:sticky; top:0; z-index:50; background:var(--warn); color:#fff;
         text-align:center; font-weight:700; padding:7px 12px; font-size:13px;
         letter-spacing:.4px; }
  .sim small { font-weight:500; opacity:.92; letter-spacing:0; }
  .app { display:flex; flex-direction:column; height:calc(100vh - 32px); min-height:560px; }
  .bar { display:flex; align-items:center; gap:14px; background:var(--accent);
         color:#fff; padding:0 16px; height:48px; flex:none; }
  .bar img { height:26px; background:#fff; border-radius:4px; padding:2px 6px; }
  .bar .ttl { font-weight:600; font-size:15px; }
  .bar .search { flex:1; max-width:440px; background:rgba(255,255,255,.15);
         border-radius:4px; color:#eaf2f8; padding:6px 12px; font-size:13px; }
  .bar .me { margin-left:auto; width:30px; height:30px; border-radius:50%;
         background:#fff; color:var(--accent); display:flex; align-items:center;
         justify-content:center; font-weight:700; }
  .main { display:flex; flex:1; min-height:0; }
  .nav { width:210px; flex:none; background:#faf9f8; border-right:1px solid var(--line);
         padding:12px 8px; overflow:auto; }
  .compose { background:var(--accent); color:#fff; border:none; border-radius:4px;
         padding:8px 12px; font-weight:600; width:100%; margin-bottom:10px; cursor:default; }
  .folder { padding:7px 10px; border-radius:4px; font-size:14px; color:#323130;
         display:flex; justify-content:space-between; }
  .folder.act { background:var(--sel); font-weight:600; color:var(--accent); }
  .folder .n { background:#c7e0f0; color:var(--accent); border-radius:9px;
         font-size:11px; padding:0 7px; font-weight:700; }
  .list { width:340px; flex:none; border-right:1px solid var(--line); overflow:auto; background:#fff; }
  .item { padding:12px 14px; border-bottom:1px solid var(--line); cursor:default; }
  .item.sel { background:var(--sel); box-shadow:inset 3px 0 0 var(--accent); }
  .item .top { display:flex; justify-content:space-between; font-size:13px; }
  .item .snd { font-weight:600; }
  .item.unread .snd { color:var(--accent); }
  .item .time { color:var(--muted); font-size:12px; }
  .item .sub { font-size:13px; margin-top:2px; }
  .item.unread .sub { font-weight:600; }
  .item .prev { font-size:12px; color:var(--muted); margin-top:2px;
         white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .read { flex:1; min-width:0; overflow:auto; background:#fff; }
  .rhd { padding:18px 24px 10px; border-bottom:1px solid var(--line); }
  .rsub { font-size:21px; font-weight:600; margin:0 0 14px; min-height:26px; }
  .rrow { display:flex; align-items:center; gap:12px; }
  .av { width:40px; height:40px; border-radius:50%; background:var(--accent); color:#fff;
        display:flex; align-items:center; justify-content:center; font-weight:700; flex:none; }
  .rfrom { font-weight:600; font-size:14px; }
  .rmeta { color:var(--muted); font-size:12px; }
  .actions { margin:12px 0 0; display:flex; gap:8px; flex-wrap:wrap; }
  .btn2 { border:1px solid var(--line); background:#fff; border-radius:4px;
          padding:6px 12px; font-size:13px; color:#323130; cursor:default; }
  .btn2.primary { background:var(--warn); color:#fff; border-color:var(--warn);
          cursor:pointer; font-weight:600; }
  .caution { margin:14px 24px 0; background:var(--caution); border:1px solid #f5d76e;
          border-radius:4px; padding:8px 12px; font-size:13px; }
  .rbody { padding:18px 24px 40px; line-height:1.6; font-size:15px; max-width:820px; }
  .cursor { display:inline-block; width:8px; background:var(--accent); margin-left:1px;
          animation:blink .9s steps(1) infinite; }
  @keyframes blink { 50% { opacity:0; } }
  .genchip { display:inline-block; margin:2px 0 14px; font-size:12px; font-weight:600;
          color:var(--accent); background:#eaf3f9; border-radius:20px; padding:4px 12px; }
  .cta { display:inline-block; margin:10px 0 4px; background:var(--accent); color:#fff;
          text-decoration:none; padding:11px 22px; border-radius:6px; font-weight:600; }
  .urlline { margin-top:12px; font-size:12px; color:var(--muted); word-break:break-all; }
  .urlline code { background:#f3f4f6; padding:2px 6px; border-radius:4px; }
  .flag { color:var(--warn); text-decoration:underline wavy var(--warn); font-weight:600; }
  .analysis { margin:18px 24px 30px; background:#fef2f2; border:1px solid #fecaca;
          border-radius:10px; padding:16px 20px; display:none; }
  .analysis.show { display:block; }
  .analysis h3 { margin:0 0 8px; color:var(--warn); font-size:15px; }
  .analysis li { margin:4px 0; }
</style></head>
<body>
  <div class="sim">&#9888; SIMULATION &middot; SECURITY-AWARENESS-TRAINING &middot; NICHT ECHT
    <small>&nbsp;Diese Nachricht wurde NICHT versendet. Der Link ist nicht funktionsfaehig.</small>
  </div>
  <div class="app">
    <div class="bar">
      <img id="brandLogo" alt="">
      <span class="ttl">Outlook</span>
      <div class="search">Suchen</div>
      <div class="me" id="meInitial">JB</div>
    </div>
    <div class="main">
      <div class="nav">
        <button class="compose">&#43; Neue E-Mail</button>
        <div class="folder act">Posteingang <span class="n" id="inboxCount">1</span></div>
        <div class="folder">Gesendete Elemente</div>
        <div class="folder">Entwuerfe</div>
        <div class="folder">Geloeschte Elemente</div>
        <div class="folder">Junk-E-Mail</div>
        <div class="folder">Archiv</div>
      </div>
      <div class="list" id="list"></div>
      <div class="read">
        <div class="rhd">
          <h1 class="rsub"><span id="subjectText"></span></h1>
          <div class="rrow">
            <div class="av" id="fromAv">?</div>
            <div>
              <div class="rfrom"><span id="fromName"></span>
                &lt;<span id="fromAddr"></span>&gt;</div>
              <div class="rmeta">An: <span id="toName"></span> &middot; <span id="dateText"></span></div>
            </div>
          </div>
          <div class="actions">
            <div class="btn2">&#8617; Antworten</div>
            <div class="btn2">&#8618; Allen antworten</div>
            <div class="btn2">&#8594; Weiterleiten</div>
            <button class="btn2 primary" id="revealBtn">&#128269; Ist das echt? Analyse zeigen</button>
          </div>
        </div>
        <div class="caution">&#9888; Vorsicht: Diese Nachricht stammt von einem <b>externen Absender</b>. Klicken Sie nur auf Links, wenn Sie den Absender kennen und ihm vertrauen.</div>
        <div class="rbody">
          <div class="genchip" id="genChip">&#9889; KI schreibt die Angriffs-Mail &hellip;</div>
          <div id="bodyText"></div><span class="cursor" id="cursor">&nbsp;</span>
          <div><a class="cta" id="ctaBtn" href="#" onclick="return false;"></a></div>
          <div class="urlline">Ziel des Links (nicht klickbar): <code id="urlText"></code></div>
        </div>
        <div class="analysis" id="analysis">
          <h3>&#128269; Awareness-Analyse &mdash; woran man das erkannt haette</h3>
          <ul id="analysisList"></ul>
        </div>
      </div>
    </div>
  </div>
<script>
window.DEMO = __DEMO_JSON__;
(function(){
  var d = window.DEMO;
  var root = document.documentElement;
  root.style.setProperty('--accent', d.brand || '#005a8c');
  document.getElementById('brandLogo').src = d.logo || '';
  document.getElementById('brandLogo').alt = d.brandName || '';

  // Kopf-Felder
  document.getElementById('fromName').textContent = d.mail.von_name || 'IT-Support';
  document.getElementById('fromAddr').textContent = d.mail.von_mail || '';
  document.getElementById('toName').textContent   = d.mail.an || '';
  document.getElementById('dateText').textContent = d.datum || '';
  document.getElementById('fromAv').textContent   = (d.mail.von_name||'?').trim().charAt(0).toUpperCase();
  document.getElementById('ctaBtn').textContent   = d.mail.cta || 'Jetzt bestaetigen';
  document.getElementById('urlText').textContent  = d.mail.fake_url || '';

  // Posteingang-Liste
  var list = document.getElementById('list');
  d.inbox.forEach(function(m, idx){
    var el = document.createElement('div');
    el.className = 'item' + (idx===0 ? ' sel unread' : (m.unread ? ' unread':''));
    el.innerHTML = '<div class="top"><span class="snd">'+m.snd+'</span>'
                 + '<span class="time">'+m.time+'</span></div>'
                 + '<div class="sub">'+m.sub+'</div>'
                 + '<div class="prev">'+m.prev+'</div>';
    list.appendChild(el);
  });

  // Analyse-Liste (versteckt bis Klick)
  var ul = document.getElementById('analysisList');
  (d.analysis||[]).forEach(function(t){
    var li = document.createElement('li'); li.textContent = t; ul.appendChild(li);
  });

  // Typewriter
  function typeInto(elId, text, speed, done){
    var el = document.getElementById(elId); var i = 0;
    (function step(){
      if(i <= text.length){
        el.innerHTML = text.slice(0,i).replace(/\n/g,'<br>');
        i++; setTimeout(step, speed);
      } else if(done){ done(); }
    })();
  }
  var body = d.mail.text || '';
  var perChar = Math.max(6, Math.min(28, Math.round(3200 / Math.max(1, body.length))));

  typeInto('subjectText', d.mail.betreff || '', 24, function(){
    typeInto('bodyText', body, perChar, function(){
      document.getElementById('cursor').style.display = 'none';
      var chip = document.getElementById('genChip');
      chip.innerHTML = '&#9889; Von der KI erzeugt in <b>'+ (d.gen_seconds||'?') +' Sekunden</b>';
    });
  });

  // Aufdecken der Warnsignale
  document.getElementById('revealBtn').addEventListener('click', function(){
    document.getElementById('analysis').classList.add('show');
    document.getElementById('fromAddr').classList.add('flag');
    document.getElementById('urlText').classList.add('flag');
    document.getElementById('analysis').scrollIntoView({behavior:'smooth', block:'nearest'});
    this.textContent = 'Analyse angezeigt';
  });
})();
</script>
</body></html>"""


DEFAULT_INBOX = [
    # idx 0 wird zur Phishing-Mail (wird zur Laufzeit ersetzt)
    {"snd": "", "time": "", "sub": "", "prev": "", "unread": True},
    {"snd": "Personalabteilung", "time": "08:41", "sub": "Ihre Entgeltabrechnung September 2026",
     "prev": "Ihre Abrechnung steht im Portal bereit.", "unread": False},
    {"snd": "Microsoft 365 Message Center", "time": "Gestern", "sub": "Geplante Wartung am Wochenende",
     "prev": "Kurzzeitige Einschraenkungen moeglich.", "unread": False},
    {"snd": "Confluence", "time": "Gestern", "sub": "3 Seiten wurden aktualisiert",
     "prev": "Zusammenfassung Ihrer beobachteten Seiten.", "unread": False},
    {"snd": "Kantine", "time": "Mo", "sub": "Speiseplan KW 38",
     "prev": "Das Angebot dieser Woche im Ueberblick.", "unread": False},
]


def build_outlook_html(mail, analyse, brand_name, gen_seconds):
    inbox = [dict(x) for x in DEFAULT_INBOX]
    inbox[0] = {"snd": mail.get("von_name", "IT-Support"),
                "time": datetime.datetime.now().strftime("%H:%M"),
                "sub": mail.get("betreff", "(kein Betreff)"),
                "prev": mail.get("preview", ""), "unread": True}
    demo = {
        "brand": BRAND_COLOR, "brandName": brand_name, "logo": LOGO_DATA_URI,
        "datum": datetime.datetime.now().strftime("%d.%m.%Y %H:%M"),
        "gen_seconds": gen_seconds,
        "mail": {k: str(mail.get(k, "")) for k in
                 ["von_name", "von_mail", "an", "betreff", "text", "cta", "fake_url"]},
        "inbox": inbox,
        "analysis": _analysis_to_list(analyse),
    }
    blob = json.dumps(demo, ensure_ascii=False).replace("</", "<\\/")
    return PAGE_TEMPLATE.replace("__DEMO_JSON__", blob)


def show_html(html_str):
    with open(HTML_OUT, "w", encoding="utf-8") as f:
        f.write(html_str)
    if in_notebook():
        from IPython.display import HTML, display
        display(HTML(html_str))
    print(f"\n{C.CY}HTML-Ansicht gespeichert:{C.R} {os.path.abspath(HTML_OUT)}")
    print(f"{C.GR}In JupyterLab im Dateibaum doppelklicken bzw. herunterladen und im "
          f"Browser oeffnen -> Vollbild (F11) fuer den Beamer.{C.R}")


# --------------------------------------------------------------------------- #
# 6) ABLAUF
# --------------------------------------------------------------------------- #
def main():
    banner("AI-PHISHING-AWARENESS-DEMO  --  SIMULATION / TRAINING")
    print("Beispiel-Phishing-Mail zu Schulungszwecken. Wird nur angezeigt, nie")
    print("versendet. Keine Speicherung personenbezogener Daten.\n")

    firmen = load_companies(COMPANY_FILE)

    banner("EINWILLIGUNG", "-")
    if input('Hat die Person ausdruecklich eingewilligt? Tippe "JA": ').strip().upper() != "JA":
        print("\nKeine Einwilligung -> Abbruch."); return
    log_consent()

    banner("FIRMA WAEHLEN", "-")
    firma = choose("Nummer der Firma: ", firmen)

    banner("ZIEL-PROFIL EINFUEGEN (LinkedIn-Text)", "-")
    profil = read_profile()
    if not profil:
        print("\nKein Profil eingegeben -> Abbruch."); return

    banner("GENERIERE MAIL (KI arbeitet) ...", "-")
    user_prompt = USER_PROMPT_TEMPLATE.format(
        profil=profil,
        firma_name=firma.get("name", "-"), branche=firma.get("branche", "-"),
        standort=firma.get("standort", "-"),
        tools=", ".join(firma.get("eingesetzte_tools", [])) or "-",
        anlass=firma.get("aktuelle_nachricht", "-"),
        absender=firma.get("gespoofter_absender", "IT-Support"),
    )
    raw, gen_seconds = chat_stream(
        [{"role": "system", "content": SYSTEM_PROMPT},
         {"role": "user", "content": user_prompt}], live_print=True)
    print(f"{C.GR}KI-Generierung: {gen_seconds} s{C.R}")

    try:
        mail = parse_json_block(raw)
    except Exception:
        mail = {"von_name": firma.get("gespoofter_absender", "IT-Support"), "von_mail": "",
                "an": "", "betreff": "(siehe Text)", "preview": "", "text": raw,
                "cta": "Jetzt bestaetigen", "fake_url": ""}

    analyse = chat([
        {"role": "system", "content": "Du bist Security-Awareness-Trainer."},
        {"role": "user", "content": ANALYSIS_PROMPT_TEMPLATE.format(
            von=mail.get("von_name", ""), mail=mail.get("von_mail", ""),
            betreff=mail.get("betreff", ""), text=mail.get("text", ""),
            fake_url=mail.get("fake_url", ""))},
    ])

    # Terminal-Kurzfassung
    banner(">>> SIMULIERTE PHISHING-MAIL (TRAINING) <<<")
    print(f"{C.GR}Von:{C.R} {mail.get('von_name','')} <{mail.get('von_mail','')}>")
    print(f"{C.B}{C.CY}Betreff: {mail.get('betreff','')}{C.R}\n")
    print(mail.get("text", ""))
    if mail.get("fake_url"):
        print(f"\n{C.YEL}Link (nicht klickbar):{C.R} {mail['fake_url']}")

    show_html(build_outlook_html(mail, analyse, firma.get("name", BRAND_NAME), gen_seconds))
    banner("ENDE DER DEMO  --  keine Daten gespeichert, nichts versendet")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAbgebrochen.")
    except requests.HTTPError as e:
        print(f"\nHTTP-Fehler vom Endpoint: {e}")
