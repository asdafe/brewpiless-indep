#ifndef DuckDNS_H
#define DuckDNS_H

// =====================================================
// DuckDNS otomatik IP güncelleyici - BrewPiLess için
// Kurulum:
//   1. Bu dosyayı src/ klasörüne koy
//   2. BrewPiLess.cpp başına: #include "DuckDNS.h"
//   3. loop() sonuna:         duckDNS.loop(now);
// =====================================================

// ---- BURAYA KENDİ BİLGİLERİNİ YAZ ----
#define DUCKDNS_DOMAIN  "orcunozden"
#define DUCKDNS_TOKEN   "0cae8222-0b5f-4438-962b-af3c19b28c92"
// ----------------------------------------

#define DUCKDNS_INTERVAL  3600   // saniye (30dk)

#ifdef ESP8266
  #include <ESP8266HTTPClient.h>
#else
  #include <HTTPClient.h>
#endif
#include <WiFiClient.h>

class DuckDNSUpdater {
public:
    DuckDNSUpdater() : _lastUpdate(0) {}

    void loop(time_t now) {
        if (WiFi.status() != WL_CONNECTED) return;
        if (now - _lastUpdate < DUCKDNS_INTERVAL) return;
        _lastUpdate = now;
        update();
    }

private:
    time_t _lastUpdate;

    void update() {
        WiFiClient client;
        HTTPClient http;
        String url = String("http://www.duckdns.org/update?domains=")
                     + DUCKDNS_DOMAIN
                     + "&token=" + DUCKDNS_TOKEN
                     + "&ip=";

        http.begin(client, url);
        int code = http.GET();
        String payload = (code > 0) ? http.getString() : "ERR:" + String(code);
        Serial.printf("[DuckDNS] HTTP %d -> %s\n", code, payload.c_str());
        http.end();
    }
};

DuckDNSUpdater duckDNS;

#endif // DuckDNS_H
