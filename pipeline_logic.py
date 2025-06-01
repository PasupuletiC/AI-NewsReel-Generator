# pipeline_logic.py
import os
import time
import config
import news_fetcher
import script_generator
import asset_manager
import video_creator 
import re
import shutil

def create_necessary_folders():
    folders = [config.TEMP_IMAGE_FOLDER, config.TEMP_AUDIO_FOLDER, config.TEMP_VIDEO_FOLDER,
               config.OUTPUT_VIDEO_FOLDER, config.FONT_FOLDER]
    all_ok = True
    for f_path in folders:
        if not os.path.exists(f_path):
            try: os.makedirs(f_path, exist_ok=True); print(f"Created: {f_path}")
            except OSError as e: print(f"Error creating {f_path}: {e}"); all_ok=False
    if all_ok: print("Dirs checked/created.")
    return all_ok

def sanitize_for_filename(text, max_len=60):
    if not text: return "untitled_reel"; text=str(text)
    text=re.sub(r'[^\w\s-]','',text); text=re.sub(r'[-\s]+','_',text).strip('_'); return text[:max_len]

def run_video_generation_pipeline():
    print("--- Starting Pipeline ---")
    res = {"success":False, "error_message":None, "article_url":None, "article_title":None, 
           "script_points":None, "video_path":None}
    if not create_necessary_folders(): res["error_message"]="Dir creation failed."; return res

    print("\n[PHASE 1: NEWS]")
    headlines = news_fetcher.get_top_trending_headlines_from_newsapi()
    if not headlines: res["error_message"]="No headlines from NewsAPI."; print(res["error_message"]); return res
    
    article_data, sel_url, sel_title_hint = None, None, None
    for hl in headlines:
        print(f"\nAttempting article: '{hl['title']}' from {hl['url']}")
        curr_data = news_fetcher.extract_article_content(hl['url'], hl['title'])
        if curr_data and curr_data.get('text'):
            article_data, sel_url, sel_title_hint = curr_data, hl['url'], hl['title']; break
        else: print(f"  Skipping '{hl['title']}' due to content issues."); time.sleep(0.1)
    
    if not article_data: 
        res["error_message"]=f"No usable content from top {len(headlines)} articles."; print(res["error_message"]); return res
    res["article_url"]=sel_url; res["article_title"]=article_data.get('title',sel_title_hint)
    print(f"\nSelected: '{res['article_title']}'. Len: {len(article_data['text'])} chars.")

    print("\n[PHASE 2: SCRIPT]")
    points = script_generator.generate_script_from_text(article_data['text'])
    if not points: res["error_message"]="No script."; print(res["error_message"]); return res
    res["script_points"]=points; print("Script Points:", points)

    print("\n[PHASE 3: ASSETS]")
    segments, minor_errs = [], []
    for i, p_text in enumerate(points):
        print(f"\n  Segment {i+1}/{len(points)}: '{p_text[:50]}...'")
        kw = asset_manager.get_image_search_keywords(p_text, article_data.get('keywords'))
        img = asset_manager.fetch_relevant_image_pexels(kw, f"seg_{i}")
        if not img: img = asset_manager.get_placeholder_image()
        if not img: msg=f"CRIT: No image seg {i+1}."; print(msg); minor_errs.append(msg); continue
        aud = asset_manager.generate_tts_audio(p_text, f"seg_{i}")
        if not aud: minor_errs.append(f"WARN: No audio seg {i+1}.")
        segments.append({"text":p_text, "image_path":img, "audio_path":aud}); time.sleep(0.05)

    if not segments: 
        res["error_message"]="No segments created (image issues)."; 
        if minor_errs: res["error_message"] += " Issues: "+" | ".join(minor_errs)
        print(res["error_message"]); return res
    if minor_errs: res["error_message"] = (res.get("error_message","") + " | Minor asset issues: "+" | ".join(minor_errs)).strip(" | ")

    print("\n[PHASE 4: VIDEO COMPILATION]")
    vid_title = sanitize_for_filename(res['article_title']); ts = time.strftime("%Y%m%d_%H%M%S")
    os.makedirs(config.OUTPUT_VIDEO_FOLDER, exist_ok=True)
    out_file = os.path.join(config.OUTPUT_VIDEO_FOLDER, f"{vid_title}_{ts}.mp4")
    
    final_vid = video_creator.compile_video(segments, out_file)
    if final_vid and os.path.exists(final_vid):
        res["success"]=True; res["video_path"]=os.path.abspath(final_vid)
        print(f"\n--- SUCCESS! Video: {res['video_path']} ---")
    else:
        err_comp = "Compilation failed. Check terminal for FFmpeg/other errors."
        cur_err = res.get("error_message","")
        res["error_message"] = (cur_err + " | " + err_comp).strip(" | ") if cur_err else err_comp
        print(f"\n--- FAILED. ({err_comp}) ---")
    print("\n--- Pipeline Finished ---"); return res

if __name__ == "__main__":
    # Basic check for placeholder API keys
    if any(val.startswith("YOUR_") for val in [config.NEWS_API_KEY, config.PEXELS_API_KEY, config.GEMINI_API_KEY]):
        print("ERROR: Default API keys found in config.py. Please replace them with your actual keys."); exit()
    outcome = run_video_generation_pipeline()
    if outcome["success"]: print(f"CLI Success: {outcome['video_path']}")
    else: print(f"CLI Failure: {outcome.get('error_message', 'Unknown error')}")