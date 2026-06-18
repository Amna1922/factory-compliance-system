"""
Reusable Streamlit dashboard components
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests


API_URL = "http://localhost:8000"


class DashboardComponents:
    """Reusable dashboard UI components"""

    @staticmethod
    def render_metric_card(label: str, value: any, color: str = "blue"):
        """Render a metric card"""
        with st.container():
            col1, col2 = st.columns([1, 4])
            with col1:
                st.markdown(f"<div style='background-color: {color}; padding: 20px; border-radius: 10px;'></div>",
                          unsafe_allow_html=True)
            with col2:
                st.markdown(f"<h3>{label}</h3>", unsafe_allow_html=True)
                st.markdown(f"<h2>{value}</h2>", unsafe_allow_html=True)

    @staticmethod
    def render_severity_badge(severity: str) -> str:
        """Render severity badge with color"""
        color_map = {
            "CRITICAL": "🔴",
            "HIGH": "🟠",
            "MEDIUM": "🟡",
            "LOW": "🟢",
            "NONE": "⚪"
        }
        return color_map.get(severity, "⚪")

    @staticmethod
    def render_status_indicator(is_safe: bool) -> str:
        """Render status indicator"""
        if is_safe:
            return "✅ SAFE"
        else:
            return "❌ VIOLATION"

    @staticmethod
    def render_event_table(events: List[Dict]):
        """Render table of events"""
        if not events:
            st.info("No events found")
            return

        # Prepare data for display
        data = []
        for event in events:
            data.append({
                "Event ID": event.get("event_id", "N/A")[:15],
                "Timestamp": event.get("timestamp", "")[:19],
                "Behavior": event.get("behavior_class", "N/A")[:20],
                "Severity": DashboardComponents.render_severity_badge(event.get("severity", "NONE")) + " " + event.get("severity", ""),
                "Zone": event.get("zone", "N/A"),
                "Status": DashboardComponents.render_status_indicator(event.get("severity") == "NONE")
            })

        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)

    @staticmethod
    def render_severity_chart(event_counts: Dict[str, int]):
        """Render severity distribution chart"""
        if not event_counts:
            st.info("No data to display")
            return

        # Create bar chart
        severities = list(event_counts.keys())
        counts = list(event_counts.values())

        color_map = {
            "CRITICAL": "#FF0000",
            "HIGH": "#FFA500",
            "MEDIUM": "#FFFF00",
            "LOW": "#00FF00",
            "NONE": "#0000FF"
        }

        colors = [color_map.get(s, "#808080") for s in severities]

        fig = go.Figure(
            data=[go.Bar(x=severities, y=counts, marker=dict(color=colors))],
            layout=go.Layout(
                title="Events by Severity",
                xaxis_title="Severity",
                yaxis_title="Count",
                template="plotly_dark"
            )
        )

        st.plotly_chart(fig, use_container_width=True)

    @staticmethod
    def render_class_distribution_chart(class_dist: Dict[str, int]):
        """Render behavior class distribution chart"""
        if not class_dist:
            st.info("No data to display")
            return

        df = pd.DataFrame(list(class_dist.items()), columns=["Behavior Class", "Count"])
        
        fig = px.pie(
            df,
            values="Count",
            names="Behavior Class",
            title="Dataset Distribution by Behavior Class",
            template="plotly_dark"
        )

        st.plotly_chart(fig, use_container_width=True)

    @staticmethod
    def render_timeline_chart(events: List[Dict]):
        """Render event timeline chart"""
        if not events:
            st.info("No events to display")
            return

        # Prepare data
        data = []
        for event in events:
            data.append({
                "Timestamp": pd.to_datetime(event.get("timestamp")),
                "Severity": event.get("severity", "NONE"),
                "Behavior": event.get("behavior_class", "Unknown")
            })

        df = pd.DataFrame(data)

        # Create scatter plot
        severity_colors = {
            "CRITICAL": "#FF0000",
            "HIGH": "#FFA500",
            "MEDIUM": "#FFFF00",
            "LOW": "#00FF00",
            "NONE": "#0000FF"
        }

        df["Color"] = df["Severity"].map(severity_colors)

        fig = go.Figure(
            data=[
                go.Scatter(
                    x=df["Timestamp"],
                    y=df["Severity"],
                    mode="markers",
                    marker=dict(
                        size=10,
                        color=df["Color"]
                    ),
                    text=df["Behavior"],
                    hovertemplate="<b>%{text}</b><br>%{x}<extra></extra>"
                )
            ],
            layout=go.Layout(
                title="Event Timeline",
                xaxis_title="Time",
                yaxis_title="Severity",
                template="plotly_dark",
                hovermode="closest"
            )
        )

        st.plotly_chart(fig, use_container_width=True)

    @staticmethod
    def render_two_column_layout():
        """Create a two-column layout"""
        col1, col2 = st.columns(2)
        return col1, col2

    @staticmethod
    def render_filter_section():
        """Render event filter section"""
        with st.expander("🔍 Filters", expanded=False):
            col1, col2, col3 = st.columns(3)

            with col1:
                severity_filter = st.multiselect(
                    "Severity",
                    options=["CRITICAL", "HIGH", "MEDIUM", "LOW"],
                    default=[]
                )

            with col2:
                behavior_filter = st.text_input("Behavior Class")

            with col3:
                zone_filter = st.text_input("Zone")

            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=7))
            with col2:
                end_date = st.date_input("End Date", value=datetime.now())

            return {
                "severity": severity_filter,
                "behavior_class": behavior_filter or None,
                "zone": zone_filter or None,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            }

    @staticmethod
    def render_alert_notification(event: Dict):
        """Render alert notification"""
        severity = event.get("severity", "UNKNOWN")
        badge = DashboardComponents.render_severity_badge(severity)
        
        if severity in ["CRITICAL", "HIGH"]:
            st.error(f"{badge} **{severity} ALERT**: {event.get('behavior_class', 'Unknown')}")
        elif severity == "MEDIUM":
            st.warning(f"{badge} **{severity} WARNING**: {event.get('behavior_class', 'Unknown')}")
        else:
            st.info(f"{badge} {event.get('behavior_class', 'Unknown')}")

    @staticmethod
    def render_loading_spinner(message: str = "Loading..."):
        """Render loading spinner"""
        with st.spinner(message):
            pass

    @staticmethod
    def render_success_message(message: str):
        """Render success message"""
        st.success(f"✅ {message}")

    @staticmethod
    def render_error_message(message: str):
        """Render error message"""
        st.error(f"❌ {message}")

    @staticmethod
    def render_info_message(message: str):
        """Render info message"""
        st.info(f"ℹ️ {message}")


class APIClient:
    """Client for backend API calls"""

    @staticmethod
    def get_dataset_stats() -> Optional[Dict]:
        """Get dataset statistics"""
        try:
            response = requests.get(f"{API_URL}/dataset/stats")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Error fetching dataset stats: {str(e)}")
            return None

    @staticmethod
    def get_events(filters: Dict = None) -> Optional[List[Dict]]:
        """Get compliance events with filters"""
        try:
            params = filters or {}
            response = requests.get(f"{API_URL}/events", params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Error fetching events: {str(e)}")
            return None

    @staticmethod
    def get_system_summary() -> Optional[Dict]:
        """Get overall system summary"""
        try:
            response = requests.get(f"{API_URL}/system/summary", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Error fetching system summary: {str(e)}")
            return None

    @staticmethod
    def export_csv(severity: str = None, behavior_class: str = None) -> Optional[bytes]:
        """Export events to CSV"""
        try:
            params = {}
            if severity:
                params["severity"] = severity
            if behavior_class:
                params["behavior_class"] = behavior_class

            response = requests.get(
                f"{API_URL}/export/csv",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.content
        except Exception as e:
            st.error(f"Error exporting CSV: {str(e)}")
            return None

    @staticmethod
    def upload_video(video_file, zone: str = "Factory Floor A") -> Optional[Dict]:
        """Upload and analyze a video"""
        try:
            files = {"file": video_file}
            params = {"zone": zone}
            response = requests.post(
                f"{API_URL}/analyze-video",
                files=files,
                params=params,
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Error analyzing video: {str(e)}")
            return None

    @staticmethod
    def analyze_batch(dataset_type: str = "train", behavior_classes: List[str] = None) -> Optional[Dict]:
        """Analyze batch of dataset videos"""
        try:
            payload = {
                "dataset_type": dataset_type,
                "behavior_classes": behavior_classes
            }
            response = requests.post(
                f"{API_URL}/analyze-batch",
                json=payload,
                timeout=300  # 5 minutes for batch processing
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Error in batch analysis: {str(e)}")
            return None

    @staticmethod
    def get_severity_stats() -> Optional[Dict]:
        """Get event statistics by severity"""
        try:
            response = requests.get(f"{API_URL}/events/stats/severity", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Error fetching severity stats: {str(e)}")
            return None
