from pydantic import BaseModel, Field
from typing import List, Optional

class AdverseEffect(BaseModel):
    active_ingredient: Optional[str] = Field(
        description="Yan etkinin ait olduğu spesifik etken madde. (Sadece kombinasyon ilaçlarında, 4.8 bölümünde yan etkiler etken maddelere göre ayrılmışsa doldurulur. Tek etken maddeli ürünlerde veya ayrım yapılmamışsa null olmalıdır.)"
    )
    soc: Optional[str] = Field(
        description="System Organ Class (SOC) adı. Metinde SOC başlığı yoksa uydurma, null yap. Sadece KÜB'de yazan MedDRA kategorilerini kullan."
    )
    frequency: Optional[str] = Field(
        description="Frekans etiketi (Örn: 'Yaygın', 'Bilinmiyor'). Eğer semptom için frekans belirtilmemişse null dön."
    )
    adverse_effect: str = Field(
        description="Spesifik yan etki adı. Parantez içi detayları koru."
    )
    context: Optional[str] = Field(
        description="Metinde geçen özel durumlar, gruplama başlıkları vb. (Örn: 'İnfüzyon yeri reaksiyonları', 'Aşırı duyarlılık belirtileri'). Standart ise null dön."
    )

class ExtractionResult(BaseModel):
    adverse_effects: List[AdverseEffect] = Field(
        description="KÜB 4.8 bölümünden çıkarılan tüm yan etkilerin listesi."
    )

class ReviewReport(BaseModel):
    audit_reasoning: str = Field(
        description="KARAR VERMEDEN ÖNCE SESLİ DÜŞÜN (Chain of Thought): Çıkarıcı ajanın tembel ve dikkatsiz olduğunu varsay. KÜB 4.8 bölümündeki metni satır satır incele. JSON'da atlanmış semptom var mı? Uydurulmuş veya başka bölümden alınmış SOC/Frekans var mı? Adım adım denetim mantığını buraya yaz."
    )
    is_perfect: bool = Field(
        description="Çıkarılan JSON, orijinal KÜB metni ve kurallarla BİREBİR uyumlu mu? Herhangi bir atlanan yan etki, yanlış frekans, yanlış SOC veya 4.8 haricinden çıkarılmış veri var mı?"
    )
    errors_found: Optional[str] = Field(
        description="Eğer is_perfect False ise, bulunan hataları detaylı olarak açıkla. Örn: 'Aşağıdaki yan etki unutulmuş: XYZ', 'Şu SOC yanlış girilmiş...'"
    )
