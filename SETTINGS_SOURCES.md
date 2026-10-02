# Pro Settings provenance

Five curated profiles: zen, Vatira, M0nkey M00n, Daniel, BeastMode. This is a
compact selection of prominent pros, not a numbered or live world ranking.

Retrieved 2026-10-02 from indexed Liquipedia excerpts. Direct HTTP access returned
403 and the browser requested human verification; no verification challenge was
bypassed. Retrieval date is not the date a player last changed their settings.
The app exposes the known camera/deadzone update dates separately, links sources
and labels missing dates as unknown. No team affiliation or current ranking is
assumed by the UI.

| Profile | Source | Camera update | Deadzone update |
| --- | --- | --- | --- |
| zen | https://liquipedia.net/rocketleague/Zen | 2026-02-12 | 2026-02-12 |
| Vatira | https://liquipedia.net/rocketleague/Vatira | 2025-04-29 | 2025-11-17 |
| M0nkey M00n | https://liquipedia.net/rocketleague/M0nkey_M00n | 2025-12-20 | 2025-12-20 |
| Daniel | https://liquipedia.net/rocketleague/Daniel | 2025-11-25 | Not specified in retrieved excerpt |
| BeastMode | https://liquipedia.net/rocketleague/BeastMode | 2025-09-14 | 2022-07-17 |

Camera table: https://liquipedia.net/rocketleague/List_of_player_camera_settings

Control table: https://liquipedia.net/rocketleague/List_of_player_control_settings

Deadzone table: https://liquipedia.net/rocketleague/List_of_player_deadzone_settings

Daniel's control row was available in the indexed list template documentation:
https://liquipedia.net/rocketleague/Template:Control_settings_list/doc
(Powerslide R1; Air Roll R1; Air Roll Left L1; Air Roll Right unbound; Boost Circle;
Jump Cross; Ball Cam Triangle; Brake L2; Throttle R2). His camera/deadzone values
were available in the corresponding aggregate lists. Other control rows and
dates were present in the individual player excerpts. Control update dates were
not stated; camera dates must not be presented as binding update dates.

The supplied `/Others` control-list URL covers other players. These five notable
pros are drawn from the main control list and their individual profiles.

## Representation

`pro-settings-data.js` stores strings to preserve decimal precision. `null` means
explicitly unbound (the source's dash), not unknown. Normal Air Roll is separate
from directional Air Roll Left/Right. PS button names are transcribed from image
alt text. Xbox display maps equivalent button positions: Square=X, Cross=A,
Circle=B, Triangle=Y, L1=LB, R1=RB, L2=LT, R2=RT. This is an app conversion, not
evidence that the player uses Xbox. Copy text identifies the selected scheme.

Deadzone Shape is labeled as a controller/input configuration rather than a
normal in-game field. Copying writes plain text, never modifies game config.
All values remain available offline; only source links need internet.
