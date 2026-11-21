# Evidence-based gameplay observations

## 1. Activity is concentrated on AmbroseValley

**Observed:** AmbroseValley has 61,013 of 89,104 events (68.5%); Lockdown has
21,238 (23.8%), and GrandRift 6,853 (7.7%). The manifest contains 566,
171, and 59 matches for those maps respectively.

**Why it matters:** Level-design feedback derived from raw totals will be
dominated by AmbroseValley. Prioritize its journey and heatmap review, while
considering whether GrandRift's lower activity reflects rotation exposure rather
than low player engagement.

**Recommendation:** Compare normalized per-match and per-player activity before
making map-population changes. The present dataset cannot establish why map
selection differs.

## 2. Telemetry is primarily movement and loot, not human-versus-human combat

**Observed:** Position and BotPosition events total 73,059 (82.0%). Loot occurs
12,885 times. Only 3 `Kill` and 3 `Killed` events are recorded, whereas
BotKill/BotKilled total 3,115. These figures are dataset-wide and visible in
the app's event filters.

**Why it matters:** Journey routes and loot interaction are the strongest
evidence streams for map review. The dataset cannot support robust conclusions
about human-versus-human combat hot spots.

**Recommendation:** Use movement/loot density to identify candidate traversal
and reward areas, while requesting fuller PvP telemetry before changing combat
spaces.

## 3. Raw event ordering needs defensive handling

**Observed:** 3 timestamp inversions occur in 3 of 1,243 player files; 1,505
exact duplicate rows occur globally. All 89,104 raw rows are retained.

**Why it matters:** Rendering source row order could produce backwards trails
or duplicate markers, misleading a designer’s timeline interpretation.

**Recommendation:** Keep canonical raw data intact, sort every selected match
by raw timestamp for playback, and expose duplicate/inversion counts in analysis
views. This is a data-handling recommendation, not a player-behavior claim.
