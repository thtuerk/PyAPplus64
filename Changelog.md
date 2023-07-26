# Changelog

## 27.07.2023 v1.1.0
- implementiere Zugriff auf ASMX Seiten
  - `getClient` -> `getAppClient` umbenannt
  - `getWebClient` implementiert
  - dies benötigt Paket `requests-negotiate-sspi`, das leider nur für Windows verfügbar ist

## 06.05.2023 v1.0.1
- Code-Cleanup mit Hilfe von flake8
- Bugfix: neue Python 3.10 Syntax entfernt
- kleinere Verbesserungen an Doku

## 04.05.2023 v1.0.0
erste veröffentlichte Version