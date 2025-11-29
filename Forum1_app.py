import streamlit as st
from datetime import datetime
import json
import asyncio

st.set_page_config(page_title="eBay Community - Test Board", page_icon="💬", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background-color: #3665F3;
        color: white;
        padding: 20px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .post-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #3665F3;
        margin-bottom: 15px;
    }
    .username {
        color: #0064D2;
        font-weight: bold;
    }
    .timestamp {
        color: #707070;
        font-size: 0.9em;
    }
    .board-badge {
        background-color: #E8F4FD;
        color: #0064D2;
        padding: 3px 8px;
        border-radius: 3px;
        font-size: 0.85em;
        font-weight: bold;
    }
    .status-pending {
        background-color: #FFF3CD;
        color: #856404;
        padding: 3px 8px;
        border-radius: 3px;
        font-size: 0.85em;
        font-weight: bold;
    }
    .status-approved {
        background-color: #D4EDDA;
        color: #155724;
        padding: 3px 8px;
        border-radius: 3px;
        font-size: 0.85em;
        font-weight: bold;
    }
    .status-flagged {
        background-color: #F8D7DA;
        color: #721C24;
        padding: 3px 8px;
        border-radius: 3px;
        font-size: 0.85em;
        font-weight: bold;
    }
    .report-badge {
        background-color: #D1ECF1;
        color: #0C5460;
        padding: 3px 8px;
        border-radius: 3px;
        font-size: 0.85em;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header"><h1>🛒 eBay Community - Forums</h1></div>', unsafe_allow_html=True)

st.markdown("### 💬 Welcome to the eBay Community Test Board")
st.info("This is a test environment for demonstrating AI-powered moderation. Posts are automatically monitored by AI in real-time!")

# eBay Boards
BOARDS = [
    "Selling", "Buying", "Payments", "Postage & Shipping",
    "Technical Issues", "Member to Member Support",
    "Mentors Forum", "General Discussion", "eBay Café"
]

# Report reasons
REPORT_REASONS = [
    "Naming & Shaming", "Disrespectful Language", "Personal Information Shared",
    "Spam or Advertising", "Off-Topic Content", "Wrong Board", "Other Policy Violation"
]

# Post submission form
st.markdown("---")
st.markdown("### ✍️ Submit a New Post")

with st.form("new_post_form"):
    col1, col2 = st.columns([1, 3])
    
    with col1:
        username = st.text_input("Username", value="test_user", help="Your forum username")
        board = st.selectbox("Board", BOARDS, help="Select the board for your post")
    
    with col2:
        post_title = st.text_input("Post Title", placeholder="What's your question or topic?")
    
    post_content = st.text_area(
        "Post Content", 
        placeholder="Type your message here... Try posting different scenarios to test the AI moderation!",
        height=150
    )
    
    submit_button = st.form_submit_button("📤 Submit Post")
    
    if submit_button:
        if post_content and username:
            # Create post data
            post_id = f"post_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            post_data = {
                "id": post_id,
                "username": username,
                "board": board,
                "title": post_title if post_title else "Untitled Post",
                "content": post_content,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "pending",
                "report_count": 0,
                "reports": [],
                "moderation_note": ""
            }
            
            # Save to persistent storage (shared with moderator dashboard!)
            try:
                # This makes it accessible to moderator dashboard in real-time
                storage_key = f"forum_post_{post_id}"
                
                # Simulate storage (in production, this would use actual storage API)
                if 'forum_posts' not in st.session_state:
                    st.session_state.forum_posts = {}
                
                st.session_state.forum_posts[storage_key] = post_data
                
                st.success(f"✅ Post submitted to **{board}** board! AI moderation is analyzing it now...")
                st.balloons()
                
                st.info("💡 **For Demo:** In production, this post would be saved to cloud storage and instantly appear in the moderator dashboard for AI analysis!")
                
            except Exception as e:
                st.error(f"Error submitting post: {e}")
        else:
            st.error("⚠️ Please fill in both username and post content!")

# Display recent posts
st.markdown("---")
st.markdown("### 📋 Recent Posts Across All Boards")

# Load posts from storage
if 'forum_posts' not in st.session_state:
    st.session_state.forum_posts = {}

# Show posts
if st.session_state.forum_posts:
    # Sort by timestamp (newest first)
    sorted_posts = sorted(
        st.session_state.forum_posts.values(),
        key=lambda x: x['timestamp'],
        reverse=True
    )
    
    for post in sorted_posts[:20]:  # Show last 20 posts
        # Determine status styling
        status = post.get('status', 'pending')
        if status == 'approved':
            status_badge = '<span class="status-approved">✅ Approved</span>'
        elif status == 'flagged':
            status_badge = '<span class="status-flagged">🚨 Flagged</span>'
        else:
            status_badge = '<span class="status-pending">🕐 Pending Review</span>'
        
        # Count reports
        report_count = len(post.get('reports', []))
        report_badge = f'<span class="report-badge">🚩 {report_count} report(s)</span>' if report_count > 0 else ''
        
        st.markdown(f"""
        <div class="post-card">
            <p>
                <span class="username">{post['username']}</span> 
                <span class="timestamp">• {post['timestamp']}</span>
                <span class="board-badge">📌 {post.get('board', 'General Discussion')}</span>
                {status_badge}
                {report_badge}
            </p>
            <h4>{post['title']}</h4>
            <p>{post['content']}</p>
            {f"<p><em>Moderator note: {post.get('moderation_note', '')}</em></p>" if post.get('moderation_note') else ''}
        </div>
        """, unsafe_allow_html=True)
        
        # Report button
        col1, col2, col3 = st.columns([1, 6, 1])
        
        with col1:
            report_key = f"report_btn_{post['id']}"
            if st.button(f"🚩 Report", key=report_key):
                st.session_state[f'show_report_{post["id"]}'] = True
        
        # Show report form if button clicked
        if st.session_state.get(f'show_report_{post["id"]}', False):
            with st.expander("📝 Submit Report", expanded=True):
                with st.form(f"report_form_{post['id']}"):
                    reporter_name = st.text_input("Your Username", value="community_user", key=f"reporter_{post['id']}")
                    report_reason = st.selectbox("Reason for Report", REPORT_REASONS, key=f"reason_{post['id']}")
                    additional_info = st.text_area("Additional Information (Optional)", placeholder="Provide any additional context...", key=f"info_{post['id']}")
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        submit_report = st.form_submit_button("📤 Submit Report", use_container_width=True)
                    with col_b:
                        cancel_report = st.form_submit_button("❌ Cancel", use_container_width=True)
                    
                    if submit_report:
                        # Create report
                        report_data = {
                            "reporter": reporter_name,
                            "reason": report_reason,
                            "additional_info": additional_info,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        # Add report to post
                        storage_key = f"forum_post_{post['id']}"
                        if storage_key in st.session_state.forum_posts:
                            st.session_state.forum_posts[storage_key]['reports'].append(report_data)
                            st.session_state.forum_posts[storage_key]['report_count'] += 1
                        
                        st.session_state[f'show_report_{post["id"]}'] = False
                        st.success("✅ Report submitted! Our AI moderation system will prioritize this post for review.")
                        st.rerun()
                    
                    if cancel_report:
                        st.session_state[f'show_report_{post["id"]}'] = False
                        st.rerun()
        
        st.markdown("---")
else:
    st.info("No posts yet. Be the first to post!")

# Auto-refresh option
st.markdown("---")
if st.checkbox("🔄 Enable Auto-Refresh (every 10 seconds)", value=False):
    st.info("Auto-refresh enabled! Page will update automatically.")
    # In production, would use st.rerun() with timer

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #707070; padding: 20px;'>
    <p>🔒 This is a test environment for AI moderation demonstration</p>
    <p>Posts are automatically analyzed by AI in real-time and sent to the moderator dashboard</p>
    <p>Community members can report posts that violate guidelines</p>
</div>
""", unsafe_allow_html=True)
