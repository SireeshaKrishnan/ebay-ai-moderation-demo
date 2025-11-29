import streamlit as st
from datetime import datetime

st.set_page_config(page_title="eBay Community - Test Board", page_icon="💬", layout="wide")

# Initialize session state for posts and reports
if 'posts' not in st.session_state:
    st.session_state.posts = []
if 'reports' not in st.session_state:
    st.session_state.reports = []

# Custom CSS to make it look like eBay forums
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
    .report-badge {
        background-color: #FFF3CD;
        color: #856404;
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
st.info("This is a test environment for demonstrating AI-powered moderation. Post questions, comments, or test scenarios below!")

# Post submission form
st.markdown("---")
st.markdown("### ✍️ Submit a New Post")

# Define eBay boards
BOARDS = [
    "Selling",
    "Buying", 
    "Payments",
    "Postage & Shipping",
    "Technical Issues",
    "Member to Member Support",
    "Mentors Forum",
    "General Discussion",
    "eBay Café"
]

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
            # Create post data with unique ID
            post_id = f"post_{len(st.session_state.posts) + 1}"
            post_data = {
                "id": post_id,
                "username": username,
                "board": board,
                "title": post_title if post_title else "Untitled Post",
                "content": post_content,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "pending",
                "report_count": 0
            }
            
            st.session_state.posts.append(post_data)
            st.success(f"✅ Post submitted to **{board}** board! The moderation team will review it shortly.")
            st.balloons()
        else:
            st.error("⚠️ Please fill in both username and post content!")

# Display recent posts
st.markdown("---")
st.markdown("### 📋 Recent Posts Across All Boards")

# Report reasons
REPORT_REASONS = [
    "Naming & Shaming",
    "Disrespectful Language",
    "Personal Information Shared",
    "Spam or Advertising",
    "Off-Topic Content",
    "Wrong Board",
    "Other Policy Violation"
]

# Show posts from session state
if st.session_state.posts:
    for idx, post in enumerate(reversed(st.session_state.posts[-10:])):  # Show last 10 posts
        post_idx = len(st.session_state.posts) - idx - 1  # Get actual index
        status_emoji = "✅" if post.get("status") == "approved" else "🕐" if post.get("status") == "pending" else "🚫"
        
        # Count reports for this post
        post_reports = [r for r in st.session_state.reports if r['post_id'] == post['id']]
        report_count = len(post_reports)
        
        st.markdown(f"""
        <div class="post-card">
            <p>
                <span class="username">{post['username']}</span> 
                <span class="timestamp">• {post['timestamp']}</span> 
                {status_emoji}
                <span class="board-badge">📌 {post.get('board', 'General Discussion')}</span>
                {f'<span class="report-badge">🚩 {report_count} report(s)</span>' if report_count > 0 else ''}
            </p>
            <h4>{post['title']}</h4>
            <p>{post['content']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Report button and form
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
                            "post_id": post['id'],
                            "reporter": reporter_name,
                            "reason": report_reason,
                            "additional_info": additional_info,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "post_content": post['content'][:100] + "...",  # Store snippet
                            "post_board": post['board'],
                            "post_username": post['username']
                        }
                        
                        st.session_state.reports.append(report_data)
                        st.session_state[f'show_report_{post["id"]}'] = False
                        st.success("✅ Report submitted! Our moderation team will review it shortly.")
                        st.rerun()
                    
                    if cancel_report:
                        st.session_state[f'show_report_{post["id"]}'] = False
                        st.rerun()
        
        st.markdown("---")
else:
    st.info("No posts yet. Be the first to post!")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #707070; padding: 20px;'>
    <p>🔒 This is a test environment for AI moderation demonstration</p>
    <p>Posts are monitored by AI for policy violations and board placement in real-time</p>
    <p>Community members can report posts that violate guidelines</p>
</div>
""", unsafe_allow_html=True)
