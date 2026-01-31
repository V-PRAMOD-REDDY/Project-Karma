import streamlit as st
import cv2
import time
import config
import tempfile
import base64
import os
from modules.detector import ObjectDetector
from modules.tracker import ObjectTracker
from modules.analytics import AnalyticsEngine

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Karma AI - Smart Crowd Monitor",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. ADVANCED CSS STYLING (Glassmorphism & Neon) ---
st.markdown("""
    <style>
        /* Import Google Font */
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Roboto:wght@300;400;700&display=swap');

        /* Main Background */
        .stApp {
            background-color: #050505;
            background-image: 
                radial-gradient(at 0% 0%, hsla(253,16%,7%,1) 0, transparent 50%), 
                radial-gradient(at 50% 0%, hsla(225,39%,30%,1) 0, transparent 50%), 
                radial-gradient(at 100% 0%, hsla(339,49%,30%,1) 0, transparent 50%);
            font-family: 'Roboto', sans-serif;
        }

        /* Navbar Styling */
        .navbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 30px;
            background: rgba(20, 20, 20, 0.6);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 0 0 20px 20px;
            margin-bottom: 30px;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        }
        
        .navbar-brand {
            font-family: 'Orbitron', sans-serif;
            font-size: 24px;
            font-weight: 700;
            background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 0 20px rgba(0, 201, 255, 0.5);
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #0a0a0a;
            border-right: 1px solid #333;
        }

        /* Metric Cards (Glassmorphism) */
        .metric-container {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 25px;
            text-align: center;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .metric-container::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
            transition: 0.5s;
        }
        
        .metric-container:hover::before {
            left: 100%;
        }

        .metric-container:hover {
            transform: translateY(-5px);
            border-color: #00C9FF;
            box-shadow: 0 10px 30px rgba(0, 201, 255, 0.2);
        }
        .metric-value {
            font-family: 'Orbitron', sans-serif;
            font-size: 2.8rem;
            font-weight: bold;
            color: #fff;
            margin: 10px 0;
            text-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
        }
        .metric-label {
            font-size: 0.9rem;
            color: #ccc;
            letter-spacing: 2px;
            text-transform: uppercase;
            font-weight: 500;
        }

        /* Status Indicators */
        .status-safe { 
            color: #00FFCC; 
            text-shadow: 0 0 15px rgba(0, 255, 204, 0.8); 
        }
        .status-danger { 
            color: #FF0055; 
            text-shadow: 0 0 15px rgba(255, 0, 85, 0.8);
            animation: danger-pulse 1s infinite alternate;
        }
        
        @keyframes danger-pulse {
            from { text-shadow: 0 0 10px rgba(255, 0, 85, 0.5); }
            to { text-shadow: 0 0 25px rgba(255, 0, 85, 1); }
        }

        /* Video Frame Container */
        .video-wrapper {
            background: #000;
            padding: 5px;
            border-radius: 15px;
            border: 1px solid #333;
            box-shadow: 0 0 40px rgba(0, 0, 0, 0.5);
            position: relative;
        }
        
        /* Custom Buttons */
        .stButton button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 10px 20px;
            font-weight: bold;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        .stButton button:hover {
            transform: scale(1.02);
            box-shadow: 0 6px 20px rgba(118, 75, 162, 0.4);
        }
        
        /* Stop Button Specific */
        div[data-testid="column"]:nth-of-type(2) .stButton button {
             background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
        }

        /* Logs Console */
        .console-logs {
            background-color: #0a0a0a;
            border: 1px solid #333;
            border-radius: 10px;
            padding: 15px;
            font-family: 'Courier New', monospace;
            color: #00FF00;
            height: 400px;
            overflow-y: auto;
            box-shadow: inset 0 0 20px rgba(0,0,0,0.5);
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if 'run_detection' not in st.session_state:
    st.session_state['run_detection'] = False
if 'current_page' not in st.session_state:
    st.session_state['current_page'] = 'Dashboard'

def start_detection():
    st.session_state['run_detection'] = True

def stop_detection():
    st.session_state['run_detection'] = False
    
def set_page(page_name):
    st.session_state['current_page'] = page_name

# --- 4. INITIALIZATION ---
@st.cache_resource
def load_system():
    detector = ObjectDetector(config.MODEL_PATH)
    tracker = ObjectTracker()
    return detector, tracker

# --- 5. AUDIO ALERT FUNCTION ---
def autoplay_audio(file_path: str):
    try:
        with open(file_path, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            md = f"""
                <audio autoplay>
                <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                </audio>
                """
            st.markdown(md, unsafe_allow_html=True)
    except FileNotFoundError:
        pass 

def main():
    # --- CUSTOM NAVBAR ---
    with st.container():
        # Layout: Brand | Spacer | Nav Items
        col_brand, col_nav = st.columns([1, 2])
        
        with col_brand:
            st.markdown('<div class="navbar-brand">KARMA AI</div>', unsafe_allow_html=True)
            
        with col_nav:
            # Using columns for horizontal buttons
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                if st.button("Dashboard", use_container_width=True): set_page('Dashboard')
            with c2:
                if st.button("About", use_container_width=True): set_page('About')
            with c3:
                if st.button("Manual", use_container_width=True): set_page('Manual')
            with c4:
                if st.button("Contact", use_container_width=True): set_page('Contact')
        
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True) # Spacer

    # --- PAGE ROUTING ---
    
    # ---------------- PAGE 1: DASHBOARD ----------------
    if st.session_state['current_page'] == 'Dashboard':
        
        # --- SIDEBAR CONTROLS ---
        st.sidebar.markdown("## 🎛️ Control Center")
        st.sidebar.markdown("Configure your surveillance parameters here.")
        st.sidebar.divider()
        
        st.sidebar.markdown("### 📡 Source")
        input_source = st.sidebar.radio("Input Type", ["Live Webcam", "Upload Video"], label_visibility="collapsed")
        
        video_path = None
        if input_source == "Upload Video":
            uploaded_file = st.sidebar.file_uploader("Upload MP4/AVI", type=['mp4', 'avi', 'mov'])
            if uploaded_file:
                tfile = tempfile.NamedTemporaryFile(delete=False)
                tfile.write(uploaded_file.read())
                video_path = tfile.name
        else:
            video_path = 0

        st.sidebar.markdown("### ⚙️ Settings")
        conf_thresh = st.sidebar.slider("Detection Confidence", 0.1, 1.0, config.CONFIDENCE_THRESHOLD)
        panic_thresh = st.sidebar.slider("Panic Sensitivity", 5.0, 50.0, config.PANIC_VELOCITY_THRESHOLD)
        
        c1, c2 = st.sidebar.columns(2)
        with c1:
            show_heatmap = st.toggle("Heatmap", value=False)
        with c2:
            enable_audio = st.toggle("Audio Alert", value=True)

        st.sidebar.divider()
        
        # Action Buttons
        col_start, col_stop = st.sidebar.columns(2)
        with col_start:
            st.button("▶ START", on_click=start_detection, type="primary", use_container_width=True)
        with col_stop:
            st.button("⏹ STOP", on_click=stop_detection, type="secondary", use_container_width=True)

        # --- METRICS DISPLAY ---
        m1, m2, m3, m4 = st.columns(4)
        
        with m1:
            kpi_occupancy = st.empty()
            kpi_occupancy.markdown(f"""<div class="metric-container"><div class="metric-label">Live Occupancy</div><div class="metric-value">0</div></div>""", unsafe_allow_html=True)
        with m2:
            kpi_velocity = st.empty()
            kpi_velocity.markdown(f"""<div class="metric-container"><div class="metric-label">Crowd Velocity</div><div class="metric-value">0.0</div></div>""", unsafe_allow_html=True)
        with m3:
            kpi_status = st.empty()
            kpi_status.markdown(f"""<div class="metric-container"><div class="metric-label">Status</div><div class="metric-value status-safe">SAFE</div></div>""", unsafe_allow_html=True)
        with m4:
            kpi_fps = st.empty()
            kpi_fps.markdown(f"""<div class="metric-container"><div class="metric-label">System FPS</div><div class="metric-value">0</div></div>""", unsafe_allow_html=True)

        st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)

        # --- MAIN VISUALIZATION AREA ---
        col_video, col_logs = st.columns([2.5, 1])
        
        with col_video:
            st.markdown("### Live Surveillance Feed")
            video_placeholder = st.empty()
            video_placeholder.markdown(
                """
                <div style='background:#000; height:480px; border-radius:15px; display:flex; flex-direction:column; align-items:center; justify-content:center; border:1px solid #333; box-shadow: 0 0 20px rgba(0,0,0,0.5);'>
                    <h1 style='font-size: 60px;'>📹</h1>
                    <h3 style='color:#555; font-family:Roboto;'>System Standby</h3>
                    <p style='color:#444;'>Click START to activate</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
            audio_placeholder = st.empty()

        with col_logs:
            st.markdown("### System Events")
            log_placeholder = st.empty()
            log_placeholder.markdown(
                """
                <div class="console-logs">
                > System initialized...<br>
                > Waiting for video stream...<br>
                > Logic engine ready.
                </div>
                """, 
                unsafe_allow_html=True
            )

        # --- BACKEND LOGIC ---
        if st.session_state['run_detection']:
            if input_source == "Upload Video" and video_path is None:
                st.toast("⚠️ Please upload a video file first!", icon="⚠️")
                st.session_state['run_detection'] = False
            else:
                detector, tracker = load_system()
                analytics = AnalyticsEngine(config.FRAME_WIDTH, config.FRAME_HEIGHT)
                
                cap = cv2.VideoCapture(video_path)
                prev_time = 0
                alert_sound_path = "alert.mp3" 
                
                while cap.isOpened() and st.session_state['run_detection']:
                    ret, frame = cap.read()
                    if not ret:
                        st.toast("✅ Video Playback Finished", icon="✅")
                        st.session_state['run_detection'] = False
                        break

                    # 1. Processing
                    frame_resized = cv2.resize(frame, (config.FRAME_WIDTH, config.FRAME_HEIGHT))
                    detections = detector.detect(frame_resized, conf_thresh)
                    tracks = tracker.update_tracks(detections, frame_resized)
                    is_panic, avg_velocity = analytics.process_behavior(tracks, panic_thresh)

                    # 2. Visualization
                    visual_frame = frame_resized.copy()
                    if show_heatmap:
                        visual_frame = analytics.get_heatmap_overlay(visual_frame)

                    for track in tracks:
                        if not track.is_confirmed(): continue
                        track_id = track.track_id
                        ltrb = track.to_ltrb()
                        
                        # Logic Colors
                        color = (0, 0, 255) if is_panic else (0, 255, 127) # Red / Green
                        
                        # Fancy Bounding Box
                        p1 = (int(ltrb[0]), int(ltrb[1]))
                        p2 = (int(ltrb[2]), int(ltrb[3]))
                        
                        # Corner Style Box
                        cv2.rectangle(visual_frame, p1, p2, color, 1)
                        
                        # ID Tag
                        label = f"ID {track_id}"
                        (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
                        cv2.rectangle(visual_frame, (p1[0], p1[1]-20), (p1[0]+w+10, p1[1]), color, -1)
                        cv2.putText(visual_frame, label, (p1[0]+5, p1[1]-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255), 1)

                    # 3. Alert Logic
                    log_content = ""
                    if is_panic:
                        # Warning Overlay
                        overlay = visual_frame.copy()
                        cv2.rectangle(overlay, (0, 0), (config.FRAME_WIDTH, config.FRAME_HEIGHT), (0, 0, 255), -1)
                        cv2.addWeighted(overlay, 0.3, visual_frame, 0.7, 0, visual_frame)
                        cv2.putText(visual_frame, "!!! PANIC DETECTED !!!", (100, 250), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
                        
                        status_html = f"""<div class="metric-container" style="border-color:#FF0055; box-shadow:0 0 30px rgba(255,0,85,0.6);"><div class="metric-label">Status</div><div class="metric-value status-danger">PANIC</div></div>"""
                        
                        log_content = f"""
                        <div class="console-logs">
                        <span style="color:red;">[CRITICAL] High Velocity Detected: {avg_velocity:.2f} px/f</span><br>
                        <span style="color:red;">[ALERT] Triggering Safety Protocols...</span><br>
                        > Occupancy: {analytics.occupancy}<br>
                        > Analysis Active...
                        </div>
                        """
                        
                        if enable_audio and os.path.exists(alert_sound_path):
                            autoplay_audio(alert_sound_path)
                    else:
                        status_html = f"""<div class="metric-container"><div class="metric-label">Status</div><div class="metric-value status-safe">SAFE</div></div>"""
                        log_content = f"""
                        <div class="console-logs">
                        <span style="color:#00FF00;">[NORMAL] System Nominal</span><br>
                        > Velocity: {avg_velocity:.2f} px/f<br>
                        > Occupancy: {analytics.occupancy}<br>
                        > Tracking {len(tracks)} individuals...
                        </div>
                        """
                        audio_placeholder.empty()

                    # 4. FPS Calculation
                    curr_time = time.time()
                    fps = 1 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0
                    prev_time = curr_time

                    # 5. UI Updates
                    kpi_occupancy.markdown(f"""<div class="metric-container"><div class="metric-label">Live Occupancy</div><div class="metric-value">{analytics.occupancy}</div></div>""", unsafe_allow_html=True)
                    kpi_velocity.markdown(f"""<div class="metric-container"><div class="metric-label">Crowd Velocity</div><div class="metric-value">{avg_velocity:.1f}</div></div>""", unsafe_allow_html=True)
                    kpi_status.markdown(status_html, unsafe_allow_html=True)
                    kpi_fps.markdown(f"""<div class="metric-container"><div class="metric-label">System FPS</div><div class="metric-value">{int(fps)}</div></div>""", unsafe_allow_html=True)
                    
                    log_placeholder.markdown(log_content, unsafe_allow_html=True)
                    
                    video_placeholder.image(cv2.cvtColor(visual_frame, cv2.COLOR_BGR2RGB), channels="RGB", use_column_width=True)

                cap.release()

    # ---------------- PAGE 2: ABOUT ----------------
    elif st.session_state['current_page'] == 'About':
        st.markdown("## About Karma AI")
        st.markdown("""
        <div style="background: rgba(255,255,255,0.05); padding: 30px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.1);">
            <p style="font-size: 18px; line-height: 1.6;">
            <b>Karma AI</b> is a next-generation surveillance system that transforms passive CCTV cameras into active intelligent agents. 
            By leveraging <b>YOLOv8</b> for detection and <b>DeepSORT</b> for tracking, it provides real-time behavioral analytics to prevent crowd disasters.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### Core Features")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("""
            <div class="metric-container">
            <h4>Advanced AI</h4>
            <p style="font-size:14px;">Powered by YOLOv8 Nano for high-speed, accurate person detection.</p>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown("""
            <div class="metric-container">
            <h4>Instant Alerts</h4>
            <p style="font-size:14px;">Detects panic situations (running) and triggers immediate alarms.</p>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown("""
            <div class="metric-container">
            <h4>Heatmap Analytics</h4>
            <p style="font-size:14px;">Visualizes crowd density hotspots for better resource management.</p>
            </div>
            """, unsafe_allow_html=True)

    # ---------------- PAGE 3: MANUAL ----------------
    elif st.session_state['current_page'] == 'Manual':
        st.markdown("## User Guide")
        
        st.info("Follow this step-by-step guide to set up your surveillance system.")
        
        st.markdown("""
        ### 1. System Setup
        - Ensure your **Webcam** is connected or have a **Video File** ready.
        - Check the **Control Panel** on the left sidebar.

        ### 2. Configuration
        - **Source:** Select 'Live Webcam' for real-time monitoring.
        - **Confidence:** Adjust slider to filter weak detections (Default: 0.4).
        - **Panic Threshold:** Set the speed limit for triggering alarms (Default: 15.0).

        ### 3. Execution
        - Click the **START** button to begin analysis.
        - The dashboard will update with live metrics and video feed.
        - **Red Alert** means panic is detected. **Green** means safe.

        ### 4. Features
        - Toggle **Heatmap** to see density zones.
        - Toggle **Audio Alert** to mute/unmute the siren.
        """)

    # ---------------- PAGE 4: CONTACT ----------------
    elif st.session_state['current_page'] == 'Contact':
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("## 📞 Get in Touch")
            st.write("Have questions or want to deploy Karma AI in your facility? Send us a message!")
            
            with st.form("contact_form"):
                name = st.text_input("Name", placeholder="Thanvika")
                email = st.text_input("Email", placeholder="Thanvika@gmail.com")
                type_ = st.selectbox("Inquiry Type", ["General Support", "Business Deployment", "Technical Issue"])
                msg = st.text_area("Message", placeholder="How can we help you?")
                
                submitted = st.form_submit_button("Send Message", use_container_width=True)
                if submitted:
                    st.success("Message Sent! We will get back to you shortly.")

        with col2:
            st.markdown("### 📍 Contact Info")
            st.markdown("""
            <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 15px;">
                <p><b>Team Karma</b></p>
                <p>Siddartha Institute of Science and Technology</p>
                <p>Puttur, Andhra Pradesh, India</p>
                <br>
                <p>📧 support@karma-ai.com</p>
                <p>📱 +91 8867549105</p>
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()