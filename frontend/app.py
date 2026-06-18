import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime, timedelta
import time
from pathlib import Path

# Configuration
API_URL = "http://localhost:8000"

def main():
    st.set_page_config(
        page_title="Factory Compliance Dashboard",
        page_icon="🏭",
        layout="wide"
    )
    
    st.title("🏭 Factory Compliance & Alert System")
    
    # Sidebar
    page = st.sidebar.selectbox(
        "Navigation",
        ["Dataset Overview", "Live Monitor", "Batch Analysis", "Alert Timeline", "Historical Log"]
    )
    
    if page == "Dataset Overview":
        dataset_overview()
    elif page == "Live Monitor":
        live_monitor()
    elif page == "Batch Analysis":
        batch_analysis()
    elif page == "Alert Timeline":
        alert_timeline()
    elif page == "Historical Log":
        historical_log()

def dataset_overview():
    st.header("📊 Dataset Overview")
    
    try:
        response = requests.get(f"{API_URL}/dataset/stats")
        if response.status_code == 200:
            stats = response.json()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Training Videos", stats["train"]["total"])
            with col2:
                st.metric("Total Test Videos", stats["test"]["total"])
            with col3:
                total_unsafe = stats["train"]["unsafe"] + stats["test"]["unsafe"]
                st.metric("Total Unsafe Videos", total_unsafe)
            
            # Show class distribution
            st.subheader("Class Distribution - Training Set")
            train_classes = stats["train"].get("class_counts", {})
            if train_classes:
                df = pd.DataFrame({
                    "Class": list(train_classes.keys()),
                    "Count": list(train_classes.values())
                })
                st.bar_chart(df.set_index("Class"))
            
            st.subheader("Class Distribution - Test Set")
            test_classes = stats["test"].get("class_counts", {})
            if test_classes:
                df = pd.DataFrame({
                    "Class": list(test_classes.keys()),
                    "Count": list(test_classes.values())
                })
                st.bar_chart(df.set_index("Class"))
        else:
            st.error("Failed to fetch dataset stats")
    except Exception as e:
        st.error(f"Error: {e}")
        show_mock_stats()

def batch_analysis():
    st.header("🔍 Batch Analysis")
    
    col1, col2 = st.columns(2)
    with col1:
        split = st.selectbox("Dataset Split", ["train", "test"])
    with col2:
        max_videos = st.slider("Max Videos to Process", 1, 20, 5)
    
    if st.button("Run Batch Analysis"):
        with st.spinner(f"Analyzing {max_videos} videos..."):
            response = requests.post(
                f"{API_URL}/analyze-batch",
                params={"split": split, "max_videos": max_videos}
            )
            
            if response.status_code == 200:
                result = response.json()
                
                st.success(f"✅ Analysis complete!")
                st.metric("Violations Found", result.get("violations", 0))
                st.metric("Videos Processed", result.get("processed", 0))
                
                if result.get("events"):
                    st.subheader("Detected Violations")
                    for event in result["events"][:10]:
                        severity = event['severity']
                        emoji = {
                            "LOW": "🟢",
                            "MEDIUM": "🟡",
                            "HIGH": "🟠",
                            "CRITICAL": "🔴"
                        }.get(severity, "⚪")
                        
                        st.markdown(f"""
                        {emoji} **{severity}** - {event['behavior_class']}
                        - File: {event['clip_id']}
                        - {event['event_description'][:100]}...
                        """)
            else:
                st.error("Analysis failed")

def live_monitor():
    st.header("📹 Live Monitor")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("Video Feed")
        st.image("https://via.placeholder.com/800x450.png?text=Live+Video+Feed", use_column_width=True)
    
    with col2:
        st.subheader("Compliance Status")
        
        # Show recent alerts
        try:
            response = requests.get(f"{API_URL}/events")
            if response.status_code == 200:
                events = response.json().get("events", [])
                if events:
                    latest = events[0]
                    severity = latest['severity']
                    color = {
                        "LOW": "🟢",
                        "MEDIUM": "🟡",
                        "HIGH": "🟠",
                        "CRITICAL": "🔴"
                    }.get(severity, "⚪")
                    
                    st.markdown(f"""
                    ### Latest Alert
                    {color} **{severity}** - {latest['behavior_class']}
                    Time: {latest['timestamp'][:19]}
                    """)
        except:
            pass
        
        # Mock stats
        st.metric("Active Alerts", "2")
        st.metric("Today's Violations", "12")

def alert_timeline():
    st.header("⏱️ Alert Timeline")
    
    # Filters
    col1, col2 = st.columns(2)
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
    
    # Fetch events
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
    
    # Export options
    col1, col2 = st.columns(2)
    with col1:
        export_format = st.selectbox("Export Format", ["CSV", "JSON"])
    with col2:
        if st.button("Export Log"):
            try:
                response = requests.get(f"{API_URL}/events")
                if response.status_code == 200:
                    events = response.json().get("events", [])
                    if events:
                        df = pd.DataFrame(events)
                        if export_format == "CSV":
                            csv = df.to_csv(index=False)
                            st.download_button(
                                label="Download CSV",
                                data=csv,
                                file_name="compliance_log.csv",
                                mime="text/csv"
                            )
                        else:
                            json_str = df.to_json(orient='records', indent=2)
                            st.download_button(
                                label="Download JSON",
                                data=json_str,
                                file_name="compliance_log.json",
                                mime="application/json"
                            )
                    else:
                        st.warning("No events to export")
            except:
                st.error("Failed to export")
    
    # Display log
    try:
        response = requests.get(f"{API_URL}/events")
        if response.status_code == 200:
            events = response.json().get("events", [])
            if events:
                df = pd.DataFrame(events)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                st.dataframe(df)
            else:
                st.info("No events found")
        else:
            st.error("Failed to fetch events")
    except:
        st.warning("Could not connect to API")

def show_mock_timeline():
    """Show mock timeline data"""
    mock_events = [
        {"timestamp": datetime.now() - timedelta(minutes=5), "severity": "HIGH", 
         "behavior_class": "Safe Walkway Violation", "event_description": "Person outside green markings"},
        {"timestamp": datetime.now() - timedelta(minutes=12), "severity": "CRITICAL", 
         "behavior_class": "Carrying Overload with Forklift", "event_description": "Forklift carrying 4 blocks"},
        {"timestamp": datetime.now() - timedelta(minutes=23), "severity": "MEDIUM", 
         "behavior_class": "Unauthorized Intervention", "event_description": "Person near equipment without green vest"},
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

def show_mock_stats():
    """Show mock dataset statistics"""
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Videos", "1000+")
    with col2:
        st.metric("Unsafe Videos", "500+")
    with col3:
        st.metric("Safe Videos", "500+")

if __name__ == "__main__":
    main()