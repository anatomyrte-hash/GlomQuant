# Eğitim kökeni denetimi — 30 Eylül 2026

## Sonuç

Mevcut kayıtlar ve görüntü içerikleri, kullanılan pilot modelin yerel eğitim verisinin yalnız 59477'den oluştuğunu güçlü biçimde destekliyor. Beş değerlendirme slaytının (59487, 59489, 59491, 59494, 59496) bu yerel eğitim kümesine karıştığına dair bulgu yok. Bu sonuç klasör adına değil, ağırlık içindeki kayıt, eğitim ayarı, dosya listesi ve tüm eğitim görüntülerinin kaynak slaytla piksel karşılaştırmasına dayanır.

## Doğrulanan kanıt zinciri

1. Kullanılan best.pt dosyasının SHA256 özeti, beş slaytın çıkarımında kaydedilen model özetiyle aynıdır: 98e9ce2434a3839e4dad168a114f48227b704fdc135adebcaa4ad00a4a7853aa.
2. Ağırlık dosyasının içindeki metin kayıtları pilot_20ep ve pilot_train.yaml yolunu içerir. Dosya çalıştırılmadan, ZIP içindeki pickle işlemleri yalnız sözdizimsel olarak okunmuştur. Dış args.yaml aynı eğitim veri yoluna işaret eder.
3. pilot_train.yaml, GlomDetect_59477_centered/images klasörünü hem train hem val olarak tanımlar. Dolayısıyla eğitim sırasında raporlanan doğrulama ölçütleri bağımsız test sonucu değildir.
4. Manifestte 484 satır, görüntü klasöründe 484 eğitim görüntüsü vardır; listede olmayan ek veya eksik görüntü yoktur. Üretim özeti 242 pozitif ve 242 negatif karo, 721 kaynak glomerül bildirir.
5. Manifestteki koordinatlardan 59477.svs üzerinden 484 adet 1024×1024 görüntü yeniden oluşturuldu ve üretici betikteki varsayılan JPEG kalite 90 ile kaydedildi. Yeniden açılan RGB pikselleri mevcut 484 eğitim görüntüsünün TAMAMIYLA bire bir aynıdır: 484/484, en yüksek ortalama piksel farkı 0. Bu, mevcut eğitim görüntülerinin 59477 kaynaklı olduğunu içerik düzeyinde doğrular.
6. Altı veri sürümünün manifestleri ayrıca incelendi: 484, 2337, 2337, 2337, 792 ve 786 satır. Karo kimlikleri yalnız 59477 öneki taşır; beş değerlendirme slaytının kimlikleri bulunmadı. Bu diğer sürümlerin tamamına piksel denetimi uygulanmadı; kullanılan modelin işaret ettiği 484 görüntüye uygulandı.

## Kapsam sınırı

Bu denetim mevcut yerel dosyaları doğrular. Eğitim anında oluşturulmuş değişmez görüntü hash listesi bulunmadığından dosyaların geçmişte hiç değişmediğine ilişkin mutlak kanıt değildir. Başlangıç modeli yolo11n.pt olarak kayıtlıdır; bu başlangıç ağırlığının tüm önceki eğitim geçmişi bu denetimde doğrulanmadı. GNCnn ve U-Net farklı modellerdir; onların eğitim kökeni hakkında bu denetimden sonuç çıkarılmaz.

Yeni seri için “yerel pilot eğitim kümesinden ayrı beş hayvan” ifadesi mevcut kanıtlarla desteklenir. Bu, dış merkez doğrulaması veya farklı deney koşullarına genelleme anlamına gelmez. Model sonrası referans düzeltmeleri nedeniyle ilk kör sonuçlar ile ikincil analiz yine ayrı tutulmalıdır.

## Tekrar üretilebilir kayıtlar

- audit.json: ayarlar, dosya özetleri, altı manifestin özeti ve ağırlıktan okunan ilgili metin kayıtları.
- image_source_checks.json: 484 görüntünün dosya özeti ve piksel karşılaştırma sonucu.
- Kaynak SVS SHA256: f8148b3c2c7293fc95641549898e9e11de6762b4607db439557dad953751983c.

Kaynak dosyalar ve model değiştirilmedi; yeni eğitim yapılmadı.
