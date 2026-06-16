#include <SPI.h>

const int ldrPin = A0;
const int buzzerPin = 5;
const int redPin = 2;
const int greenPin = 3;
const int bluePin = 4;

// 🔒 LED PİNLERİ
const int butonPin = 6;       
const int kriptoYesilLED = 8;   
const int kriptoKirmiziLED = 9; 

// 📝 CÜMLE MODU SWITCHI
const int cumleModuSwitchPin = 7; 
const int cumleModuLED = 13;      

String cumleHafizasi = "";        
bool boslukEklendi = false;       
bool cumleFirlatildi = false;     

// Kalibrasyon ortalamaları
unsigned long uzunSureler[3];
unsigned long kisaSureler[3];
unsigned long esikSuresi = 500; 

bool hizliBasimKisaMi = true; 

const unsigned long harfBeklemeSuresi = 1500; 
String mevcutMorsSinyali = ""; 
unsigned long lazerAcikBaslangic = 0;
bool harfTamamlaniyor = false;

// 🚨 YENİ EKLENEN DONANIM TAKİP DEĞİŞKENLERİ
bool sonModDurumu = false;
bool ilkOkuma = true;

// 💥 [YENİ]: SPI KABLOSUNDAN GELEN ANLIK VERİLER İÇİN VOLATILE DEĞİŞKENLER
volatile byte spiGelenHamVeri = 0;
volatile bool spiVeriGeldi = false;
volatile int aktifKriptoKey = 3; // Python arayüzüyle senkronize giden canlı anahtar

void setup() {
  Serial.begin(9600);
  
  pinMode(buzzerPin, OUTPUT);
  pinMode(redPin, OUTPUT);
  pinMode(greenPin, OUTPUT);
  pinMode(bluePin, OUTPUT);
  
  pinMode(butonPin, INPUT_PULLUP);
  pinMode(kriptoYesilLED, OUTPUT);
  pinMode(kriptoKirmiziLED, OUTPUT);
  
  pinMode(cumleModuSwitchPin, INPUT_PULLUP);
  pinMode(cumleModuLED, OUTPUT); 
  
  // 🚨 [YENİ]: NANO'YU SPI SLAVE (İŞÇİ) MODUNA ALIYORUZ
  pinMode(MISO, OUTPUT);    // Uno'ya geri cevap vereceksek hat hazır kalsın
  SPCR |= _BV(SPE);         // SPI Donanımını Nano üzerinde aktif et
  SPI.attachInterrupt();    // Uno kablodan üflediği an Nano otomatik uyansın
  
  renkAyarla(255, 0, 0); 
  delay(2000);
  while(Serial.available() > 0) { Serial.read(); } 
  
  yeniKalibrasyonYap();
}

// 🛡️ [YENİ]: UNO KABLODAN BİR BYTE ATTIĞI AN DURDURULAMAZ ŞEKİLDE TETİKLENEN SİBER FONKSİYON
ISR (SPI_STC_vect) {
  spiGelenHamVeri = SPDR; // SPI Veri Kaydedicisinden (Register) akan byte'ı al
  
  // Eğer gelen byte 1 ile 25 arasındaysa, bu kesinlikle siteden kilitlenen Sezar anahtarıdır usta!
  if (spiGelenHamVeri > 0 && spiGelenHamVeri < 26) {
    aktifKriptoKey = spiGelenHamVeri;
    
    // Python terminaline doğrudan bu formatta fırlatıyoruz ki siber dinleyici anında yakalasın!
    Serial.print("[⚡ SPI KRİPTO]: Anahtarımız Güncellendi! Yeni Anahtar: ");
    Serial.println(aktifKriptoKey);
  } else {
    // Eğer gelen veri 1-25 arası değilse bu Uno'nun lazer söndüğünde attığı normal karakterdir (Örn: 'A' -> ASCII 65)
    spiVeriGeldi = true; 
  }
}

void loop() {
  // 📝 CÜMLE MODU SWITCH KONTROLÜ
  bool cumleModuAktif = (digitalRead(cumleModuSwitchPin) == LOW);
  if (cumleModuAktif) {
    digitalWrite(cumleModuLED, HIGH); 
  } else {
    digitalWrite(cumleModuLED, LOW);
    if (cumleHafizasi != "") { cumleHafizasi = ""; } 
  }

  // 🔒 FİZİKSEL ŞALTERİN PYTHON'A ANLIK BİLDİRİLMESİ
  bool guvenliModAktif = (digitalRead(butonPin) == LOW);
  if (guvenliModAktif != sonModDurumu || ilkOkuma) {
    if (guvenliModAktif) {
      digitalWrite(kriptoYesilLED, HIGH);   
      digitalWrite(kriptoKirmiziLED, LOW);
      Serial.println("=> [DONANIM]: GÜVENLİ MOD AKTİF");
    } else {
      digitalWrite(kriptoYesilLED, LOW);
      digitalWrite(kriptoKirmiziLED, HIGH); 
      Serial.println("=> [DONANIM]: ŞİFRESİZ MOD AKTİF");
    }
    sonModDurumu = guvenliModAktif;
    ilkOkuma = false;
  }

  int ldrDegeri = analogRead(ldrPin);
  
  // 💥 LAZER SİNYALİ GELDİĞİNDE
  if (ldrDegeri <= 600) {
    renkAyarla(0, 255, 0); 
    unsigned long baslangicZamani = millis();
    
    digitalWrite(buzzerPin, HIGH); 
    while (analogRead(ldrPin) <= 600) { } 
    
    unsigned long sinyalSuresi = millis() - baslangicZamani;
    digitalWrite(buzzerPin, LOW); 
    
    if (hizliBasimKisaMi) {
      if (sinyalSuresi < esikSuresi) { mevcutMorsSinyali += "."; Serial.print("."); }
      else { mevcutMorsSinyali += "-"; Serial.print("-"); }
    } else {
      if (sinyalSuresi < esikSuresi) { mevcutMorsSinyali += "-"; Serial.print("-"); }
      else { mevcutMorsSinyali += "."; Serial.print("."); }
    }
    
    lazerAcikBaslangic = millis(); 
    harfTamamlaniyor = true;
    boslukEklendi = false; 
    cumleFirlatildi = false;
    delay(50); 
  }
  
  // ⏳ HARF ÇÖZME SÜRECİ
  if (ldrDegeri > 600 && harfTamamlaniyor) {
    renkAyarla(0, 0, 255); 
    
    if (millis() - lazerAcikBaslangic >= harfBeklemeSuresi) {
      char cozulenhArf = morsToChar(mevcutMorsSinyali);
      
      if (cozulenhArf != '?') {
        if (cumleModuAktif) {
          cumleHafizasi += cozulenhArf;
          bip(1); 
        } else {
          // Nano artık harfi doğrudan fırlatıyor
          if (guvenliModAktif) {
            Serial.print(" => [🔒 GÜVENLİ HAT]: ");  Serial.println(cozulenhArf);
          } else {
            Serial.print(" => [🔓 ŞİFRESİZ HAT]: "); Serial.println(cozulenhArf);
          }
          bip(2);
        }
      } else {
        Serial.println(" => [Bilinmeyen Sinyal]");
      }
      
      // Döngü bittiğinde SPI bayraklarını sıfırlıyoruz usta
      spiVeriGeldi = false;
      mevcutMorsSinyali = "";
      harfTamamlaniyor = false;
      renkAyarla(0, 255, 0); 
    }
  }

  // 📝 CÜMLE BİTİRME VE FIRLATMA TAKİBİ
  if (ldrDegeri > 600 && !harfTamamlaniyor && cumleModuAktif && cumleHafizasi != "") {
    unsigned long sessizlikSuresi = millis() - lazerAcikBaslangic;

    if (sessizlikSuresi >= 5000 && sessizlikSuresi < 10000 && !boslukEklendi) {
      cumleHafizasi += " ";
      boslukEklendi = true; 
      bip(1); 
    }

    if (sessizlikSuresi >= 10000 && !cumleFirlatildi) {
      if (guvenliModAktif) {
        Serial.print("\n => [🔒 GÜVENLİ CÜMLE]: ");
        Serial.println(cumleHafizasi);
      } else {
        Serial.print("\n => [🔓 ŞİFRESİZ CÜMLE]: ");
        Serial.println(cumleHafizasi);
      }
      
      bip(3); 
      cumleHafizasi = ""; 
      cumleFirlatildi = true; 
    }
  }
}

void yeniKalibrasyonYap() {
  renkAyarla(0, 0, 255); 
  Serial.println("\n=== L.O.S. BIYOMETRIK KALIBRASYON MODU ===");
  delay(1000);
  
  for (int i = 0; i < 3; i++) {
    Serial.print("UZUN (-) sinyali verin ("); Serial.print(i+1); Serial.println("/3)...");
    while (analogRead(ldrPin) > 600) { } 
    unsigned long baslangic = millis();
    digitalWrite(buzzerPin, HIGH);
    while (analogRead(ldrPin) <= 600) { } 
    uzunSureler[i] = millis() - baslangic;
    digitalWrite(buzzerPin, LOW);
    Serial.print("[✓] Olculen Sure: "); Serial.print(uzunSureler[i]); Serial.println(" ms");
    bip(1);
    delay(800);
  }
  
  for (int i = 0; i < 3; i++) {
    Serial.print("KISA (.) sinyali verin ("); Serial.print(i+1); Serial.println("/3)...");
    while (analogRead(ldrPin) > 600) { } 
    unsigned long baslangic = millis();
    digitalWrite(buzzerPin, HIGH);
    while (analogRead(ldrPin) <= 600) { } 
    kisaSureler[i] = millis() - baslangic;
    digitalWrite(buzzerPin, LOW);
    Serial.print("[✓] Olculen Sure: "); Serial.print(kisaSureler[i]); Serial.println(" ms");
    bip(1);
    delay(800);
  }
  
  unsigned long uzunOrtalama = (uzunSureler[0] + uzunSureler[1] + uzunSureler[2]) / 3;
  unsigned long kisaOrtalama = (kisaSureler[0] + kisaSureler[1] + kisaSureler[2]) / 3;
  esikSuresi = (uzunOrtalama + kisaOrtalama) / 2;
  
  if (kisaOrtalama < uzunOrtalama) { hizliBasimKisaMi = true; } 
  else { hizliBasimKisaMi = false; }
  
  Serial.print("ESIK:");
  Serial.println(esikSuresi);
  renkAyarla(0, 255, 0); 
  bip(3);
}

char morsToChar(String mors) {
  if (mors == ".-")    return 'A'; if (mors == "-...") return 'B';
  if (mors == "-.-.") return 'C'; if (mors == "-..")   return 'D';
  if (mors == ".")    return 'E'; if (mors == "..-.") return 'F';
  if (mors == "--.")  return 'G'; if (mors == "....") return 'H';
  if (mors == "..")   return 'I'; if (mors == ".---") return 'J';
  if (mors == "-.-")  return 'K'; if (mors == ".-..") return 'L';
  if (mors == "--")   return 'M'; if (mors == "-.")   return 'N';
  if (mors == "---")  return 'O'; if (mors == ".--.") return 'P';
  if (mors == "--.-") return 'Q'; if (mors == ".-.")   return 'R';
  if (mors == "...")  return 'S'; if (mors == "-")    return 'T';
  if (mors == "..-")  return 'U'; if (mors == "...-") return 'V';
  if (mors == ".--")  return 'W'; if (mors == "-..-") return 'X';
  if (mors == "-.--") return 'Y'; if (mors == "--..") return 'Z';
  return '?';
}

void renkAyarla(int r, int g, int b) { analogWrite(redPin, r); analogWrite(greenPin, g); analogWrite(bluePin, b); }
void bip(int tekrar) { for(int i=0; i<tekrar; i++){ digitalWrite(buzzerPin, HIGH); delay(80); digitalWrite(buzzerPin, LOW); delay(80); } }