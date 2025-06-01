# video_creator.py
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import config
import subprocess
from pydub import AudioSegment
import textwrap
import shutil

def get_font_object(font_path_or_name, font_size):
    if os.path.isfile(font_path_or_name):
        try: return ImageFont.truetype(font_path_or_name, font_size)
        except IOError as e: print(f"    PillowFont: CRITICAL - Error loading font file '{font_path_or_name}': {e}.")
    else:
        try: return ImageFont.truetype(font_path_or_name, font_size)
        except IOError as e: print(f"    PillowFont: Font name '{font_path_or_name}' not found as system font: {e}.")
    print(f"    PillowFont: CRITICAL - Falling back to Pillow's basic default font. This may cause encoding errors.")
    return ImageFont.load_default()

def get_segment_duration_cv(text, audio_path):
    min_d, max_d = config.MIN_IMAGE_DURATION, config.MAX_IMAGE_DURATION
    if audio_path and os.path.exists(audio_path):
        try: dur = len(AudioSegment.from_file(audio_path)) / 1000.0; return max(min_d, min(dur + 0.5, max_d))
        except Exception as e: print(f"    pydub: Error reading '{audio_path}' duration: {e}.")
    return max(min_d, min(len(text.split()) * config.IMAGE_DURATION_PER_WORD, max_d))

def add_text_to_image_pillow(image_cv, text_overlay):
    pil_font = get_font_object(config.TEXT_FONT, config.TEXT_FONT_SIZE)
    pil_image_bgra = cv2.cvtColor(image_cv, cv2.COLOR_BGR2BGRA)
    pil_image = Image.fromarray(pil_image_bgra, 'RGBA'); draw = ImageDraw.Draw(pil_image)
    avg_char_w = config.TEXT_FONT_SIZE * 0.5
    try:
        rep_str = "Aa"; bbox = pil_font.getbbox(rep_str) if hasattr(pil_font,'getbbox') else (0,0,*pil_font.getsize(rep_str))
        if bbox and (bbox[2]-bbox[0])>0 and len(rep_str)>0: avg_char_w=(bbox[2]-bbox[0])/float(len(rep_str))
        else: raise ValueError("Invalid font metrics")
    except Exception: avg_char_w = config.TEXT_FONT_SIZE * 0.55
    max_chars = int((config.VIDEO_WIDTH*0.90)/avg_char_w) if avg_char_w>0.1 else 30
    if max_chars<=0: max_chars=30
    wrapper = textwrap.TextWrapper(width=max_chars,break_long_words=True,replace_whitespace=True,drop_whitespace=True)
    lines = wrapper.wrap(text=text_overlay);
    if not lines: lines=[text_overlay[:max_chars]]
    line_heights,total_h,spacing = [],0,5
    for line in lines:
        try:
            bbox_l=draw.textbbox((0,0),line,font=pil_font) if hasattr(draw,'textbbox') else (0,0,*draw.textsize(line,font=pil_font))
            h=bbox_l[3]-bbox_l[1]; line_heights.append(h); total_h+=h
        except UnicodeEncodeError as uee: print(f"    PFont: UnicodeErr line '{line[:20]}': {uee}"); line_heights.append(config.TEXT_FONT_SIZE); total_h+=config.TEXT_FONT_SIZE
        except Exception as e_ts: print(f"    PFont: Err text size '{line[:20]}': {e_ts}"); line_heights.append(config.TEXT_FONT_SIZE); total_h+=config.TEXT_FONT_SIZE
    total_h+=(len(lines)-1)*spacing if len(lines)>1 else 0
    y_s=config.VIDEO_HEIGHT-total_h-config.TEXT_MARGIN_VERTICAL
    if y_s<config.TEXT_MARGIN_VERTICAL*0.5: y_s=config.TEXT_MARGIN_VERTICAL*0.5
    curr_y=y_s
    for i,line in enumerate(lines):
        try:
            bbox_l=draw.textbbox((0,0),line,font=pil_font) if hasattr(draw,'textbbox') else (0,0,*draw.textsize(line,font=pil_font))
            txt_w=bbox_l[2]-bbox_l[0]; x_p=(config.VIDEO_WIDTH-txt_w)/2
            pad_x,pad_y=10,5; r_coords=(x_p-pad_x,curr_y-pad_y,x_p+txt_w+pad_x,curr_y+line_heights[i]+pad_y)
            rect_l=Image.new('RGBA',pil_image.size,(255,255,255,0)); ImageDraw.Draw(rect_l).rectangle(r_coords,fill=(*config.TEXT_BG_COLOR,config.TEXT_BG_OPACITY))
            pil_image=Image.alpha_composite(pil_image,rect_l); draw=ImageDraw.Draw(pil_image)
            draw.text((x_p,curr_y),line,font=pil_font,fill=config.TEXT_COLOR)
        except UnicodeEncodeError as uee_d: print(f"    PFont: UnicodeErr draw '{line[:20]}': {uee_d}.")
        except Exception as e_d: print(f"    PFont: Err draw text '{line[:20]}': {e_d}")
        curr_y+=line_heights[i]+spacing
    return cv2.cvtColor(np.array(pil_image.convert('RGB')),cv2.COLOR_RGB2BGR)

def create_silent_video_opencv(segments_data, silent_video_path):
    if not segments_data: print("CV: No segments."); return False
    os.makedirs(os.path.dirname(silent_video_path), exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(silent_video_path, fourcc, config.VIDEO_FPS, (config.VIDEO_WIDTH, config.VIDEO_HEIGHT))
    if not writer.isOpened(): print(f"CV: Err opening writer: {silent_video_path}"); return False
    print(f"CV: Gen silent vid: {silent_video_path}")
    for i, seg in enumerate(segments_data):
        print(f"  CV: Seg {i+1}/{len(segments_data)}: '{seg['text'][:20]}...'")
        img = cv2.imread(seg["image_path"]);
        if img is None: print(f"    CV: Err loading {seg['image_path']}"); continue
        h,w=img.shape[:2]; vw,vh=config.VIDEO_WIDTH,config.VIDEO_HEIGHT; ar_i=w/h if h>0 else 1; ar_v=vw/vh if vh>0 else 1
        frm=img
        if ar_i==0 or ar_v==0: frm=cv2.resize(img,(vw,vh),cv2.INTER_AREA)
        elif ar_i>ar_v: nh=vh;nw=int(ar_i*nh);r=cv2.resize(img,(nw,nh),cv2.INTER_LANCZOS4);x=(nw-vw)//2;frm=r[:,x:x+vw]
        else: nw=vw;nh=int(nw/ar_i) if ar_i>0.001 else vh;r=cv2.resize(img,(nw,nh),cv2.INTER_LANCZOS4);y=(nh-vh)//2;frm=r[y:y+vh,:]
        if frm.shape[1]!=vw or frm.shape[0]!=vh: frm=cv2.resize(frm,(vw,vh),cv2.INTER_AREA)
        frm_txt=add_text_to_image_pillow(frm.copy(),seg["text"])
        d=get_segment_duration_cv(seg["text"],seg["audio_path"]);n=int(d*config.VIDEO_FPS);[writer.write(frm_txt) for _ in range(n)]
    writer.release();cv2.destroyAllWindows();print(f"CV: Silent vid saved: {silent_video_path}");return True

def concatenate_audio_pydub(audio_paths, output_path):
    if not audio_paths: print("pydub: No audio paths."); return None
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    master, processed = AudioSegment.empty(), False
    for p in audio_paths:
        if p and os.path.exists(p):
            try: master+=AudioSegment.from_file(p); processed=True
            except Exception as e: print(f"pydub: Err with '{p}': {e}")
    if not processed: print("pydub: No valid audio processed."); return None
    try: master.export(output_path,format="mp3"); print(f"pydub: Master audio: {output_path}"); return output_path
    except Exception as e: print(f"pydub: Export error: {e}"); return None

def merge_video_audio_ffmpeg(silent_vid, audio_file, final_out):
    if not os.path.exists(silent_vid): print(f"FFmpeg: Silent vid missing: {silent_vid}"); return False
    os.makedirs(os.path.dirname(final_out), exist_ok=True)
    cmd = ['ffmpeg','-y','-i',silent_vid]
    if audio_file and os.path.exists(audio_file):
        cmd.extend(['-i',audio_file,'-c:a','aac','-b:a','192k','-shortest'])
        print(f"FFmpeg: Merging video and audio.")
    else:
        cmd.extend(['-an']) 
        print(f"FFmpeg: No audio file provided or found. Encoding video without audio track.")
    cmd.extend(['-c:v','libx264','-preset','medium','-crf','23','-pix_fmt','yuv420p','-movflags','+faststart',final_out])
    print(f"FFmpeg: Executing: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        print(f"FFmpeg: Output video: {final_out}"); return True
    except subprocess.CalledProcessError as e: print(f"FFmpeg Error: RC: {e.returncode}\nStderr: {e.stderr}"); return False # Simplified to show only stderr
    except FileNotFoundError: print("FFmpeg: CRITICAL - ffmpeg command not found. Check PATH."); return False

def compile_video(segments_data, output_filename):
    base=os.path.splitext(os.path.basename(output_filename))[0]
    os.makedirs(config.TEMP_VIDEO_FOLDER,exist_ok=True); os.makedirs(config.TEMP_AUDIO_FOLDER,exist_ok=True)
    s_path=os.path.join(config.TEMP_VIDEO_FOLDER,f"{base}_silent.mp4")
    m_audio=os.path.join(config.TEMP_AUDIO_FOLDER,f"{base}_master_audio.mp3")
    if not create_silent_video_opencv(segments_data,s_path): return None
    aud_list=[s.get("audio_path") for s in segments_data if s.get("audio_path")]
    cat_aud=concatenate_audio_pydub(aud_list,m_audio)
    if merge_video_audio_ffmpeg(s_path,cat_aud,output_filename):
        # CORRECTED CLEANUP LINES:
        if os.path.exists(s_path): 
            try: os.remove(s_path)
            except OSError as e: print(f"Warning: could not remove temp silent video '{s_path}': {e}")
        if cat_aud and os.path.exists(cat_aud): 
            try: os.remove(cat_aud)
            except OSError as e: print(f"Warning: could not remove temp master audio '{cat_aud}': {e}")
        return output_filename
    return None