import streamlit as st
import pandas as pd
import time
import re
from datetime import datetime, timedelta
import json

# Import the ultra-strict policy (would be from separate file in production)
from policy_engine import ULTRA_STRICT_POLICY, analyze_post_strict

# ================================
# PAGE CONFIG
# ================================

st.set_page_config(
    page_title="eBay AI Moderation Dashboard",
    page_icon="🛡️",
    layout="wide"
)

# Custom CSS for color coding
st.markdown("""
<style>
/* Green - AI Approved */
.approved-section {
    background-color: #d4edda !important;
    border-left: 5px solid #28a745 !important;
    padding: 15px;
    margin: 10px 0;
    border-radius: 5px;
}

/* Blue variations - User Reported */
.user-reported-low {
    background-color: #d1ecf1 !important;
    border-left: 5px solid #17a2b8 !important;
    padding: 15px;
    margin: 10px 0;
    border-radius: 5px;
}

.user-reported-medium {
    background-color: #b8daff !important;
    border-left: 5px solid #0056b3 !important;
    padding: 15px;
    margin: 10px 0;
    border-radius: 5px;
}

.user-reported-high {
    background-color: #9fcdff !important;
    border-left: 5px solid #003d82 !important;
    padding: 15px;
    margin: 10px 0;
    border-radius: 5px;
}

/* Red variations - AI Flagged */
.flagged-low {
    background-color: #fff3cd !important;
    border-left: 5px solid #ffc107 !important;
    padding: 15px;
    margin: 10px 0;
    border-radius: 5px;
}

.flagged-medium {
    background-color: #f8d7da !important;
    border-left: 5px solid #dc3545 !important;
    padding: 15px;
    margin: 10px 0;
    border-radius: 5px;
}

.flagged-high {
    background-color: #f5c6cb !important;
    border-left: 5px solid #bd2130 !important;
    padding: 15px;
    margin: 10px 0;
    border-radius: 5px;
}

.flagged-critical {
    background-color: #e7b3ba !important;
    border-left: 5px solid #8b0000 !important;
    padding: 15px;
    margin: 10px 0;
    border-radius: 5px;
    font-weight: bold;
}

.stat-card {
    background: white;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)

# ================================
# SAMPLE DATA WITH TIMESTAMPS
# ================================

def generate_sample_data():
    """Generate sample posts with various violation types and timestamps"""
    base_date = datetime.now()
    
    posts = [
        # AI APPROVED - Green
        {
            "post_id": "P001",
            "source": "ai_approved",
            "username": "HelpfulSeller",
            "board": "Selling",
            "content": "What's the best way to price vintage collectibles? I have some rare stamps.",
            "timestamp": base_date - timedelta(hours=2),
            "status": "assured",
            "priority": "low",
            "confidence": 96,
            "violations": [],
            "time_saved": 2
        },
        {
            "post_id": "P002",
            "source": "ai_approved",
            "username": "NewSeller123",
            "board": "Member to Member Support",
            "content": "Can someone explain the seller protection policy? I'm new to selling.",
            "timestamp": base_date - timedelta(hours=5),
            "status": "assured",
            "priority": "low",
            "confidence": 98,
            "violations": [],
            "time_saved": 2
        },
        {
            "post_id": "P003",
            "source": "ai_approved",
            "username": "SatisfiedBuyer",
            "board": "Community Spirit",
            "content": "Excellent seller! Fast shipping and item exactly as described. Highly recommend!",
            "timestamp": base_date - timedelta(days=1, hours=3),
            "status": "assured",
            "priority": "low",
            "confidence": 99,
            "violations": [],
            "time_saved": 2
        },
        
        # USER REPORTED - Blue variations
        {
            "post_id": "P004",
            "source": "user_reported",
            "username": "ConfusedUser",
            "board": "Buying",
            "content": "I'm looking for vintage cameras. Anyone selling?",
            "timestamp": base_date - timedelta(hours=1),
            "status": "reported",
            "priority": "low",
            "confidence": 75,
            "report_reason": "Possible wanted post (against policy)",
            "reporter": "CommunityExpert42",
            "violations": [],
            "time_saved": 1
        },
        {
            "post_id": "P005",
            "source": "user_reported",
            "username": "DebatingUser",
            "board": "General Discussion",
            "content": "I disagree with the new shipping policy. It doesn't make sense for international sellers.",
            "timestamp": base_date - timedelta(hours=4),
            "status": "reported",
            "priority": "medium",
            "confidence": 70,
            "report_reason": "Possible policy breach discussion",
            "reporter": "Moderator_Assistant",
            "violations": [],
            "time_saved": 2
        },
        {
            "post_id": "P006",
            "source": "user_reported",
            "username": "FrustratedSeller",
            "board": "Selling",
            "content": "Why was my listing removed? I followed all the rules!",
            "timestamp": base_date - timedelta(days=1),
            "status": "reported",
            "priority": "high",
            "confidence": 85,
            "report_reason": "Discussion of moderation action",
            "reporter": "Sandy_Pebbles",
            "violations": ["Discussion of Moderation"],
            "time_saved": 3
        },
        
        # AI FLAGGED - Red variations
        {
            "post_id": "P007",
            "source": "ai_flagged",
            "username": "TechHelper",
            "board": "Selling",
            "content": "My app keeps crashing when I try to login. Anyone else having this issue?",
            "timestamp": base_date - timedelta(hours=3),
            "status": "flagged",
            "priority": "medium",
            "confidence": 92,
            "violations": [
                {
                    "type": "Wrong Board Placement",
                    "evidence": "Technical issue posted in Selling board",
                    "policy": "Board Usage Policy - Stay On Topic",
                    "confidence": 92
                }
            ],
            "recommended_action": "move",
            "move_to": "Technical Issues",
            "time_saved": 2
        },
        {
            "post_id": "P008",
            "source": "ai_flagged",
            "username": "AngryUser",
            "board": "Community",
            "content": "You're all idiots if you think eBay cares about sellers. F*cking ridiculous!",
            "timestamp": base_date - timedelta(hours=6),
            "status": "flagged",
            "priority": "high",
            "confidence": 98,
            "violations": [
                {
                    "type": "Disrespect - Insult",
                    "evidence": "\"You're all idiots\"",
                    "policy": "Board Usage Policy - Be Respectful",
                    "confidence": 96
                },
                {
                    "type": "Disrespect - Profanity",
                    "evidence": "\"F*cking\"",
                    "policy": "Board Usage Policy - Be Respectful",
                    "confidence": 98
                }
            ],
            "recommended_action": "edit",
            "time_saved": 6
        },
        {
            "post_id": "P009",
            "source": "ai_flagged",
            "username": "FrustratedBuyer",
            "board": "Buying",
            "content": "Seller abc123 is a total scammer! Never shipped my item. Call me at 020-5555-1234 if this happened to you!",
            "timestamp": base_date - timedelta(days=1, hours=2),
            "status": "flagged",
            "priority": "critical",
            "confidence": 100,
            "violations": [
                {
                    "type": "PII - Phone Number",
                    "evidence": "020-5555-1234",
                    "policy": "Contact Information Sharing Policy",
                    "confidence": 100
                },
                {
                    "type": "Naming and Shaming",
                    "evidence": "\"Seller abc123 is a total scammer\"",
                    "policy": "Board Usage Policy - Naming and Shaming",
                    "confidence": 96
                }
            ],
            "recommended_action": "edit",
            "time_saved": 11
        },
        {
            "post_id": "P010",
            "source": "ai_flagged",
            "username": "SpamBot",
            "board": "Selling",
            "content": "Better deals on Amazon.com! Skip eBay fees and shop direct!",
            "timestamp": base_date - timedelta(hours=8),
            "status": "flagged",
            "priority": "high",
            "confidence": 100,
            "violations": [
                {
                    "type": "Spam - External Link",
                    "evidence": "amazon.com",
                    "policy": "Board Usage Policy - Advertising",
                    "confidence": 100
                },
                {
                    "type": "Fee Avoidance",
                    "evidence": "\"Skip eBay fees\"",
                    "policy": "Avoiding eBay Fees Policy",
                    "confidence": 95
                }
            ],
            "recommended_action": "remove",
            "time_saved": 10
        }
    ]
    
    return posts

# ================================
# SESSION STATE INITIALIZATION
# ================================

if 'posts_data' not in st.session_state:
    st.session_state.posts_data = generate_sample_data()
    st.session_state.filter_start_date = datetime.now() - timedelta(days=30)
    st.session_state.filter_end_date = datetime.now()
    st.session_state.selected_board = "All Boards"
    st.session_state.selected_priority = "All Priorities"

# ================================
# HEADER
# ================================

st.title("🛡️ eBay Community AI Moderation Dashboard")
st.markdown("**Advanced Multi-Stream Monitoring System**")
st.markdown("---")

# ================================
# DATE RANGE FILTER SIDEBAR
# ================================

with st.sidebar:
    st.header("📊 Analytics Filters")
    
    st.subheader("Date Range")
    
    # Quick filters
    quick_filter = st.selectbox(
        "Quick Select",
        ["Custom Range", "Today", "Yesterday", "Last 7 Days", "Last 30 Days", "This Month", "Last Month"]
    )
    
    if quick_filter == "Today":
        st.session_state.filter_start_date = datetime.now().replace(hour=0, minute=0, second=0)
        st.session_state.filter_end_date = datetime.now()
    elif quick_filter == "Yesterday":
        st.session_state.filter_start_date = (datetime.now() - timedelta(days=1)).replace(hour=0, minute=0, second=0)
        st.session_state.filter_end_date = (datetime.now() - timedelta(days=1)).replace(hour=23, minute=59, second=59)
    elif quick_filter == "Last 7 Days":
        st.session_state.filter_start_date = datetime.now() - timedelta(days=7)
        st.session_state.filter_end_date = datetime.now()
    elif quick_filter == "Last 30 Days":
        st.session_state.filter_start_date = datetime.now() - timedelta(days=30)
        st.session_state.filter_end_date = datetime.now()
    elif quick_filter == "This Month":
        st.session_state.filter_start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0)
        st.session_state.filter_end_date = datetime.now()
    elif quick_filter == "Last Month":
        last_month = datetime.now().replace(day=1) - timedelta(days=1)
        st.session_state.filter_start_date = last_month.replace(day=1, hour=0, minute=0, second=0)
        st.session_state.filter_end_date = last_month.replace(hour=23, minute=59, second=59)
    
    if quick_filter == "Custom Range":
        st.session_state.filter_start_date = st.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=30)
        )
        st.session_state.filter_end_date = st.date_input(
            "End Date",
            value=datetime.now()
        )
    else:
        st.info(f"Showing: {quick_filter}")
    
    st.markdown("---")
    
    # Board filter
    st.subheader("Board Filter")
    all_boards = ["All Boards"] + sorted(list(set([p['board'] for p in st.session_state.posts_data])))
    st.session_state.selected_board = st.selectbox("Select Board", all_boards)
    
    # Priority filter
    st.subheader("Priority Filter")
    all_priorities = ["All Priorities", "Critical", "High", "Medium", "Low"]
    st.session_state.selected_priority = st.selectbox("Select Priority", all_priorities)
    
    st.markdown("---")
    st.caption("💡 Tip: Use date ranges to track trends over time")

# ================================
# FILTER DATA
# ================================

def filter_posts(posts, start_date, end_date, board, priority):
    """Filter posts based on date range, board, and priority"""
    filtered = []
    
    for post in posts:
        # Convert start/end to datetime if they're date objects
        if isinstance(start_date, datetime):
            start_dt = start_date
        else:
            start_dt = datetime.combine(start_date, datetime.min.time())
            
        if isinstance(end_date, datetime):
            end_dt = end_date
        else:
            end_dt = datetime.combine(end_date, datetime.max.time())
        
        # Date filter
        if not (start_dt <= post['timestamp'] <= end_dt):
            continue
        
        # Board filter
        if board != "All Boards" and post['board'] != board:
            continue
        
        # Priority filter
        if priority != "All Priorities" and post.get('priority', '').lower() != priority.lower():
            continue
        
        filtered.append(post)
    
    return filtered

filtered_posts = filter_posts(
    st.session_state.posts_data,
    st.session_state.filter_start_date,
    st.session_state.filter_end_date,
    st.session_state.selected_board,
    st.session_state.selected_priority
)

# ================================
# SUMMARY STATISTICS
# ================================

ai_approved = [p for p in filtered_posts if p['source'] == 'ai_approved']
user_reported = [p for p in filtered_posts if p['source'] == 'user_reported']
ai_flagged = [p for p in filtered_posts if p['source'] == 'ai_flagged']

total_time_saved = sum([p.get('time_saved', 0) for p in filtered_posts])

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Posts", len(filtered_posts))

with col2:
    st.metric("✅ AI Approved", len(ai_approved), 
              delta=f"{len(ai_approved)/max(len(filtered_posts),1)*100:.0f}%",
              delta_color="normal")

with col3:
    st.metric("👤 User Reported", len(user_reported),
              delta=f"{len(user_reported)/max(len(filtered_posts),1)*100:.0f}%",
              delta_color="off")

with col4:
    st.metric("🚨 AI Flagged", len(ai_flagged),
              delta=f"{len(ai_flagged)/max(len(filtered_posts),1)*100:.0f}%",
              delta_color="inverse")

with col5:
    st.metric("⏱️ Time Saved", f"{total_time_saved} min",
              delta=f"{total_time_saved/60:.1f} hrs")

st.markdown("---")

# ================================
# THREE COLUMNS LAYOUT
# ================================

col_approved, col_reported, col_flagged = st.columns(3)

# ================================
# COLUMN 1: AI APPROVED (GREEN)
# ================================

with col_approved:
    st.subheader("✅ AI Approved Posts")
    st.caption(f"**{len(ai_approved)} posts** - No violations detected")
    
    if ai_approved:
        for post in sorted(ai_approved, key=lambda x: x['timestamp'], reverse=True):
            st.markdown(f"""
            <div class="approved-section">
                <strong>Post #{post['post_id']}</strong> | Board: {post['board']}<br>
                👤 {post['username']} | 🕒 {post['timestamp'].strftime('%Y-%m-%d %H:%M')}<br><br>
                📝 <em>{post['content'][:120]}{'...' if len(post['content']) > 120 else ''}</em><br><br>
                <strong>Status:</strong> ✅ ASSURED | Confidence: {post['confidence']}%<br>
                ⏱️ Time saved: {post['time_saved']} min
            </div>
            """, unsafe_allow_html=True)
            
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("🔍 View Full Post", key=f"view_approve_{post['post_id']}"):
                    st.info(f"Full content: {post['content']}")
            with col_b:
                if st.button("⚠️ Flag Manually", key=f"flag_{post['post_id']}"):
                    st.warning("Post marked for manual review")
            
            st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.info("No approved posts in selected date range")

# ================================
# COLUMN 2: USER REPORTED (BLUE)
# ================================

with col_reported:
    st.subheader("👤 User Reported Posts")
    st.caption(f"**{len(user_reported)} posts** - Community flagged content")
    
    if user_reported:
        # Sort by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        sorted_reported = sorted(user_reported, key=lambda x: priority_order.get(x.get('priority', 'low').lower(), 3))
        
        for post in sorted_reported:
            priority = post.get('priority', 'low').lower()
            
            if priority == 'high':
                css_class = "user-reported-high"
                emoji = "🔵🔵🔵"
            elif priority == 'medium':
                css_class = "user-reported-medium"
                emoji = "🔵🔵"
            else:
                css_class = "user-reported-low"
                emoji = "🔵"
            
            st.markdown(f"""
            <div class="{css_class}">
                {emoji} <strong>{priority.upper()}</strong> | <strong>Post #{post['post_id']}</strong><br>
                Board: {post['board']} | 👤 {post['username']}<br>
                🕒 {post['timestamp'].strftime('%Y-%m-%d %H:%M')}<br><br>
                📝 <em>{post['content'][:120]}{'...' if len(post['content']) > 120 else ''}</em><br><br>
                <strong>Reported by:</strong> {post.get('reporter', 'Unknown')}<br>
                <strong>Reason:</strong> {post.get('report_reason', 'Not specified')}<br>
                ⏱️ Needs review: ~{post['time_saved']} min
            </div>
            """, unsafe_allow_html=True)
            
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                if st.button("✅ No Violation", key=f"clear_report_{post['post_id']}"):
                    st.success("Report dismissed")
            with col_b:
                if st.button("✏️ Edit Post", key=f"edit_report_{post['post_id']}"):
                    st.info("Opening editor...")
            with col_c:
                if st.button("🚫 Remove", key=f"remove_report_{post['post_id']}"):
                    st.warning("Post removed")
            
            st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.success("No user reports in selected date range")

# ================================
# COLUMN 3: AI FLAGGED (RED)
# ================================

with col_flagged:
    st.subheader("🚨 AI Flagged Posts")
    st.caption(f"**{len(ai_flagged)} posts** - Policy violations detected")
    
    if ai_flagged:
        # Sort by priority
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        sorted_flagged = sorted(ai_flagged, key=lambda x: priority_order.get(x.get('priority', 'low').lower(), 4))
        
        for post in sorted_flagged:
            priority = post.get('priority', 'low').lower()
            
            if priority == 'critical':
                css_class = "flagged-critical"
                emoji = "🚨"
            elif priority == 'high':
                css_class = "flagged-high"
                emoji = "🔴"
            elif priority == 'medium':
                css_class = "flagged-medium"
                emoji = "🟠"
            else:
                css_class = "flagged-low"
                emoji = "🟡"
            
            st.markdown(f"""
            <div class="{css_class}">
                {emoji} <strong>{priority.upper()}</strong> | <strong>Post #{post['post_id']}</strong><br>
                Board: {post['board']} | 👤 {post['username']}<br>
                🕒 {post['timestamp'].strftime('%Y-%m-%d %H:%M')}<br><br>
                📝 <em>{post['content'][:120]}{'...' if len(post['content']) > 120 else ''}</em><br><br>
            """, unsafe_allow_html=True)
            
            # Show violations
            if post.get('violations'):
                st.markdown("**Violations Detected:**", unsafe_allow_html=True)
                for v in post['violations']:
                    st.markdown(f"""
                    • **{v['type']}** ({v['confidence']}% confidence)<br>
                    &nbsp;&nbsp;&nbsp;Evidence: "{v['evidence']}"<br>
                    &nbsp;&nbsp;&nbsp;Policy: {v['policy']}<br>
                    """, unsafe_allow_html=True)
            
            st.markdown(f"""
                <br><strong>AI Recommendation:</strong> {post.get('recommended_action', 'review').upper()}<br>
                ⏱️ Time saved: {post['time_saved']} min
            </div>
            """, unsafe_allow_html=True)
            
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                if st.button("✅ Accept AI", key=f"accept_{post['post_id']}"):
                    st.success(f"Accepted: {post.get('recommended_action', 'review')}")
            with col_b:
                if st.button("✏️ Manual Edit", key=f"manual_{post['post_id']}"):
                    st.info("Opening editor...")
            with col_c:
                if st.button("🔄 Override", key=f"override_{post['post_id']}"):
                    st.warning("Marked for different action")
            
            st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.success("No flagged posts in selected date range")

# ================================
# ANALYTICS DASHBOARD
# ================================

st.markdown("---")
st.header("📊 Analytics Dashboard")

# Create tabs for different analytics views
tab1, tab2, tab3 = st.tabs(["Overview", "Violation Breakdown", "Time Trends"])

with tab1:
    st.subheader("Overview Statistics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Post Distribution by Source**")
        source_data = {
            "AI Approved": len(ai_approved),
            "User Reported": len(user_reported),
            "AI Flagged": len(ai_flagged)
        }
        st.bar_chart(source_data)
    
    with col2:
        st.markdown("**Priority Distribution (Flagged Posts)**")
        if ai_flagged:
            priority_data = {}
            for post in ai_flagged:
                p = post.get('priority', 'low').title()
                priority_data[p] = priority_data.get(p, 0) + 1
            st.bar_chart(priority_data)
        else:
            st.info("No flagged posts to analyze")

with tab2:
    st.subheader("Violation Type Breakdown")
    
    violation_counts = {}
    for post in ai_flagged:
        for v in post.get('violations', []):
            v_type = v['type']
            violation_counts[v_type] = violation_counts.get(v_type, 0) + 1
    
    if violation_counts:
        st.bar_chart(violation_counts)
        
        st.markdown("**Detailed Breakdown:**")
        for v_type, count in sorted(violation_counts.items(), key=lambda x: x[1], reverse=True):
            st.markdown(f"- **{v_type}**: {count} occurrences")
    else:
        st.info("No violations detected in selected period")

with tab3:
    st.subheader("Time-Based Trends")
    
    if filtered_posts:
        # Group by date
        df = pd.DataFrame([{
            'date': p['timestamp'].date(),
            'source': p['source']
        } for p in filtered_posts])
        
        pivot = df.groupby(['date', 'source']).size().unstack(fill_value=0)
        st.line_chart(pivot)
    else:
        st.info("No data for selected period")

# ================================
# FOOTER
# ================================

st.markdown("---")
st.caption("eBay Community AI Moderation Dashboard v3.0 | Ultra-Strict Policy Engine | Multi-Stream Monitoring")
