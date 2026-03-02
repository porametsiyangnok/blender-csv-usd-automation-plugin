# Blender CSV-USD Automation Plugin

IHK Abschlussprojekt 2025  
Fachinformatiker für Anwendungsentwicklung  

## Projektbeschreibung

Dieses Blender-Plugin automatisiert die Erstellung animierter GLB-Modelle
aus ISG-virtuos Simulationsdaten.

Dabei werden:
- USD-Dateien (3D-Geometrie)
- CSV-Dateien (Bewegungsdaten)

automatisch zusammengeführt und als animiertes GLB-Modell exportiert.

## Motivation

Die manuelle Zusammenführung von USD- und CSV-Daten ist zeitintensiv
und fehleranfällig. Ziel dieses Projektes war die vollständige
Automatisierung dieses Workflows.

## Technologien

- Python
- Blender API
- USD Import
- CSV Parsing
- Quaternion → Euler Konvertierung
- Keyframe Animation
- GLB Export

## Funktionen

- Import von USD-Dateien
- Einlesen von CSV-Bewegungsdaten
- Automatische Keyframe-Erstellung
- Fehler-Logging
- Export als GLB für Web-Anwendungen

## Architektur

Das Plugin besteht aus folgenden Modulen:

- __init__.py → Registrierung des Addons
- import_usd.py → USD Import
- import_csv.py → CSV Parsing & Datenkonvertierung
- logging_util.py → Logging

## Ergebnis

Ein vollständig automatisierter Workflow zur Erstellung
webfähiger 3D-Modelle mit Animation.
