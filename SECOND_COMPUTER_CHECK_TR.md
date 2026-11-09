# İkinci bilgisayar kontrolü

Bu belge kurulum testi içindir; araştırmacının glomerül kararlarını toplamaz.

1. Paketin ZIP dosyasını diğer araştırmacının Windows x64 bilgisayarına götürün. Kendi bilgisayarınızdaki `.venv` ortamını götürmeyin.
2. ZIP'i çıkarın, `1_KUR.cmd` dosyasını çalıştırın. Python veya yönetici yetkisi gerektirmeden tamamlanıp tamamlanmadığını kaydedin.
3. `2_ORNEK_KONTROL.cmd` dosyasını çalıştırın; beş görüntüde beklenen 14 kutunun kontrolü geçmelidir.
4. `3_BASLAT.cmd` ile uygulamayı açın. Kaynak kimliği eşleşen 59614 slaytını seçip çalıştırın. Önceki otomatik sonuç 768 kutudur. Sayı tek başına yeterli değildir; CSV kutu konumları/güven değerleri ve filtre kararları da önceki kayıtla karşılaştırılmalıdır.
5. QuPath'te aynı slaytı açın, GeoJSON işaretlerini içe aktarın. Kutu kimliklerinin ve konumların görüntüyle örtüştüğünü kontrol edin. Otomatik dosyayı değiştirmeden araştırmacı düzeltmelerini ayrı kaydedin.
6. İşletim sistemi, bellek, işlemci, QuPath sürümü, kurulum sonucu, analiz süresi, hata mesajları ve kontrol kaydını saklayın. Bu bilgiler diğer bilgisayardan alınmadan test başarılı işaretlenmez.

Kontrol kayıtları: `%LOCALAPPDATA%/GlomQuant/kurulum.log`, `self_check.json`, sonuç klasöründeki `completion.json`, `run_config.json` ve otomatik CSV/GeoJSON dosyaları. Bu belgeler mevcut araştırmacı kararlarını içermez. Testte görülen tam slayt daha sonra kör değerlendirme yapılmış gibi sunulmaz.
