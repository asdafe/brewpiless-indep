# Independent Heat/Cool Modification — Design Notes

## User requirement (TR, original)

- Isıtma ve soğutma aynı anda birbirlerinden bağımsız çalışabilecek
- Soğutma: sadece *fridge* sensörü, ayrı setpoint → kompresör
- Isıtma: sadece *beer* sensörü, ayrı setpoint (veya beer profile) → ısıtıcı
- Beer profile sekmesi çalışmaya devam edecek, ama sadece ısıtıcıyı kontrol edecek
  - Biranın fazla soğuması profile sorun değil (soğutma bağımsız, kendi setpoint'inde)

## Current architecture (BrewPiLess master)

- `ControlSettings cs` = { mode, beerSetting, fridgeSetting, heatEstimator, coolEstimator }
- `updatePID()`: in `modeIsBeer()` (= B or P), runs PID on (beerSetting − beer) → outputs `fridgeSetting`
- `updateState()`: single hysteresis loop on **fridge sensor** vs `cs.fridgeSetting`
  - fridge > fridgeSetting + idleHigh → COOLING
  - fridge < fridgeSetting + idleLow → HEATING
- `updateOutputs()`: cooler/active ↔ cooling, heater/active ↔ heating
- Beer profile drives `cs.beerSetting` via `setBeerTemp()`; PID converts to `cs.fridgeSetting`
- Modes:
  - OFF
  - MODE_BEER_CONSTANT (b): PID from beer sensor
  - MODE_FRIDGE_CONSTANT (f): user sets fridge target directly, no PID
  - MODE_BEER_PROFILE (p): profile drives beerSetting, PID converts

## New architecture

We **add** a new mode `MODE_INDEPENDENT` (char 'i') that runs two completely independent
on/off thermostat loops. The old PID-based modes are preserved so users can switch back.

### Loops

- **Cooling loop** — based on `fridgeSensor` only
  - if `fridgeFast > coolSetpoint + idleRangeHigh` → COOLING
  - if `fridgeFast <= coolSetpoint + idleRangeLow` → IDLE/cool off
  - Hysteresis via existing `idleRangeHigh`/`idleRangeLow` (defaults +1 / -1 °C)
  - Histerezis genişliği `idleRangeHigh − idleRangeLow` (varsayılan 2 °C)

- **Heating loop** — based on `beerSensor` only
  - if `beerFast < heatSetpoint − idleRangeHigh` → HEATING
  - if `beerFast >= heatSetpoint − idleRangeLow` → IDLE/heat off
  - Note: we mirror the hysteresis, so for heating the "low" range matters (sensor must rise
    by full hysteresis before heat turns off, preventing short cycling)

- The two loops do **not** share state. Both can be active simultaneously. No `mutexDeadTime`
  between them. No more "wait to cool" or "wait to heat" — replaced with a tiny per-loop
  minimum-on / minimum-off to protect the compressor and heat wrap.

### Setpoints

- `cs.fridgeSetting` continues to mean "cooler target" in all modes. In INDEPENDENT mode
  it is the **cool setpoint**.
- `cs.beerSetting` continues to mean "heater target" in all modes. In INDEPENDENT mode
  it is the **heat setpoint** (driven by user or by profile).
- `setBeerTemp()` and `setFridgeTemp()` keep their names and EEPROM-write semantics.

### Modes in the new world

| Mode char | name | cool setpoint | heat setpoint |
|-----------|------|---------------|---------------|
| `o` | OFF | — | — |
| `b` | BEER_CONSTANT (legacy, PID) | PID-derived from `cs.beerSetting` | PID-driven fridge heat |
| `f` | FRIDGE_CONSTANT (legacy) | user-set `cs.fridgeSetting` | (off) |
| `p` | BEER_PROFILE (legacy) | PID-derived from profile-driven `cs.beerSetting` | (off) |
| `i` | **INDEPENDENT** (new) | user-set `cs.fridgeSetting` | user-set or profile-driven `cs.beerSetting` |

### Beer profile in INDEPENDENT mode

- Profile keeps driving `cs.beerSetting` via `setBeerTemp()` (no change needed in BrewKeeper
  — it already writes to "beerSet" which the firmware maps to `cs.beerSetting`).
- `setMode('p')` still works in legacy sense; we add `setMode('i')` for the new INDEPENDENT
  + profile combo.
- New API: in INDEPENDENT mode the profile can be active (`profile` tab) and ramp
  `cs.beerSetting` over time. Cooling stays at `cs.fridgeSetting`. They don't interact.

## Concrete code changes

### `src/TempControl.h`
- Add `#define MODE_INDEPENDENT 'i'`
- Add helper `modeIsIndependent()` returning `cs.mode == MODE_INDEPENDENT`
- (Optional) add field comment on `cs.beerSetting` / `cs.fridgeSetting` clarifying meaning

### `src/TempControl.cpp`
- Rewrite `updatePID()`:
  - If `modeIsIndependent()`: do nothing (setpoints come straight from user/profile).
  - Else: keep existing PID logic for legacy modes b/f/p.
- Rewrite `updateState()`:
  - Split into two independent sub-state decisions.
  - Cooling branch uses `fridgeSensor` vs `cs.fridgeSetting`.
  - Heating branch uses `beerSensor` vs `cs.beerSetting`.
  - In INDEPENDENT mode, neither branch touches the other's setpoint.
  - In legacy modes, keep the original behaviour.
- `updateOutputs()`:
  - Already correct — `cooler->setActive(cooling)`, `heater->setActive(heating)`. The two
    state booleans can be true at the same time, so cooler and heater can run in parallel.
- `detectPeaks()`:
  - In INDEPENDENT mode: skip the overshoot-based peak detection (no estimator needed for
    simple on/off control). Just return.
  - Legacy modes: unchanged.
- `loadDefaultSettings()`: leave defaults; user can change via web.

### `src/JsonKeys.h`
- (No new keys needed — `beerSet` and `fridgeSet` already exist and we keep their names.)

### `src/PiLink.cpp`
- `setBeerSetting` and `setFridgeSetting` keep their current names; no change.
- `setMode` accepts the new 'i' mode.

### `src/BrewPiProxy.cpp` / `.h`
- No change — proxy just forwards to `tempControl`. The new mode char 'i' is preserved.

### `src/BrewKeeper.cpp`
- No change — already writes to "beerSet" which in INDEPENDENT mode is the heat target.

### `htmljs/src/control.tmpl.html` + `script-control.js`
- Add a 5th nav button: "Independent" (or label it clearly).
- In INDEPENDENT mode, the page still shows two temp inputs (beer-t, fridge-t) but the
  semantics are: beer-t = heat target, fridge-t = cool target. Both editable.
- Add a help text under the inputs clarifying the new semantics.

### `src/Version.h`
- Bump version so users see the new firmware.

## Backward compatibility

- Old `cs` EEPROM layout is unchanged — same struct, same blob. Existing settings load
  fine; their semantics just shift slightly in INDEPENDENT mode.
- Old modes (b, f, p) behave exactly as before.
- New `i` mode only available if the user selects it. No auto-migration.

## Risks / open questions

- Removing PID in INDEPENDENT mode means the heat wrap will be on/off around setpoint with
  `idleRangeHigh − idleRangeLow` hysteresis. For a 2 °C default hysteresis, expect ~1 %
  duty cycle around setpoint. That's the standard behaviour for a homebrew heat belt.
- If the user has a heat wrap with slow thermal response, 1 °C hysteresis on the beer
  sensor (not on the wrap surface) is reasonable. They can widen hysteresis via the
  existing `idleRangeHigh/Low` advanced settings.
- Compressor protection: we keep `minCoolTime` / `minCoolIdleTime` (existing) for cool,
  and reuse `minHeatTime` / `minHeatIdleTime` for heat. These were per-mode; in INDEPENDENT
  we apply them to each loop independently.

## Verification checklist

- [ ] `updatePID()` does nothing when `modeIsIndependent()` — `cs.fridgeSetting` is not
      overwritten by the PID formula.
- [ ] In INDEPENDENT mode, `cs.fridgeSetting` is the cool setpoint read from EEPROM.
- [ ] In INDEPENDENT mode, `cs.beerSetting` is the heat setpoint, editable / profile-driven.
- [ ] Cooling decision uses `fridgeSensor` only. Beer sensor failure does not block cooling.
- [ ] Heating decision uses `beerSensor` only. Fridge sensor failure does not block heating.
- [ ] Both actuators can be active simultaneously.
- [ ] `minCoolTime` / `minCoolIdleTime` still apply to the cooling branch.
- [ ] `minHeatTime` / `minHeatIdleTime` still apply to the heating branch.
- [ ] Beer profile still writes to `cs.beerSetting` via `setBeerTemp()`.
- [ ] Legacy modes (b, f, p) are bit-for-bit unchanged.
- [ ] Web UI shows a new tab/mode and the existing input fields are correctly labeled.
