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
    margin-bottom: 10px;
    padding: 10px;
}
[data-testid="stChatMessage"]:nth-child(odd) {
    background-color: #f8f9fa;
    border-left: 4px solid #d32f2f;
}
[data-testid="stChatMessage"]:nth-child(even) {
    background-color: #e3f2fd;
    border-right: 4px solid #007bff;
    flex-direction: row-reverse;
    text-align: right;
}
[data-testid="stChatMessageAvatar"] {
    width: 35px !important;
    height: 35px !important;
}
[data-testid="stChatMessageAvatar"] img {
    width: 35px !important;
    height: 35px !important;
    object-fit: contain;
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
    except FileNotFoundError:
        return None
    except Exception:
        st.error("Lütfen daha sonra deneyiniz.")
        return ""
    return text

@st.cache_data(ttl=3600) 
def load_web_context(url):
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()
        return soup.get_text(separator=' ', strip=True)[:10000]
    except:
        return ""

pdf_context = load_pdf_context()
web_url = "https://odb.btu.edu.tr/" 
web_context = load_web_context(web_url)

base_instruction = """
Sen Bursa Teknik Üniversitesi (BTÜ) Ortak Dersler Bölümü asistanısın.

ÇOK ÖNEMLİ KONUŞMA KURALLARI:
1. **Tekrara Düşme:** Her mesajında "Merhaba ben ODB Asistanı" veya "Size yardımcı olmaktan memnuniyet duyarım" gibi giriş cümleleri KURMA. Bunu sadece ilk tanışmada söylemen yeterli.
2. **Doğrudan Cevap:** Kullanıcı bir şey sorduğunda doğrudan cevaba gir. Sanki karşında arkadaşın varmış gibi konuş ama saygıyı koru.
3. **Örnek:**
   - Kötü Cevap: "Merhaba! Ben Asistan. Ders kaydı şöyle yapılır..."
   - İyi Cevap: "Ders kaydını OBS sistemi üzerinden yapabilirsin. Tarihleri takvimden kontrol etmeyi unutma."
4. **Bilgi Kaynağı:**
   - Öncelikle sana verilen PDF verisini ve web sitesi bilgilerini kullan.
   - PDF'de olmayan genel konularda kendi genel bilgini kullan.
   - PDF'de veya web sitesinde olmayan çok teknik/resmi konularda uydurma, "Güncel duyuruları web sitesinden takip edebilirsin" de.
   - Cevaplarında asla "PDF verisine göre", "PDF'de bu bilgi yok", "Dosyayı kontrol ettim" gibi ifadeler KULLANMA. Bilgi sende zaten varmış gibi doğal konuş.
   - Eğer bilgi sende veya PDF içeriğinde yoksa, "PDF'de yok" demek yerine; "Bu konuda güncel duyuruları web sitesinden veya bölüm sekreterliğinden teyit etmen daha sağlıklı olabilir" gibi yardımcı bir dil kullan.
   - Cevaplarında asla "PDF'de şöyle yazıyor", "Dosyaya göre", "Belgeye göre" veya "Yazıyor" gibi ifadeler kullanma. Bilgi senin kendi bilginmiş gibi doğrudan söyle.
   - Birine bilgi veren canlı bir asistan gibi konuş. "Sistemde şöyle belirtilmiş" yerine "Şu yolu izlemelisin" de.
"""

final_instruction = base_instruction
if pdf_context:
    final_instruction += f"\n--- REHBER BİLGİLER ---\n{pdf_context[:25000]}\n"
if web_context:
    final_instruction += f"\n--- WEB SİTESİNDEN ANLIK BİLGİLER ---\n{web_context}\n"

if "messages" not in st.session_state:
    st.session_state.messages = []

bot_avatar = "https://depo.btu.edu.tr/img/sayfa//1691131553_33a20881d67b04f54742.png"
user_avatar = "👤"

for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user", avatar=user_avatar):
            st.markdown(msg["content"])
    else:
        with st.chat_message("assistant", avatar=bot_avatar):
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
                for m in st.session_state.messages:
                    messages_for_groq.append({"role": m["role"], "content": m["content"]})

                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages_for_groq,
                    temperature=0.7,
                )
                
                response_text = completion.choices[0].message.content
                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
            
            except Exception:
                st.error("Lütfen daha sonra deneyiniz.")

if len(st.session_state.messages) == 0:
    st.info("👋 Selam! BTÜ Ortak Dersler Bölümü hakkında bana soru sorabilirsin.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📝 Sosyal Seçmeli Dersler"):
            st.session_state.pending_prompt = "Ders kaydı nasıl yapılır?"
            st.rerun()
            
    with col2:
        if st.button("📅 Sınav tarihleri ne zaman?"):
            st.session_state.pending_prompt = "Sınav tarihleri ne zaman?"
            st.rerun()

   # with col3:
   #     if st.button("Eleştirel Düşünme Yöntemleri/Yapay Zeka Dersleri"):
   #         st.session_state.pending_prompt = "Eleştirel Düşünme Yöntemleri/Yapay Zeka Derslerini sisteminizde göremiyorum?"
   #         st.rerun()
