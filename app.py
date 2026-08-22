import streamlit as st
import os, math, re
from groq import Groq
from pydub import AudioSegment

st.set_page_config(page_title="Kawish AI Captioner", page_icon="🎙️")
st.title("🎙️ Kawish AI Mobile Captioner")

GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)

uploaded_file = st.file_uploader("موبائل سے آڈیو فائل منتخب کریں", type=["mp3", "m4a", "wav", "aac"])

def clean_text(text):
    text = text.strip()
    
    # فالتو نام اور یوٹیوب کریڈٹس کا مکمل خاتمہ
    bad_phrases = [
        r"translated by", r"subtitles by", r"amara\.org", r"thank you for watching",
        r"ravindra singh", r"rd shahbaz", r"kumar", r"like and subscribe", r"copyright",
        r"captioned by", r"subscribe to my channel", r"bye", r"thanks for watching"
    ]
    
    for pattern in bad_phrases:
        if re.search(pattern, text, re.IGNORECASE):
            return ""
            
    # اگر صرف 2 یا اس سے کم حروف کا جملہ ہو تو ختم کر دیں
    if len(text) < 3:
        return ""
        
    return text

def format_time(seconds):
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{ms:03d}"

if uploaded_file and st.button("Generate SRT ⚡"):
    with st.spinner("آڈیو پروسیس ہو رہی ہے، براہ کرم انتظار کریں..."):
        temp_path = f"temp_{uploaded_file.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        try:
            audio = AudioSegment.from_file(temp_path)
            total_duration = len(audio)
            
            # آڈیو کو 3 منٹ کے چھوٹے ٹکڑوں میں کاٹیں تاکہ AI کا دھیان بالکل نہ بھٹکے
            CHUNK_MS = 3 * 60 * 1000
            num_chunks = math.ceil(total_duration / CHUNK_MS)
            all_segments = []

            for i in range(num_chunks):
                chunk = audio[i*CHUNK_MS : min((i+1)*CHUNK_MS, total_duration)]
                chunk_path = f"chunk_{i}.mp3"
                chunk.export(chunk_path, format="mp3", bitrate="128k")

                with open(chunk_path, "rb") as file:
                    # متبادل ترجمہ طریقہ جو بغیر ناموں کے صحیح ترجمہ تیار کرتا ہے
                    transcription = client.audio.translations.create(
                        file=(f"chunk_{i}.mp3", file.read()),
                        model="whisper-large-v3",
                        temperature=0.0,
                        response_format="verbose_json"
                    )

                time_offset = (i * CHUNK_MS) / 1000.0
                for seg in getattr(transcription, 'segments', []):
                    seg['start'] += time_offset
                    seg['end'] += time_offset
                    all_segments.append(seg)

                if os.path.exists(chunk_path): os.remove(chunk_path)

            srt_content = ""
            count = 1
            for seg in all_segments:
                start, end = format_time(seg['start']), format_time(seg['end'])
                txt = clean_text(seg['text'])
                if txt:
                    srt_content += f"{count}\n{start} --> {end}\n{txt}\n\n"
                    count += 1

            if os.path.exists(temp_path): os.remove(temp_path)

            if srt_content.strip():
                st.success("🎉 .SRT فائل مکمل ترجمے کے ساتھ تیار ہے!")
                st.download_button("📥 Download .SRT File", srt_content, file_name=f"{os.path.splitext(uploaded_file.name)[0]}.srt", mime="text/plain")
            else:
                st.error("آڈیو میں سے کوئی واضح آواز نہیں مل سکی۔ براہ کرم دوبارہ کوشش کریں۔")

        except Exception as e:
            st.error(f"Error: {e}")
