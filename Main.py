import streamlit as st
import pdfplumber
import pytesseract
from PIL import Image
import io
import speech_recognition as sr
import tempfile
import os
import threading
import base64
import time
from transformers import pipeline

# Set tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Load Granite LLM from Hugging Face
@st.cache_resource
def load_granite_model():
    try:
        generator = pipeline(
            "text-generation", 
            model="ibm-granite/granite-3b-code-instruct",
            device_map="auto"
        )
        return generator
    except Exception as e:
        st.error(f"Error loading Granite model: {str(e)}")
        return None

# Initialize the model
granite_generator = load_granite_model()

# Set page configuration
st.set_page_config(
    page_title="EchoVerse - AI for Visually Impaired Readers",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for enhanced UI
def local_css():
    st.markdown("""
    <style>
    /* Global Styles */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-attachment: fixed;
        background-size: cover;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Main Content Area */
    .main .block-container {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 2rem;
        margin-top: 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Header */
    .header {
        background: linear-gradient(135deg, #43cea2 0%, #185a9d 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    
    .header::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        animation: pulse 8s infinite linear;
    }
    
    .header h1 {
        font-size: 3rem;
        margin-bottom: 0.5rem;
        font-weight: 700;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
        position: relative;
        z-index: 2;
    }
    
    .header p {
        font-size: 1.2rem;
        opacity: 0.9;
        position: relative;
        z-index: 2;
    }
    
    /* Cards */
    .card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(245, 247, 250, 0.9) 100%);
        color: black;
        padding: 2rem;
        border-radius: 16px;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
        margin-bottom: 1.5rem;
        border-left: 5px solid #43cea2;
        transition: all 0.3s ease;
    }
    
    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 30px rgba(0, 0, 0, 0.12);
    }
    
    /* Buttons */
    .stButton button {
        background: linear-gradient(135deg, #43cea2 0%, #185a9d 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
        box-shadow: 0 4px 10px rgba(67, 206, 162, 0.3);
    }
    
    .stButton button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(67, 206, 162, 0.4);
        background: linear-gradient(135deg, #3ab894 0%, #134a80 100%);
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2c3e50 0%, #4ca1af 100%);
        padding: 2rem 1rem;
    }
    
    .sidebar-header {
        text-align: center;
        margin-bottom: 2rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid rgba(255, 255, 255, 0.2);
    }
    
    .sidebar-header h2 {
        color: white;
        font-size: 1.8rem;
        margin-bottom: 0.5rem;
        font-weight: 700;
    }
    
    .sidebar-section {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .sidebar-section h3 {
        color: white;
        font-size: 1.2rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .sidebar-section h3::before {
        content: '';
        display: inline-block;
        width: 8px;
        height: 8px;
        background: #43cea2;
        border-radius: 50%;
    }
    
    /* Voice Command Section */
    .voice-command {
        background: linear-gradient(135deg, #ff6b6b 0%, #ff8e53 100%);
        padding: 1.5rem;
        border-radius: 16px;
        color: white;
        margin-top: 1.5rem;
        box-shadow: 0 8px 20px rgba(255, 107, 107, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .voice-command::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -50%;
        width: 100%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        animation: pulse 4s infinite linear;
    }
    
    .voice-command h3 {
        margin-top: 0;
        font-size: 1.4rem;
        position: relative;
        z-index: 2;
    }
    
    .voice-command ul {
        position: relative;
        z-index: 2;
    }
    
    .voice-command li {
        margin-bottom: 0.5rem;
        padding: 0.5rem;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    
    .voice-command li:hover {
        background: rgba(255, 255, 255, 0.2);
        transform: translateX(5px);
    }
    
    /* Footer */
    .footer {
        text-align: center;
        margin-top: 3rem;
        padding: 2rem;
        color: white;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
        border-radius: 16px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Audio Controls */
    .audio-controls {
        display: flex;
        gap: 1rem;
        margin: 1.5rem 0;
    }
    
    /* Listening Indicator */
    .listening-indicator {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 50px;
        animation: pulse 1.5s infinite;
        margin: 1.5rem 0;
        text-align: center;
        font-weight: 600;
        box-shadow: 0 5px 15px rgba(255, 107, 107, 0.4);
    }
    
    /* File Uploader */
    .stFileUploader {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1.5rem;
        backdrop-filter: blur(10px);
        border: 2px dashed rgba(255, 255, 255, 0.3);
    }
    
    /* Metrics */
    .stMetric {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(245, 247, 250, 0.9) 100%);
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.08);
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #43cea2 0%, #185a9d 100%);
        color: white;
        border-radius: 12px;
        padding: 1rem;
        font-weight: 600;
    }
    
    /* Form Elements */
    .stSelectbox, .stRadio, .stSlider {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 0.5rem;
        margin: 0.5rem 0;
    }
    
    .stSelectbox > div, .stRadio > div {
        background: transparent !important;
    }
    
    /* Labels */
    .stMarkdown h4 {
        color: white !important;
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .stMarkdown h4::before {
        content: '';
        display: inline-block;
        width: 6px;
        height: 6px;
        background: #43cea2;
        border-radius: 50%;
    }
    
    /* Animations */
    @keyframes pulse {
        0% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.02); opacity: 0.9; }
        100% { transform: scale(1); opacity: 1; }
    }
    
    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
        100% { transform: translateY(0px); }
    }
    
    /* Text Elements */
    h1, h2, h3, h4, h5, h6 {
        color: #2c3e50;
    }
    
    /* Info Box */
    .stAlert {
        border-radius: 12px;
    }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #43cea2 0%, #185a9d 100%);
        border-radius: 10px;
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .header h1 {
            font-size: 2rem;
        }
        
        .card {
            padding: 1.5rem;
        }
        
        .audio-controls {
            flex-direction: column;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# Language options
LANGUAGE_OPTIONS = {
    "English": {"code": "en", "voice": "Google UK English Female"},
    "Spanish": {"code": "es", "voice": "Google español"}, 
    "French": {"code": "fr", "voice": "Google français"},
    "German": {"code": "de", "voice": "Google Deutsch"},
    "Hindi": {"code": "hi", "voice": "Google हिन्दी"}
}

# Enhance text using Granite LLM
def enhance_text_with_granite(text, mode="neutral"):
    if granite_generator is None:
        st.error("Granite model not loaded. Please check your internet connection.")
        return text
    
    if mode == "neutral":
        return text
    
    try:
        if mode == "explanatory":
            prompt = f"Rewrite the following text in a simpler and more explanatory way:\n\n{text}\n\nSimplified Version:"
        elif mode == "summary":
            prompt = f"Summarize the following text clearly and concisely:\n\n{text}\n\nSummary:"
        else:
            return text

        # Generate enhanced text
        output = granite_generator(
            prompt, 
            max_new_tokens=300, 
            temperature=0.7, 
            top_p=0.9,
            do_sample=True,
            pad_token_id=granite_generator.tokenizer.eos_token_id
        )
        
        # Extract the generated text
        generated_text = output[0]["generated_text"]
        
        # Remove the prompt from the generated text
        enhanced_text = generated_text.replace(prompt, "").strip()
        
        return enhanced_text
        
    except Exception as e:
        st.error(f"Granite LLM Error: {str(e)}")
        return text

# Browser-based text-to-speech using JavaScript
def text_to_speech(text, language="English", voice_type="Female"):
    # Clean text for JavaScript
    clean_text = text.replace('"', '\\"').replace('\n', ' ')
    
    # Voice selection
    voice_name = LANGUAGE_OPTIONS[language]["voice"]
    if voice_type == "Male" and language == "English":
        voice_name = "Google UK English Male"
    
    # JavaScript code for browser TTS
    js_code = f"""
    <script>
        function speakText() {{
            if ('speechSynthesis' in window) {{
                // Stop any ongoing speech
                window.speechSynthesis.cancel();
                
                const speech = new SpeechSynthesisUtterance();
                speech.text = "{clean_text}";
                speech.volume = 1;
                speech.rate = 1;
                speech.pitch = 1;
                speech.lang = '{LANGUAGE_OPTIONS[language]["code"]}';
                
                // Try to find the specific voice
                const voices = window.speechSynthesis.getVoices();
                const preferredVoice = voices.find(voice => 
                    voice.name.includes('{voice_name}') || 
                    voice.lang.startsWith('{LANGUAGE_OPTIONS[language]["code"]}')
                );
                
                if (preferredVoice) {{
                    speech.voice = preferredVoice;
                }}
                
                window.speechSynthesis.speak(speech);
            }} else {{
                alert("Your browser doesn't support speech synthesis. Please try Chrome or Edge.");
            }}
        }}
        
        // Wait for voices to load
        if (window.speechSynthesis.getVoices().length === 0) {{
            window.speechSynthesis.addEventListener('voiceschanged', function() {{
                speakText();
            }});
        }} else {{
            speakText();
        }}
    </script>
    """
    
    # Use Streamlit's HTML component to execute JavaScript
    st.components.v1.html(js_code, height=0)

# Stop speech function
def stop_speech():
    js_code = """
    <script>
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();
        }
    </script>
    """
    st.components.v1.html(js_code, height=0)

# Extract text from PDF
def extract_text_from_pdf(uploaded_file):
    text = ""
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        st.error(f"Error extracting text from PDF: {str(e)}")
    return text

# Extract text from image using OCR
def extract_text_from_image(uploaded_file):
    text = ""
    try:
        image = Image.open(uploaded_file)
        text = pytesseract.image_to_string(image)
    except Exception as e:
        st.error(f"Error extracting text from image: {str(e)}")
    return text

# Listen for voice commands
def listen_for_command():
    try:
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            st.session_state.listening = True
            st.info("Listening for command... (Speak now)")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                command = recognizer.recognize_google(audio).lower()
                return command
            except sr.WaitTimeoutError:
                return None
            except sr.UnknownValueError:
                st.error("Could not understand the audio")
                return None
            except sr.RequestError as e:
                st.error(f"Speech recognition error: {e}")
                return None
    except Exception as e:
        st.error(f"Microphone error: {e}")
        return None
    finally:
        st.session_state.listening = False

# Process voice commands
def process_voice_command(command):
    if not command:
        return
    
    command = command.lower()
    
    if "start reading" in command or "read" in command:
        if st.session_state.extracted_text:
            # Set flag to trigger TTS
            st.session_state.should_read = True
            st.success("Started reading the document")
        else:
            st.error("No text available to read. Please upload a document first.")
    
    elif "stop" in command:
        stop_speech()
        st.session_state.should_read = False
        st.success("Stopped reading")
    
    elif "continue" in command or "resume" in command:
        # For simplicity, we'll restart reading from the beginning
        # In a more advanced implementation, we could track reading position
        if st.session_state.extracted_text:
            st.session_state.should_read = True
            st.success("Resumed reading")
        else:
            st.error("No text available to read. Please upload a document first.")
    
    elif "next page" in command or "next" in command:
        # This would require tracking pages in PDF documents
        # For now, we'll just indicate this feature is not fully implemented
        st.info("Page navigation is not fully implemented in this version")
    
    elif "change language" in command:
        languages = list(LANGUAGE_OPTIONS.keys())
        current_index = languages.index(st.session_state.language)
        next_index = (current_index + 1) % len(languages)
        st.session_state.language = languages[next_index]
        st.success(f"Language changed to {languages[next_index]}")
        st.rerun()
    
    else:
        st.warning(f"Command not recognized: {command}")

# Main application
def main():
    # Apply custom CSS
    local_css()
    
    # Initialize session state
    if 'extracted_text' not in st.session_state:
        st.session_state.extracted_text = ""
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 0
    if 'language' not in st.session_state:
        st.session_state.language = "English"
    if 'voice_type' not in st.session_state:
        st.session_state.voice_type = "Female"
    if 'tone' not in st.session_state:
        st.session_state.tone = "neutral"
    if 'is_reading' not in st.session_state:
        st.session_state.is_reading = False
    if 'listening' not in st.session_state:
        st.session_state.listening = False
    if 'should_read' not in st.session_state:
        st.session_state.should_read = False
    if 'last_command' not in st.session_state:
        st.session_state.last_command = ""
    if 'enhanced_text' not in st.session_state:
        st.session_state.enhanced_text = ""
    
    # Header
    st.markdown("""
    <div class="header">
        <h1>📚 EchoVerse – AI-Powered Audiobook Creation Tool</h1>
        <p>Assistive Technology for Visually Impaired Readers</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-header">
            <h2>⚙ Settings</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Language selection
        st.markdown("#### 🌍 Language")
        language = st.selectbox(
            "Select Language",
            options=list(LANGUAGE_OPTIONS.keys()),
            index=list(LANGUAGE_OPTIONS.keys()).index(st.session_state.language),
            label_visibility="collapsed"
        )
        
        # Voice selection
        st.markdown("#### 🔊 Voice Type")
        voice_type = st.radio(
            "Voice Type",
            ["Female", "Male"],
            index=0 if st.session_state.voice_type == "Female" else 1,
            label_visibility="collapsed"
        )
        
        # Tone selection
        st.markdown("#### 🎵 Narration Mode")
        tone = st.radio(
            "Narration Mode",
            ["Neutral", "Explanatory", "Summary"],
            index=0 if st.session_state.tone == "neutral" else (1 if st.session_state.tone == "explanatory" else 2),
            label_visibility="collapsed"
        )
        
        # Update session state
        st.session_state.language = language
        st.session_state.voice_type = voice_type
        st.session_state.tone = tone.lower()
        
        # Voice preview
        if st.button("🔊 Preview Voice", use_container_width=True):
            preview_text = "This is a preview of the selected voice."
            if tone == "Explanatory":
                preview_text = "Let me explain. " + preview_text
            elif tone == "Summary":
                preview_text = "Here's a summary. " + preview_text
            text_to_speech(preview_text, language, voice_type)
        
        # Voice commands section
        st.markdown("""
        <div class="voice-command">
            <h3>🎤 Voice Commands</h3>
            <p>Try saying:</p>
            <ul>
                <li>"Start reading"</li>
                <li>"Stop"</li>
                <li>"Continue"</li>
                <li>"Next page"</li>
                <li>"Change language"</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # File upload
    st.markdown("### 📤 Upload Document")
    uploaded_file = st.file_uploader(
        "Upload PDF or Image", 
        type=['pdf', 'png', 'jpg', 'jpeg'],
        label_visibility="collapsed"
    )
    
    if uploaded_file is not None:
        # File details
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Filename", uploaded_file.name)
        with col2:
            st.metric("Size", f"{uploaded_file.size / 1024:.1f} KB")
        with col3:
            st.metric("Type", uploaded_file.type.split('/')[-1].upper())
        
        # Extract text
        with st.spinner("📖 Extracting text..."):
            if uploaded_file.type == "application/pdf":
                extracted_text = extract_text_from_pdf(uploaded_file)
            else:
                extracted_text = extract_text_from_image(uploaded_file)
        
        if extracted_text:
            st.session_state.extracted_text = extracted_text
            
            # Enhance text with Granite LLM based on selected tone
            if st.session_state.tone != "neutral":
                with st.spinner("🧠 Enhancing text with AI..."):
                    st.session_state.enhanced_text = enhance_text_with_granite(
                        extracted_text, st.session_state.tone
                    )
            else:
                st.session_state.enhanced_text = extracted_text
            
            # Text preview
            with st.expander("📝 View Extracted Text", expanded=True):
                if st.session_state.tone != "neutral":
                    st.info(f"Text enhanced with {st.session_state.tone} mode")
                    st.text_area("Enhanced Text", st.session_state.enhanced_text, height=300, label_visibility="collapsed")
                else:
                    st.text_area("Original Text", extracted_text, height=300, label_visibility="collapsed")
            
            # Current settings
            st.info(f"🎯 Settings: {st.session_state.language}, {st.session_state.voice_type} voice, {st.session_state.tone} mode")
            
            # Audio controls
            st.markdown("### 🔊 Audio Controls")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("🔊 Read Text", use_container_width=True, type="primary"):
                    text_to_speech(
                        st.session_state.enhanced_text, 
                        st.session_state.language, 
                        st.session_state.voice_type
                    )
            
            with col2:
                if st.button("⏹ Stop", use_container_width=True):
                    stop_speech()
                    st.session_state.should_read = False
            
            with col3:
                if st.button("📋 Copy Text", use_container_width=True):
                    st.code(st.session_state.enhanced_text)
                    st.success("Text copied to clipboard!")
                    
            with col4:
                # New voice commands button
                if st.button("🎤 Start Voice Commands", use_container_width=True):
                    command = listen_for_command()
                    if command:
                        st.session_state.last_command = command
                        process_voice_command(command)
            
            # Display last command
            if st.session_state.last_command:
                st.info(f"Last command: '{st.session_state.last_command}'")
            
            # Listening indicator
            if st.session_state.get('listening', False):
                st.markdown('<div class="listening-indicator">🎤 Listening...</div>', unsafe_allow_html=True)
            
            # Trigger TTS if should_read is True
            if st.session_state.get('should_read', False):
                text_to_speech(
                    st.session_state.enhanced_text, 
                    st.session_state.language, 
                    st.session_state.voice_type
                )
                st.session_state.should_read = False
        
        else:
            st.error("❌ Could not extract text from the file")
    else:
        # Instructions
        st.markdown("""
        <div class="card">
            <h3>👆 Get Started</h3>
            <p>Upload a document to convert it to audio</p>
            
            <h4>📋 Supported formats:</h4>
            <ul>
                <li>PDF documents</li>
                <li>Images (PNG, JPG, JPEG)</li>
            </ul>
            
            <h4>🎯 Features:</h4>
            <ul>
                <li>Multi-language support (5 languages)</li>
                <li>Male/Female voices</li>
                <li>AI-enhanced text (explanatory/summary modes)</li>
                <li>Voice commands</li>
                <li>Browser-based text-to-speech</li>
            </ul>
            
            <h4>🔊 Audio Requirements:</h4>
            <ul>
                <li>Use Chrome or Edge for best results</li>
                <li>Allow audio permissions in your browser</li>
                <li>Ensure your speakers are working</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Granite LLM status
    if granite_generator:
        st.success("✅ Granite LLM loaded successfully")
    else:
        st.warning("⚠️ Granite LLM not available. Using basic text processing.")
    
    # Browser compatibility note
    st.markdown("""
    <div class="card">
        <h4 style="color: black;">ℹ Browser Compatibility</h4>
        <p>For the best audio experience, please use:</p>
        <ul>
            <li>Google Chrome (recommended)</li>
            <li>Microsoft Edge</li>
            <li>Mozilla Firefox</li>
        </ul>
        <p>Make sure to allow audio permissions when prompted by your browser.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div class="footer">
        <p>EchoVerse - Making reading accessible for everyone | Built with ❤ for visually impaired readers</p>
        <p>Powered by Granite LLM from IBM</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
