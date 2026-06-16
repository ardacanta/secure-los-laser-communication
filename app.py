from flask import Flask, render_template, request, jsonify
import serial
import time
import threading
import logging

app = Flask(__name__)

# ⚠️ Port tanımlamaları
PORT_ADI = 'COM3'   # Lazer Verici Uno
NANO_PORT = 'COM5'  # Alıcı ve Kalibrasyon Yapan Nano

OTOMATIK_ESIK = 500
GELEN_LOGLAR = []   
AKTIF_KRIPTO_KEY = 3  

# 🚨 FİZİKSEL ŞALTER DURUMU
FIZIKSEL_GUVENLI_MOD = True 

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

# 🛡️ GELENİ DEŞİFRE EDEN MOTOR (GERİ SARAR) - UNUTULAN KISIM BUYDU USTA!
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


# 📡 2. NANO ARKA PLAN DİNLEYİCİ - GELENLERİ DEŞİFRE EDER!
def nano_dinle():
    global OTOMATIK_ESIK, GELEN_LOGLAR, AKTIF_KRIPTO_KEY, FIZIKSEL_GUVENLI_MOD
    try:
        arduino_nano = serial.Serial(NANO_PORT, 9600, timeout=1)
        print(f"[+] {NANO_PORT} portu üzerinden Nano otomatik takibe alındı!")
        
        while True:
            if arduino_nano.in_waiting > 0:
                raw_line = arduino_nano.readline()
                line = raw_line.decode('utf-8', errors='ignore').strip()
                
                if line:
                    print(f"[🟢 NANO HAM VERİ]: {line}")
                    
                    if "=> [" in line:
                        
                        if "=> [DONANIM]: GÜVENLİ MOD AKTİF" in line:
                            FIZIKSEL_GUVENLI_MOD = True
                            GELEN_LOGLAR.append("> [⚙️ SİSTEM]: Donanım Güvenli Moda Geçti. Şifreli Fırlatma AKTİF!")
                            print("\n[⚡ ŞALTER]: Güvenli Mod ON - Artık Uno'dan şifreli fırlatılacak.")
                        elif "=> [DONANIM]: ŞİFRESİZ MOD AKTİF" in line:
                            FIZIKSEL_GUVENLI_MOD = False
                            GELEN_LOGLAR.append("> [⚙️ SİSTEM]: Donanım Şifresiz Moda Geçti. Çıplak Fırlatma AKTİF!")
                            print("\n[⚡ ŞALTER]: Güvenli Mod OFF - Artık Uno'dan çıplak fırlatılacak.")
                            
                        # 🚨 1. DURUM: GÜVENLİ MOD BUTONU AÇIKKEN (GERİ SARARAK ÇÖZÜYORUZ)
                        elif "GÜVENLİ HAT" in line:
                            try:
                                ham_harf = line.split("]:")[1].strip()
                                gercek_harf = sezar_geri_kaydir(ham_harf, AKTIF_KRIPTO_KEY)
                                temiz_log = f"=> [🔒 GÜVENLİ MOD ÇÖZÜLDÜ +{AKTIF_KRIPTO_KEY}]: {gercek_harf}"
                                GELEN_LOGLAR.append(temiz_log)
                                print(f"    ↳ [🔥 SİBER DEŞİFRE] Sitedeki Ekrana Giden: {temiz_log}")
                            except Exception as ex:
                                print(f"Hata var usta: {ex}")
                                GELEN_LOGLAR.append(line)
                                
                        # 🚨 2. DURUM: ŞİFRESİZ MOD 
                        elif "ŞİFRESİZ HAT" in line:
                            try:
                                ham_harf = line.split("]:")[1].strip()
                                temiz_log = f"=> [🔓 ŞİFRESİZ HAT]: {ham_harf}"
                                GELEN_LOGLAR.append(temiz_log)
                                print(f"    ↳ [⚡ DİREKT GEÇİŞ] Sitedeki Ekrana Giden: {temiz_log}")
                            except:
                                GELEN_LOGLAR.append(line)
                                
                        # 🚨 3. DURUM: CÜMLE MODU LOGLARI (GERİ SARARAK ÇÖZÜYORUZ)
                        elif "GÜVENLİ CÜMLE" in line or "CÜMLE]:" in line or "CÜMLESİ]:" in line:
                            try:
                                ham_cumle = line.split("]:")[1].strip()
                                gercek_cumle = sezar_geri_kaydir(ham_cumle, AKTIF_KRIPTO_KEY)
                                temiz_log = f"=> [📜 GERÇEK GÜNCEL CÜMLE]: {gercek_cumle}"
                                GELEN_LOGLAR.append(temiz_log)
                                print(f"    ↳ [🔥 CÜMLE DEŞİFRESİ] Sitedeki Ekrana Giden: {temiz_log}")
                                
                                if arduino:
                                    arduino.write(f"CUMLE:{gercek_cumle}\n".encode('utf-8'))
                                    arduino.flush()
                            except:
                                GELEN_LOGLAR.append(line)
                        else:
                            GELEN_LOGLAR.append(line)
                    
                    elif line == "." or line == "-":
                        GELEN_LOGLAR.append(f"Sinyal: {line}")

                    if "ESIK" in line:
                        try:
                            deger = int(line.split("ESIK:")[1].strip())
                            OTOMATIK_ESIK = deger
                        except:
                            pass
                    
                    if len(GELEN_LOGLAR) > 40:
                        GELEN_LOGLAR.pop(0)
                            
            time.sleep(0.01)
    except Exception as e:
        print(f"[X] Nano Dinleme Hatası (Thread Pasif): {e}")

nano_thread = threading.Thread(target=nano_dinle, daemon=True)
nano_thread.start()

MORS_SOZLUK = {
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
    global GELEN_LOGLAR
    return jsonify({'esik': OTOMATIK_ESIK, 'loglar': list(GELEN_LOGLAR)})

@app.route('/key-guncelle', methods=['POST'])
def key_guncelle():
    global AKTIF_KRIPTO_KEY
    try:
        AKTIF_KRIPTO_KEY = int(request.form.get('kripto_key', 3))
        print(f"\n[🔒 SİBER GÜVENLİK] Canlı Şifreleme Anahtarı +{AKTIF_KRIPTO_KEY} Yapıldı usta!\n")
        return jsonify({'durum': f'Sistem: Kripto Anahtarı +{AKTIF_KRIPTO_KEY} Olarak Kilitlendi! ✓'})
    except:
        return jsonify({'durum': 'Hata: Anahtar kilitlenemedi!'})

# 🚀 WEB BUTONUYLA GÖNDERME MOTORU (TERMİNAL GÖRÜNTÜSÜ EKLENDİ)
@app.route('/gonder', methods=['POST'])
def gonder():
    global AKTIF_KRIPTO_KEY, FIZIKSEL_GUVENLI_MOD
    mesaj = request.form.get('mesaj', '').upper()
    esik_suresi = int(request.form.get('esik', OTOMATIK_ESIK))
    
    try:
        gecerli_key = int(request.form.get('kripto_key', AKTIF_KRIPTO_KEY))
    except:
        gecerli_key = AKTIF_KRIPTO_KEY

    if not arduino: return jsonify({'durum': 'Hata: Verici bağlı değil!'})
    if not mesaj: return jsonify({'durum': 'Hata: Kelime boş!'})

    kisa_ms = int(esik_suresi * 0.6)  
    uzun_ms = int(esik_suresi * 1.5)  

    # 💥 İŞTE VSCODE TERMİNALİNDE GÖRMEK İSTEDİĞİN O LOG BLOKLARI:
    print("\n" + "="*50)
    print(f"[📝 SİTEDEN YAZILAN METİN] : {mesaj}")

    if FIZIKSEL_GUVENLI_MOD:
        firlatilacak_mesaj = sezar_ileri_kaydir(mesaj, gecerli_key)
        print(f"[🔒 LAZERDEN GİDEN SİNYAL] : {firlatilacak_mesaj}  (MOD: GÜVENLİ | KEY: +{gecerli_key})")
        durum_metni = f'"{mesaj}" kelimesi (+{gecerli_key} ile Şifrelenerek: "{firlatilacak_mesaj}") fırlatıldı! ✓'
    else:
        firlatilacak_mesaj = mesaj.strip().upper()
        print(f"[🔓 LAZERDEN GİDEN SİNYAL] : {firlatilacak_mesaj}  (MOD: ŞİFRESİZ / ÇIPLAK)")
        durum_metni = f'"{mesaj}" kelimesi (🔓 ŞİFRESİZ) çıplak fırlatıldı! ✓'
        
    print("="*50 + "\n")

    # Uno kartı tamamen bu "firlatilacak_mesaj" içeriğini fiziksel sinyale çeviriyor usta
    for sinyal_harfi in firlatilacak_mesaj:
        if sinyal_harfi in MORS_SOZLUK:
            mors_karsiligi = MORS_SOZLUK[sinyal_harfi]
            for sinyal in mors_karsiligi:
                komut = f"K{kisa_ms}-{sinyal_harfi}\n" if sinyal == '.' else f"U{uzun_ms}-{sinyal_harfi}\n"
                arduino.write(komut.encode('utf-8'))
                arduino.flush()
                time.sleep((kisa_ms/1000.0 if sinyal == '.' else uzun_ms/1000.0) + 0.3)
            time.sleep(1.6) 
            
    return jsonify({'durum': durum_metni})

if __name__ == '__main__':
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    print("[*] L.O.S. Web Sunucusu Başlatılıyor... Tarayıcıyı açabilirsin usta.")
    app.run(host='0.0.0.0', port=5000, debug=False)