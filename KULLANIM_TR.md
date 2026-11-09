# GlomQuant kullanım kılavuzu

## Amaç ve desteklenen ortam

GlomQuant, sıçan böbreği histoloji görüntülerindeki iki boyutlu glomerül profili adaylarını bulur ve sayar. İşaretler QuPath'te kontrol edilebilir. Bütün böbreğin gerçek nefron sayısını ölçmez. Araştırma amaçlıdır. İnsan görüntüleri, başka organlar, boyamalar ve tarayıcılar için başarı iddiası yoktur.

Bu paket Windows 10/11 x64 ve işlemciyle çalışma için hazırlanmıştır; ayrı ekran kartı gerekmez. Python 3.11.9 çalıştırıcısı pakette bulunur. İlk kurulumda internet ve diskte birkaç gigabayt boş alan gerekir. Bellek gereksinimi ve desteklenen donanım aralığı başka bilgisayarda ölçülmemiştir. macOS, Linux, Windows ARM ve çevrimdışı ilk kurulum bu dağıtımda test edilmemiştir.

## Kurulum ve başlatma

ZIP'in tamamını yazılabilir yerel bir klasöre çıkarın. `1_KUR.cmd` dosyasına çift tıklayın. Bağımlılıklar sabit sürümleriyle ayrı `.venv` ortamına kurulur. Mevcut Python kurulumları değiştirilmez. Kurulum sonunda beş küçük görüntünün beklenen model çıktıları kontrol edilir; uyuşmazlık olursa analiz başlatılmaz. Bu durumda kayıtları koruyun; model veya eşik değiştirerek kontrolü geçirmeye çalışmayın.

`2_ORNEK_KONTROL.cmd` bu kontrolü tekrarlar. `3_BASLAT.cmd` uygulamayı açar. Slaytı seçin, analizi başlatın ve bitmesini bekleyin. Analiz sırasında pencere kapatılmaz. Aynı slaytın kimliği ve tamamlanmış sonuç dosyaları uyuşuyorsa kayıtlı sonuç açılır; yeniden hesaplama yapılmaz. Süre alanı eski kayıt yeniden açıldığında yeni analiz süresi olarak yorumlanmaz. Klasör kurulumdan sonra taşındıysa kurulumu yeni konumda yeniden çalıştırın.

## Çıktılar ve QuPath

Sonuçlar `Yerel uygulama verileri/GlomQuant/results` altında tutulur; uygulamadaki **Sonuç dosyalarını aç** düğmesi doğru klasörü açar. Her slayt dosya içeriğinin kimliğiyle kaydedilir. İlk çıktı değiştirilmez. Sonuç klasöründe:

- `MODEL_REVIEW.geojson`: QuPath'te açılacak, kimlik numaralı son otomatik kutular.
- `detections_filtered.csv`: son kutular, koordinatlar ve güven değerleri.
- `detections_raw.csv` ve `detections_nms.csv`: birleştirme öncesi/sonrası kutular.
- `filter_audit.json`: tekrar filtresinin kaldırdığı kutular ve gerekçeleri.
- `run_config.json` ve `completion.json`: model/slayt kimliği, sabit ayarlar, sayılar, zaman ve çıktı dosyalarının kimlikleri.

QuPath ayrı kurulur: https://qupath.github.io/ . Aynı orijinal `.svs` dosyasını açın. **File → Object data → Import objects** komutuyla `MODEL_REVIEW.geojson` dosyasını içe aktarın. Menü adları QuPath sürümüne göre küçük farklılık gösterebilir. Koordinatlar orijinal görüntünün tam çözünürlük piksel koordinatlarıdır; yeniden boyutlandırılmış veya kırpılmış farklı görüntüye uygulanmaz. İlk model kutularını koruyun; düzeltmeleri ayrı QuPath projesi/kayıt ve ayrı GeoJSON olarak kaydedin. İki araştırmacı ilk dosyanın ayrı kopyalarını kullanmalı ve birbirinin kararlarını görmeden kontrol etmelidir.

## Örnek kontrolü ve tam slayt denemesi

Pakette, arşivdeki 59479 slaytından beş kayıpsız görüntü parçası ve önceki 14 kutunun konum/güven kayıtları bulunur. Bu filtre ayarı slaytıdır; bağımsız doğrulama değildir. Örnek kontrolü yalnız çalıştırma ortamının eski çıktılarla uyumunu gösterir. Bütün slaytın doğruluğunu göstermez.

Tam slayt için arşivdeki 59614 numaralı görüntü kullanılabilir. Kaynak koleksiyon: https://dbarchive.biosciencedbc.jp/data/open-tggates-pathological-images/LATEST/images/phorone/Kidney/ . Aynı kaynak dosyanın kimliği ve önceki otomatik 768 kutu referansı `examples/full_slide_reference.json` dosyasındadır. Orijinal slayt dosyası büyük olduğundan pakete eklenmemiştir. Aynı slaytın başka sürümü veya aynı adla farklı bir dosya aynı örnek değildir. 768 sayısı uzman tarafından doğrulanmış gerçek glomerül sayısı değildir. Sonuç farklıysa ayar değiştirmeyin; kontrol kayıtlarını inceleyin.

## Sabit yöntem ve sınırlılıklar

YOLO11n, yerel olarak yalnız 59477 slaytında 484 görüntü parçasıyla 20 döngü eğitilmiştir. Eğitim sırasında aynı veri doğrulama için de kullanılmıştır; eğitim doğrulama ölçütleri bağımsız test değildir. Filtre 59479 üzerinde ayarlanmıştır. Daha sonra eklenen beş geçici kontur eğitim referansına katılmaz. Bu iki slayt geliştirme içindir.

Güven eşiği 0,10; görüntü parçası 1024 piksel; kaydırma 768 piksel; model girdisi 640 piksel; model kutu birleştirme eşiği 0,70; tam slayt kutu birleştirme eşiği 0,50'dir. Ardından kesişim/küçük kutu alanı **0,50'den büyükse**, güven puanına göre fazladan kutu kaldırılır. Eşit güven durumunda düşük kutu kimliği önce gelir. Renk dönüşümü ve işlemci seçimi önceki motorla aynıdır. Doku veya medulla dışlaması yapılmaz. Ayarlar kullanıcı ekranından değiştirilmez.

Bu sürümün farklı bilgisayarda kurulumu ve tam slayt çıktısı henüz onaylanmamıştır. Bu kontrol tamamlanmadan yazılımın bağımsız kullanıcılarca doğrulandığı veya her bilgisayarda çalıştığı söylenmez.

## Dosyalar ve lisanslar

Kod ve model dağıtımı AGPL-3.0-or-later koşullarıyla hazırlanmıştır; tam metin `LICENSE` dosyasındadır. Üçüncü taraf bileşenler kendi lisanslarıyla kullanılır. Örnek histoloji görüntüleri ve anotasyon verileri kod lisansından ayrı olarak Open TG-GATEs kaynak ve paylaşım koşullarına tabidir; `licenses/DATA_NOTICE.md` dosyasına bakın. Veri dosyalarının lisansı yeniden adlandırılmaz. Görüntüler analiz sırasında uzak sunucuya gönderilmez; kurulum yalnız yazılım paketlerini indirir. GitHub veya Zenodo yayını bu paket hazırlanırken yapılmamıştır.
