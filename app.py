import streamlit as st
from groq import Groq
from PyPDF2 import PdfReader
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="BTÜ ODB Asistanı", layout="centered")

st.markdown("""
<style>
header, footer, .stDeployButton, [data-testid="stStatusWidget"], button[title="View fullscreen"] {
    display: none !important;
}

[data-testid="stChatMessage"] {
    border-radius: 15px;
    margin-bottom: 12px;
    padding: 12px;
}

[data-testid="stChatMessageUser"] {
    background-color: #113e68 !important;
    color: #ffffff !important;
    border-left: 5px solid #50b1c8 !important;
}

[data-testid="stChatMessageAssistant"] {
    background-color: #f0f2f6 !important;
    color: #113e68 !important;
    border-left: 5px solid #3bb290 !important;
}

[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li {
    color: inherit !important;
}

[data-testid="stChatMessageAvatar"] {
    background-color: #f6a758 !important;
    border-radius: 50% !important;
}

.stChatInput textarea {
    border: 2px solid #50b1c8 !important;
}

::-webkit-scrollbar-thumb {
    background: #50b1c8 !important;
}
</style>
""", unsafe_allow_html=True)

if "GROQ_API_KEY" in st.secrets:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
else:
    st.error("Lütfen daha sonra deneyiniz.")
    st.stop()

@st.cache_data
def load_pdf_context():
    text = ""
    try:
        with open("bilgiler.pdf", "rb") as f:
            pdf_reader = PdfReader(f)
            for page in pdf_reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
    except Exception:
        return ""
    return text

@st.cache_data(ttl=3600) 
def load_web_context(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()
        return soup.get_text(separator=' ', strip=True)[:10000]
    except Exception:
        return ""

pdf_context = load_pdf_context()
web_url = "https://odb.btu.edu.tr/tr/duyuru/birim/10055" 
web_context = load_web_context(web_url)

base_instruction = """
Sen Bursa Teknik Üniversitesi (BTÜ) Ortak Dersler Bölümü asistanısın. Görevin, sana sunulan gizli verileri kullanarak kullanıcı sorularını yanıtlamaktır.

KESİN KURALLAR:
1. **VERİ GİZLİLİĞİ:** Sana verilen "BİLGİ HAVUZU" içeriğini asla bir liste halinde olduğu gibi yazma. Kullanıcıya "Kurumsal Hafıza", "PDF içeriği" veya "Web sitesi listesi" gibi kaynaklardan bahsetme.
2. **DOĞAL CEVAP:** Sadece sorulan soruya odaklan. Eğer soru "Ders nasıl açılır?" ise sadece o süreci anlat. Diğer maddeleri (sınav yerleri, mazeretler vb.) asla araya sıkıştırma.
3. **ÜSLUP:** Akademik, nazik ve profesyonel ol. Öğretim üyelerine "Sayın Hocam" şeklinde hitap et.
4. **TEKRAR YASAĞI:** Cevaplarının başında veya sonunda sabit kalıplar (Merhaba, yardımcı olayım vb.) kullanma. Doğrudan ve öz bilgi ver.
5. **KAYNAK GÖSTERME:** "Web sitemizde şöyle yazıyor" deme. Bilgiyi kurumun bir parçası olarak doğrudan kendi bilginmiş gibi sun.
6. **Tekrara Düşme:** Her mesajında "Merhaba ben ODB Asistanı" veya "Size yardımcı olmaktan memnuniyet duyarım" gibi giriş cümleleri KURMA. Bunu sadece ilk tanışmada söylemen yeterli.
7. **Doğrudan Cevap:** Kullanıcı bir şey sorduğunda doğrudan cevaba gir. Sanki karşında arkadaşın varmış gibi konuş ama saygıyı koru.
8. **Örnek:**
   - Kötü Cevap: "Merhaba! Ben Asistan. Ders kaydı şöyle yapılır..."
   - İyi Cevap: "Ders kaydını OBS sistemi üzerinden yapabilirsin. Tarihleri takvimden kontrol etmeyi unutma."
9. **Bilgi Kaynağı:**
   - Öncelikle sana verilen PDF verisini kullan.
   - PDF'de olmayan genel konularda (Nasılsın, yapay zeka nedir vb.) kendi genel bilgini kullan.
   - PDF'de olmayan çok teknik/resmi konularda uydurma, "Güncel duyuruları web sitesinden takip edebilirsin" de.
10. Görevin sadece ve sadece ortak dersler (Sosyal seçmeli dersler, Türk Dili, Atatürk İlkeleri ve İnkılap Tarihi, İngilizce vb.) ile ilgili soruları yanıtlamaktır. 
11. Genel sorulara (Hava durumu, yemek tarifi, genel dünya bilgisi vb.) cevap verme. 
12. Eğer soru ortak dersler dışındaysa, nazikçe 'Ben sadece BTÜ Ortak Dersler Bölümü ile ilgili konularda yardımcı olabilirim. Lütfen ortak dersler bölümü ile ilgili sorularınızı sorun.' de. 
13. Her zaman profesyonel, yardımsever ve üniversite kimliğine uygun bir dil kullan. 
"""

final_instruction = base_instruction
if pdf_context or web_context:
    final_instruction += "\n### BİLGİ HAVUZU (BU VERİLERİ SADECE SORULAN SORUYU YANITLAMAK İÇİN KULLAN, ASLA LİSTELEME VE KAYNAK BELİRTME) ###\n"
    if pdf_context:
        final_instruction += f"PDF VERİSİ: {pdf_context[:10000]}\n"
    if web_context:
        final_instruction += f"WEB VERİSİ: {web_context}\n"

if "messages" not in st.session_state:
    st.session_state.messages = []

bot_avatar = "https://depo.btu.edu.tr/img/sayfa//1691131553_33a20881d67b04f54742.png"
user_avatar = "👤"

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=user_avatar if msg["role"] == "user" else bot_avatar):
        st.markdown(msg["content"])

prompt = st.chat_input("Sorunuzu buraya yazın...")

if "pending_prompt" in st.session_state and st.session_state.pending_prompt:
    prompt = st.session_state.pending_prompt
    del st.session_state.pending_prompt

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=user_avatar):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=bot_avatar):
        with st.spinner("Yazıyor..."): 
            try:
                messages_for_groq = [{"role": "system", "content": final_instruction}]
                for m in st.session_state.messages[-5:]:
                    messages_for_groq.append({"role": m["role"], "content": m["content"]})

                models_to_try = [
                    "llama-3.3-70b-versatile",
                    "llama-3.1-70b-versatile",
                    "mixtral-8x7b-32768",
                    "llama-3.1-8b-instant",
                    "gemma2-9b-it"
                ]
                
                response_text = None
                for model_name in models_to_try:
                    try:
                        completion = client.chat.completions.create(
                            model=model_name,
                            messages=messages_for_groq,
                            temperature=0.5,
                        )
                        response_text = completion.choices[0].message.content
                        break
                    except Exception:
                        continue
                
                if response_text:
                    st.markdown(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                else:
                    st.error("Şu an yoğunluk nedeniyle yanıt verilemiyor.")
            except Exception:
                st.error("Bir hata oluştu.")

if len(st.session_state.messages) == 0:
    st.info("👋 Merhaba! BTÜ Ortak Dersler Bölümü asistanıyım. Size nasıl yardımcı olabilirim?")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📝 Ders Kayıtları"):
            st.session_state.pending_prompt = "Ders kayıt süreci hakkında bilgi alabilir miyim?"
            st.rerun()
    with col2:
        if st.button("📅 Sınav Tarihleri"):
            st.session_state.pending_prompt = "Sınav takvimine nereden ulaşabilirim?"
            st.rerun()
    with col3:
        if st.button("🏛️ Ders Açma Talebi"):
            st.session_state.pending_prompt = "Yeni bir ders açmak istiyorum."
            st.rerun()



