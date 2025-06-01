# app.py
import streamlit as st
import os
import pipeline_logic 
import config 
import time 

st.set_page_config(page_title="AI NewsReel Generator", layout="wide", initial_sidebar_state="expanded")

st.title("📰 AI NewsReel Generator 🤖")
st.caption("Generates short news summary videos from trending articles using AI.")

os.makedirs(config.OUTPUT_VIDEO_FOLDER, exist_ok=True)

if 'pipeline_results' not in st.session_state:
    st.session_state.pipeline_results = None
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'logs_visible' not in st.session_state: # Renamed from show_logs for clarity
    st.session_state.logs_visible = False


st.sidebar.header("⚙️ Controls")
generate_button = st.sidebar.button("🚀 Generate NewsReel Video", 
                                    key="generate_video_button", 
                                    disabled=st.session_state.processing,
                                    help="Click to start the video generation process.")

st.sidebar.markdown("---")
# The checkbox doesn't directly control terminal output visibility,
# it's more of a user hint. Actual logs always go to terminal.
st.session_state.logs_visible = st.sidebar.checkbox("Processing logs appear in your terminal/console", value=True, disabled=True)
st.sidebar.markdown("---")
st.sidebar.info("""
This application will:
1. Fetch a current trending news article.
2. Use AI to generate a concise script.
3. Gather relevant images and generate voiceover.
4. Compile these into a short video.
""")
st.sidebar.markdown("---")
st.sidebar.caption(f"Output videos will be saved in: `{os.path.abspath(config.OUTPUT_VIDEO_FOLDER)}`")


if generate_button:
    st.session_state.processing = True
    st.session_state.pipeline_results = None 
    
    # API Key Check
    missing_keys_info = []
    if not config.NEWS_API_KEY or config.NEWS_API_KEY.startswith("YOUR_"): missing_keys_info.append("NewsAPI Key")
    if not config.GEMINI_API_KEY or config.GEMINI_API_KEY.startswith("YOUR_"): missing_keys_info.append("Gemini API Key")
    if not config.PEXELS_API_KEY or config.PEXELS_API_KEY.startswith("YOUR_"): missing_keys_info.append("Pexels API Key")

    if missing_keys_info:
        st.error(f"Configuration Error: Please set the following API keys in `config.py`: {', '.join(missing_keys_info)}")
        st.session_state.processing = False
        st.stop() # Stop further execution of this Streamlit script run

    # Font File Check
    font_file_path = os.path.join(config.FONT_FOLDER, os.path.basename(config.TEXT_FONT)) # Construct full path if TEXT_FONT is relative
    if not os.path.isfile(config.TEXT_FONT) and not os.path.isfile(font_file_path): # Check both relative and assumed full path
        st.error(f"Font File Error: Font specified in `config.py` (`{config.TEXT_FONT}`) not found. Please ensure the `fonts` folder and the .ttf file exist in your project directory.")
        st.session_state.processing = False
        st.stop()
        
    st.info("Checking prerequisites... Ensure FFmpeg is installed and in your system PATH. Errors will appear in the terminal if FFmpeg is not found by the backend processes.")

    with st.spinner("🤖 Generating your AI NewsReel... This can take several minutes! Please wait... ⏳"):
        print("\n" + "="*10 + " Streamlit App: Starting Pipeline " + "="*10 + "\n")
        
        results = pipeline_logic.run_video_generation_pipeline()
        st.session_state.pipeline_results = results
        print("\n" + "="*10 + " Streamlit App: Pipeline Finished " + "="*10 + "\n")

    st.session_state.processing = False
    st.experimental_rerun() # Rerun to display results


if st.session_state.pipeline_results:
    results = st.session_state.pipeline_results
    st.markdown("---") # Visual separator
    st.header("✨ Generation Results ✨")

    col1, col2 = st.columns([2,1]) # Create two columns, video on left, info on right

    with col1: # Content for the left column (video)
        if results["success"] and results.get("video_path") and os.path.exists(results["video_path"]):
            st.subheader("🎬 Generated Video")
            try:
                video_file = open(results["video_path"], 'rb')
                video_bytes = video_file.read()
                st.video(video_bytes, format='video/mp4')
                video_file.close()
                
                with open(results["video_path"], "rb") as file_dl:
                    st.download_button(
                        label="⬇️ Download Video",
                        data=file_dl,
                        file_name=os.path.basename(results["video_path"]),
                        mime="video/mp4",
                        key=f"download_button_{results['video_path']}" # Unique key using path
                    )
            except FileNotFoundError:
                st.error(f"Video File Not Found: Could not find the video at `{results['video_path']}`. Please check the terminal for errors during generation.")
            except Exception as e:
                st.error(f"An error occurred displaying the video: {e}")
        elif results.get("video_path") and not os.path.exists(results["video_path"]):
             st.error(f"Video File was expected at `{results['video_path']}` but not found. Check terminal logs.")

    with col2: # Content for the right column (article info and script)
        if results.get("article_title"):
            st.subheader("📰 Original Article")
            st.markdown(f"**Title:** {results['article_title']}")
        if results.get("article_url"):
            st.markdown(f"**Link:** [{results['article_url']}]({results['article_url']})")

        if results.get("script_points"):
            st.subheader("📜 Generated Script")
            script_display_md = ""
            for i, point in enumerate(results["script_points"]):
                script_display_md += f"{i+1}. {point}\n"
            st.text_area("Script:", script_display_md, height=200, disabled=True, key=f"script_display_{results.get('article_url', time.time())}")

    # Display error messages below the columns if any
    if results.get("error_message"):
        st.markdown("---") # Separator before error message
        if results["success"]: 
            st.warning(f"⚠️ Heads up (minor issues may have occurred): {results['error_message']}")
        else: 
            st.error(f"⛔ Pipeline Failed: {results['error_message']}")
    elif not results["success"] and not results.get("video_path"): # If no video and no specific error msg
        st.error("⛔ Pipeline Failed: Video could not be generated. Check terminal for detailed logs.")

else:
    if not st.session_state.processing: 
        st.info("Click the 'Generate NewsReel Video' button in the sidebar to start.")

st.markdown("---")
st.caption("AI NewsReel Generator - Powered by Python & Streamlit")