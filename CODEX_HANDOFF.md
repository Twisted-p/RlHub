# RL Hub – instruks til Codex på en annen maskin

**Gjennomgang rettet 04.10.2026:** Pauset og redusert bevegelse gjør `.reveal`
synlig uten å vente på animasjonen. Stats API avviser ugyldige Game/Teams/Players
før spilltilstanden endres, og fortsetter med neste melding. Spilleridentitet
oppdateres ved tilkobling og hvert femte sekund; coaching viser kontomismatch
og blander ikke MMR fra rankprofilen med en annen innlogget konto.
Standalone-rankoppslag bruker nå POST `/api/profile` med samme Origin;
GET returnerer bare lagret profil. Alle lokale endepunkter kontrollerer Host.
Overlay-endringer rulles tilbake ved skrivefeil. Milepæl-lukking lykkes først
når lagringen lykkes; kortet viser feil og tillater nytt forsøk.
`.github/workflows/app.yml` kjører Python-/JS-tester, kontrollerer pakkede assets,
bygger Windows-appen og tester ekte WebView2 og executable på push/PR.
Lokalt verifisert: 80 Python-tester, fire JS-suiter, spillvinduets pause/synlighet
og rankkortets lagringsfeil/nytt forsøk i WebView2. Brukerens tidligere test
uten feil i ekte Rocket League gjaldt v0.6.0; disse ekstra feiltilfellene er
testet isolert, ikke bekreftet i en ny ekte kamp.

**Rankfeiring:** Originalt JS/CSS-kort på alle standalone-faner, med rankikon,
farger, dato og observerte stats. Bare en ny høyeste rankkategori per konto/modus
utløser feiring; første oppslag og eksisterende historikk setter baseline.
Lukking lagres i `rank-promotions.json`. Ingen React Bits Pro-lisens kreves.
Les `RANK_CELEBRATION_HANDOFF.md` for kodekart, datagrunnlag og tester.

Les denne filen sammen med `AGENTS.md`, `README.md`, `STANDALONE_SETUP.md` og, ved overlay-arbeid, `gamebar/README.md` før du endrer prosjektet. Brukerens nye forespørsel bestemmer hva som skal utvikles; denne filen beskriver utgangspunktet.


**Training Packs** viser tre unike koder fra et lokalt utvalg på 18 pakker. Utvalget byttes ved hvert kvarter (:00, :15, :30, :45), med nedtelling og kopiering per kode. Navigasjon og omstart innen samme kvarter beholder utvalget; etter hvilemodus brukes gjeldende kvarter. Kodene er kontrollert mot de to Dignitas-artiklene 02.10.2026, ikke testet i spillet. RL Garage blokkerte uthenting (HTTP 403) og er derfor bare lenket som en ekstra katalog. Ingen nettsider hentes automatisk ved hvert bytte.


**Dashboard-rankkort:** React Bits Lanyard svinger inn ved åpning av Dashboard og viser ikonet for sist hentede rank. Velg 1v1/2v2/3v3 (standard 2v2); valget huskes. Rankdata oppdateres fra appens lokale tjeneste, uten ekstra MMR-oppslag. Manglende rank gir lenke til Profile. Redusert bevegelse/3D-feil gir statisk kort; scenen stoppes når siden er skjult. Kilde, bygging og tilpasninger: `frontend/lanyard/README.md`.


**Dashboard-progresjon:** Oransje MMR-kurve med omtrentlige ranksoner, 1v1/2v2/3v3 og 30/90/365 dager eller hele historikken. `rank-history.json` lagrer faktiske rankoppslag per spiller og modus (maks 10 000 målinger per modus), uavhengig av øktreset. Eksisterende sist hentede rank kan bli første punkt; eldre historikk kan ikke rekonstrueres fra kampscore. `/api/progression` viser historikk og de siste egne ranked-resultatene. Dagens fokus bruker lokale regler: lang økt, flere tap siste døgn, MMR-endring siste sju dager, seiere eller et dagsvariert treningstips. Dette er coaching, ikke AI eller en garantert prestasjonsanalyse. Rankkort og graf deler valgt modus. Ranksonene gjenbruker Goals sine omtrentlige opprykksgrenser; de er ikke nøyaktige divisjonsgrenser.

## Prosjekt og siste funksjoner

Repo: https://github.com/Twisted-p/RlHub. `main` inneholder den samlede standalone-versjonen. Repoet er privat; maskinen må ha tilgang til brukerens GitHub-konto. Utvikling av overlay, Dashboard og Goals ligger også historisk på `codex/standalone-overlay`.

RL Hub er en Windows-app med Python, pywebview/WebView2 og lokale HTML/CSS/JS-sider. Den har ingen Overwolf-avhengighet og trenger ingen API-nøkkel. Bevar disse funksjonene:

- Octane-intro på hver oppstart, omtrent 6,6 sekunder, med hopp-over-knapp.
- Profile: plattform + gamertag → rank/MMR for 1v1, 2v2 og 3v3. Offentlig spiller-ID finnes automatisk i lokal Rocket League-loginlogg. Tekniske ID-felt er skjult for brukeren.
- Performance: automatisk post-match-oppsummering fra Rocket Leagues lokale Stats API. Kamper kan filtreres på gamemode/resultat og sorteres på dato eller egne tall. Grafer viser skudd, mål, saves og assists for siste 5, 10 eller 20 kamper.
- Dashboard: faktisk treningstid, siste fem egne ranked/casual-kamper, snitt og MMR-endring i økten. Etter hver femkampers blokk gir minst tre tap rådet om 15 min pause; minst tre seiere gir 5 min pause + 5 min ny trening. Fokustimer på 90 min senker readiness gradvis. Dette er coachingregler, ikke offisiell spillstatistikk eller et dokumentert universelt fokusmaksimum.
- Goals: separate rankmål for 1v1/2v2/3v3, MMR-avstand og `ceil(MMR igjen / 9)` seiere på rad. Rankgrenser og +9 MMR er anslag. Mål lagres per spiller.
- Garage: visuelt bibliotek med fire kildebelagte, historiske proffdesign, lokale bilbilder, søk/bilfilter, favoritter og egne varianter. Egne presets beholdes og lagres lokalt. Aktivt preset gjelder RL Hub, ikke automatisk bilbytte i spillet. Bildet av en egen variant viser originalreferansen. Training lagrer rutiner lokalt.
- Settings: fem utvalgte profiler (zen, Vatira, M0nkey M00n, Daniel, BeastMode), med kamera, bindinger, deadzone og følsomhet. Kopiering gir tekst for en kategori eller én verdi. PS/Xbox-visning oversetter knappesteder; ingen spillfiler endres. Kildegrunnlag og kjente kildedatoer er dokumentert i `SETTINGS_SOURCES.md`.
- Native Windows-overlay for kantløst vindu/vindu. Lobby, trening og etterkampvisning, samt egen bryter for statistikk under kamp. Ctrl+Shift+O skjuler/viser overlayet.
- Fullskjerm-overlay via en egen Xbox Game Bar-widget. Widget 1.0.2.0 er kontrollert i ekte Rocket League-fullskjerm på utviklingsmaskinen. Ny maskin må teste sin egen visning; HTTP-forbindelse er ikke bevis på synlige piksler.

## 1. Klone og installere

Bruk Windows x64, Git, **Python 3.13 x64** og Microsoft Edge WebView2 Runtime. Windows 11 og Xbox Game Bar kreves for den medfølgende unsigned utviklingswidgeten. Node.js er valgfritt og brukes bare av JS-beregningstesten. Ikke installer Visual Studio for vanlig Python-/UI-utvikling.

Kjør fra PowerShell i en mappe hvor brukeren vil ha prosjektet:

```powershell
git clone https://github.com/Twisted-p/RlHub.git
cd RlHub
git switch main
git pull --ff-only
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
```

Hvis `py -3.13` mangler: installer Python 3.13 x64, eller bruk den verifiserte Python 3.13-installeringens absolutte sti. Ikke kopier `.venv` fra en annen maskin. `requirements-build.txt` inkluderer desktop-avhengighetene og PyInstaller; ekstra Node-/npm-pakker trengs ikke for appen.

## 2. Kjøre appen

```powershell
.\.venv\Scripts\python.exe desktop_app.py
```

Appen åpner hovedvinduet og starter lokal server på `http://127.0.0.1:18765`. Hold denne adressen stabil for vanlig bruk fordi WebView-lagringen er knyttet til den. Bare én vanlig appinstans skal kjøre. Hvis porten er opptatt, finn den eksisterende RL Hub-instansen; ikke drep andre programmer eller endre brukerens faste port uten grunn.

**Pass på at hovedvinduet faktisk er synlig.** Det er ikke tilstrekkelig at overlayet eller `/health` svarer. En tidligere oppstart med Windows' skjul-vindu-flagg skjulte hovedappen mens overlayet kjørte. Start appen med kommandoen over. Hvis et verktøy må starte prosessen skjult, gjenopprett RL Hubs hovedvindu eksplisitt etter oppstart og kontroller det.

Før bruk på en ny maskin:

1. Start Rocket League med brukerens konto én gang, så lokal spiller-ID kan finnes.
2. Åpne Profile, velg plattform, skriv gamertag og trykk Hent rank.
3. RL Hub aktiverer kampoppsummeringer automatisk i bakgrunnen ved oppstart og prøver igjen hvis spillet først blir funnet senere. Åpne Performance for status, og start Rocket League på nytt dersom spillet allerede kjørte ved aktivering. Appen endrer bare en deaktivert Stats API-konfigurasjon og beholder en `.rlhub.bak`-kopi. Manglende skriverettigheter vises i appen. Ikke endre anti-cheat eller injiser kode i spillet.
4. Fullfør en kort privat kamp helt til resultatskjermen for å kontrollere Performance. «Forlat kamp» før slutt skal ikke telle som en fullført kamp. Private kamper vises i Performance, men teller ikke i Dashboardets ranked/casual-blokker.
5. La RL Hub være åpen under spilling. Innsamlingen fortsetter når en annen appfane er valgt.

MMR kommer fra tredjeparten `mmr.kmdw.dev`, ikke fra Stats API. Tjenesten kan være forsinket eller utilgjengelig. Behold sist kjente rank ved feil; ikke oppfinn en faktisk MMR-endring fra seier/tap, score eller Goals' +9-anslag.

## 3. Bygge én Windows-exe

Fra repo-roten:

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm "RL Hub.spec"
.\.venv\Scripts\python.exe tests/packaged_smoke.py "dist/RL Hub.exe"
```

Resultat: `dist/RL Hub.exe`. Python, UI, logo, intro og lokale tjenester pakkes inn. WebView2 Runtime må være installert på brukermaskinen. Ikke bruk tilfeldige løse `--add-data`-kommandoer som utelater assets: bruk spec-filen.

Alternative bygg for å unngå å erstatte en kjørende exe:

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --distpath dist/candidate --workpath build/candidate "RL Hub.spec"
.\.venv\Scripts\python.exe tests/packaged_smoke.py "dist/candidate/RL Hub.exe"
```

`dist/latest/RL Hub.exe` var en lokal snarvei til siste kontrollerte bygg på utviklingsmaskinen; denne mappen opprettes ikke av vanlig kloning. Bygg lokalt eller last ned appen fra Releases. Exe og ZIP publiseres som release-assets, ikke i Git-kildehistorikken.

## 4. Fullskjerm-widget

Release 0.4.0 leverer **RL Hub Complete.zip** med appen, WebView2 offline-installer, widget 1.0.2.0 og alle tre x64 UWP-runtimeavhengigheter. Pakk ut hele ZIP-en og kjør `Start RL Hub.cmd`; WebView2 installeres bare ved behov. `Install Fullscreen Overlay.cmd` ber om administratortillatelse for widgeten og dens lokale loopback exemption. Hvis Windows-appen Game Bar mangler, åpnes Microsoft Store. Game Bar er ikke nødvendig for vanlig app/kantløst overlay og følger ikke med som offline-installer. Se `distribution/README.md` for reproduksjon og kontroll av pakken.

Etter installasjon: velg Fullskjerm / Xbox Game Bar under Overlay i RL Hub, lagre, åpne Win+G, finn RL Hub under Widgets, fest med tegnestiften og aktiver museklikkgjennomgang. Lukk Win+G og kontroller overlayet over spillet. Game Bar styrer plassering/størrelse i denne modusen. Vanlig Windows-overlay støtter kantløst vindu, ikke eksklusiv fullskjerm.

For å bygge widgeten selv kan du bruke workflowen **Build Game Bar overlay** under GitHub Actions, med `workflow_dispatch` på `main`. Last ned hele artefakten `RLHub-GameBar` og behold `Dependencies/x64` ved siden av pakken.

Alternativ lokal bygging krever Visual Studio 2022 med UWP C#-verktøy, .NET Native-kompilering og Windows SDK **10.0.19041**. Kjør i Developer PowerShell hvor `msbuild` finnes:

```powershell
msbuild gamebar/RLHubGameBar.csproj /restore /p:Configuration=Release /p:Platform=x64 /p:GenerateAppxPackageOnBuild=true /p:AppxBundle=Never /p:UapAppxPackageBuildMode=SideloadOnly
```

Behold `UseDotNetNativeToolchain=true` og `Optimize=true`. Den første managed/CoreCLR-varianten krasjet på utviklingsmaskinen. `OverlayPage` er kodebasert og må opprettes direkte i SDK-rammen (`frame.Content = new OverlayPage()`), ikke via XAML-navigasjonsmetadata. Behold Microsoft-lisensen og NuGet-referansene.

## 5. Tester og trygg validering

Start med enhetstestene, som ikke trenger et kjørende spill:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
node tests/performance_analytics.test.cjs
```

Node-kommandoen kan utelates når Node ikke er installert. Ved denne overleveringen passerer **48 Python-enhetstester**. Ikke lås videre utvikling til dette antallet.

Kjør relevante WebView2-tester etter UI-endringer:

```powershell
.\.venv\Scripts\python.exe tests/splash_ui_smoke.py
.\.venv\Scripts\python.exe tests/performance_ui_smoke.py
.\.venv\Scripts\python.exe tests/readiness_ui_smoke.py
.\.venv\Scripts\python.exe tests/goals_ui_smoke.py
.\.venv\Scripts\python.exe tests/overlay_ui_smoke.py
```

Testene bruker isolert lagring og egne porter. Exe-testen bruker også unikt vindusnavn. Ikke steng brukerens spill for å kjøre dem. Performance/Readiness/Goals tar bilder fra WebView2s egen overflate; skjermdump av skrivebordet kan ellers vise spillet i stedet for appen.

Manuell kontroll etter endringer: hovedvindu synlig, intro ferdig innen 7 sekunder, riktig side i menyen, reelle manglende-data-tilstander og fortsatt fungerende overlay. Test bare videre når nye endringer eller feil gir en grunn.

## 6. Kodekart og regler

| Fil(er) | Ansvar |
| --- | --- |
| `desktop_app.py` | Appvindu, same-origin HTTP/API, bakgrunnstjenester, asset-allowlist og avslutning |
| `RL Hub.spec`, `requirements*.txt` | Reproduserbart Python-/exe-oppsett og alle runtime-assets |
| `desktop-runtime.js`, `script.js`, `styles.css`, HTML-sider | Standalone-meny, profiltilpasning, lokal UI og design |
| `mmr_provider.py` | Offentlig spilleridentitet og MMR-oppslag |
| `performance_service.py` | Stats API, live data, fullførte kamper og historikk |
| `performance-analytics.js`, `performance.js` | Filtrering, sortering, egne spillerdata og grafer |
| `garage.js`, `garage.css`, `garage-presets.js`, `assets/garage/` | Visuelt preset-bibliotek, lokale bilder og dokumenterte community-kilder |
| `settings.html`, `settings.js`, `settings.css`, `pro-settings-data.js` | Fem proffprofiler, kildebelagte innstillinger og tekstkopiering |
| `readiness_service.py`, `readiness.js` | Målt økt/trening, femkampers blokker, hvile/oppvarming og fokus |
| `goals_service.py`, `goals.js`, `goals.html` | Rankmål per spiller/modus, omtrentlige rankgrenser og seiersanslag |
| `overlay_service.py`, `native_overlay.py`, `overlay-settings.js` | Økt-MMR, rendererinnstillinger og transparent click-through Windows-overlay |
| `gamebar/`, `.github/workflows/gamebar.yml` | Separat UWP Game Bar-renderer og bygging |
| `assets/rlhub-intro.mp4`, `App Logo.png` | Eksisterende intro og logo |
| `tests/` | Beregningstester og Windows/WebView-/exe-kontroller |

Når du legger til en UI-fil, oppdater **både** `desktop_app.py:UI_FILES` og asset-listen i `RL Hub.spec`. Hold undermapper intakte. Muterende API-kall må kreve appens eksakte lokale Origin; ikke aktiver wildcard CORS.

Stats API kan sende JSON-tekst inne i `Data`, og slutthendelser kan mangle `MatchGuid`. Behold deduplisering og håndtering av replays, trening/freeplay og kamper forlatt før slutt. Egen spiller identifiseres med eksakt offentlig spiller-ID, ellers eksakt navn; aldri bruk første spiller i listen som gjetning.

Dashboard bruker serverens bakgrunnsinnsamling, ikke en timer som bare går mens siden er åpen. Appens offline-/suspenderte tid skal ikke bli ny treningstid. En startet pause oppfylles ikke mens spilleren er i kamp/trening, og gammel trening skal ikke oppfylle fem minutters trening etter en pause.

Bruk norsk og enkel tekst i UI. Gjenbruk eksisterende mørke design og turkise aksenter. Ikke eksponer tekniske ID-er, logger eller konfigurasjonsdetaljer som brukeren kan endre ved et uhell. Behold eldre `overwolf/`-filer for senere arbeid uten å laste dem i standalone-appen.

## 7. Lagring og personvern

`game_window.py` følger `PerformanceService.activity_snapshot()` uavhengig av
overlayets visningsbrytere. MatchCreated/Initialized og trening minimerer
hovedvinduet én gang og sender pauseflagget til alle faner. MatchEnded beholder
pause under resultatskjerm; MatchDestroyed etterfulgt av 1,5 sekunder stabil
lobby gjenoppretter vinduet. Ukjent status eller frakobling skal ikke utløse
gjenoppretting. `desktop-runtime.js` styrer CSS-pause og `rlhub:motion`;
Lanyard/Aurora unmountes og CountUp/TiltedCard blir statiske. Ny navigasjon arver
flagget i hostens HTML. Backend, overlay, Stats API og rank-oppslag fortsetter.
Tester: `tests/test_game_window.py` og `tests/game_window_ui_smoke.py` med
syntetiske spillhendelser, faktisk WebView2-minimering og GPU/CSS pause/resume.

Spillogger leses gjennom `mmr_provider.game_log_lines`: UTF-8 (med/uten BOM),
UTF-16 med BOM og Windows-1252-fallback for ikke-UTF-8-linjer. Dette bevarer
æ/ø/å både ved lokal kontoidentifikasjon og navn i Performance/overlay.
Gamertag sammenlignes med Unicode-normalisering og uten hensyn til store/små
bokstaver, men feil navn/plattform skal fortsatt avvises. Regresjonstester:
`tests/test_mmr_provider.py`. Ikke anta at en venns logg er bekreftet uten å lese den.

Personlige data ligger i `%LOCALAPPDATA%\RL Hub`, blant annet `performance.json`, `overlay.json`, `readiness.json`, `goals.json`, `rank-history.json`, `WebView/` og `desktop.log`. En ny maskin starter med egen historikk og egne innstillinger. Ikke last opp denne mappen, Rocket League-logger, tokens eller innloggingsdata til GitHub. Les bare offentlig spilleridentitet fra spilloggene.

Garage bruker de eksisterende nøklene `rlhub:garagePresets` og `rlhub:uiState`, pluss `rlhub:garageFavorites`. `script.js:normalizePreset` bevarer katalog-/referansefelter ved gjenstart. Test Garage med `.\.venv\Scripts\python.exe tests/garage_ui_smoke.py`; testen bruker isolert lagring og dekker eldre presets, favoritter, søk, deleliste, redigering, bildevisning og smal layout. Bilder og kilder dokumenteres i `assets/garage/SOURCES.md`; ikke omtale community-design som bekreftede nåværende oppsett.

Settings lagrer bare valgt profil og knappevisning i `rlhub:proSettings`. Verdiene er et lokalt kildesnapshot; ikke anta at det er spillerens live innstillinger. Test med `.\.venv\Scripts\python.exe tests/settings_ui_smoke.py`. Testen dekker fem profiler, korrekt skille mellom Air Roll/Left/Right, PS/Xbox-knappesteder, kategorier/enkeltverdier, omstart, manuell kopiering ved avvist utklippstavle, navigasjon fra Garage og smal layout. `desktop-runtime.js` legger Settings-lenken til på eldre sider.

Kildekoden, introen, logoen, widget-assets, modellfiler og lisensfiler er med i Git. `.venv/`, `build/`, `dist/`, widgetens `bin/obj/packages`, logger og lokale backupfiler er ignorert. Det er tilsiktet; genererte filer bygges på nytt eller leveres gjennom Releases.

## 8. Fortsette og publisere

React Bits-effektene bygges fra `frontend/lanyard/`: `npm run build:polish`
(CountUp, TiltedCard, SpotlightCard, Aurora) og `npm run build:goals`
(StarBorder). De lokale JS/CSS-bundlene under `assets/` skal følge exe-bygget.
Aurora stopper og frigir WebGL ved mistet fokus, skjult vindu, header utenfor
skjermen eller redusert bevegelse. Test med `tests/app_polish_ui_smoke.py` i
isolert WebView2-lagring. Bevar de eksisterende HTML-kontrollene ved nye effekter.

Åpne den klonede repo-mappen i Codex, og gi for eksempel instruksen:

> Les AGENTS.md og CODEX_HANDOFF.md. Sett opp og test RL Hub på denne Windows-maskinen, bygg appen med RL Hub.spec og åpne hovedvinduet. Fortsett deretter med følgende endring: [beskriv ønsket endring]. Bevar standalone-appen, intro, Performance, Dashboard, Goals og begge overlay-modusene.

Før nye endringer: sjekk Git-status og ikke overskriv brukerens arbeid. Opprett normalt en `codex/…`-gren fra oppdatert `main`. Kjør relevante tester, lag et kontrollert exe-bygg ved runtime-endringer, og beskriv hva som faktisk ble verifisert. Ved publisering som brukeren har bedt om, ta med kildeendringer, oppdaterte instrukser og de testede release-filene. Oppdater `main` uten force push når den samlede versjonen skal være standard ved ny kloning.
