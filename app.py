import streamlit as st
import cv2
import time
import config
from modules.detector import ObjectDetector
from modules.tracker import ObjectTracker
from modules.analytics import AnalyticsEngine

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="DeepCrowd AI",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CREATIVE STYLING (Cyberpunk Theme) ---
st.markdown("""
    <style>
        .stApp { background-color: #0e1117; }
        
        /* Header */
        .main-header {
            background: linear-gradient(90deg, #FF4B4B 0%, #4B0082 100%);
            padding: 20px;
            border-radius: 15px;
            color: white;
            text-align: center;
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(255, 75, 75, 0.3);
        }
        
        /* Glassmorphism Cards */
        .metric-card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            color: white;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }
        .metric-value {
            font-size: 36px;
            font-weight: bold;
            margin: 10px 0;
            background: -webkit-linear-gradient(#00AAFF, #00FFCC);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .metric-label { font-size: 14px; color: #aaa; text-transform: uppercase; }
        
        /* Alert Animation */
        .alert-box {
            background: linear-gradient(45deg, #ff0000, #ff4d4d);
            padding: 20px;
            border-radius: 15px;
            color: white;
            font-weight: bold;
            text-align: center;
            font-size: 24px;
            animation: pulse 1.5s infinite;
            border: 2px solid #fff;
        }
        @keyframes pulse {
            0% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.02); opacity: 0.9; }
            100% { transform: scale(1); opacity: 1; }
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. INITIALIZATION ---
@st.cache_resource
def load_system():
    detector = ObjectDetector(config.MODEL_PATH)
    tracker = ObjectTracker()
    return detector, tracker

def main():
    # --- SIDEBAR ---
    st.sidebar.title("⚙️ Control Panel")
    conf_thresh = st.sidebar.slider("🎯 Confidence", 0.1, 1.0, config.CONFIDENCE_THRESHOLD)
    panic_thresh = st.sidebar.slider("⚡ Panic Sensitivity", 5.0, 50.0, config.PANIC_VELOCITY_THRESHOLD)
    show_heatmap = st.sidebar.toggle("🔥 Show Heatmap", value=False)
    use_webcam = st.sidebar.toggle("📷 Live Webcam", value=True)

    # --- HEADER ---
    st.markdown("""
        <div class="main-header">
            <h1>📹 Smart Crowd Monitoring System</h1>
            <p>Real-Time Anomaly Detection | Density Estimation</p>
        </div>
    """, unsafe_allow_html=True)

    # --- METRICS ---
    col1, col2, col3, col4 = st.columns(4)
    kpi_occupancy = col1.empty()
    kpi_velocity = col2.empty()
    kpi_status = col3.empty()
    kpi_fps = col4.empty()

    # --- VIDEO FEED ---
    video_placeholder = st.empty()
    alert_placeholder = st.empty()

    # --- LOGIC ---
    detector, tracker = load_system()
    analytics = AnalyticsEngine(config.FRAME_WIDTH, config.FRAME_HEIGHT)

    if st.button("🚀 ACTIVATE SURVEILLANCE", type="primary", use_container_width=True):
        source = 0 if use_webcam else "video.mp4"
        cap = cv2.VideoCapture(source)
        prev_time = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break

            # Pre-processing
            frame = cv2.resize(frame, (config.FRAME_WIDTH, config.FRAME_HEIGHT))
            
            # Detection & Tracking
            detections = detector.detect(frame, conf_thresh)
            tracks = tracker.update_tracks(detections, frame)
            
            # Analytics
            is_panic, avg_velocity = analytics.process_behavior(tracks, panic_thresh)

            # Visualization
            if show_heatmap:
                frame = analytics.get_heatmap_overlay(frame)

            for track in tracks:
                if not track.is_confirmed(): continue
                track_id = track.track_id
                ltrb = track.to_ltrb()
                box_color = config.COLOR_RED if is_panic else config.COLOR_GREEN
                
                # Draw Box & ID
                cv2.rectangle(frame, (int(ltrb[0]), int(ltrb[1])), (int(ltrb[2]), int(ltrb[3])), box_color, 2)
                cv2.putText(frame, f"ID:{track_id}", (int(ltrb[0]), int(ltrb[1])-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2)

            # FPS Calculation
            curr_time = time.time()
            fps = 1 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0
            prev_time = curr_time

            # Update UI Cards
            kpi_occupancy.markdown(f"<div class='metric-card'><div class='metric-label'>Occupancy</div><div class='metric-value'>{analytics.occupancy}</div></div>", unsafe_allow_html=True)
            kpi_velocity.markdown(f"<div class='metric-card'><div class='metric-label'>Velocity</div><div class='metric-value'>{avg_velocity:.1f}</div></div>", unsafe_allow_html=True)
            
            status_text = "CRITICAL" if is_panic else "SAFE"
            status_color = "#FF0000" if is_panic else "#00FFCC"
            kpi_status.markdown(f"<div class='metric-card' style='border-color:{status_color}'><div class='metric-label'>Status</div><div class='metric-value' style='-webkit-text-fill-color:{status_color}'>{status_text}</div></div>", unsafe_allow_html=True)
            
            kpi_fps.markdown(f"<div class='metric-card'><div class='metric-label'>Latency</div><div class='metric-value'>{int(fps)} FPS</div></div>", unsafe_allow_html=True)

            if is_panic:
                alert_placeholder.markdown("<div class='alert-box'>🚨 STAMPEDE DETECTED!</div>", unsafe_allow_html=True)
            else:
                alert_placeholder.empty()

            video_placeholder.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), channels="RGB", use_column_width=True)

        cap.release()

if __name__ == "__main__":
    main()