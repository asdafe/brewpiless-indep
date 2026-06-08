# BrewPiLess — Independent Heat/Cool Modification (Source Package)

Bu pakette `feature/independent-heat-cool` branch'inde yaptığım değişikliklerin
kaynak dosyaları var. İstersen doğrudan bu dosyaları kendi klonunda
override edersin, istersen aşağıdaki `git apply` yolunu kullanırsın.

## İçerik

```
src/                      ← C++ firmware dosyaları (6 dosya)
  TempControl.h           ← enum, MODE_INDEPENDENT, modeIsIndependent()
  TempControl.cpp         ← updatePID / updateState / detectPeaks bağımsız mod
  BrewKeeper.cpp          ← profil sürücüsü: 'i' modunda da çalışır
  BrewPiProxy.cpp         ← HEAT_AND_COOL state'i için getStatusTime fix
  DisplayLcd.cpp          ← LCD'de "Heat+Cool" gösterimi
  Version.h               ← 0.3.0-indep

htmljs/src/               ← Web UI kaynak dosyaları
  control.tmpl.html       ← Yeni "Independent" sekmesi (navbar + body)
  control_s.tmpl.html     ← Aynısı, küçük ekran versiyonu
  js/script-control.js    ← modekeeper: 5. mod + apply handler
  locales/*.json          ← 7 dil dosyası (yeni anahtarlar eklendi)

wdoc/                     ← Önceden derlenmiş C header'lar (gz web UI binary)
  english_*.h             ← Bunları src/ ile aynı build path'ine koy
  chinese_*.h                → platformio otomatik wdoc/*.h'i include eder
  ... 49 dosya toplam

plan/MODIFICATION_PLAN.md ← Tasarım kararları, edge case'ler, doğrulama
```

## Yöntem A — git apply (en temiz)

```bash
# 1. BrewPiLess'in güncel master'ını klonla
git clone --depth 50 https://github.com/vitotai/BrewPiLess.git
cd BrewPiLess

# 2. Yeni branch aç
git checkout -b feature/independent-heat-cool

# 3. code-only.patch'i uygula
git apply /path/to/code-only.patch

# 4. (opsiyonel) wdoc/ header'larını da atla — grunt çalıştırmak istemiyorsan
cp -r /path/to/wdoc/* wdoc/

# 5. Build
pio run -e esp32
```

`.bin` çıktısı: `.pio/build/esp32/firmware.bin`

## Yöntem B — Manuel dosya kopyalama

Eğer `git apply` kullanmak istemezsen, bu paketteki dosyaları doğrudan
kendi klonundaki yerlerine kopyala:

```bash
# Kendi klonun
LOCAL=/path/to/your/BrewPiLess

cp src/*              $LOCAL/src/
cp htmljs/src/*       $LOCAL/htmljs/src/
cp htmljs/src/js/*    $LOCAL/htmljs/src/js/
cp htmljs/src/locales/*  $LOCAL/htmljs/src/locales/
cp wdoc/*             $LOCAL/wdoc/         # wdoc/ yoksa mkdir
cp plan/MODIFICATION_PLAN.md $LOCAL/
```

Sonra `pio run -e esp32`.

## Yöntem C — Sıfırdan değişiklik yap (öğrenmek istiyorsan)

1. `code-only.patch` dosyasını bir editörde aç (gerrit-style diff)
2. Her bloğu kendi dosyalarına uygula, anlamaya çalış
3. `MODIFICATION_PLAN.md` ile karşılaştır, tasarım gerekçelerini oku
4. Kendi varyasyonlarını yaz (örn. hysteresis genişliği, ayrı fan kontrolü vs.)

## Build ortamı

İhtiyacın olanlar:
- **PlatformIO** (Python 3 ile): `pip install platformio`
- (opsiyonel) Web UI'ı sıfırdan derlemek istersen: Node.js + `cd htmljs && npm install && npx grunt i18n`

ESP32 derlemek için başka bir şey gerekmiyor — PlatformIO toolchain'i otomatik indiriyor.

## Sadece .bin istiyorsan

`/path/to/BrewPiLess-0.3.0-indep-esp32.bin` dosyası kullanıma hazır.
Web arayüzü firmware içinde gömülü, ayrıca dosya yüklemeye gerek yok.

## Değişen dosyaların kısa özeti

### src/TempControl.h
- `MODE_INDEPENDENT 'i'` macro eklendi
- `enum states`'e `HEAT_AND_COOL = 10` eklendi
- `modeIsIndependent()` helper eklendi

### src/TempControl.cpp
- `updatePID()`: bağımsız modda no-op
- `updateState()`: bağımsız mod için iki paralel on/off döngüsü
- `detectPeaks()`: bağımsız modda atlanır
- `stateIsCooling()` / `stateIsHeating()`: HEAT_AND_COOL'u da kapsar

### src/BrewKeeper.cpp
- `keep()`: mode 'i' ise profili de çalıştır
- `setModeFromRemote()`: 'i' moduna geçildiğinde profil başlangıç zamanını set et

### src/BrewPiProxy.cpp
- `getStatusTime()`: HEAT_AND_COOL state'i için sinceIdleTime kullan

### src/DisplayLcd.cpp
- LCD'de HEAT_AND_COOL için "Heat+Cool" string'i
- printState sayaç bloğu: HEAT_AND_COOL'u da dahil et

### src/Version.h
- 0.2.4 → 0.3.0-indep

### htmljs/src/control.tmpl.html + control_s.tmpl.html
- 5. nav butonu: "Independent"
- Yeni `<div id="independent-s">`: iki input (cool-t, heat-t) + açıklama

### htmljs/src/js/script-control.js
- `modekeeper.modes` array'ine "independent" eklendi
- `apply()`: 'independent' için iki değer oku, `j{mode:i, beerSet:X, fridgeSet:Y}` gönder

### htmljs/src/locales/*.json
- `control_independent`, `control_setheattemp`, `control_setcooltemp`,
  `control_independent_help` anahtarları eklendi (7 dil)

### wdoc/*.h
- grunt i18n + xxd -i ile yeniden üretildi (yeni web UI artık firmware'de)
