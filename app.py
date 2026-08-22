import streamlit as st
import whisper
import os

st.set_page_config(page_title="Kawish AI Captioner", layout="centered")

st.title("Kawish AI Captioner")
st.write("اپنی ویڈیو یا آڈیو اپلوڈ کریں اور پرفیکٹ کیپشن حاصل کریں")

# 1. آڈیو اور ویڈیو دونوں فارمیٹس کے لیے اپلوڈر
uploaded_file = st.file_uploader(
    "فائل منتخب کریں (آڈیو یا ویڈیو)...", 
    type=["mp4", "mov", "avi", "mkv", "mp3", "wav", "m4a", "aac", "flac", "ogg"]
)

if uploaded_file is not None:
    # فائل کی ایکسٹینشن (Type) چیک کرنا
    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
    temp_filename = f"temp_input{file_extension}"
    
    # فائل کو عارضی سیو کرنا
    with open(temp_filename, "wb") as f:
        f.write(uploaded_file.read())
    
    # اگر ویڈیو ہے تو ویڈیو پلیئر، آڈیو ہے تو آڈیو پلیئر دکھانا
    if file_extension in [".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"]:
        st.audio(temp_filename)
    else:
        st.video(temp_filename)
    
    if st.button("کیپشن تیار کریں"):
        try:
            with st.spinner("AI آواز سن رہا ہے اور امریکی انگلش میں ترجمہ کر رہا ہے..."):
                
                # Whisper ماڈل لوڈ کرنا
                model = whisper.load_model("small")
                
                # 2. آڈیو/ویڈیو سے 100% درست US English ٹرانسلیشن
                result = model.transcribe(temp_filename, task="translate")
                
                st.progress(100)
                st.success("✨ کیپشن کامیابی سے تیار ہو گیا ہے!")
                
                # 3. زیادہ سے زیادہ 2 لائنوں میں دکھانے کا فارمیٹ
                segments = result["segments"]
                st.subheader("آپ کے کیپشن (2-Line Format):")
                
                for seg in segments:
                    text = seg['text'].strip()
                    # اگر ٹیکسٹ لمبا ہو تو خود بخود 2 لائنوں میں توڑنا
                    words = text.split()
                    if len(words) > 10:
                        mid = len(words) // 2
                        line1 = " ".join(words[:mid])
                        line2 = " ".join(words[mid:])
                        formatted_caption = f"{line1}\n{line2}"
                    else:
                        formatted_caption = text
                    
                    st.text_area(
                        label=f"Time: {round(seg['start'], 1)}s - {round(seg['end'], 1)}s", 
                        value=formatted_caption, 
                        height=75
                    )
                    
        except Exception as e:
            st.error(f"ایرر آ گیا ہے: {str(e)}")
            
        finally:
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
