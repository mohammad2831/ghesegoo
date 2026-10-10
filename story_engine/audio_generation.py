import sys
import os
import re
import io
import torch
import torchaudio as ta
import logging
from huggingface_hub import snapshot_download
from safetensors.torch import load_file as load_safetensors

logger = logging.getLogger(__name__)

# ==========================================
# توابع کمکی (دقیقا کدهای بهینه شده خودتان)
# ==========================================
SENTENCE_SPLITTER = re.compile(r'([.?!؟!؛\n]+)')
COMMA_SPLITTER = re.compile(r'(،+)')
PUNCT_ONLY_CHECK = re.compile(r'^[\s.?!؟!؛،\n]+$')

def clean_persian_text(text):
    cleaned = re.sub(r'[^\u0600-\u06FF\s0-9.,!?]', '', text)
    cleaned = cleaned.replace('\u200c', ' ')
    return ' '.join(cleaned.split())

def chunk_persian_text(text, max_words=15):
    # کدهای چانکینگ که خودتان نوشته بودید کاملا اینجا قرار می‌گیرد
    if not text: return []
    final_chunks = []
    parts = SENTENCE_SPLITTER.split(text)
    sentences = []
    current_chunk = ""
    
    for part in parts:
        if SENTENCE_SPLITTER.match(part):
            current_chunk += part
            if current_chunk.strip():
                sentences.append(current_chunk.strip())
            current_chunk = ""
        else:
            current_chunk += part
    if current_chunk.strip():
        sentences.append(current_chunk.strip())

    for sentence in sentences:
        if len(sentence.split()) <= max_words:
            final_chunks.append(sentence)
        else:
            sub_parts = COMMA_SPLITTER.split(sentence)
            current_sub = ""
            for sub in sub_parts:
                if COMMA_SPLITTER.match(sub):
                    current_sub += sub
                    if current_sub.strip():
                        final_chunks.append(current_sub.strip())
                    current_sub = ""
                else:
                    current_sub += sub
            if current_sub.strip():
                final_chunks.append(current_sub.strip())
    return [chunk for chunk in final_chunks if not PUNCT_ONLY_CHECK.match(chunk)]

# ==========================================
# کلاس اصلی و Singleton مدل چترباکس
# ==========================================
class ChatterboxService:
    _instance = None
    _model = None
    _device = "cuda" if torch.cuda.is_available() else "cpu"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ChatterboxService, cls).__new__(cls)
        return cls._instance

    @classmethod
    def get_model(cls):
        if cls._model is not None:
            return cls._model # مدل قبلا لود شده

        logger.info(f"Loading Chatterbox on {cls._device} (Lazy Load in Celery)...")
        if "./chatterbox_git/src" not in sys.path:
            sys.path.append("./chatterbox_git/src")
            
        from chatterbox import mtl_tts

        try:
            model_dir = snapshot_download(repo_id="Thomcles/Chatterbox-TTS-Persian-Farsi")
            multilingual_model = mtl_tts.ChatterboxMultilingualTTS.from_pretrained(device=cls._device)
            
            # لود کردن وزن‌های مدل... (مطابق کد قبلی شما)
            t3_path = os.path.join(model_dir, "t3_fa.safetensors")
            if os.path.exists(t3_path):
                multilingual_model.t3.load_state_dict(load_safetensors(t3_path, device=cls._device), strict=False)
                multilingual_model.t3.to(cls._device).eval()
            
            s3gen_path = os.path.join(model_dir, "s3gen_fa.safetensors") 
            if os.path.exists(s3gen_path):
                multilingual_model.s3gen.load_state_dict(load_safetensors(s3gen_path, device=cls._device), strict=False)
                multilingual_model.s3gen.to(cls._device).eval()
            
            cls._model = multilingual_model
            logger.info("✅ Chatterbox Model is ready in VRAM.")
            return cls._model
            
        except Exception as e:
            logger.error(f"TTS Load Error: {e}")
            raise e

    def generate_audio(self, raw_text, ref_audio_path):
        target_text = clean_persian_text(raw_text)
        if not target_text: return False, "متن خالی است."
        if not os.path.exists(ref_audio_path): return False, "فایل رفرنس یافت نشد."

        try:
            model = self.get_model()
            sample_rate = model.sr
            text_chunks = chunk_persian_text(target_text, max_words=18)
            all_waveforms = []

            with torch.inference_mode():
                for chunk in text_chunks:
                    wav_chunk = model.generate(
                        text=chunk, language_id=None,
                        temperature=0.7, cfg_weight=0.5, top_p=0.5,
                        exaggeration=0.6, audio_prompt_path=ref_audio_path
                    )
                    if isinstance(wav_chunk, torch.Tensor):
                        wav_chunk = wav_chunk.cpu().to(torch.float32).view(1, -1)
                        all_waveforms.append(wav_chunk)
                        # سکوت 0.3 ثانیه
                        all_waveforms.append(torch.zeros((1, int(sample_rate * 0.3)), dtype=torch.float32))

            if not all_waveforms: return False, "صوتی تولید نشد."

            final_waveform = torch.cat(all_waveforms, dim=1)
            # نرمال سازی
            max_amp = final_waveform.abs().max()
            if max_amp > 1.0: final_waveform /= max_amp

            # تبدیل به فایل مجازی در رم
            audio_buffer = io.BytesIO()
            ta.save(audio_buffer, final_waveform, sample_rate, format="wav", encoding="PCM_S", bits_per_sample=16)
            
            return True, audio_buffer.getvalue()

        except Exception as e:
            return False, str(e)