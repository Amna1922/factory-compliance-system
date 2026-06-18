"""
Streamlit Dashboard for Factory Compliance & Alert Escalation System
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
from frontend.components import DashboardComponents, APIClient

# Page configuration
st.set_page_config(
    page_title="Compliance Dashboard",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .alert-critical {
        background-color: #ff0000;
        color: white;
        padding: 10px;
        border-radius: 5px;
    }
    .alert-high {
        background-color: #ffa500;
        color: white;
        padding: 10px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Page selector
page = st.sidebar.radio(
    "📊 Select View",
    ["🏠 Dashboard Overview", "📹 Upload Video", "⚙️ Batch Analysis", "🔴 Alert Timeline", "📋 Historical Log"]
)

# ==================== PAGE: Dashboard Overview ====================
if page == "🏠 Dashboard Overview":
    st.title("🏭 Compliance System Dashboard")
    
    # Get system summary
    summary = APIClient.get_system_summary()
    
    if summary:
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Videos",
                summary["dataset"]["total_videos"],
                f"Train: {summary['dataset']['train_videos']}, Test: {summary['dataset']['test_videos']}"
            )
        
        with col2:
            st.metric(
                "Events (24h)",
                summary["recent_events_24h"],
                "Last 24 hours"
            )
        
        with col3:
            unsafe_count = summary["dataset"]["unsafe_count"]
            safe_count = summary["dataset"]["safe_count"]
            st.metric(
                "Classes",
                f"{unsafe_count} Unsafe",
                f"{safe_count} Safe"
            )
        
        with col4:
            severity_stats = summary["event_severity_distribution"]
            critical_count = severity_stats.get("CRITICAL", 0)
            high_count = severity_stats.get("HIGH", 0)
            st.metric(
                "Critical/High",
                critical_count + high_count,
                "Requires attention"
            )
        
        # Show event severity distribution
        st.subheader("Event Distribution by Severity")
        if summary["event_severity_distribution"]:
            DashboardComponents.render_severity_chart(summary["event_severity_distribution"])
        else:
            st.info("No events recorded yet")
        
        # Show behavior class distribution
        st.subheader("Dataset Distribution")
        if summary["dataset"]["class_distribution"]:
            DashboardComponents.render_class_distribution_chart(summary["dataset"]["class_distribution"])
        else:
            st.info("Dataset not available")
        
        # Recent events
        st.subheader("Recent Events")
        events = APIClient.get_events(filters={"limit": 10})
        if events:
            DashboardComponents.render_event_table(events)
        else:
            st.info("No recent events")
    else:
        st.error("Unable to connect to backend")


# ==================== PAGE: Upload Video ====================
elif page == "📹 Upload Video":
    st.title("📹 Upload & Analyze Video")
    
    st.markdown("Upload a video file for compliance violation detection")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader("Choose a video file", type=["mp4", "avi", "mov", "mkv"])
    
    with col2:
        zone = st.text_input("Zone", value="Factory Floor A")
    
    if uploaded_file is not None:
        if st.button("🔍 Analyze Video", use_container_width=True):
            with st.spinner("Analyzing video..."):
                result = APIClient.upload_video(uploaded_file, zone)
                
                if result:
                    st.success("Video analyzed successfully!")
                    
                    # Display results
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Event ID", result.get("event_id", "N/A")[:15])
                    
                    with col2:
                        severity = result.get("severity", "UNKNOWN")
                        badge = DashboardComponents.render_severity_badge(severity)
                        st.metric("Severity", f"{badge} {severity}")
                    
                    with col3:
                        st.metric("Behavior", result.get("behavior_class", "Unknown")[:20])
                    
                    # Show detailed information
                    st.subheader("Detection Details")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info(f"**Clip ID**: {result.get('clip_id', 'N/A')}")
                        st.info(f"**Zone**: {result.get('zone', 'N/A')}")
                        st.info(f"**Policy Ref**: {result.get('policy_rule_ref', 'N/A')}")
                    
                    with col2:
                        st.info(f"**Description**: {result.get('event_description', 'N/A')}")
                        st.info(f"**Action**: {result.get('escalation_action', 'N/A')}")
                        st.info(f"**Timestamp**: {result.get('timestamp', 'N/A')}")
                    
                    # Alert notification if needed
                    if result.get("severity") in ["CRITICAL", "HIGH"]:
                        st.warning(f"🚨 Real-time alert triggered!")
                else:
                    st.error("Failed to analyze video")


# ==================== PAGE: Batch Analysis ====================
elif page == "⚙️ Batch Analysis":
    st.title("⚙️ Batch Analysis")
    
    st.markdown("Analyze multiple videos from the dataset")
    
    col1, col2 = st.columns(2)
    
    with col1:
        dataset_type = st.radio("Select Dataset", ["train", "test"])
    
    with col2:
        behaviors = st.multiselect(
            "Select Behavior Classes (empty = all)",
            options=[
                "Safe Walkway Violation",
                "Unauthorized Intervention",
                "Opened Panel Cover",
                "Carrying Overload with Forklift",
                "Safe Walkway",
                "Authorized Intervention",
                "Closed Panel Cover"
            ]
        )
    
    if st.button("▶️ Start Batch Analysis", use_container_width=True):
        with st.spinner("Processing batch... This may take a few minutes..."):
            result = APIClient.analyze_batch(
                dataset_type=dataset_type,
                behavior_classes=behaviors if behaviors else None
            )
            
            if result:
                st.success(result.get("status", "Completed"))
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Videos Analyzed", result.get("total_videos_analyzed", 0))
                
                with col2:
                    st.metric("Events Processed", result.get("events_processed", 0))
                
                with col3:
                    st.metric("Alerts Triggered", result.get("alerts_triggered", 0))
                
                st.info(f"Analysis completed at {result.get('timestamp', 'N/A')}")
            else:
                st.error("Batch analysis failed")


# ==================== PAGE: Alert Timeline ====================
elif page == "🔴 Alert Timeline":
    st.title("🔴 Alert Timeline")
    
    st.markdown("View real-time compliance violation events with alert status")
    
    # Filters
    filters = DashboardComponents.render_filter_section()
    
    # Get events
    if st.button("🔄 Refresh Events", use_container_width=True):
        st.rerun()
    
    # Fetch events
    severity_list = filters["severity"] if filters["severity"] else None
    
    # Build params
    params = {
        "limit": 100,
    }
    if filters["behavior_class"]:
        params["behavior_class"] = filters["behavior_class"]
    if filters["zone"]:
        params["zone"] = filters["zone"]
    if filters["start_date"]:
        params["start_date"] = filters["start_date"]
    if filters["end_date"]:
        params["end_date"] = filters["end_date"]
    
    events = APIClient.get_events(filters=params)
    
    if events:
        # Filter by severity if selected
        if severity_list:
            events = [e for e in events if e.get("severity") in severity_list]
        
        # Display timeline
        st.subheader(f"Events Timeline ({len(events)} events)")
        DashboardComponents.render_timeline_chart(events)
        
        # Display events
        st.subheader("Event Details")
        for event in events[:20]:  # Show max 20
            DashboardComponents.render_alert_notification(event)
    else:
        st.info("No events found")


# ==================== PAGE: Historical Log ====================
elif page == "📋 Historical Log":
    st.title("📋 Historical Log")
    
    st.markdown("View and export compliance event history")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        severity_filter = st.multiselect(
            "Severity Level",
            options=["CRITICAL", "HIGH", "MEDIUM", "LOW"],
            default=[]
        )
    
    with col2:
        behavior_filter = st.text_input("Behavior Class")
    
    with col3:
        limit = st.slider("Limit Results", 10, 1000, 100)
    
    # Fetch events
    params = {"limit": limit}
    
    if severity_filter:
        # Fetch all and filter client-side
        params["limit"] = 1000
    
    events = APIClient.get_events(filters=params)
    
    if events:
        # Client-side filtering
        if severity_filter:
            events = [e for e in events if e.get("severity") in severity_filter]
        if behavior_filter:
            events = [e for e in events if behavior_filter.lower() in e.get("behavior_class", "").lower()]
        
        events = events[:limit]
        
        # Display table
        st.subheader(f"Events ({len(events)} total)")
        DashboardComponents.render_event_table(events)
        
        # Export button
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Export as CSV", use_container_width=True):
                csv_data = APIClient.export_csv(
                    severity=severity_filter[0] if severity_filter else None,
                    behavior_class=behavior_filter or None
                )
                if csv_data:
                    st.download_button(
                        label="Download CSV",
                        data=csv_data,
                        file_name=f"compliance_events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
        
        with col2:
            st.info(f"Total events in database: ~{len(events)}")
    else:
        st.info("No events found in historical log")


# Sidebar info
st.sidebar.markdown("---")
st.sidebar.markdown("""
### 🏭 Compliance System
**Version**: 1.0.0
**Status**: Active

#### Features
- ✅ Real-time violation detection
- ✅ Policy-based severity classification
- ✅ Automated alert escalation
- ✅ Complete audit trail

#### Quick Stats
- 🎥 Dataset: Available
- 🗄️ Database: Connected
- 🔌 API: Running
- 📡 WebSocket: Active
""")

st.sidebar.markdown("---")
st.sidebar.markdown("📞 Support: contact@compliance-system.local")
