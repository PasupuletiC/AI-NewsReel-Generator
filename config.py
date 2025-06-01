# config.py

# --- API KEYS ---
NEWS_API_KEY = "d3372e14d7cd464ca08b8b3547db056e" # REPLACE WITH YOUR ACTUAL KEY
PEXELS_API_KEY = "NRLHMvw4W7UBb88u1LOUbiHUm52x9jsgU1qhxLGfSNAiF9Ie4fLBYw2T" # REPLACE WITH YOUR ACTUAL KEY
GEMINI_API_KEY = "AIzaSyCQbQjmeMsmMogTz5ARrc_0W27G75i124c" # REPLACE WITH YOUR ACTUAL KEY

# --- SCRIPT GENERATION (Google Gemini) ---
GEMINI_MODEL_NAME = "gemini-1.5-flash-latest"
SCRIPT_MAX_POINTS = 4
SCRIPT_PROMPT_TEMPLATE_GEMINI = """
Analyze the following news article text and generate a concise script for a short video.
The script should consist of exactly {num_points} main talking points.
Each talking point must be a single, engaging, and complete sentence.
Focus on the most important information, presenting it clearly and neutrally.
Do not use any introductory phrases. Do not use any concluding phrases.
Directly present the key information as requested.
Article Text:\n---\n{article_text}\n---\nOutput:
Provide the {num_points} talking points. Each point should be on a new line. Do not number them or use bullet points.
"""

# --- VIDEO CREATION (OpenCV & FFmpeg settings) ---
VIDEO_WIDTH = 1280; VIDEO_HEIGHT = 720; VIDEO_FPS = 24
IMAGE_DURATION_PER_WORD = 0.5; MIN_IMAGE_DURATION = 3.0; MAX_IMAGE_DURATION = 8.0
TEXT_FONT = "fonts/Roboto-Regular.ttf" # CRITICAL: Ensure this file exists
TEXT_FONT_SIZE = 40; TEXT_COLOR = (255, 255, 255); TEXT_BG_COLOR = (0, 0, 0)
TEXT_BG_OPACITY = 128; TEXT_MARGIN_VERTICAL = 50

# --- NETWORK TIMEOUTS ---
NETWORK_TIMEOUT_SECONDS = 120

# --- DIRECTORIES ---
TEMP_IMAGE_FOLDER = "temp_images"; TEMP_AUDIO_FOLDER = "temp_audio"
TEMP_VIDEO_FOLDER = "temp_videos_cv"; OUTPUT_VIDEO_FOLDER = "generated_videos"
FONT_FOLDER = "fonts"
NEWS_CATEGORY = None # For general trending news
NEWS_COUNTRY = "us" # Required if category is None for NewsAPI top-headlines
NEWS_NUM_ARTICLES_TO_CONSIDER = 10
IMAGE_SEARCH_PROVIDER = "pexels"; TTS_LANG = 'en'