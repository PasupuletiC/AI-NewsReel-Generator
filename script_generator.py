# script_generator.py
import config
import google.generativeai as genai
import time
import re

def generate_script_from_text(article_text, num_points=config.SCRIPT_MAX_POINTS):
    if not article_text: print("Article text missing for script."); return None
    if not config.GEMINI_API_KEY or config.GEMINI_API_KEY.startswith("YOUR_"):
        print("ERROR: Gemini API key not configured."); return None
    try: genai.configure(api_key=config.GEMINI_API_KEY)
    except Exception as e: print(f"Error configuring Gemini: {e}"); return None
    prompt = config.SCRIPT_PROMPT_TEMPLATE_GEMINI.format(num_points=num_points, article_text=article_text)
    gen_conf = {"temperature":0.7, "top_p":0.95, "top_k":40, "max_output_tokens":250*num_points}
    try: model = genai.GenerativeModel(config.GEMINI_MODEL_NAME, generation_config=gen_conf)
    except Exception as e: print(f"Error initializing Gemini Model: {e}"); return None
    for attempt in range(3):
        try:
            print(f"Attempting script generation (Attempt {attempt+1}/3)...")
            resp = model.generate_content(prompt); gen_text = resp.text if resp.parts else None
            if not gen_text and hasattr(resp,'prompt_feedback') and resp.prompt_feedback.block_reason:
                print(f"Gemini blocked: {resp.prompt_feedback.block_reason}"); return None
            if not gen_text: print(f"Gemini: No text. Resp: {resp}"); time.sleep(5); continue
            pts = [p.strip() for p in gen_text.split('\n') if p.strip() and len(p.strip()) > 10]
            if not pts or len(pts) < num_points/2:
                sents = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s', gen_text)
                fb_pts = [s.strip() for s in sents if s.strip() and len(s.strip()) > 10][:num_points]
                if len(fb_pts) >= num_points/2: pts = fb_pts
            if not pts: print("LLM: Unusable script."); return None
            return pts[:num_points]
        except Exception as e:
            print(f"Gemini API error: {e}")
            if "API key" in str(e) or "PERMISSION_DENIED" in str(e): return None
            if attempt < 2: time.sleep(5+attempt*5)
            else: print("Max retries for Gemini."); return None
    return None