import streamlit as st
import whisper
import os

st.set_page_config(page_title="Kawish AI Captioner", layout="centered")

st.title("Kawish AI Captioner")
st.write("اپنی ویڈیو اپلوڈ کریں اور پرفیکٹ کیپشن حاصل کریں")

# 1. ویڈیو اپلوڈر (3000MB لمٹ کے ساتھ)
uploaded_file = st.file_uploader("ویڈیو منتخب کریں...", type=["mp4", "mov", "avi", "mkv"])

if uploaded_file is not None:
    # ویڈیو کو عارضی سیو کرنا
    with open("temp_video.mp4", "wb") as f:
        f.write(uploaded_file.read())
    
    st.video("temp_video.mp4")
    
    if st.button("کیپشن تیار کریں"):
        try:
            # اسکرین پر سرچنگ اور لوڈنگ کا اینیمیشن
            with st.spinner("AI آواز سن رہا ہے اور امریکی انگلش میں ترجمہ کر رہا ہے..."):
                
                # Whisper ماڈل لوڈ کرنا (Small یا Medium بہتر رزلٹ دیتا ہے)
                model = whisper.load_model("small")
                
                # 2. آواز کو سن کر امریکن انگلش میں ٹرانسلیٹ کرنا (task='translate')
                result = model.transcribe("temp_video.mp4", task="translate", language="ur") # یا جو بھی زبان ہو
                
                st.progress(100)
                st.success("✨ کیپشن کامیابی سے تیار ہو گیا ہے!")
                
                # 3. میکسیمم 2 لائنوں میں دکھانے کا فارمیٹ
                segments = result["segments"]
                st.subheader("آپ کے کیپشن (2-Line Format):")
                
                full_text = ""
                for seg in segments:
                    text = seg['text'].strip()
                    # اگر ٹیکسٹ بڑا ہو تو اسے 2 لائنوں پر محدود رکھنا
                    words = text.split()
                    if len(words) > 12:
                        mid = len(words) // 2
                        line1 = " ".join(words[:mid])
                        line2 = " ".join(words[mid:])
                        formatted_caption = f"{line1}\n{line2}"
                    else:
                        formatted_caption = text
                    
                    st.text_area(label="Time: " + str(round(seg['start'], 1)) + "s - " + str(round(seg['end'], 1)) + "s", 
                                 value=formatted_caption, 
                                 height=70)
                    
        except Exception as e:
            st.error(f"ایرر آ گیا ہے: {str(e)}")
            
        finally:
            if os.path.exists("temp_video.mp4"):
                os.remove("temp_video.mp4")
