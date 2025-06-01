# asset_manager.py
import requests
from gtts import gTTS
import os
import config
import re
from PIL import Image
import shutil

def _s(text,l=50): t=str(text);t=re.sub(r'[^\w\s-]','',t.lower());t=re.sub(r'[-\s]+','-',t).strip('-_'); return t[:l]if t else "u"
def fetch_relevant_image_pexels(q,pfx="image"):
    if not config.PEXELS_API_KEY or config.PEXELS_API_KEY.startswith("YOUR_"): print("ERR: Pexels key"); return None
    h={"Authorization":config.PEXELS_API_KEY}; P={"query":q,"per_page":1,"orientation":"landscape","size":"large"}
    url="https://api.pexels.com/v1/search"
    try:
        print(f"    Pexels: Srch '{q}'..."); r=requests.get(url,headers=h,params=P,timeout=config.NETWORK_TIMEOUT_SECONDS)
        r.raise_for_status(); d=r.json()
        if d.get("photos") and d["photos"]:
            iu=(d["photos"][0]["src"].get('large2x')or d["photos"][0]["src"].get('large')or d["photos"][0]["src"].get('original')or d["photos"][0]["src"].get('medium'))
            if not iu: print(f"    Pexels: No URL for '{q}'."); return None
            ir=requests.get(iu,stream=True,timeout=config.NETWORK_TIMEOUT_SECONDS); ir.raise_for_status()
            os.makedirs(config.TEMP_IMAGE_FOLDER,exist_ok=True); e=os.path.splitext(iu)[1].split('?')[0]; e=e if e in['.jpg','.jpeg','.png']else'.jpg'
            ip=os.path.join(config.TEMP_IMAGE_FOLDER,f"{pfx}_{_s(q)}{e}")
            with open(ip,'wb')as f:shutil.copyfileobj(ir.raw,f); del ir
            try:
                with Image.open(ip) as i_o: i_o.verify()
                print(f"    Pexels: Img: {ip}"); return ip
            except Exception as ev: print(f"    Pexels: Invalid img {ip}: {ev}"); os.remove(ip); return None
        else: print(f"    Pexels: No images for '{q}'."); return None
    except Exception as e: print(f"    Pexels: Error fetching '{q}': {e}"); return None
def generate_tts_audio(t,pfx="audio"):
    if not t: print("    TTS: No text"); return None
    try:
        tts=gTTS(t,lang=config.TTS_LANG,slow=False); os.makedirs(config.TEMP_AUDIO_FOLDER,exist_ok=True)
        st=_s(t.split('.')[0]if'.'in t else t,20); ap=os.path.join(config.TEMP_AUDIO_FOLDER,f"{pfx}_{st}.mp3")
        tts.save(ap); print(f"    TTS: Audio: {ap}"); return ap
    except Exception as e:print(f"    TTS: Error for '{t[:20]}...': {e}");return None
def get_image_search_keywords(spt,akw=None):
    sw=set(["a","an","the","is","are","was","were","be","in","on","at","for","and","to","of","it","this","that","with","by","from","its","will","has","have","as","but","some","about","then","there","their"])
    w=[x for x in re.split(r'\W+',spt.lower())if x and x not in sw and len(x)>2]
    q=" ".join(w[:3])if len(w)>=3 else" ".join(w)
    if not q and akw and isinstance(akw,list)and len(akw)>0:q=" ".join(akw[:2])
    if not q:q=spt[:25].strip()
    print(f"    Image Keywords: '{q}' (from: '{spt[:30]}...')");return q
def get_placeholder_image():
    p=os.path.join(config.TEMP_IMAGE_FOLDER,"placeholder_image.png")
    if not os.path.exists(p):
        try:os.makedirs(config.TEMP_IMAGE_FOLDER,exist_ok=True);Image.new('RGB',(config.VIDEO_WIDTH,config.VIDEO_HEIGHT),color='dimgray').save(p);print(f"    Placeholder: {p}")
        except Exception as e:print(f"    CRIT: No placeholder: {e}");return None
    return p
def cleanup_temp_files():
    for fld in[config.TEMP_IMAGE_FOLDER,config.TEMP_AUDIO_FOLDER,config.TEMP_VIDEO_FOLDER]:
        if os.path.exists(fld):
            try:shutil.rmtree(fld);print(f"Removed: {fld}")
            except Exception as e:print(f"Err removing {fld}:{e}")
        try:os.makedirs(fld,exist_ok=True)
        except Exception as e:print(f"Err recreating {fld}:{e}")
    print("Temp cleanup done.")