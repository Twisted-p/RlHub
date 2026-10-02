# RL Hub

En standalone Rocket League-app for Windows, uten Overwolf. Den samler rank/MMR, kampoppsummeringer, garage og trening, med et eget Windows-overlay. Ved oppstart kjører en 6,6 sekunders intro der Octane powerslider og blir til RL Hub-logoen.

## Bruke den ferdige appen

Last ned **RL Hub.exe** fra [Releases](https://github.com/Twisted-p/RlHub/releases). Ingen Python-installasjon er nødvendig. Appen bruker Microsoft Edge WebView2 Runtime, som må være installert på maskinen.

Velg plattform og gamertag under Profile for å hente rank. Start Rocket League med kontoen én gang slik at appen kan finne den offentlige spiller-ID-en i den lokale spilloggen. RL Hub aktiverer kampoppsummeringer automatisk ved oppstart når spillinstallasjonen blir funnet. Hvis Rocket League allerede kjører, må spillet startes på nytt etter aktiveringen. La RL Hub kjøre mens du spiller. Performance viser beskjed dersom spillet ikke finnes eller aktiveringen krever skriverettigheter.

Performance har fanene **Kamper** og **Grafer**. Filtrer på gamemode og seier/tap, sorter kamper etter dato eller egne tall, og se skudd, mål, saves og assists for de siste 5, 10 eller 20 kampene. Grafene viser også totaler, snitt og samlet skuddprosent. Du kan åpne kampoppsummeringen direkte fra tabellen under grafene.

Dashboard viser **Dagens spillform** med faktisk treningstid, siste fem egne ranked/casual-kamper, statistiske snitt og MMR-endring per modus i økten. Økten starter automatisk ved første trenings- eller kampdata. Etter hver femkampers blokk anbefales 15 minutter pause ved minst tre tap, eller 5 minutter pause og 5 minutter ny trening ved minst tre seiere. Start pausen i appen; tid i trening/kamp avbryter hvilen. En 90-minutters fokustimer senker readiness gradvis. Dette er lokal coaching, ikke en offisiell stat eller en dokumentert universell fokusgrense. Detaljene i beregningen kan åpnes i Dashboard.

**Goals** lar deg lagre ett rankmål for hver av 1v1, 2v2 og 3v3. Siden bruker siste hentede MMR, omtrentlige rankgrenser per modus og `ceil(MMR igjen / 9)` for anslåtte seiere på rad. Mål lagres separat per tilkoblet spiller i `goals.json`; +9 er et planleggingsanslag, ikke en garanti for MMR-endringen i en kamp.

**Garage** har et visuelt preset-bibliotek med community-gjenskapinger av design fra zen, jstn, Squishy og Retals. Se bilbilder, delelister, farger og kildelenker; søk, filtrer på bil, lagre favoritter eller lag egne varianter. Eksisterende egne presets beholdes. Aktivt preset gjelder RL Hub; delene velges manuelt i Rocket League. Bildene er lokale og viser originalreferansen også når en egen variant redigeres. Designene er historiske inspirasjonsforslag, ikke bekreftede nåværende proffoppsett.

## Fortsette utvikling på en annen maskin

Åpne repoet i Codex og be den lese [CODEX_HANDOFF.md](CODEX_HANDOFF.md) og [AGENTS.md](AGENTS.md). Guiden dekker installasjon, bygging, tester, fullskjerm-widget, kodekart og videre utvikling. `main` inneholder den samlede nyeste versjonen.

Du trenger Windows, Git, Python 3.13 og [WebView2 Runtime](https://developer.microsoft.com/en-us/microsoft-edge/webview2/).

```powershell
git clone https://github.com/Twisted-p/RlHub.git
cd RlHub
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe desktop_app.py
```

For å bygge én kjørbar fil:

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm "RL Hub.spec"
```

Resultatet ligger i `dist/RL Hub.exe`. Kildekoden, logoen, introvideoen, modeller og alle filer som trengs til byggingen følger med repoet. `.venv`, `build` og `dist` opprettes lokalt. Det trengs ingen API-nøkkel for funksjonene som er implementert nå.

## Tester

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
.\.venv\Scripts\python.exe tests/splash_ui_smoke.py
.\.venv\Scripts\python.exe tests/performance_ui_smoke.py
.\.venv\Scripts\python.exe tests/garage_ui_smoke.py
.\.venv\Scripts\python.exe tests/readiness_ui_smoke.py
.\.venv\Scripts\python.exe tests/goals_ui_smoke.py
.\.venv\Scripts\python.exe tests/overlay_ui_smoke.py
.\.venv\Scripts\python.exe tests/packaged_smoke.py
```

UI-testene krever Windows og WebView2. Testen av exe-filen bruker egen port, eget vindusnavn og separat lagring slik at den vanlige appen kan fortsette å kjøre.

Med Node.js kan du også kjøre `node tests/performance_analytics.test.cjs` for beregningene bak grafene. Node.js er bare nødvendig for denne utviklertesten.

## Prosjektfiler

- `desktop_app.py`: desktop-vindu, lokal HTTP-server og tjenester.
- `index.html`, øvrige HTML-filer, `script.js`, `styles.css`: grensesnitt.
- `desktop-runtime.js`: tilpasning for standalone-versjonen.
- `garage.js`, `garage.css`, `garage-presets.js`, `assets/garage/`: preset-bibliotek, lokale bilder og kildeoversikt.
- `mmr_provider.py`: rank og MMR via tredjepartstjenesten `mmr.kmdw.dev`.
- `performance_service.py`, `performance.js`, `performance.html`: Rocket Leagues lokale Stats API og kampoppsummeringer.
- `native_overlay.py`, `overlay_service.py`, `overlay.html`, `overlay-settings.js`: Windows-overlay, rank-økter og innstillinger.
- `readiness_service.py`, `readiness.js`: automatisk økt, spillform, femkampers blokker og pause-/treningstimer.
- `goals_service.py`, `goals.js`, `goals.html`: rankmål for 1v1/2v2/3v3 og anslått MMR-avstand/seiersbehov.
- `CODEX_HANDOFF.md`, `AGENTS.md`: instrukser til Codex ved bygging og videre utvikling på en ny maskin.
- `assets/rlhub-intro.mp4`, `App Logo.png`: intro og logo, inkludert i exe-filen.
- `RL Hub.spec`, `requirements*.txt`: bygging og avhengigheter.
- `Ball modell`, `Fennec modell`: modellfiler med teksturer, kilder og lisensinformasjon for videre utvikling.
- `overwolf`, `manifest.json`: den eldre Overwolf-versjonen; standalone-appen laster ikke disse.

Se [STANDALONE_SETUP.md](STANDALONE_SETUP.md) for lagring, rank-oppslag, Performance og feilsøking. Personlige innstillinger, kontoopplysninger og kamphistorikk ligger på maskinen i `%LOCALAPPDATA%\RL Hub` og følger ikke med repoet. En ny maskin får sin egen tomme historikk.

## Modellkreditering

Modellene er laget av [Jako](https://sketchfab.com/fairlight51), lisensiert under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/): [Fennec – Rocket League Car](https://sketchfab.com/3d-models/fennec-rocket-league-car-5b43b50b6eeb4a12a29671df3418f57a) og [Ball – Rocket League](https://sketchfab.com/3d-models/ball-rocket-league-2c8911aa1dcd4c53bad842f2d354dfe2). Originale lisensfiler følger med modellmappene.
