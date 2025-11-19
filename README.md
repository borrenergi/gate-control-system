# 🚪 Grindstyrning via Telefon

Ett komplett system för att styra din grind via telefonsamtal med 46elks och Home Assistant.

## Funktioner

✅ **Telefonstyrd åtkomst** - Ring för att öppna grinden  
✅ **Betrodda nummer** - Endast godkända nummer kan öppna  
✅ **Webbgränssnitt** - Hantera nummer och se loggar  
✅ **Multi-användare** - Ge åtkomst till hyresgäster  
✅ **Samtalslogg** - Se alla försök och öppningar  
✅ **Docker-support** - Enkel deployment  
✅ **Home Assistant integration** - Fungerar med din befintliga setup  

## Snabbstart

### 1. Klona eller Ladda Ner

```bash
cd /home/ubuntu
# Projektet finns redan i gate-control-system/
```

### 2. Konfigurera

```bash
cd gate-control-system
cp .env.example .env
nano .env  # Fyll i dina uppgifter
```

### 3. Starta med Docker

```bash
docker-compose up -d
```

### 4. Öppna Webbgränssnittet

Gå till: `http://localhost:5000`

**Standard inloggning:**
- Användarnamn: `admin`
- Lösenord: `admin123`

**⚠️ BYT LÖSENORD DIREKT!**

## Systemkrav

- Docker & Docker Compose
- Home Assistant med webhook-automation
- 46elks-konto med virtuellt nummer
- Publik URL (ngrok, Cloudflare Tunnel, eller port forwarding)

## Arkitektur

```
[Uppringare] 
    ↓
[46elks +46766865568]
    ↓ (webhook)
[Din Server - Flask App]
    ↓ (kontrollerar betrodda nummer)
[Home Assistant Webhook]
    ↓
[Grind Öppnas]
```

## Projektstruktur

```
gate-control-system/
├── app.py                          # Huvudapplikation
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Docker image
├── docker-compose.yml              # Docker Compose config
├── .env.example                    # Miljövariabel mall
├── README.md                       # Denna fil
├── SETUP_GUIDE.md                  # Detaljerad installationsguide
├── config/
│   ├── trusted_numbers.json        # Betrodda telefonnummer
│   └── users.json                  # Användarkonton
├── templates/
│   └── index.html                  # Webbgränssnitt
└── logs/
    ├── gate_control.log            # Systemloggar
    └── call_attempts.log           # Samtalsloggar
```

## API Endpoints

### Publika Endpoints
- `GET /health` - Hälsokontroll
- `POST /elks/incoming-call` - 46elks webhook (används av 46elks)

### Admin Endpoints (kräver inloggning)
- `GET /` - Webbgränssnitt
- `GET /admin/stats` - Statistik
- `GET /admin/logs` - Samtalsloggar
- `GET /admin/trusted-numbers` - Lista betrodda nummer
- `POST /admin/add-number` - Lägg till nummer
- `POST /admin/remove-number` - Ta bort nummer

## Konfiguration

### Miljövariabler (.env)

```env
# 46elks API
ELKS_USERNAME=u123456789abcdef
ELKS_PASSWORD=your_api_key_here

# Home Assistant
HOME_ASSISTANT_URL=http://192.168.1.100:8123
HOME_ASSISTANT_WEBHOOK_ID=your_secret_webhook_id

# Server
FLASK_SECRET_KEY=generate_random_string
SERVER_PORT=5000
DEBUG=False
LOG_LEVEL=INFO
```

### Betrodda Nummer (config/trusted_numbers.json)

```json
{
  "numbers": [
    "+46701234567",
    "+46709876543"
  ],
  "description": "E.164 format required"
}
```

## Home Assistant Automation

```yaml
automation:
  - alias: "Grindstyrning - Öppna via Telefon"
    trigger:
      - platform: webhook
        webhook_id: "din_hemliga_webhook_id"
        allowed_methods:
          - POST
        local_only: false
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.gate_opener
```

## 46elks Konfiguration

1. Gå till: https://46elks.se/numbers
2. Klicka "Edit" på ditt nummer
3. Fyll i **voice_start**: `https://din-url.com/elks/incoming-call`
4. Spara

## Användning

### Öppna Grinden

1. Ring: **+46766865568**
2. Systemet kontrollerar ditt nummer
3. Om betrott: grinden öppnas automatiskt
4. Samtalet avslutas

### Hantera Nummer

1. Logga in på webbgränssnittet
2. Lägg till nummer i format: `+46701234567`
3. Numret kan nu öppna grinden

### Ge Åtkomst till Hyresgäster

1. Skapa användarkonto åt dem
2. De kan själva lägga till/ta bort sina nummer
3. Alla ser samma samtalslogg

## Säkerhet

### Rekommendationer

- ✅ Använd HTTPS (ngrok/Cloudflare ger detta)
- ✅ Håll webhook ID hemligt
- ✅ Använd stark Flask secret key
- ✅ Byt standardlösenord direkt
- ✅ Backup config-filer regelbundet

### Generera Säkra Nycklar

```bash
# Flask secret key
python3 -c "import secrets; print(secrets.token_hex(32))"

# Home Assistant webhook ID
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Felsökning

### Servern startar inte

```bash
# Kontrollera loggar
docker-compose logs -f

# Kontrollera .env-filen
cat .env
```

### Inget samtal når servern

```bash
# Testa att servern är publik
curl https://din-url.com/health

# Kontrollera 46elks konfiguration
# Gå till: https://46elks.se/numbers
```

### Grinden öppnas inte

```bash
# Testa Home Assistant webhook
curl -X POST http://192.168.1.100:8123/api/webhook/din_webhook_id

# Kontrollera Home Assistant loggar
```

## Kostnader

- **46elks nummer:** 30 SEK/månad
- **Inkommande samtal:** ~0.03 SEK per öppning (5 sek)
- **100 öppningar/månad:** ~33 SEK totalt

## Utveckling

### Köra Utan Docker

```bash
# Installera dependencies
pip3 install -r requirements.txt

# Starta servern
python3 app.py
```

### Testa Lokalt

```bash
# Simulera inkommande samtal
curl -X POST http://localhost:5000/elks/incoming-call \
  -d "from=%2B46701234567&callid=test123&to=%2B46766865568&direction=incoming"
```

## Support

- **46elks Dokumentation:** https://46elks.se/docs
- **Home Assistant Docs:** https://www.home-assistant.io/docs/
- **46elks Support:** help@46elks.com / 076-686 10 04

## Licens

Detta projekt är skapat för personligt bruk.

## Författare

Byggt med 46elks API och Home Assistant.

---

**Lycka till med ditt grindstyrningssystem! 🎉**
