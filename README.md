# Fitness Tracker

Kleine Webseite zum gemeinsamen Tracken von Sportaktivitäten für zwei Personen.
Kalenderansicht (ein Tag pro Zeile), zwei Spalten, Freitext-Einträge per Klick auf "+".

## ⚠️ Sicherheitshinweis

Diese App hat **kein Login**. Der Port darf nicht direkt ins Internet weitergeleitet
werden. Absicherung muss extern erfolgen, z. B.:

- Synology Reverse Proxy (Systemsteuerung → Anmeldeportal → Erweitert → Reverse-Proxy)
  kombiniert mit dem Synology-Anmeldeportal, oder
- Zugriff nur über VPN (z. B. Tailscale) freigeben.

## Setup

```bash
cp .env.example .env
# Namen in .env anpassen (PERSON_A_NAME, PERSON_B_NAME)
docker compose up -d --build
```

Die Seite ist danach unter `http://<nas-ip>:8080` erreichbar.

## Daten

Die SQLite-Datenbank liegt unter `./data/fitness.db` (Bind-Mount) und bleibt bei
`docker compose down`/`up` sowie Updates erhalten. Für Backups reicht es, diese
Datei zu sichern.

## Update

```bash
git pull
docker compose up -d --build
```

## Lokale Entwicklung ohne Docker

```bash
pip install -r requirements.txt
python app.py
```

Läuft dann unter `http://localhost:5000`.
