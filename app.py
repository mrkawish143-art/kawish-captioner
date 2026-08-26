import streamlit as st
import os
import math
import re
from groq import Groq
from pydub import AudioSegment

# 🔑 آپ کی Groq API Key
GROQ_API_KEY = "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"

st.set_page_config(page_title="Kawish Mobile AI Captioner", layout="centered")

st.title("Kawish AI Captioner 📱⚡")
st.write("موبائل اور لیپ ٹاپ دونوں پر 100% فاسٹ کیپشنز حاصل کریں")

def format_time(seconds):
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{ms:03d}"

def clean_text(text):
    text = text.strip()
    if re.search(r"Amara\.org|Subtitles by|Thank you for watching", text, re.IGNORECASE):
        return ""
    if re.search(r"[\u0600-\u06FF]", text):
        return ""
    return text

uploaded_file = st.file_uploader(
    "فائل منتخب کریں (آڈیو یا ویڈیو)...", 
    type=["mp4", "mov", "avi", "mkv", "mp3", "wav", "m4a", "aac", "flac", "ogg"]
)

if uploaded_file is not None:
    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
    temp_filename = f"temp_input{file_extension}"
    
    with open(temp_filename, "wb") as f:
        f.write(uploaded_file.read())
    
    if file_extension in [".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"]:
        st.audio(temp_filename)
    else:
        st.video(temp_filename)
    
    if st.button("کیپشن تیار کریں ⚡"):
        try:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("آڈیو پروسیس کی جا رہی ہے...")
            progress_bar.progress(10)

            client = Groq(api_key=GROQ_API_KEY)
            
            # 🔥 5 منٹ (300 سیکنڈز) کے سمارٹ چنکس - 3000 کی لمٹ سے بچنے کے لیے
            audio = AudioSegment.from_file(temp_filename)
            chunk_length_ms = 5 * 60 * 1000  # 5 Minutes Chunks
            total_duration_ms = len(audio)
            total_chunks = math.ceil(total_duration_ms / chunk_length_ms)
            
            all_raw_segs = []

            for index, i in enumerate(range(0, total_duration_ms, chunk_length_ms)):
                chunk_num = index + 1
                prog_val = 10 + int((index / total_chunks) * 75)
                
                status_text.text(f"حصہ {chunk_num} / {total_chunks} پروسیس ہو رہا ہے...")
                progress_bar.progress(prog_val)

                chunk_audio = audio[i:i + chunk_length_ms]
                temp_chunk_name = f"temp_chunk_{i}.mp3"
                chunk_audio.export(temp_chunk_name, format="mp3", bitrate="128k")
                
                offset_seconds = i / 1000.0

                with open(temp_chunk_name, "rb") as file:
                    transcription = client.audio.translations.create(
                        file=(os.path.basename(temp_chunk_name), file.read()),
                        model="whisper-large-v3",
                        temperature=0.0,
                        response_format="verbose_json"
                    )

                segs = transcription.segments if hasattr(transcription, 'segments') else []
                for s in segs:
                    s_start = (s['start'] if isinstance(s, dict) else s.start) + offset_seconds
                    s_end = (s['end'] if isinstance(s, dict) else s.end) + offset_seconds
                    s_text = s['text'] if isinstance(s, dict) else s.text
                    all_raw_segs.append({'start': s_start, 'end': s_end, 'text': s_text})

                if os.path.exists(temp_chunk_name):
                    os.remove(temp_chunk_name)

            status_text.text("SRT فائل تیار ہو رہی ہے...")
            progress_bar.progress(90)

            srt_content = ""
            count = 1
            max_words_per_block = 8
            
            for seg in all_raw_segs:
                cleaned = clean_text(seg['text'])
                if not cleaned:
                    continue

                all_words = cleaned.split()
                total_words = len(all_words)
                total_duration = max(0.5, seg['end'] - seg['start'])
                time_per_word = total_duration / total_words

                for i in range(0, total_words, max_words_per_block):
                    block_words = all_words[i:i + max_words_per_block]
                    b_start = seg['start'] + (i * time_per_word)
                    b_end = min(seg['end'], seg['start'] + ((i + len(block_words)) * time_per_word))

                    if len(block_words) >= 6:
                        mid = math.ceil(len(block_words) / 2)
                        line1 = " ".join(block_words[:mid])
                        line2 = " ".join(block_words[mid:])
                        fmt_text = f"{line1}\n{line2}"
                    else:
                        fmt_text = " ".join(block_words)

                    start_t = format_time(b_start)
                    end_t = format_time(b_end)

                    srt_content += f"{count}\n{start_t} --> {end_t}\n{fmt_text}\n\n"
                    count += 1

            progress_bar.progress(100)
            status_text.text("مکمل ہو گیا! ✅")
            st.success("✨ کیپشن کامیابی سے تیار ہو گئے ہیں!")
            
            base_name = os.path.splitext(uploaded_file.name)[0]
            st.download_button(
                label="⬇️ Download SRT Subtitles",
                data=srt_content,
                file_name=f"{base_name}.srt",
                mime="text/plain"
            )
            
            st.markdown("---")
            st.subheader("کیپشنز کا پریویو (Preview):")
            st.text_area("SRT Preview", value=srt_content, height=250)

        except Exception as e:
            st.error(f"ایرر آ گیا ہے: {str(e)}")
            
        finally:
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
