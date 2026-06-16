#include <SPI.h>

const int laserPin = 7;

// Python'dan gelen harfi hafızada tutmak için değişken
char gonderilecekHarf = ' '; 

void setup() {
  Serial.begin(9600);
  pinMode(laserPin, OUTPUT);
  
  // SPI hattını Master olarak açıyoruz
  SPI.begin();
  SPI.setClockDivider(SPI_CLOCK_DIV16);
  
  // SS (Pin 10) kontrolü için çıkış yapıyoruz usta
  pinMode(SS, OUTPUT);
  digitalWrite(SS, HIGH);
  
  digitalWrite(laserPin, HIGH); // Başlangıçta lazer açık
  Serial.println("=== L.O.S. WEB+SPI MASTER UNO AKTIF ===");
}

void loop() {
  if (Serial.available() > 0) {
    String gelenKomut = Serial.readStringUntil('\n');
    gelenKomut.trim();
    
    if (gelenKomut.length() > 0) {
      
      // 🚨 [YENİ EKLEME]: EĞER PYTHON'DAN "KEY:X" KOMUTU GELDİYSE
      if (gelenKomut.startsWith("KEY:")) {
        int yeniKey = gelenKomut.substring(4).toInt();
        
        // Lazere hiç dokunmuyoruz, gizli hattan (SPI) Nano'ya yeni anahtarı üflüyoruz
        digitalWrite(SS, LOW);
        SPI.transfer(yeniKey); // Sayısal değeri doğrudan byte olarak gönderiyoruz usta
        digitalWrite(SS, HIGH);
        
        // Debug için Uno'dan onay basabiliriz (İsteğe bağlı)
        // Serial.print("[Uno-SPI]: Yeni anahtar Nano'ya uçuruldu: ");
        // Serial.println(yeniKey);
        return; // İşlem bitti, döngünün başına dön lazer patlatma
      }
      
      // ==========================================
      // MEVCUT LAZER VE MORS GÖNDERME MANTIĞIN (DOKUNULMADI)
      // ==========================================
      char sinyalTuru = gelenKomut[0]; // 'K' veya 'U'
      
      // Tire işaretinin konumunu bulup süreyi ve harfi ayırıyoruz
      int tireIndeksi = gelenKomut.indexOf('-');
      if (tireIndeksi != -1) { // Güvenlik kontrolü
        int aktifSure = gelenKomut.substring(1, tireIndeksi).toInt(); // ms süresi
        gonderilecekHarf = gelenKomut.substring(tireIndeksi + 1)[0]; // Aktif harf
        
        if (sinyalTuru == 'K' || sinyalTuru == 'U') {
          // 1. ADIM: Lazeri söndür (Nano kronometreyi başlatsın)
          digitalWrite(laserPin, LOW);
          
          // Nano'nun sönme anını kararlı yakalaması için küçük bir avans
          delay(50); 
          
          // 2. ADIM: Tam karanlığın ortasındayken harfi SPI ile fırlat!
          digitalWrite(SS, LOW);
          SPI.transfer(gonderilecekHarf);
          digitalWrite(SS, HIGH);
          
          // Kalan süreyi tamamla (Örn: 300ms ise 250ms daha kapalı kalır)
          if (aktifSure > 50) {
            delay(aktifSure - 50);
          }
          
          // 3. ADIM: Lazeri geri aç (Nano kronometreyi durdursun)
          digitalWrite(laserPin, HIGH);
        }
      }
    }
  }
}