from typing import TypedDict, Optional
from google import genai
from google.genai import types
from models import ExtractionResult, ReviewReport
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv

load_dotenv()

# Initialize Gemini Client with extended timeout (in milliseconds)
client = genai.Client(http_options={'timeout': 600000})

try:
    with open("kompakt_kilavuz.txt", "r", encoding="utf-8") as f:
        KILAVUZ_KURALLARI = f.read()
except FileNotFoundError:
    KILAVUZ_KURALLARI = "Kurallar dosyası bulunamadı."

EXTRACTOR_SYSTEM_PROMPT = f"""You are a strict pharmacovigilance data extraction specialist.

GÖREVİN:
1. İlacın ETKEN MADDESİNİ (active_ingredient) belgenin '2. KALİTATİF VE KANTİTATİF BİLEŞİM' bölümünden bularak çıkar (Eğer çoklu etken madde varsa aralarına virgül koyarak yaz. Örn: 'Dekstroz monohidrat, Sodyum klorür'). İlacın ticari adını (örn: %5 Dekstroz Laktatlı Ringer Solüsyonu) etken madde olarak YAZMA.
2. YAN ETKİLERİ ise KESİNLİKLE VE YALNIZCA '4.8. İstenmeyen Etkiler' başlığı altındaki metinlerden ve tablolardan çıkar. 

ÇOK ÖNEMLİ KISITLAMA: 
Yan etkileri ararken belgenin başka hiçbir bölümünü (örn: 4.4 Özel Uyarılar veya 4.9 Doz Aşımı) KESİNLİKLE dikkate alma! Sadece 4.8 bölümündeki semptomları çıkar.

AŞAĞIDAKİ T.C. SAĞLIK BAKANLIĞI KILAVUZ KURALLARINA HARFİYEN UYMALISIN:
{KILAVUZ_KURALLARI}

CRITICAL RULES:
- STRICT EXTRACTION: Do NOT invent, translate, or categorize data using your own medical knowledge. Only use the text provided.
- NO HALLUCINATED SOCs: If the text lists symptoms without an overarching System Organ Class (SOC) header, set "soc" to null.
- FLAT LIST: One record per specific adverse effect. Flatten comma-separated lists into individual records.
- EXCLUDE HEADERS: Do NOT extract descriptive grouping headers (e.g., "Aşırı duyarlılık belirtileri", "Elektrolit bozuklukları", "İnfüzyon yeri reaksiyonları") as an adverse effect. Extract ONLY the actual symptoms below them, and put those headers into the "context" field.
- EXCLUDE PROSE: Skip introductory paragraphs, footnotes, and explanatory full sentences.
"""

REVIEWER_SYSTEM_PROMPT = f"""You are a strict, aggressive, and highly skeptical Pharmacovigilance QA Auditor.

Görevin, Çıkarım Ajanının (Extractor) '4.8 İstenmeyen Etkiler' bölümünden çıkardığı JSON verisini, orijinal PDF ile karşılaştırarak DENETLEMEK ve AÇIK BULMAKTIR. Çıkarım ajanı genellikle tembeldir ve detayları atlama eğilimindedir. Ona GÜVENME.

AŞAĞIDAKİ T.C. SAĞLIK BAKANLIĞI KILAVUZ KURALLARINI BİLİYORSUN VE BUNA GÖRE DENETİM YAPACAKSIN:
{KILAVUZ_KURALLARI}

KONTROL LİSTESİ:
1. Başka Bölüm İhlali: Çıkarılan herhangi bir yan etki '4.8 İstenmeyen Etkiler' dışındaki bir bölümden (örn 4.4 Özel Uyarılar) mi gelmiş? Eğer öyleyse raporla.
2. Eksik Veri: 4.8 bölümünde olup da JSON'a eklenmeyen (atlanan) tek bir yan etki bile var mı? Satır satır oku.
3. Hatalı Sınıflandırma: Frekans (Frequency) veya SOC yanlış eşleştirilmiş mi?
4. Uydurma (Hallucination): KÜB'de olmayan bir SOC veya Yan Etki JSON'a eklenmiş mi?
5. Başlık Hatası: "Aşırı duyarlılık", "Laboratuvar bulguları" gibi alt başlıklar "yan etki" olarak çıkarılmış mı? Bunlar context'te olmalıdır.

ÖNEMLİ: Kararını vermeden önce JSON'daki 'audit_reasoning' alanında SESLİ DÜŞÜN. Adım adım neler bulduğunu ve nerelerin eksik olduğunu anlat.
Eğer tüm veri %100 kusursuzsa ve KÜB 4.8 ile BİREBİR eşleşiyorsa is_perfect: true yap.
Eğer en ufak bir hata, eksik veya fazlalık varsa is_perfect: false yap ve hataları detaylıca 'errors_found' alanında açıkla.
"""

class AgentState(TypedDict):
    pdf_path: str
    pdf_bytes: Optional[bytes]
    extraction_result: Optional[ExtractionResult]
    review_report: Optional[ReviewReport]
    iteration: int
    max_iterations: int
    log: list[str]

def upload_pdf_node(state: AgentState):
    """Reads the PDF file as bytes (Bypassing File API network issues)"""
    log = state.get("log", [])
    if not state.get("pdf_bytes"):
        log.append(f"Reading PDF: {state['pdf_path']} locally...")
        with open(state["pdf_path"], "rb") as f:
            pdf_bytes = f.read()
            
        log.append(f"PDF read complete. Size: {len(pdf_bytes)} bytes")
        return {"pdf_bytes": pdf_bytes, "log": log, "iteration": 0, "max_iterations": 5}
    return {}

def extractor_node(state: AgentState):
    """Extracts adverse effects using Gemini."""
    log = state.get("log", [])
    iteration = state.get("iteration", 0) + 1
    log.append(f"--- Extractor Agent Running (Iteration {iteration}) ---")
    
    # If there is a previous review report, add it to the prompt
    prompt = "Lütfen PDF dosyasındaki '4.8. İstenmeyen Etkiler' bölümünden yan etkileri çıkar."
    if state.get("review_report") and not state["review_report"].is_perfect:
        prompt += f"\n\nÖnceki çıkarımda hatalar bulundu. Denetleyici Raporu:\n{state['review_report'].errors_found}\n\nLütfen bu hataları düzelterek yeniden çıkarım yap."

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[
            types.Part.from_bytes(data=state["pdf_bytes"], mime_type="application/pdf"),
            prompt
        ],
        config=types.GenerateContentConfig(
            system_instruction=EXTRACTOR_SYSTEM_PROMPT,
            temperature=0.0,
            response_mime_type="application/json",
            response_schema=ExtractionResult,
        ),
    )
    
    result = response.parsed
    log.append(f"Extraction complete. Found {len(result.adverse_effects)} adverse effects.")
    
    return {"extraction_result": result, "iteration": iteration, "log": log}

def reviewer_node(state: AgentState):
    """Reviews the extraction result."""
    log = state.get("log", [])
    log.append("--- Reviewer Agent Running ---")
    
    extraction_json = state["extraction_result"].model_dump_json(indent=2)
    prompt = f"Lütfen PDF belgesini ve aşağıdaki çıkarılmış JSON verisini incele.\n\nÇIKARILAN JSON:\n{extraction_json}"
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[
            types.Part.from_bytes(data=state["pdf_bytes"], mime_type="application/pdf"),
            prompt
        ],
        config=types.GenerateContentConfig(
            system_instruction=REVIEWER_SYSTEM_PROMPT,
            temperature=0.0,
            response_mime_type="application/json",
            response_schema=ReviewReport,
        ),
    )
    
    report = response.parsed
    if report.is_perfect:
        log.append("Reviewer: ✅ JSON is perfect. No errors found.")
    else:
        log.append(f"Reviewer: ❌ Errors found: {report.errors_found}")
        
    return {"review_report": report, "log": log}

def router_node(state: AgentState):
    """Decides whether to loop back to the extractor or end."""
    report = state.get("review_report")
    iteration = state.get("iteration", 0)
    max_iterations = state.get("max_iterations", 5)
    
    if report.is_perfect:
        return "end"
    if iteration >= max_iterations:
        state["log"].append("Max iterations reached. Ending with current best result.")
        return "end"
    return "extract"

def build_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("upload", upload_pdf_node)
    workflow.add_node("extract", extractor_node)
    workflow.add_node("review", reviewer_node)
    
    workflow.add_edge(START, "upload")
    workflow.add_edge("upload", "extract")
    workflow.add_edge("extract", "review")
    
    workflow.add_conditional_edges(
        "review",
        router_node,
        {
            "extract": "extract",
            "end": END
        }
    )
    
    return workflow.compile()
