from fastapi import FastAPI, HTTPException, UploadFile, Form, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
import uuid
import shutil

# استيراد حزم المونتاج والخط العربي والاتجاهات
from moviepy.editor import TextClip, CompositeVideoClip, ColorClip, AudioFileClip
import arabic_reshaper
from bidi.algorithm import get_display

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "temp_videos"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/generate-video")
async def generate_video(text: str = Form(...), audio: UploadFile = File(None)):
    unique_id = str(uuid.uuid4())[:8]
    output_video = os.path.join(UPLOAD_DIR, f"final_{unique_id}.mp4")
    saved_audio_path = None
    
    try:
        # 1. إذا أرسل التطبيق ملف موسيقى، يتم حفظه مؤقتاً على السيرفر لدمجه
        if audio:
            saved_audio_path = os.path.join(UPLOAD_DIR, f"audio_{unique_id}.mp3")
            with open(saved_audio_path, "wb") as buffer:
                shutil.copyfileobj(audio.file, buffer)

        # 2. إصلاح ومعالجة الخط العربي لكي يظهر صحيحاً وغير مقلوب
        reshaped_text = arabic_reshaper.reshape(text)
        final_text = get_display(reshaped_text)
        
        # 3. صناعة الخلفية الملونة الفخمة (بنفسجي غامق جداً) عمودية لمدة 7 ثوانٍ
        bg_clip = ColorClip(size=(1080, 1920), color=[15, 12, 32]).set_duration(7)
        
        # 4. صناعة طبقة النص وتوسيطها في الشاشة
        txt_clip = TextClip(
            final_text, 
            fontsize=55, 
            color='white', 
            font='Arial', 
            method='caption', 
            size=(900, None)
        )
        txt_clip = txt_clip.set_position('center').set_duration(bg_clip.duration)
        
        # 5. دمج طبقة النص فوق الخلفية البرمجية الملونة
        video = CompositeVideoClip([bg_clip, txt_clip])
        
        # 6. تركيب ملف الموسيقى المرفوع حيّاً من تليفونك
        if saved_audio_path and os.path.exists(saved_audio_path):
            audio_clip = AudioFileClip(saved_audio_path).subclip(0, 7)
            video = video.set_audio(audio_clip)
        
        # 7. التصدير والرندرة وإنتاج الفيديو النهائي بجودة عالية وضغط سريع
        video.write_videofile(output_video, codec="libx264", audio_codec="aac", fps=24, logger=None)
        
        # إغلاق وتحرير الذاكرة لمنع تشنج السيرفر
        bg_clip.close()
        txt_clip.close()
        if saved_audio_path:
            audio_clip.close()
        video.close()

        # مسح ملف الصوت المؤقت المرفوع للحفاظ على مساحة السيرفر
        if saved_audio_path and os.path.exists(saved_audio_path):
            os.remove(saved_audio_path)

        return FileResponse(output_video, media_type="video/mp4", filename="ai_video.mp4")

    except Exception as e:
        if saved_audio_path and os.path.exists(saved_audio_path):
            os.remove(saved_audio_path)
        raise HTTPException(status_code=500, detail=f"خطأ داخلي في السيرفر: {str(e)}")

@app.get("/")
def read_root():
    return {"status": "السيرفر شغال بنجاح ونظام الموسيقى المرفوعة جاهز!"}
