import streamlit as st
from datetime import datetime
import json
import time

st.set_page_config(page_title="eBay Community - Test Board", page_icon="💬", layout="wide")

# ================================
# SESSION STATE INITIALIZATION
# ================================

if 'forum_posts' not in st.session_state:
    st.session_state.forum_posts = {}

if 'unsaved_posts' not in st.session_state:
    st.session_state.unsaved_posts = []

if 'ebay_forum_posts_v1' not in st.session_state:
    st.session_state['ebay_forum_posts_v1'] = {}

if 'posts_sync_timestamp' not in st.session_state:
    st.session_state['posts_sync_timestamp'] = datetime.now().timestamp()

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
st.success("✨ **LIVE CONNECTION:** Posts automatically sync to Moderator Dashboard in real-time!")

# CRITICAL: Storage sync component - ALWAYS runs on every page load
# This component saves all unsaved posts
posts_to_save = st.session_state.unsaved_posts.copy()
posts_json = json.dumps(posts_to_save)

st.components.v1.html(f"""
<script>
async function syncPosts() {{
    const postsToSave = {posts_json};
    
    if (postsToSave.length === 0) {{
        console.log('No posts to sync');
        return;
    }}
    
    let savedCount = 0;
    
    if (window.storage) {{
        for (const post of postsToSave) {{
            try {{
                await window.storage.set('forum_post_' + post.id, JSON.stringify(post), true);
                console.log('✅ Saved post:', post.id);
                savedCount++;
            }} catch (e) {{
                console.error('Failed to save post', post.id, e);
            }}
        }}
        console.log('📤 Saved', savedCount, 'posts to storage');
    }} else {{
        console.error('Storage API not available!');
    }}
}}
syncPosts();
</script>
""", height=0, key="storage_sync")

# Show sync status and clear unsaved posts
if len(posts_to_save) > 0:
    st.info(f"💾 Syncing {len(posts_to_save)} post(s) to storage...")
    # Clear unsaved posts after attempting to save
    st.session_state.unsaved_posts = []

# Manual load button
if st.button("📥 Load All Posts from Storage", use_container_width=True, type="primary"):
    st.components.v1.html("""
    <script>
    async function loadAllPosts() {
        if (!window.storage) {
            console.error('Storage API not available');
            return;
        }
        
        try {
            const keys = await window.storage.list('forum_post_', true);
            let loadedPosts = {};
            
            if (keys && keys.keys) {
                for (const key of keys.keys) {
                    try {
                        const result = await window.storage.get(key, true);
                        if (result && result.value) {
                            const post = JSON.parse(result.value);
                            loadedPosts[key] = post;
                            console.log('Loaded:', key);
                        }
                    } catch (e) {
                        console.error('Error loading', key, e);
                    }
                }
            }
            
            console.log('📥 Total posts loaded:', Object.keys(loadedPosts).length);
            
            // Send to parent - this won't work but at least logs are visible
            window.parent.postMessage({
                type: 'loadedPosts',
                posts: loadedPosts,
                count: Object.keys(loadedPosts).length
            }, '*');
            
        } catch (e) {
            console.error('Load error:', e);
        }
    }
    loadAllPosts();
    </script>
    """, height=0, key="load_posts_trigger")
    
    st.success("✅ Check browser console to see loaded posts. Refresh page to see them in the list.")
    time.sleep(2)
    st.rerun()

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
                "replies": [],
                "moderation_note": "",
                "violations": [],
                "ai_analyzed": False
            }
            
            # Save to session state
            storage_key = f"forum_post_{post_id}"
            st.session_state.forum_posts[storage_key] = post_data
            st.session_state['ebay_forum_posts_v1'][storage_key] = post_data
            
            # Add to unsaved posts queue
            st.session_state.unsaved_posts.append(post_data)
            
            st.session_state['posts_sync_timestamp'] = datetime.now().timestamp()
            
            st.success(f"✅ Post submitted to **{board}** board!")
            st.info("🤖 Post will sync to storage on next page load. Refresh to complete sync.")
            st.balloons()
            
            # Show what moderators will see
            with st.expander("👀 Preview: How Moderators See Your Post"):
                st.markdown(f"""
                **Post ID:** {post_id}  
                **Username:** {username}  
                **Board:** {board}  
                **Status:** 🟡 Pending Review  
                **Content:** {post_content}
                
                *This post will appear in the Moderator Dashboard after syncing to storage.*
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
        
        # Count replies
        replies = post.get('replies', [])
        reply_count = len(replies)
        
        st.markdown(f"""
        <div class="post-card">
            <p>
                <span class="username">{post['username']}</span> 
                <span class="timestamp">• Posted on {post['timestamp']}</span>
                <span class="board-badge">📌 {post.get('board', 'General Discussion')}</span>
                {status_badge}
                {report_badge}
            </p>
            <h4>{post['title']}</h4>
            <p>{post['content']}</p>
            <p style="color: #666; font-size: 0.9em;">💬 {reply_count} replies</p>
            {f"<p><em>Moderator note: {post.get('moderation_note', '')}</em></p>" if post.get('moderation_note') else ''}
        </div>
        """, unsafe_allow_html=True)
        
        # Show violations if any
        if post.get('violations'):
            with st.expander("⚠️ AI Detected Violations"):
                for v in post['violations']:
                    st.warning(f"**{v.get('type')}**: {v.get('evidence')}")
        
        # Show replies if any
        if replies:
            with st.expander(f"💬 View {reply_count} Replies"):
                for reply in replies:
                    st.markdown(f"""
                    <div style="background-color: #f8f9fa; padding: 10px; margin: 5px 0; border-left: 3px solid #ccc;">
                        <strong>{reply['username']}</strong> • <span style="color: #666; font-size: 0.85em;">{reply['timestamp']}</span><br>
                        {reply['content']}
                    </div>
                    """, unsafe_allow_html=True)
        
        # Reply form and Report button
        col1, col2, col3 = st.columns([1, 4, 1])
        
        with col1:
            report_key = f"report_btn_{post['id']}"
            if st.button(f"🚩 Report", key=report_key):
                st.session_state[f'show_report_{post["id"]}'] = True
        
        with col2:
            reply_key = f"reply_btn_{post['id']}"
            if st.button(f"💬 Reply", key=reply_key):
                st.session_state[f'show_reply_{post["id"]}'] = True
        
        # Show reply form
        if st.session_state.get(f'show_reply_{post["id"]}', False):
            with st.form(f"reply_form_{post['id']}"):
                reply_username = st.text_input("Your Username", value="community_user", key=f"reply_user_{post['id']}")
                reply_content = st.text_area("Your Reply", placeholder="Type your reply here...", key=f"reply_content_{post['id']}")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    submit_reply = st.form_submit_button("📤 Post Reply", use_container_width=True)
                with col_b:
                    cancel_reply = st.form_submit_button("❌ Cancel", use_container_width=True)
                
                if submit_reply and reply_content:
                    # Create reply
                    reply_data = {
                        "username": reply_username,
                        "content": reply_content,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    # Add reply to post
                    storage_key = f"forum_post_{post['id']}"
                    if storage_key in st.session_state.forum_posts:
                        if 'replies' not in st.session_state.forum_posts[storage_key]:
                            st.session_state.forum_posts[storage_key]['replies'] = []
                        st.session_state.forum_posts[storage_key]['replies'].append(reply_data)
                        
                        # Add updated post to unsaved queue
                        st.session_state.unsaved_posts.append(st.session_state.forum_posts[storage_key])
                    
                    st.session_state[f'show_reply_{post["id"]}'] = False
                    st.success("✅ Reply posted!")
                    st.rerun()
                
                if cancel_reply:
                    st.session_state[f'show_reply_{post["id"]}'] = False
                    st.rerun()
        
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
                            
                            # Add updated post to unsaved queue
                            st.session_state.unsaved_posts.append(st.session_state.forum_posts[storage_key])
                        
                        st.session_state[f'show_report_{post["id"]}'] = False
                        st.success("✅ Report submitted! Refresh page to sync to dashboard.")
                        st.rerun()
                    
                    if cancel_report:
                        st.session_state[f'show_report_{post["id"]}'] = False
                        st.rerun()
        
        st.markdown("---")
else:
    st.info("📭 No posts loaded yet.")
    st.markdown("### 👆 Click the '📥 Load All Posts' button above to load existing posts from storage")
    st.markdown("### OR submit a new post using the form above")

# Auto-refresh option
st.markdown("---")
col1, col2 = st.columns([3, 1])

with col1:
    if st.checkbox("🔄 Enable Auto-Refresh (every 10 seconds)", value=False):
        st.info("Auto-refresh enabled! Page will update automatically.")
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
    <p>✨ <strong>{len(st.session_state.forum_posts)} post(s) in session</strong> • Posts sync to storage on page refresh</p>
    <p>💾 Unsaved posts: {len(st.session_state.unsaved_posts)} • Check browser console (F12) for storage logs</p>
</div>
""", unsafe_allow_html=True)
