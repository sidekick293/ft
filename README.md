# Fitness Tracker

Kleine Webseite zum gemeinsamen Tracken von Sportaktivitäten für zwei Personen.
Kalenderansicht (ein Tag pro Zeile), zwei Spalten, Freitext-Einträge per Klick auf "+".

## ⚠️ Sicherheitshinweis

Diese App hat **kein Login**. Der Port darf nicht direkt ins Internet weitergeleitet
werden. Absicherung muss extern erfolgen, z. B.:

- Synology Reverse Proxy (Systemsteuerung → Anmeldeportal → Erweitert → Reverse-Proxy)
  kombiniert mit dem Synology-Anmeldeportal, oder
- Zugriff nur über VPN (z. B. Tailscale) freigeben.

## Setup (Portainer, Deployment via Git-Repository)

1. Auf dem NAS einmalig den Ordner `/volume1/docker/fitness-tracker/data` anlegen
   (z. B. per File Station) – das ist der Bind-Mount-Zielordner für die Datenbank.
2. In Portainer: **Stacks → Add stack**, Build method **Repository**, diese
   Repo-URL eintragen, Compose-Pfad `docker-compose.yml`.
3. Unter **Environment variables** `PERSON_A_NAME` und `PERSON_B_NAME` setzen
   (steht nicht im Repo, siehe `.env.example` als Vorlage).
4. **Deploy the stack**.

Die Seite ist danach unter `http://<nas-ip>:8080` erreichbar.

## Setup (lokal, ohne Portainer)

```bash
cp .env.example .env
# Namen in .env anpassen (PERSON_A_NAME, PERSON_B_NAME)
docker compose up -d --build
```

Hinweis: `docker-compose.yml` verwendet aktuell den festen NAS-Pfad
`/volume1/docker/fitness-tracker/data`. Für rein lokale Tests auf einem anderen
Rechner diesen Pfad temporär auf `./data` zurückändern.

## Daten

Die SQLite-Datenbank liegt unter `/volume1/docker/fitness-tracker/data/fitness.db`
(Bind-Mount) und bleibt bei Stack-Neudeploys/Updates erhalten. Für Backups reicht
es, diese Datei bzw. den Ordner zu sichern.

## Update

Code-Änderungen committen und pushen, danach in Portainer den Stack öffnen und
**Pull and redeploy** klicken (oder Webhook einrichten).

## Lokale Entwicklung ohne Docker

```bash
pip install -r requirements.txt
python app.py
```

Läuft dann unter `http://localhost:5000`.
