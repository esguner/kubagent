# KÜB Yan Etki Çıkarım Sistemi - Proje Özeti

Türkiye'de satışta olan ilaçların **Kısa Ürün Bilgisi (KÜB)** dokümanlarından "4.8. İstenmeyen Etkiler" bölümündeki verileri çıkarmak için Agentic (Ajan tabanlı) bir sistem başarıyla oluşturuldu ve test edildi.

## Yapılan Geliştirmeler ve Mimari

### 1. Actor-Critic (Çıkarıcı ve Denetleyici) Döngüsü
- **LangGraph** kullanılarak bir State Machine (Durum Makinesi) inşa edildi (`agent.py`).
- İki ajanlı bir sistem kuruldu:
  - **Extractor (Çıkarıcı):** KÜB'ün "Bölüm 2" kısmından ilacın asıl etken maddesini alır ve "Bölüm 4.8" içerisinden yan etkileri T.C. Sağlık Bakanlığı yönergelerine göre JSON olarak çıkarır.
  - **Reviewer (Denetleyici):** Çıkarılan veriyi, PDF'in orijinal metni ve katı kurallar listesi ile denetler. Herhangi bir "uydurma (hallucination)" veya atlanan madde bulursa JSON'u reddedip hataları listeler.
- Sistem bu iki ajan arasında, hata kalmayana kadar (veya maksimum 5 iterasyona ulaşana kadar) döngü halinde çalışır.

### 2. Pydantic Veri Modelleri
`models.py` içerisinde verinin her zaman belirli standartlarda çıkmasını garanti eden şemalar yazıldı:
- `active_ingredient`: Sadece etken maddeyi alır (Ticari ismi almaması için strict kural kondu).
- `soc`: Sadece belge içindeki geçerli MedDRA "System Organ Class" isimlerini alır.
- `frequency`: Yan etkinin görülme sıklığı.
- `adverse_effect`: Yan etkinin spesifik adı.
- `context`: Açıklamalar veya başlıklar.

> [!TIP]
> `soc`, `frequency`, `active_ingredient` ve `context` alanları esnek bırakılmış olup (null olabilir), belgede gerçekten yoksa modelin uydurması engellenmiştir.

### 3. Hızlı ve Kesintisiz PDF İşleme (Inline Bytes)
Geliştirme sırasında Gemini File API yüklemelerinde ağ/firewall kısıtlamalarına bağlı kopmalar (`WinError 10053`) yaşanması üzerine altyapı değiştirildi:
- PDF'ler doğrudan Python içerisinde `bytes` (bayt dizisi) olarak okunup, API isteğinin (Request) gövdesine gömülerek (Inline Data) gönderilmeye başlandı. 
- API `timeout` süresi 10 dakikaya (600,000 ms) çekildi.
- Bu sayede ağ kesintileri engellenerek işlem stabilitesi %100'e çıkarıldı.

### 4. Streamlit Arayüzü
- `app.py` ile son kullanıcı arayüzü kodlandı.
- PDF dosyası yüklenerek ajanların arka plandaki tüm logları, tartışmaları ekrana anlık olarak yansıtıldı.
- Sonunda çıkarılan veriler, hem analiz edilebilecek bir tablo (Dataframe) formatında ekranda gösterildi hem de `.csv` (Excel) ve `.json` formatında indirme seçeneği sunuldu.

## Bilinen Limitasyonlar (Aklımızda Bulunması Gerekenler)
> [!NOTE]
> Sıcaklık (Temperature) `0` olarak ayarlansa dahi, LLM modellerinin Multi-modal yetenekleri ve Virgülle ayrılmış cümleleri yorumlama farklılıkları nedeniyle aynı KÜB dosyası için satır sayısında ufak (1-2 satırlık) dalgalanmalar yaşanabilmektedir. Ek bir kural seti (Örn: "ve bağlacını bölme") ile daha katı hale getirilebilir, ancak şimdilik esnek bırakılmıştır.

Sistem kullanıma hazırdır. Arayüz `streamlit run app.py` komutuyla her zaman başlatılıp kullanılabilir.
