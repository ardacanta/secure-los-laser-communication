from flask import Flask, render_template, request, jsonify
import serial
import time
import threading
import logging

app = Flask(__name__)

# ⚠️ Donanım Port Tanımlamaları
PORT_ADI = 'COM3'   # Lazer Verici Uno
NANO_PORT = 'COM5'  # Alıcı ve Kalibrasyon Yapan Nano

# Süreçlerin canlı senkronize olabilmesi için ortak hafıza havuzu
SISTEM_AYARLARI = {
    'esik_suresi': 500,
    'kripto_key': 3,
    'kripto_yon': 'ileri',  # 'ileri' veya 'geri'
    'guvenli_mod': True     # Web arayüzündeki siber şalterin durumu
}

GELEN_LOGLAR = []   
ayar_kilidi = threading.Lock()

try:
    arduino = serial.Serial(PORT_ADI, 9600, timeout=1)
    time.sleep(2) 
    print(f"[+] {PORT_ADI} portu üzerinden Arduino Uno BAŞARIYLA BAĞLANDI! ✓")
except Exception as e:
    arduino = None
    print(f"[X] DONANIM HATASI: Uno portuna bağlanılamadı: {e}")


# 🚀 GİDENİ ŞİFRELEYEN MOTOR (İLERİ SARAR)
def sezar_ileri_kaydir(metin, key):
    sifreli = ""
    alfabe = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    temiz_metin = str(metin).strip().upper()
    
    for karakter in temiz_metin:
        if karakter in alfabe:
            idx = alfabe.index(karakter)
            yeni_idx = (idx + key) % 26
            sifreli += alfabe[yeni_idx]
        elif karakter in ['İ', 'I']: 
            sifreli += alfabe[(alfabe.index('I') + key) % 26]
        elif karakter == 'Ş': 
            sifreli += alfabe[(alfabe.index('S') + key) % 26]
        elif karakter == 'Ğ': 
            sifreli += alfabe[(alfabe.index('G') + key) % 26]
        elif karakter == 'Ç': 
            sifreli += alfabe[(alfabe.index('C') + key) % 26]
        elif karakter == 'Ö': 
            sifreli += alfabe[(alfabe.index('O') + key) % 26]
        elif karakter == 'Ü': 
            sifreli += alfabe[(alfabe.index('U') + key) % 26]
        else:
            sifreli += karakter
    return sifreli

# 🛡️ GELENİ DEŞİFRE EDEN MOTOR (GERİ SARAR)
def sezar_geri_kaydir(metin, key):
    cozulmus = ""
    alfabe = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    temiz_metin = str(metin).strip().upper()
    
    for karakter in temiz_metin:
        if karakter in alfabe: 
            idx = alfabe.index(karakter)
            yeni_idx = (idx - key) % 26
            cozulmus += alfabe[yeni_idx]
        elif karakter in ['İ', 'I']: 
            cozulmus += alfabe[(alfabe.index('I') - key) % 26]
        elif karakter == 'Ş': 
            cozulmus += alfabe[(alfabe.index('S') - key) % 26]
        elif karakter == 'Ğ': 
            cozulmus += alfabe[(alfabe.index('G') - key) % 26]
        elif karakter == 'Ç': 
            cozulmus += alfabe[(alfabe.index('C') - key) % 26]
        elif karakter == 'Ö': 
            cozulmus += alfabe[(alfabe.index('O') - key) % 26]
        elif karakter == 'Ü': 
            cozulmus += alfabe[(alfabe.index('U') - key) % 26]
        else:
            cozulmus += karakter
    return cozulmus


# 📡 2. NANO ARKA PLAN DİNLEYİCİ - SAF LOGLAMA MODU
def nano_dinle():
    global GELEN_LOGLAR, SISTEM_AYARLARI
    try:
        arduino_nano = serial.Serial(NANO_PORT, 9600, timeout=1)
        print(f"[+] {NANO_PORT} portu üzerinden Nano otomatik takibe alındı!")
        
        while True:
            if arduino_nano.in_waiting > 0:
                raw_line = arduino_nano.readline()
                line = raw_line.decode('utf-8', errors='ignore').strip()
                
                if line:
                    print(f"[🟢 NANO HAM VERİ]: {line}")
                    
                    # 1. DONANIM SİSTEM LOGLARINI AYIKLA
                    if "=> [DONANIM]: GÜVENLİ MOD AKTİF" in line:
                        with ayar_kilidi: SISTEM_AYARLARI['guvenli_mod'] = True
                        GELEN_LOGLAR.append("> [⚙️ SİSTEM]: Donanım Güvenli Moda Geçti. Şifreli Fırlatma AKTİF!")
                        continue
                    elif "=> [DONANIM]: ŞİFRESİZ MOD AKTİF" in line:
                        with ayar_kilidi: SISTEM_AYARLARI['guvenli_mod'] = False
                        GELEN_LOGLAR.append("> [⚙️ SİSTEM]: Donanım Şifresiz Moda Geçti. Çıplak Fırlatma AKTİF!")
                        continue
                    elif "ESIK" in line:
                        try:
                            deger = int(line.split("ESIK:")[1].strip())
                            with ayar_kilidi: SISTEM_AYARLARI['esik_suresi'] = deger
                        except: pass
                        continue
                    elif line == "." or line == "-":
                        GELEN_LOGLAR.append(f"Sinyal: {line}")
                        continue

                    # 2. HARF YAKALAMA VE KRİPTO KATMANI
                    ham_harf = line
                    if "]:" in line:
                        ham_harf = line.split("]:")[1].strip()
                    else:
                        ham_harf = ham_harf.replace("=>", "").replace("[", "").replace("]", "").strip()

                    # Ayıklanan veri tek bir harf ise siber lojiği işlet
                    if ham_harf and len(ham_harf) == 1 and ham_harf.isalpha():
                        with ayar_kilidi:
                            anlik_salter = SISTEM_AYARLARI['guvenli_mod']
                            aktif_yon = SISTEM_AYARLARI['kripto_yon']
                            aktif_key = SISTEM_AYARLARI['kripto_key']

                        # Arayüzdeki şalter aktifse elinle kestiğin harfi panel kuralına göre yansıt
                        if anlik_salter:
                            if aktif_yon == 'ileri':
                                donusen_harf = sezar_ileri_kaydir(ham_harf, aktif_key)
                                temiz_log = f"=> [🔒 GÜVENLİ HAT - YAKALANAN SİNYAL (İLERİ +{aktif_key})]: {donusen_harf}"
                            else:
                                donusen_harf = sezar_geri_kaydir(ham_harf, aktif_key)
                                temiz_log = f"=> [🔒 GÜVENLİ HAT - YAKALANAN SİNYAL (GERİ -{aktif_key})]: {donusen_harf}"
                        else:
                            temiz_log = f"=> [🔓 ŞİFRESİZ HAT]: {ham_harf}"

                        GELEN_LOGLAR.append(temiz_log)
                        print(f"    ↳ [📡 HAT LOGU] Sitedeki Ekrana Giden: {temiz_log}")
                    else:
                        GELEN_LOGLAR.append(line)

                    if len(GELEN_LOGLAR) > 40:
                        GELEN_LOGLAR.pop(0)
                            
            time.sleep(0.01)
    except Exception as e:
        print(f"[X] Nano Dinleme Hatası (Thread Pasif): {e}")

nano_thread = threading.Thread(target=nano_dinle, daemon=True)
nano_thread.start()


# 🌟 İSTEĞİN ÜZERİNE TANIMLANAN YENİ ALFABE2 SÖZLÜĞÜ (Mors Çıktıları Buradan Okunacak)
ALFABE2 = {
    'A': '.-',    'B': '-...',  'C': '-.-.',  'D': '-..',   'E': '.',
    'F': '..-.',  'G': '--.',   'H': '....',  'I': '..',    'J': '.---',
    'K': '-.-',   'L': '.-..',  'M': '--',    'N': '-.',    'O': '---',
    'P': '.--.',  'Q': '--.-',  'R': '.-.',   'S': '...',   'T': '-',
    'U': '..-',   'V': '...-',  'W': '.--',   'X': '-..-',  'Y': '-.--',
    'Z': '--..'
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/esik-cek', methods=['GET'])
def esik_cek():
    global GELEN_LOGLAR, SISTEM_AYARLARI
    with ayar_kilidi:
        guncel_esik = SISTEM_AYARLARI['esik_suresi']
    return jsonify({'esik': guncel_esik, 'loglar': list(GELEN_LOGLAR)})

@app.route('/key-guncelle', methods=['POST'])
def key_guncelle():
    global SISTEM_AYARLARI
    try:
        yeni_key = int(request.form.get('kripto_key', 3))
        guvenli_mod_istegi = request.form.get('guvenli_mod') == 'true'
        with ayar_kilidi:
            SISTEM_AYARLARI['kripto_key'] = yeni_key
            SISTEM_AYARLARI['guvenli_mod'] = guvenli_mod_istegi
            
        if arduino:
            arduino.write(f"KEY:{yeni_key}\n".encode('utf-8'))
            arduino.flush()
            
        return jsonify({'durum': f'Sistem: Kripto Anahtarı +{yeni_key} Olarak Kilitlendi! ✓'})
    except:
        return jsonify({'durum': 'Hata: Anahtar kilitlenemedi!'})

@app.route('/yon-guncelle', methods=['POST'])
def yon_guncelle():
    global SISTEM_AYARLARI
    try:
        yeni_yon = request.form.get('kripto_yon', 'ileri')
        with ayar_kilidi:
            SISTEM_AYARLARI['kripto_yon'] = yeni_yon
        return jsonify({'durum': f'Sistem: Şifreleme Vektörü [{yeni_yon.upper()}] Olarak Sabitlendi! ✓'})
    except:
        return jsonify({'durum': 'Hata: Yön kilitlenemedi!'})


# ⚡ UNO SPI DONANIMINA GÖRE SİNYAL FIRLATAN AKILLI LAZER MOTORU
def asenkron_lazer_firlat(firlatilacak_mesaj, kisa_ms, uzun_ms):
    if not arduino: return
    time.sleep(0.5) 
    
    # Döngü doğrudan Sezar motorundan çıkmış olan SON MESAJIN harflerini döner (Örn: 'D')
    for sinyal_harfi in firlatilacak_mesaj: 
        if sinyal_harfi in ALFABE2:
            mors_karsiligi = ALFABE2[sinyal_harfi]  # Doğrudan ALFABE2 dizisinden D'nin morsunu çeker!
            
            for sinyal in mors_karsiligi:
                # Nano'ya SPI hattan sürekli boşluk gitmesin, aktif harf basılsın diye parametre harfin kendisi yapıldı
                komut = f"K{kisa_ms}-{sinyal_harfi}\n" if sinyal == '.' else f"U{uzun_ms}-{sinyal_harfi}\n"
                try:
                    arduino.write(komut.encode('utf-8'))
                    arduino.flush()
                except:
                    pass
                
                time.sleep((kisa_ms/1000.0 if sinyal == '.' else uzun_ms/1000.0) + 0.55)
                
            # Nano'nun 1.5 saniyelik (1500 ms) harf birleştirme süresini tam doldurması için bekleme payı
            time.sleep(1.8) 

@app.route('/gonder', methods=['POST'])
def gonder():
    global SISTEM_AYARLARI
    mesaj = request.form.get('mesaj', '').upper()
    anlik_salter = request.form.get('guvenli_mod') == 'true'
    
    with ayar_kilidi:
        esik_suresi = SISTEM_AYARLARI['esik_suresi']
        kripto_yon = SISTEM_AYARLARI['kripto_yon']
        gecerli_key = SISTEM_AYARLARI['kripto_key']

    if not arduino: return jsonify({'durum': 'Hata: Verici bağlı değil!'})
    if not mesaj: return jsonify({'durum': 'Hata: Kelime boş!'})

    kisa_ms = int(esik_suresi * 0.6)  
    uzun_ms = int(esik_suresi * 1.5)  

    print("\n" + "="*50)
    print(f"[📝 SİTEDEN YAZILAN METİN] : {mesaj}")

    if anlik_salter:
        if kripto_yon == 'ileri':
            firlatilacak_mesaj = sezar_ileri_kaydir(mesaj, gecerli_key)
            durum_metni = f'"{mesaj}" kelimesi (+{gecerli_key} İLERİ Şifrelenerek: "{firlatilacak_mesaj}") fırlatıldı! ✓'
        else:
            firlatilacak_mesaj = sezar_geri_kaydir(metin=mesaj, key=gecerli_key)
            durum_metni = f'"{mesaj}" kelimesi (-{gecerli_key} GERİ Şifrelenerek: "{firlatilacak_mesaj}") fırlatıldı! ✓'
    else:
        firlatilacak_mesaj = mesaj.strip().upper()
        durum_metni = f'"{mesaj}" kelimesi (🔓 ŞİFRESİZ) çıplak fırlatıldı! ✓'
        
    print(f"[🔒 LAZERDEN GİDEN SİNYAL] : {firlatilacak_mesaj}")
    print("="*50 + "\n")

    # BURASI ÇOK ÖNEMLİ: Asenkron fonksiyona kaydırılmış (firlatilacak_mesaj) gidiyor, yani ALFABE2 doğrudan D'yi bulacak!
    t = threading.Thread(target=asenkron_lazer_firlat, args=(firlatilacak_mesaj, kisa_ms, uzun_ms))
    t.start()
            
    return jsonify({'durum': durum_metni})

if __name__ == '__main__':
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    print("[*] L.O.S. Web Sunucusu Başlatılıyor... Tarayıcıyı açabilirsin usta.")
    app.run(host='0.0.0.0', port=5000, debug=False)