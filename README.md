# RL Hub

En standalone Rocket League-app for Windows, uten Overwolf. Den samler rank/MMR, kampoppsummeringer, garage og trening. Ved oppstart kjører en 6,6 sekunders intro der Octane powerslider og blir til RL Hub-logoen.

## Bruke den ferdige appen

Last ned **RL Hub.exe** fra [Releases](https://github.com/Twisted-p/RlHub/releases). Ingen Python-installasjon er nødvendig. Appen bruker Microsoft Edge WebView2 Runtime, som må være installert på maskinen.

Velg plattform og gamertag under Profile for å hente rank. Start Rocket League med kontoen én gang slik at appen kan finne den offentlige spiller-ID-en i den lokale spilloggen. Under Performance aktiverer du kampoppsummeringer én gang og starter spillet på nytt. La RL Hub kjøre mens du spiller.

## Fortsette utvikling på en annen maskin

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
.\.venv\Scripts\python.exe tests/packaged_smoke.py
```

UI-testene krever Windows og WebView2. Testen av exe-filen bruker egen port, eget vindusnavn og separat lagring slik at den vanlige appen kan fortsette å kjøre.

## Prosjektfiler

- `desktop_app.py`: desktop-vindu, lokal HTTP-server og tjenester.
- `index.html`, øvrige HTML-filer, `script.js`, `styles.css`: grensesnitt.
- `desktop-runtime.js`: tilpasning for standalone-versjonen.
- `mmr_provider.py`: rank og MMR via tredjepartstjenesten `mmr.kmdw.dev`.
- `performance_service.py`, `performance.js`, `performance.html`: Rocket Leagues lokale Stats API og kampoppsummeringer.
- `assets/rlhub-intro.mp4`, `App Logo.png`: intro og logo, inkludert i exe-filen.
- `RL Hub.spec`, `requirements*.txt`: bygging og avhengigheter.
- `Ball modell`, `Fennec modell`: modellfiler med teksturer, kilder og lisensinformasjon for videre utvikling.
- `overwolf`, `manifest.json`: den eldre Overwolf-versjonen; standalone-appen laster ikke disse.

Se [STANDALONE_SETUP.md](STANDALONE_SETUP.md) for lagring, rank-oppslag, Performance og feilsøking. Personlige innstillinger, kontoopplysninger og kamphistorikk ligger på maskinen i `%LOCALAPPDATA%\RL Hub` og følger ikke med repoet. En ny maskin får sin egen tomme historikk.

## Modellkreditering

Modellene er laget av [Jako](https://sketchfab.com/fairlight51), lisensiert under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/): [Fennec – Rocket League Car](https://sketchfab.com/3d-models/fennec-rocket-league-car-5b43b50b6eeb4a12a29671df3418f57a) og [Ball – Rocket League](https://sketchfab.com/3d-models/ball-rocket-league-2c8911aa1dcd4c53bad842f2d354dfe2). Originale lisensfiler følger med modellmappene.
