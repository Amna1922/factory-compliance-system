import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime, timedelta
import time

# Configuration
API_URL = "http://localhost:8000"

def main():
    st.set_page_config(
        page_title="Factory Compliance Dashboard",
        page_icon="🏭",
        layout="wide"
    )
    
    st.title("🏭 Factory Compliance & Alert System")
    
    # Sidebar for navigation
    page = st.sidebar.selectbox(
        "Navigation",
        ["Live Monitor", "Alert Timeline", "Historical Log", "Upload Video"]
    )
    
    if page == "Live Monitor":
        live_monitor()
    elif page == "Alert Timeline":
        alert_timeline()
    elif page == "Historical Log":
        historical_log()
    elif page == "Upload Video":
        upload_video()

def live_monitor():
    st.header("📹 Live Feed Monitor")
    
    # Placeholder for video feed
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("Video Feed")
        # Placeholder for video
        st.image("https://via.placeholder.com/800x450.png?text=Live+Video+Feed", use_column_width=True)
    
    with col2:
        st.subheader("Compliance Status")
        
        # Mock status indicators
        st.markdown("### Active Alerts")
        alert_placeholder = st.empty()
        
        # Simulate real-time updates
        if st.button("Start Monitoring"):
            for i in range(10):
                # Simulate random events
                severity = ["LOW", "MEDIUM", "HIGH", "CRITICAL"][i % 4]
                color = {
                    "LOW": "🟢",
                    "MEDIUM": "🟡",
                    "HIGH": "🟠",
                    "CRITICAL": "🔴"
                }[severity]
                
                alert_placeholder.markdown(f"""
                {color} **{severity} ALERT** - Zone-{(i % 4) + 1}
                Violation: {["Walkway", "Intervention", "Panel", "Forklift"][i % 4]}
                Time: {datetime.now().strftime('%H:%M:%S')}
                """)
                time.sleep(1)
        
        # Mock stats
        st.metric("Total Violations Today", "23")
        st.metric("Active Alerts", "2")
        st.metric("Critical Alerts", "1")

def alert_timeline():
    st.header("⏱️ Alert Timeline")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        severity_filter = st.selectbox(
            "Severity",
            ["All", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
        )
    with col2:
        behavior_filter = st.selectbox(
            "Behavior Class",
            ["All", "Safe Walkway Violation", "Unauthorized Intervention", 
             "Opened Panel Cover", "Carrying Overload with Forklift"]
        )
    with col3:
        time_range = st.selectbox(
            "Time Range",
            ["Last Hour", "Last 24 Hours", "Last 7 Days"]
        )
    
    # Fetch events from API
    try:
        response = requests.get(f"{API_URL}/events")
        if response.status_code == 200:
            events = response.json().get("events", [])
            
            if events:
                df = pd.DataFrame(events)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp', ascending=False)
                
                # Apply filters
                if severity_filter != "All":
                    df = df[df['severity'] == severity_filter]
                if behavior_filter != "All":
                    df = df[df['behavior_class'] == behavior_filter]
                
                # Display as timeline
                for _, row in df.iterrows():
                    color = {
                        "LOW": "#28a745",
                        "MEDIUM": "#ffc107",
                        "HIGH": "#fd7e14",
                        "CRITICAL": "#dc3545"
                    }.get(row['severity'], "#6c757d")
                    
                    st.markdown(f"""
                    <div style="border-left: 4px solid {color}; padding: 10px; margin: 5px 0; background-color: #f8f9fa;">
                        <strong>{row['timestamp'].strftime('%H:%M:%S')}</strong> - 
                        <span style="color: {color}; font-weight: bold;">{row['severity']}</span> - 
                        {row['behavior_class']}<br>
                        <small>{row['event_description']}</small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No events found")
        else:
            st.error("Failed to fetch events")
    except:
        st.warning("Could not connect to API. Showing mock data.")
        show_mock_timeline()

def historical_log():
    st.header("📊 Historical Log")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=7))
    with col2:
        end_date = st.date_input("End Date", datetime.now())
    with col3:
        export_format = st.selectbox("Export Format", ["CSV", "JSON"])
    
    # Fetch and display events
    try:
        response = requests.get(f"{API_URL}/events")
        if response.status_code == 200:
            events = response.json().get("events", [])
            
            if events:
                df = pd.DataFrame(events)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                # Filter by date
                mask = (df['timestamp'] >= pd.Timestamp(start_date)) & (df['timestamp'] <= pd.Timestamp(end_date))
                df_filtered = df.loc[mask]
                
                if not df_filtered.empty:
                    st.dataframe(df_filtered)
                    
                    # Export button
                    if st.button("Export"):
                        if export_format == "CSV":
                            csv = df_filtered.to_csv(index=False)
                            st.download_button(
                                label="Download CSV",
                                data=csv,
                                file_name="compliance_log.csv",
                                mime="text/csv"
                            )
                        else:
                            json_str = df_filtered.to_json(orient='records', indent=2)
                            st.download_button(
                                label="Download JSON",
                                data=json_str,
                                file_name="compliance_log.json",
                                mime="application/json"
                            )
                else:
                    st.info("No events in selected date range")
            else:
                st.info("No events found")
        else:
            st.error("Failed to fetch events")
    except:
        st.warning("Could not connect to API. Showing mock data.")
        show_mock_history()

def upload_video():
    st.header("📤 Upload Video for Analysis")
    
    uploaded_file = st.file_uploader("Choose a video file", type=['mp4', 'avi', 'mov'])
    
    if uploaded_file is not None:
        if st.button("Analyze Video"):
            with st.spinner("Processing video..."):
                # Upload to API
                files = {"file": uploaded_file}
                response = requests.post(f"{API_URL}/analyze-video", files=files)
                
                if response.status_code == 200:
                    result = response.json()
                    st.success(f"Analysis complete! Found {result['total_violations']} violations")
                    
                    # Display results
                    for event in result['events']:
                        severity = event['severity']
                        color = {
                            "LOW": "✅",
                            "MEDIUM": "⚠️",
                            "HIGH": "🚨",
                            "CRITICAL": "🔥"
                        }.get(severity, "ℹ️")
                        
                        st.markdown(f"""
                        {color} **{severity}**: {event['behavior_class']}
                        - {event['event_description'][:100]}...
                        """)
                else:
                    st.error("Analysis failed")

def show_mock_timeline():
    """Show mock timeline data"""
    mock_events = [
        {"timestamp": datetime.now() - timedelta(minutes=5), "severity": "HIGH", "behavior_class": "Safe Walkway Violation", "event_description": "Person outside green markings"},
        {"timestamp": datetime.now() - timedelta(minutes=12), "severity": "CRITICAL", "behavior_class": "Carrying Overload with Forklift", "event_description": "Forklift carrying 4 blocks"},
        {"timestamp": datetime.now() - timedelta(minutes=23), "severity": "MEDIUM", "behavior_class": "Unauthorized Intervention", "event_description": "Person near equipment without green vest"},
    ]
    
    for event in mock_events:
        color = {
            "LOW": "#28a745",
            "MEDIUM": "#ffc107",
            "HIGH": "#fd7e14",
            "CRITICAL": "#dc3545"
        }.get(event['severity'], "#6c757d")
        
        st.markdown(f"""
        <div style="border-left: 4px solid {color}; padding: 10px; margin: 5px 0; background-color: #f8f9fa;">
            <strong>{event['timestamp'].strftime('%H:%M:%S')}</strong> - 
            <span style="color: {color}; font-weight: bold;">{event['severity']}</span> - 
            {event['behavior_class']}<br>
            <small>{event['event_description']}</small>
        </div>
        """, unsafe_allow_html=True)

def show_mock_history():
    """Show mock historical data"""
    mock_data = {
        "Event ID": ["EVT001", "EVT002", "EVT003"],
        "Timestamp": ["2026-01-15T10:30:00Z", "2026-01-15T10:15:00Z", "2026-01-15T09:45:00Z"],
        "Zone": ["Zone-1", "Zone-2", "Zone-1"],
        "Behavior": ["Walkway Violation", "Forklift Overload", "Panel Open"],
        "Severity": ["HIGH", "CRITICAL", "LOW"]
    }
    df = pd.DataFrame(mock_data)
    st.dataframe(df)

if __name__ == "__main__":
    main()