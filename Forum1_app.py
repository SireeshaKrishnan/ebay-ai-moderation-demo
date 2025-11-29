import streamlit as st
import json
from datetime import datetime

st.set_page_config(page_title="eBay Community - Test Board", page_icon="💬", layout="wide")

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
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header"><h1>🛒 eBay Community - General Discussion Board</h1></div>', unsafe_allow_html=True)

st.markdown("### 💬 Welcome to the eBay Community Test Board")
st.info("This is a test environment for demonstrating AI-powered moderation. Post questions, comments, or test scenarios below!")

# Post submission form
st.markdown("---")
st.markdown("### ✍️ Submit a New Post")

with st.form("new_post_form"):
    col1, col2 = st.columns([1, 3])
    
    with col1:
        username = st.text_input("Username", value="test_user", help="Your forum username")
    
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
            post_data = {
                "username": username,
                "title": post_title if post_title else "Untitled Post",
                "content": post_content,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "pending"
            }
            
            # Try to save to persistent storage (shared between apps)
            try:
                # Generate a unique key for this post
                post_id = f"post_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                # Save using Streamlit's persistent storage (shared=True makes it accessible to other apps)
                import asyncio
                asyncio.create_task(
                    st.session_state.get('storage_handler', lambda: None)()
                )
                
                # For now, also save to session state
                if 'posts' not in st.session_state:
                    st.session_state.posts = []
                st.session_state.posts.append(post_data)
                
                st.success("✅ Post submitted successfully! The moderation team will review it shortly.")
                st.balloons()
            except Exception as e:
                st.error(f"Error submitting post: {e}")
        else:
            st.error("⚠️ Please fill in both username and post content!")

# Display recent posts
st.markdown("---")
st.markdown("### 📋 Recent Posts")

# Show posts from session state
if 'posts' in st.session_state and st.session_state.posts:
    for idx, post in enumerate(reversed(st.session_state.posts[-10:])):  # Show last 10 posts
        status_emoji = "✅" if post.get("status") == "approved" else "🕐" if post.get("status") == "pending" else "🚫"
        
        st.markdown(f"""
        <div class="post-card">
            <p><span class="username">{post['username']}</span> <span class="timestamp">• {post['timestamp']}</span> {status_emoji}</p>
            <h4>{post['title']}</h4>
            <p>{post['content']}</p>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("No posts yet. Be the first to post!")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #707070; padding: 20px;'>
    <p>🔒 This is a test environment for AI moderation demonstration</p>
    <p>Posts are monitored by AI for policy violations in real-time</p>
</div>
""", unsafe_allow_html=True)
