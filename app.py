import streamlit as st
import whisper
import os
import math

st.set_page_config(page_title="Kawish AI Captioner", layout="centered")

st.title("Kawish AI Captioner 🎙️⚡")
st.write("اپنی ویڈیو یا آڈیو اپلوڈ کریں اور پرفیکٹ کیپشنز حاصل کریں")

# ٹائم کو SRT فارمیٹ (00:00:00,000) میں تبدیل کرنے کا فنکشن
def format_time(seconds):
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{ms:03d}"

# 1. آڈیو اور ویڈیو دونوں فارمیٹس کے لیے اپلوڈر
uploaded_file = st.file_uploader(
    "فائل منتخب کریں (آڈیو یا ویڈیو)...", 
    type=["mp4", "mov", "avi", "mkv", "mp3", "wav", "m4a", "aac", "flac", "ogg"]
)

if uploaded_file is not None:
    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
    temp_filename = f"temp_input{file_extension}"
    
    # فائل کو عارضی سیو کرنا
    with open(temp_filename, "wb") as f:
        f.write(uploaded_file.read())
    
    if file_extension in [".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"]:
        st.audio(temp_filename)
    else:
        st.video(temp_filename)
    
    if st.button("کیپشن تیار کریں ⚡"):
        try:
            with st.spinner("AI آواز سن رہا ہے اور امریکی انگلش میں ترجمہ کر رہا ہے..."):
                
                # Whisper ماڈل لوڈ کرنا
                model = whisper.load_model("small")
                
                # 2. آڈیو/ویڈیو سے 100% درست US English ٹرانسلیشن
                result = model.transcribe(temp_filename, task="translate")
                
                st.success("✨ کیپشن کامیابی سے تیار ہو گیا ہے!")
                
                # SRT کنٹینٹ اور ڈسپلے کا ڈیٹا بنانا
                srt_content = ""
                count = 1
                
                max_words_per_block = 8  # 👈 میکسمم 8 الفاظ
                
                for seg in result["segments"]:
                    s_start = seg['start']
                    s_end = seg['end']
                    all_words = seg['text'].strip().split()
                    
                    if not all_words:
                        continue
                        
                    total_words = len(all_words)
                    total_duration = max(0.5, s_end - s_start)
                    time_per_word = total_duration / total_words
                    
                    for i in range(0, total_words, max_words_per_block):
                        block_words = all_words[i:i + max_words_per_block]
                        b_start = s_start + (i * time_per_word)
                        b_end = min(s_end, s_start + ((i + len(block_words)) * time_per_word))

                        # 6 یا اس سے زیادہ الفاظ پر 2 لائنیں
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

                st.subheader("📥 کیپشن فائل ڈاؤن لوڈ کریں:")
                
                # 🔥 3. SRT ڈاؤن لوڈ بٹن
                base_name = os.path.splitext(uploaded_file.name)[0]
                st.download_button(
                    label="⬇️ Download SRT Subtitles",
                    data=srt_content,
                    file_name=f"{base_name}.srt",
                    mime="text/plain"
                )
                
                st.markdown("---")
                st.subheader("کیپشنز کا پریویو (Preview):")
                st.text_area("SRT Preview", value=srt_content, height=300)
                    
        except Exception as e:
            st.error(f"ایرر آ گیا ہے: {str(e)}")
            
        finally:
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
