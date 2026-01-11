import streamlit as st
from groq import Groq
from PyPDF2 import PdfReader

st.set_page_config(page_title="BTÜ ODB Asistanı", layout="centered")

st.markdown("""
<style>
/* Gereksiz öğeleri gizle */
header, footer, .stDeployButton, [data-testid="stStatusWidget"], button[title="View fullscreen"] {
    display: none !important;
}
/* Sohbet balonları tasarımı */
[data-testid="stChatMessage"] {
    border-radius: 15px;
    margin-bottom: 10px;
    padding: 10px;
}
/* Asistan mesajı */
[data-testid="stChatMessage"]:nth-child(odd) {
    background-color: #f8f9fa;
    border-left: 4px solid #d32f2f;
}
/* Kullanıcı mesajı */
[data-testid="stChatMessage"]:nth-child(even) {
    background-color: #e3f2fd;
    border-right: 4px solid #007bff;
    flex-direction: row-reverse;
    text-align: right;
}
/* --- LOGO BOYUTU AYARI (YENİ) --- */
/* Avatar kutusunu ve içindeki resmi küçült */
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

pdf_context = load_pdf_context()

base_instruction = """
Sen Bursa Teknik Üniversitesi (BTÜ) Ortak Dersler Bölümü asistanısın.

ÇOK ÖNEMLİ KONUŞMA KURALLARI:
1. **Tekrara Düşme:** Her mesajında "Merhaba ben ODB Asistanı" veya "Size yardımcı olmaktan memnuniyet duyarım" gibi giriş cümleleri KURMA. Bunu sadece ilk tanışmada söylemen yeterli.
2. **Doğrudan Cevap:** Kullanıcı bir şey sorduğunda doğrudan cevaba gir. Sanki karşında arkadaşın varmış gibi konuş ama saygıyı koru.
3. **Örnek:**
   - Kötü Cevap: "Merhaba! Ben Asistan. Ders kaydı şöyle yapılır..."
   - İyi Cevap: "Ders kaydını OBS sistemi üzerinden yapabilirsin. Tarihleri takvimden kontrol etmeyi unutma."
4. **Bilgi Kaynağı:**
   - Öncelikle sana verilen PDF verisini kullan.
   - PDF'de olmayan genel konularda (Nasılsın, yapay zeka nedir vb.) kendi genel bilgini kullan.
   - PDF'de olmayan çok teknik/resmi konularda uydurma, "Güncel duyuruları web sitesinden takip edebilirsin" de.
5. **PDF'den Bahsetme:** Cevaplarında asla "PDF verisine göre", "PDF'de bu bilgi yok", "Dosyayı kontrol ettim" gibi ifadeler KULLANMA. Bilgi sende zaten varmış gibi doğal konuş.
6. **Bilmeme Durumu:** Eğer bilgi sende veya PDF içeriğinde yoksa, "PDF'de yok" demek yerine; "Bu konuda güncel duyuruları web sitesinden veya bölüm sekreterliğinden teyit etmen daha sağlıklı olabilir" gibi yardımcı bir dil kullan.
7. **Tekrara Düşme:** Giriş cümleleri (Merhaba ben asistan vb.) kurma, doğrudan soruya cevap ver.
8. **Samimiyet:** Saygılı ama arkadaş canlısı bir üslup kullan.
9. **KAYNAK BELİRTME:** Cevaplarında asla "PDF'de şöyle yazıyor", "Dosyaya göre", "Belgeye göre" veya "Yazıyor" gibi ifadeler kullanma. Bilgi senin kendi bilginmiş gibi doğrudan söyle.
10. **DOĞAL ÜSLUP:** Birine bilgi veren canlı bir asistan gibi konuş. "Sistemde şöyle belirtilmiş" yerine "Şu yolu izlemelisin" de.
11. **BİLGİ SINIRI:** Eğer bir bilgi sende veya sana sunulan metinde yoksa, "PDF'de yok" demek yerine "Bu detay hakkında güncel bilgiyi web sitesinden kontrol edebilirsin" de.

Aşağıdaki PDF verisini referans al:
"""

final_instruction = base_instruction
if pdf_context:
    final_instruction += f"\n--- PDF İÇERİĞİ ---\n{pdf_context[:30000]}\n--- SON ---\n"
else:
    final_instruction += "\n(Sistemde PDF yok, genel bilgini kullan.)\n"

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
                # Groq için mesaj geçmişini hazırla
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
        if st.button("📅 Akademik Takvim"):
            st.session_state.pending_prompt = "Sınav tarihleri ne zaman?"
            st.rerun()

    with col3:
        if st.button("Eleştirel Düşünme Yöntemleri/Yapay Zeka Dersleri"):
            st.session_state.pending_prompt = "Eleştirel Düşünme Yöntemleri/Yapay Zeka Derslerini sisteminizde göremiyorum?"
            st.rerun()


