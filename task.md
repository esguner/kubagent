# KÜB Yan Etki Çıkarım Ajanı - Görev Listesi

- `[x]` **1. Proje Yapılandırması**
  - Gerekli kütüphanelerin (`langgraph`, `google-genai`, `streamlit`, `pydantic`) `requirements.txt` dosyasına eklenmesi.
  - Ortam değişkenleri (`.env`) için şablon oluşturulması.

- `[x]` **2. Veri Modellerinin (Pydantic) Tanımlanması**
  - `AdverseEffect` ve `ExtractionResult` sınıflarının JSON şemasına uygun şekilde oluşturulması.
  - `ReviewReport` modelinin Denetleyici ajan için tasarlanması.

- `[x]` **3. LLM ve Prompt Entegrasyonu**
  - Gemini 2.5 Flash için API bağlantı fonksiyonunun yazılması (Native PDF File API desteği ile).
  - Çıkarım Ajanı (Extractor) Sistem Promptunun kılavuz kurallarına ve eski koda sadık kalarak oluşturulması.
  - Denetleyici Ajan (Reviewer) Sistem Promptunun oluşturulması.

- `[x]` **4. LangGraph Mimarisinin (State Machine) Kurulması**
  - Ajanların paylaştığı durum (State) sınıfının yazılması.
  - Düğümlerin (Extractor Node, Reviewer Node) yazılması.
  - Yönlendirme (Conditional Edges) mantığının kurulması (Hata varsa geri dön, yoksa bitir).

- `[x]` **5. Streamlit Arayüzünün Geliştirilmesi**
  - PDF yükleme alanının yapılması.
  - Ajanların kendi aralarındaki konuşmalarının/döngülerinin ekranda anlık (log şeklinde) gösterilmesi.
  - Final JSON çıktısının ve indirilebilir tablo (Excel/CSV) versiyonunun sunulması.

- `[x]` **6. Test ve Doğrulama**
  - Klasöre eklenecek örnek KÜB dokümanları ile sistemin çalıştırılması.
  - Hataların gözlemlenip promptların/mantığın iyileştirilmesi.
