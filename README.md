# Operations KPI Automation – Python / API / Power BI Demo

Portfolio-MVP für ein typisches kleines Automatisierungspaket: operative
CSV-Daten werden validiert, mit Python zu belastbaren KPIs verdichtet und über
eine FastAPI-Schnittstelle für Power BI, n8n oder andere Systeme bereitgestellt.

Die Demo nutzt ausschließlich synthetische Daten.

[![Tests](https://github.com/leonwwest/operations-kpi-automation-demo/actions/workflows/tests.yml/badge.svg)](https://github.com/leonwwest/operations-kpi-automation-demo/actions/workflows/tests.yml)
[![Live-Demo](https://img.shields.io/badge/Live--Demo-öffnen-d5ff3f)](https://operations-kpi-automation-demo.vercel.app)

![Operations KPI Dashboard](demo-preview.png)

**Direkt ausprobieren:** [operations-kpi-automation-demo.vercel.app](https://operations-kpi-automation-demo.vercel.app)

**Kurzer Browser-Rundgang:** [Portfolio-Video ansehen](portfolio-demo.mp4)

## Was die Demo zeigt

- reproduzierbare CSV-Validierung ohne versteckte manuelle Schritte
- fehlerhafte Zeilen (u. a. verkürzte Zeilen, NaN/Infinity, Regelverletzungen)
  werden quarantänisiert und im Quality-Block der API gemeldet, statt den Lauf
  abzubrechen
  ([`data/operations-broken.csv`](data/operations-broken.csv) zum Ausprobieren)
- KPI-Berechnung für Aufträge, Umsatz, Termintreue, Bearbeitungszeit und
  Störungen über 12 Monate und drei Teams
- REST-API mit typisierten Response-Modellen, Healthcheck, Ergebnisabruf und
  simuliertem Refresh inkl. Lauf-Protokoll
- interaktives Management-Dashboard mit Zielwert-Ampel und Trend-Indikator
- Power-Query-M-Vorlage und DAX-Beispielkennzahlen
- importierbarer n8n-Workflow: täglicher Schedule-Trigger, Refresh-Aufruf und
  getrennte Status-/Fehlermeldung
- automatisierte Tests und GitHub Actions

```mermaid
flowchart LR
    CSV["Synthetische CSV-Daten"] --> PY["Python Validierung & Aggregation"]
    PY --> API["FastAPI KPI API"]
    API --> BI["Power BI / Power Query"]
    API --> N8N["n8n Workflow"]
    API --> WEB["Live Dashboard"]
```

## Schnellstart

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

Danach:

- Dashboard: http://127.0.0.1:8001
- API-Dokumentation: http://127.0.0.1:8001/docs
- KPI-Endpunkt: http://127.0.0.1:8001/api/kpis

## Tests

```bash
pytest -q
```

## Power BI

Unter [`powerbi/operations-kpi-query.m`](powerbi/operations-kpi-query.m) liegt
eine Power-Query-Abfrage für die Live-API. Beispielkennzahlen stehen in
[`powerbi/measures.dax`](powerbi/measures.dax).

## n8n

[`workflows/n8n-kpi-refresh.json`](workflows/n8n-kpi-refresh.json) kann direkt
in n8n importiert werden. Der Workflow läuft täglich um 06:00 Uhr, ruft den
Refresh-Endpunkt der Live-Demo auf, prüft das Ergebnis und bereitet je nach
Ausgang eine kompakte Status- oder Fehlermeldung vor.

## Abgrenzung

Die Demo ist ein bewusst kleines, vorführbares Arbeitspaket. In einer
Produktionsumsetzung würden Datenbank-/ERP-Anbindung, Authentifizierung,
fachliche KPI-Freigabe, Monitoring und ein abgestimmtes Berechtigungskonzept
ergänzt.

## Lizenz

MIT
