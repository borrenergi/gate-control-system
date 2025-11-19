# Grindstyrning - Komplett Installationsguide

## Översikt

Detta system låter dig styra din grind via telefonsamtal. När någon ringer ditt 46elks-nummer kontrollerar systemet om numret finns i listan över betrodda nummer. Om ja, öppnas grinden automatiskt via Home Assistant.

## Ditt 46elks Nummer

**Telefonnummer:** +46766865568  
**Kostnad:** 30 SEK/månad  
**Typ:** Svenskt mobilnummer med SMS och röstsamtal

---

## Steg 1: Förbered Din Server

### Alternativ A: Lokal Server (Rekommenderas)
Kör systemet på samma nätverk som Home Assistant.

```bash
# Installera Docker och Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo apt-get install docker-compose-plugin
```

### Alternativ B: Cloud Server (VPS)
Använd DigitalOcean, Linode, eller liknande.

---

## Steg 2: Konfigurera Miljövariabler

Skapa en `.env` fil i projektmappen:

```bash
cd /home/ubuntu/gate-control-system
cp .env.example .env
nano .env
```

Fyll i följande värden:

```env
# 46elks API Credentials
# Hitta dessa på: https://46elks.se/account
ELKS_USERNAME=u123456789abcdef
ELKS_PASSWORD=your_api_key_here

# Home Assistant Configuration
HOME_ASSISTANT_URL=http://192.168.1.100:8123
HOME_ASSISTANT_WEBHOOK_ID=your_secret_webhook_id_here

# Server Configuration  
FLASK_SECRET_KEY=generate_random_string_here
SERVER_PORT=5000
DEBUG=False
LOG_LEVEL=INFO
```

### Generera Säkra Nycklar

```bash
# Generera Flask secret key
python3 -c "import secrets; print(secrets.token_hex(32))"

# Generera Home Assistant webhook ID
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Steg 3: Konfigurera Home Assistant

### 3.1 Skapa Webhook Automation

Gå till Home Assistant → Settings → Automations & Scenes → Create Automation

**YAML-konfiguration:**

```yaml
automation:
  - alias: "Grindstyrning - Öppna via Telefon"
    description: "Öppnar grinden när webhook triggas"
    trigger:
      - platform: webhook
        webhook_id: "din_hemliga_webhook_id"  # Samma som i .env
        allowed_methods:
          - POST
        local_only: false  # Sätt till true om servern är lokal
    condition: []
    action:
      # Byt ut mot din grind-enhet
      - service: switch.turn_on
        target:
          entity_id: switch.gate_opener
      
      # Valfritt: Skicka notifikation
      - service: notify.mobile_app_your_phone
        data:
          message: "Grinden öppnades via telefon kl {{ now().strftime('%H:%M') }}"
          title: "🚪 Grind Öppnad"
    
    mode: single
```

### 3.2 Testa Webhooken

```bash
# Testa från terminalen
curl -X POST http://192.168.1.100:8123/api/webhook/din_hemliga_webhook_id \
  -H "Content-Type: application/json" \
  -d '{"test": "true"}'
```

Om grinden öppnas fungerar webhooken!

---

## Steg 4: Exponera Servern Publikt

46elks behöver kunna nå din server via internet.

### Alternativ A: Ngrok (Enklast för Test)

```bash
# Installera ngrok
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | \
  sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null && \
  echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | \
  sudo tee /etc/apt/sources.list.d/ngrok.list && \
  sudo apt update && sudo apt install ngrok

# Starta ngrok
ngrok http 5000
```

Du får en URL som: `https://abc123.ngrok.io`

### Alternativ B: Cloudflare Tunnel (Gratis, Permanent)

```bash
# Installera cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Autentisera
cloudflared tunnel login

# Skapa tunnel
cloudflared tunnel create gate-control

# Kör tunnel
cloudflared tunnel --url http://localhost:5000 run gate-control
```

### Alternativ C: Port Forwarding (Om du har statisk IP)

1. Logga in på din router
2. Forwarda port 5000 till din servers lokala IP
3. Använd din publika IP: `http://your-public-ip:5000`

---

## Steg 5: Starta Systemet

### Med Docker (Rekommenderas)

```bash
cd /home/ubuntu/gate-control-system

# Bygg och starta
docker-compose up -d

# Visa loggar
docker-compose logs -f

# Stoppa
docker-compose down
```

### Utan Docker

```bash
cd /home/ubuntu/gate-control-system

# Installera dependencies
pip3 install -r requirements.txt

# Starta servern
python3 app.py
```

---

## Steg 6: Konfigurera 46elks Nummer

### 6.1 Sätt Webhook URL

Gå till: https://46elks.se/number?id=nf500c1b38bffa483b876d671e78d11de

Fyll i fältet **voice_start**:

```
https://din-publika-url.com/elks/incoming-call
```

Exempel:
- Ngrok: `https://abc123.ngrok.io/elks/incoming-call`
- Cloudflare: `https://gate.yourdomain.com/elks/incoming-call`
- Port Forward: `http://your-ip:5000/elks/incoming-call`

Klicka **Save changes**

### 6.2 Verifiera Konfigurationen

```bash
# Testa att servern svarar
curl https://din-publika-url.com/health

# Bör returnera:
{
  "status": "healthy",
  "service": "Gate Control System",
  "version": "1.0.0"
}
```

---

## Steg 7: Lägg Till Betrodda Nummer

### Via Webbgränssnittet

1. Öppna: `http://localhost:5000` (eller din publika URL)
2. Logga in (standard: admin / admin123)
3. **VIKTIGT: Byt lösenord direkt!**
4. Lägg till telefonnummer i format: `+46701234567`

### Via API

```bash
curl -X POST http://localhost:5000/admin/add-number \
  -H "Content-Type: application/json" \
  -d '{"number": "+46701234567"}'
```

---

## Steg 8: Testa Systemet

1. **Ring ditt 46elks-nummer:** +46766865568
2. **Kontrollera loggarna:**
   ```bash
   docker-compose logs -f
   # eller
   tail -f logs/gate_control.log
   ```
3. **Verifiera att grinden öppnas**
4. **Kolla webbgränssnittet** för att se samtalsloggen

---

## Säkerhet

### Ändra Standardlösenord

```bash
# Generera nytt lösenord-hash
python3 -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('ditt_nya_lösenord'))"

# Uppdatera config/users.json med det nya hashet
```

### Säkra Webhooken

- Använd HTTPS (ngrok/Cloudflare ger detta automatiskt)
- Håll webhook ID hemligt
- Använd stark Flask secret key
- Aktivera rate limiting om möjligt

### Brandväggsregler

```bash
# Tillåt endast nödvändiga portar
sudo ufw allow 5000/tcp
sudo ufw enable
```

---

## Felsökning

### Problem: Inget samtal når servern

**Lösning:**
1. Kontrollera att servern är publik tillgänglig:
   ```bash
   curl https://din-url.com/health
   ```
2. Verifiera att voice_start är korrekt konfigurerad på 46elks
3. Kolla 46elks loggar: https://46elks.se/logs

### Problem: Grinden öppnas inte

**Lösning:**
1. Testa Home Assistant webhooken manuellt:
   ```bash
   curl -X POST http://192.168.1.100:8123/api/webhook/din_webhook_id
   ```
2. Kontrollera att grind-enheten fungerar i Home Assistant
3. Kolla Home Assistant loggar

### Problem: "Untrusted number"

**Lösning:**
1. Kontrollera att numret är i E.164 format: `+46701234567`
2. Verifiera i webbgränssnittet att numret finns
3. Kolla `config/trusted_numbers.json`

---

## Underhåll

### Visa Loggar

```bash
# Docker
docker-compose logs -f

# Direktkörning
tail -f logs/gate_control.log
tail -f logs/call_attempts.log
```

### Backup

```bash
# Backup konfiguration och loggar
tar -czf gate-backup-$(date +%Y%m%d).tar.gz config/ logs/
```

### Uppdatera Systemet

```bash
# Med Docker
docker-compose down
docker-compose pull
docker-compose up -d

# Utan Docker
git pull  # Om du använder git
pip3 install -r requirements.txt --upgrade
python3 app.py
```

---

## Kostnader

### 46elks
- **Nummer:** 30 SEK/månad
- **Inkommande samtal:** ~0.35 SEK/minut
- **Per grindöppning (5 sek):** ~0.03 SEK
- **100 öppningar/månad:** ~33 SEK/månad totalt

### Server
- **Lokal (Raspberry Pi):** 0 SEK (el ~10 SEK/månad)
- **VPS (DigitalOcean):** ~50-100 SEK/månad
- **Ngrok gratis:** 0 SEK (begränsad)
- **Cloudflare Tunnel:** 0 SEK

**Total kostnad:** ~30-130 SEK/månad beroende på setup

---

## Support

### Dokumentation
- 46elks API: https://46elks.se/docs
- Home Assistant: https://www.home-assistant.io/docs/

### Kontakt
- 46elks Support: help@46elks.com
- 46elks Telefon: 076-686 10 04

---

## Nästa Steg

1. ✅ Lägg till dina hyresgästers nummer
2. ✅ Skapa separata användarkonton åt dem
3. ✅ Testa systemet grundligt
4. ✅ Sätt upp automatisk backup
5. ✅ Övervaka loggarna första veckan

**Grattis! Ditt grindstyrningssystem är nu klart! 🎉**
