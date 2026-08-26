import streamlit as st
import os
import math
import re
from groq import Groq

# 🔑 آپ کی Groq API Key
GROQ_API_KEY = "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"

st.set_page_config(page_title="Kawish AI Captioner", layout="centered")

st.title("Kawish AI Captioner 🎙️⚡")
st.write("اپنی ویڈیو یا آڈیو اپلوڈ کریں اور الٹرا فاسٹ SRT فائل حاصل کریں")

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
            with st.spinner("AI راکٹ سپیڈ پر ترجمہ کر رہا ہے..."):
                client = Groq(api_key=GROQ_API_KEY)
                
                with open(temp_filename, "rb") as file:
                    transcription = client.audio.translations.create(
                        file=(os.path.basename(temp_filename), file.read()),
                        model="whisper-large-v3",
                        temperature=0.0,
                        response_format="verbose_json"
                    )

                raw_segs = transcription.segments if hasattr(transcription, 'segments') else []
                
                srt_content = ""
                count = 1
                max_words_per_block = 8
                
                for seg in raw_segs:
                    s_start = seg['start'] if isinstance(seg, dict) else seg.start
                    s_end = seg['end'] if isinstance(seg, dict) else seg.end
                    s_text = seg['text'] if isinstance(seg, dict) else seg.text

                    cleaned = clean_text(s_text)
                    if not cleaned:
                        continue

                    all_words = cleaned.split()
                    total_words = len(all_words)
                    total_duration = max(0.5, s_end - s_start)
                    time_per_word = total_duration / total_words

                    for i in range(0, total_words, max_words_per_block):
                        block_words = all_words[i:i + max_words_per_block]
                        b_start = s_start + (i * time_per_word)
                        b_end = min(s_end, s_start + ((i + len(block_words)) * time_per_word))

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
