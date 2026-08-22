import streamlit as st
import os, math, re
from groq import Groq
from pydub import AudioSegment, effects

# ایپ کا فائنل نام
st.set_page_config(page_title="کاوش اے آئی کیپشن", page_icon="🎙️", layout="centered")
st.title("🎙️ کاوش اے آئی کیپشن")
st.caption("3,000 MB File Limit | Max 2 Lines Subtitles | Clean English Translation")

GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)

# 3,000MB Limit and file types
uploaded_file = st.file_uploader(
    "موبائل یا پی سی سے آڈیو/ویڈیو فائل منتخب کریں (حداکثر 3,000MB)", 
    type=["mp3", "m4a", "wav", "aac", "mp4", "mkv", "mov", "avi"]
)

def clean_text(text):
    text = text.strip()
    
    bad_patterns = [
        r"translated by", r"subtitles by", r"amara\.org", r"thank you for watching",
        r"ravindra singh", r"rd shahbaz", r"kumar", r"like and subscribe", r"copyright",
        r"captioned by", r"subscribe to my channel", r"bye", r"thanks for watching",
        r"translated urdu", r"clear english", r"realtor"
    ]
    
    for pattern in bad_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return ""
            
    if len(text) < 2:
        return ""
        
    return text

def format_time(seconds):
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{ms:03d}"

def split_text_into_max_two_lines(text, max_words_per_line=6):
    """جملوں کو 2 لائنوں پر تقسیم کرنے کے لیے"""
    words = text.split()
    if len(words) <= max_words_per_line:
        return text
    elif len(words) <= max_words_per_line * 2:
        mid = len(words) // 2
        return " ".join(words[:mid]) + "\n" + " ".join(words[mid:])
    else:
        line1 = " ".join(words[:max_words_per_line])
        line2 = " ".join(words[max_words_per_line:max_words_per_line*2])
        return line1 + "\n" + line2

def process_audio_chunk(chunk_path):
    try:
        audio = AudioSegment.from_file(chunk_path)
        audio = effects.normalize(audio)
        audio.export(chunk_path, format="mp3", bitrate="128k")
    except Exception as e:
        pass

if uploaded_file and st.button("Generate Perfect SRT ⚡"):
    status_box = st.empty()
    progress_bar = st.progress(0)
    
    status_box.info("فائل اپ لوڈ ہو رہی ہے، براہ کرم انتظار کریں...")
    temp_path = f"temp_{uploaded_file.name}"
    
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    try:
        status_box.info("ویڈیو/آڈیو پروسیس کی جا رہی ہے اور آواز صاف کی جا رہی ہے...")
        audio = AudioSegment.from_file(temp_path)
        audio = effects.normalize(audio)
        
        total_duration = len(audio)
        CHUNK_MS = 60 * 1000 
        num_chunks = math.ceil(total_duration / CHUNK_MS)
        all_segments = []

        status_box.info("کاوش اے آئی کیپشن ترجمہ تیار کر رہا ہے...")
        
        for i in range(num_chunks):
            chunk = audio[i*CHUNK_MS : min((i+1)*CHUNK_MS, total_duration)]
            chunk_path = f"chunk_{i}.mp3"
            chunk.export(chunk_path, format="mp3", bitrate="128k")

            process_audio_chunk(chunk_path)

            with open(chunk_path, "rb") as file:
                prompt_text = "Accurate Urdu to English translation. Short sentences only. Avoid long paragraphs."
                
                transcription = client.audio.translations.create(
                    file=(f"chunk_{i}.mp3", file.read()),
                    model="whisper-large-v3",
                    prompt=prompt_text,
                    temperature=0.0,
                    response_format="verbose_json"
                )

            time_offset = (i * CHUNK_MS) / 1000.0
            for seg in getattr(transcription, 'segments', []):
                seg['start'] += time_offset
                seg['end'] += time_offset
                all_segments.append(seg)

            if os.path.exists(chunk_path): 
                os.remove(chunk_path)
                
            progress_bar.progress((i + 1) / num_chunks)

        srt_content = ""
        count = 1
        for seg in all_segments:
            start, end = format_time(seg['start']), format_time(seg['end'])
            txt = clean_text(seg['text'])
            if txt:
                formatted_txt = split_text_into_max_two_lines(txt)
                srt_content += f"{count}\n{start} --> {end}\n{formatted_txt}\n\n"
                count += 1

        if os.path.exists(temp_path): 
            os.remove(temp_path)

        progress_bar.empty()
        
        if srt_content.strip():
            status_box.success("🎉 .SRT فائل شارٹ کیپشنز (Max 2 Lines) کے ساتھ تیار ہے!")
            st.download_button(
                "📥 Download .SRT Subtitle File", 
                srt_content, 
                file_name=f"{os.path.splitext(uploaded_file.name)[0]}.srt", 
                mime="text/plain"
            )
        else:
            status_box.error("آڈیو میں سے کوئی واضح گفتگو نہیں مل سکی۔")

    except Exception as e:
        if os.path.exists(temp_path): os.remove(temp_path)
        status_box.error(f"Error: {e}")
