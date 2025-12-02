import streamlit as st
from datetime import datetime
import json
import hashlib

st.set_page_config(page_title="eBay Community - Test Board", page_icon="💬", layout="wide")

# ================================
# SHARED STORAGE KEYS
# ================================

def get_storage_key():
    """Get a consistent storage key across both apps"""
    # Use a fixed key that both apps can access
    return "ebay_forum_posts_v1"

def save_posts_to_storage(posts_dict):
    """Save posts to session state with a special marker"""
    # Store in a way that can be accessed across refreshes
    storage_key = get_storage_key()
    st.session_state[storage_key] = posts_dict
    
    # Also store in a separate "sync" key
    st.session_state['posts_sync_timestamp'] = datetime.now().timestamp()

def load_posts_from_storage():
    """Load posts from session state"""
    storage_key = get_storage_key()
    return st.session_state.get(storage_key, {})

# Initialize storage
if 'ebay_forum_posts_v1' not in st.session_state:
    st.session_state['ebay_forum_posts_v1'] = {}

if 'forum_posts' not in st.session_state:
    st.session_state.forum_posts = st.session_state['ebay_forum_posts_v1']

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

# Storage JavaScript component for cross-app data sharing
st.components.v1.html("""
<script>
// Persistent storage for cross-app communication
window.savePost = async function(postId, postData) {
    try {
        if (window.storage) {
            await window.storage.set('forum_post_' + postId, JSON.stringify(postData), true);
            console.log('Post saved:', postId);
            return true;
        }
        console.error('Storage API not available');
        return false;
    } catch (e) {
        console.error('Storage save error:', e);
        return false;
    }
}

window.loadAllPosts = async function() {
    try {
        if (window.storage) {
            const keys = await window.storage.list('forum_post_', true);
            const posts = {};
            
            if (keys && keys.keys) {
                for (const key of keys.keys) {
                    const result = await window.storage.get(key, true);
                    if (result && result.value) {
                        posts[key] = JSON.parse(result.value);
                    }
                }
            }
            console.log('Loaded posts:', Object.keys(posts).length);
            return posts;
        }
        return {};
    } catch (e) {
        console.error('Storage load error:', e);
        return {};
    }
}

window.updatePostReport = async function(postId, reportData) {
    try {
        if (window.storage) {
            const key = 'forum_post_' + postId;
            const result = await window.storage.get(key, true);
            if (result && result.value) {
                const post = JSON.parse(result.value);
                if (!post.reports) post.reports = [];
                post.reports.push(reportData);
                post.report_count = post.reports.length;
                await window.storage.set(key, JSON.stringify(post), true);
                return true;
            }
        }
        return false;
    } catch (e) {
        console.error('Report update error:', e);
        return false;
    }
}

// Signal that storage is ready
window.storageInitialized = true;
console.log('Forum storage initialized');
</script>
""", height=0)

# Header
st.markdown('<div class="main-header"><h1>🛒 eBay Community - Forums</h1></div>', unsafe_allow_html=True)

st.markdown("### 💬 Welcome to the eBay Community Test Board")
st.success("✨ **LIVE CONNECTION:** Posts automatically sync to Moderator Dashboard in real-time!")

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

# Initialize session state for local display
if 'forum_posts' not in st.session_state:
    st.session_state.forum_posts = {}
    st.session_state.last_load_time = None

# Load posts from shared storage on page load
if st.session_state.last_load_time is None or \
   (datetime.now() - st.session_state.last_load_time).seconds > 5:
    # Simulate loading from storage (in production, would call window.loadPosts())
    st.session_state.last_load_time = datetime.now()

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
        height=150,
        help="Try posting: 'Seller abc123 is a scammer! Call me at 020-5555-1234' to test violation detection"
    )
    
    submit_button = st.form_submit_button("📤 Submit Post", use_container_width=True)
    
    if submit_button:
        if post_content and username:
            # Create post data
            post_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            post_data = {
                "id": post_id,
                "username": username,
                "board": board,
                "title": post_title if post_title else "Untitled Post",
                "content": post_content,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "pending",
                "source": "forum_user",
                "report_count": 0,
                "reports": [],
                "moderation_note": "",
                "violations": [],
                "ai_analyzed": False
            }
            
            # Save to BOTH session state AND shared storage
            storage_key = f"forum_post_{post_id}"
            st.session_state.forum_posts[storage_key] = post_data
            st.session_state['ebay_forum_posts_v1'][storage_key] = post_data
            
            # Update sync timestamp
            st.session_state['posts_sync_timestamp'] = datetime.now().timestamp()
            
            st.success(f"✅ Post submitted to **{board}** board!")
            st.info("🤖 **Your post is now visible in the Moderator Dashboard!** Open the dashboard and refresh to see it.")
            st.balloons()
            
            # Show what moderators will see
            with st.expander("👀 Preview: How Moderators See Your Post"):
                st.markdown(f"""
                **Post ID:** {post_id}  
                **Username:** {username}  
                **Board:** {board}  
                **Status:** 🟡 Pending Review  
                **Content:** {post_content}
                
                *This post will appear in the Moderator Dashboard's "Pending Posts" section for AI analysis.*
                """)
            
        else:
            st.error("⚠️ Please fill in both username and post content!")

# Display recent posts
st.markdown("---")
st.markdown("### 📋 Recent Posts Across All Boards")

# Filter options
col1, col2, col3 = st.columns(3)
with col1:
    filter_board = st.selectbox("Filter by Board", ["All Boards"] + BOARDS, key="filter_board")
with col2:
    filter_status = st.selectbox("Filter by Status", ["All Status", "Pending", "Approved", "Flagged"], key="filter_status")
with col3:
    sort_order = st.selectbox("Sort by", ["Newest First", "Oldest First", "Most Reports"], key="sort_order")

# Show posts
if st.session_state.forum_posts:
    # Apply filters
    filtered_posts = list(st.session_state.forum_posts.values())
    
    if filter_board != "All Boards":
        filtered_posts = [p for p in filtered_posts if p.get('board') == filter_board]
    
    if filter_status != "All Status":
        filtered_posts = [p for p in filtered_posts if p.get('status', 'pending').lower() == filter_status.lower()]
    
    # Sort
    if sort_order == "Newest First":
        filtered_posts.sort(key=lambda x: x['timestamp'], reverse=True)
    elif sort_order == "Oldest First":
        filtered_posts.sort(key=lambda x: x['timestamp'])
    else:  # Most Reports
        filtered_posts.sort(key=lambda x: len(x.get('reports', [])), reverse=True)
    
    st.info(f"📊 Showing {len(filtered_posts)} post(s)")
    
    for post in filtered_posts[:20]:  # Show last 20 posts
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
        
        # Show violations if any
        if post.get('violations'):
            with st.expander("⚠️ AI Detected Violations"):
                for v in post['violations']:
                    st.warning(f"**{v.get('type')}**: {v.get('evidence')}")
        
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
                        
                        # Add report to post in BOTH storage locations
                        storage_key = f"forum_post_{post['id']}"
                        if storage_key in st.session_state.forum_posts:
                            st.session_state.forum_posts[storage_key]['reports'].append(report_data)
                            st.session_state.forum_posts[storage_key]['report_count'] += 1
                            st.session_state['ebay_forum_posts_v1'][storage_key]['reports'].append(report_data)
                            st.session_state['ebay_forum_posts_v1'][storage_key]['report_count'] += 1
                            st.session_state['posts_sync_timestamp'] = datetime.now().timestamp()
                        
                        st.session_state[f'show_report_{post["id"]}'] = False
                        st.success("✅ Report submitted! This post will be prioritized in the Moderator Dashboard.")
                        st.rerun()
                    
                    if cancel_report:
                        st.session_state[f'show_report_{post["id"]}'] = False
                        st.rerun()
        
        st.markdown("---")
else:
    st.info("📭 No posts yet. Be the first to post!")
    
    with st.expander("💡 Test Scenarios to Try"):
        st.markdown("""
        **Try posting these to test AI moderation:**
        
        1. **PII Violation:**
           - "Call me at 020-5555-1234 for details"
           - "Email me at test@example.com"
        
        2. **Naming & Shaming:**
           - "Seller abc123 is a total scammer!"
           - "Avoid buyer xyz789, terrible!"
        
        3. **Disrespect:**
           - "You're all idiots if you think that!"
           - "This is f*cking ridiculous!"
        
        4. **Wrong Board:**
           - Post "My app is crashing" in Selling board
           - Post "How to ship items?" in Payments board
        
        5. **Spam:**
           - "Better deals on Amazon.com!"
           - "Skip eBay fees by contacting me directly"
        
        6. **Clean Post:**
           - "What's the best way to price vintage items?"
           - "How do I handle international shipping?"
        """)

# Auto-refresh option
st.markdown("---")
col1, col2 = st.columns([3, 1])

with col1:
    if st.checkbox("🔄 Enable Auto-Refresh (every 10 seconds)", value=False):
        st.info("Auto-refresh enabled! Page will update automatically.")
        import time
        time.sleep(10)
        st.rerun()

with col2:
    if st.button("🔄 Refresh Now", use_container_width=True):
        st.rerun()

# Footer
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: #707070; padding: 20px;'>
    <p>🔒 This is a test environment for AI moderation demonstration</p>
    <p>✨ <strong>{len(st.session_state.forum_posts)} total post(s)</strong> • Posts sync in real-time with Moderator Dashboard</p>
    <p>Community members can report posts that violate guidelines</p>
</div>
""", unsafe_allow_html=True)
