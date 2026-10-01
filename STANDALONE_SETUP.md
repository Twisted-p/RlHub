# RL Hub for Windows

Last ned `RL Hub.exe` fra GitHub Releases, eller bygg den selv til `dist/RL Hub.exe`. Appen kjører i sitt eget vindu og starter lokale rank- og Performance-tjenester automatisk. Overwolf og Python trengs ikke for den ferdigbygde appen.

Desktop-versjonen har dashboard, garage, trening, spilleroppslag, Performance med kampoppsummeringer og en Octane-intro. Den har foreløpig ingen ingame-overlay. Desktop-appen henter rank, divisjon og MMR for 1v1, 2v2 og 3v3 fra [mmr-api-v2](https://github.com/Kalilamodow/mmr-api-v2), på `mmr.kmdw.dev`, uten Tracker eller nettleservindu. Det er en tredjepartstjeneste og ingen garanti for oppetid eller helt ferske data. Lifetime-statistikk og kampantall leveres ikke av denne kilden. Sist lagrede statistikk beholdes ved feil og merkes som ikke oppdatert.

Brukeren velger plattform, skriver gamertag og trykker **Hent rank**. Spiller-ID håndteres i bakgrunnen og kan ikke endres i skjemaet. Appen finner ID fra Rocket Leagues lokale login-logg, med eksakt navnematching, og husker den etter vellykket oppslag. Lagret ID brukes bare når både plattform og gamertag stemmer. Loggen brukes bare til å lese offentlig spiller-ID; innloggingstokens og passord brukes ikke. Hvis kontoen ikke finnes i loggene, må brukeren starte spillet med kontoen én gang. Vilkårlige kontoer som aldri har vært brukt på maskinen kan foreløpig ikke slås opp bare med gamertag. Bare offentlig spiller-ID sendes til MMR-tjenesten.

Profiloppslag, sist hentede statistikk, presets og trening lagres under `%LOCALAPPDATA%/RL Hub`. Nettleser- og Overwolf-lagring flyttes ikke automatisk over. Eksempelpresets følger med; rank-statistikk vises først når en profil er hentet.

Appen bruker Microsoft Edge WebView2 Runtime. Hvis den mangler på maskinen, installer den fra [Microsoft](https://developer.microsoft.com/en-us/microsoft-edge/webview2/). Internett trengs for MMR-oppslag og nettfonter, mens lokale presets og trening kan brukes uten nett.

## Kjøre fra kildekode

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-desktop.txt
.\.venv\Scripts\python.exe desktop_app.py
```

## Bygge én exe-fil

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm "RL Hub.spec"
```

Resultatet er `dist/RL Hub.exe`, med grensesnitt, Python, introvideo og lokale tjenester pakket inn. Filen er foreløpig ikke signert.

## Verifisering

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe tests/desktop_smoke.py write "$env:TEMP\rl-hub-smoke-webview"
.\.venv\Scripts\python.exe tests/desktop_smoke.py read "$env:TEMP\rl-hub-smoke-webview"
.\.venv\Scripts\python.exe tests/packaged_smoke.py
```

UI-testen bruker egen lagring. Bruk en ny tom testmappe for hver testsekvens. Lokal tjeneste bruker port 18765 for å bevare samme lagringsadresse mellom oppstarter, og stenges når appen lukkes. Oppstartsfeil logges i `%LOCALAPPDATA%/RL Hub/desktop.log`.

Eksisterende Overwolf-filer ligger fortsatt i prosjektet. Desktop-versjonen laster dem ikke.

## Performance

**Performance** viser oppsummeringer etter kamp fra [Rocket Leagues offisielle Stats API](https://www.rocketleague.com/developer/stats-api). Trykk **Aktiver kampoppsummeringer** én gang og start Rocket League på nytt. Ha RL Hub åpen mens du spiller; mottakeren kjører også når en annen fane er valgt.

Aktiveringen finner spillinstallasjonen fra lokal spillogg, tar en `.rlhub.bak`-kopi av den aktive Stats API-konfigurasjonen og setter `PacketSendRate=2` og en gyldig `WebPort`. Kommentarer og andre innstillinger beholdes. Appen kobler bare til lokal WebSocket og sender ingen spillkommandoer. Aktivering kan kreve skriverettigheter til spillmappen. API-et må aktiveres på nytt hvis en spilloppdatering tilbakestiller konfigurasjonen.

Resultat, scoreboard, mål, assists, saves, skudd og skuddprosent lagres i `%LOCALAPPDATA%/RL Hub/performance.json`, med maksimalt 100 kamper. Egne tall velges fra profilen eller kontoen i spilloggen. Historiske replays, freeplay og kamper du forlater før en sluttmelding lagres ikke. Ved tilkobling midt i kamp merkes oppsummeringen som delvis innsamlet. API-et leverer ikke MMR, så denne fanen viser ingen beregnet MMR-endring.

Mottakeren støtter både JSON-tekst i `Data` (observert på den ekte spillforbindelsen) og ferdige dataobjekter. Slutthendelser uten `MatchGuid` knyttes til den aktive kampen. Private kamper uten GUID får en lokal ID. Statusen skiller mellom en åpen forbindelse, mottatte kampdata og pågående kamp.

Kontroller med `python -m unittest discover -s tests` og `.venv\Scripts\python.exe tests/performance_ui_smoke.py`. Testene dekker også tekstkodede payloads over WebSocket, hendelser uten GUID og feil i meldingsformatet.

Live-flyten ble bekreftet 1. oktober 2026 med en fullført privat kamp: tekstkodede spillmeldinger ble tolket, sluttresultat og spillerstatistikk ble lagret i lokal historikk. En kamp som ble forlatt før sluttmeldingen, ble ikke lagret som en fullført kamp.
