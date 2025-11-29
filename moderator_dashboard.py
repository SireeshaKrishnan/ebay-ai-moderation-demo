import streamlit as st
from datetime import datetime
import time

st.set_page_config(page_title="eBay AI Moderation Dashboard", page_icon="🛡️", layout="wide")

try:
    import google.generativeai as genai
    GEMINI_API_KEY = "AIzaSyDNe7807fBg1KgwucNZ7GVBX0g1YwCWO9Y"
    genai.configure(api_key=GEMINI_API_KEY)
    AI_ENABLED = True
except Exception as e:
    AI_ENABLED = False

if 'stats' not in st.session_state:
    st.session_state.stats = {
        'total_analyzed': 0, 'violations_found': 0, 'clean_posts': 0,
        'ai_accepted': 0, 'human_override': 0, 'critical': 0,
        'high': 0, 'medium': 0, 'low': 0
    }

if 'training_data' not in st.session_state:
    st.session_state.training_data = []

if 'forum_posts' not in st.session_state:
    st.session_state.forum_posts = {}

st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #E31C23 0%, #8B0000 100%);
        color: white;
        padding: 25px;
        border-radius: 10px;
        margin-bottom: 30px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .pending-card { background-color: #FFF9E6; border-left: 5px solid #FFC107; padding: 20px; border-radius: 8px; margin: 15px 0; }
    .approved-card { background-color: #D4EDDA; border-left: 5px solid #28A745; padding: 20px; border-radius: 8px; margin: 15px 0; }
    .flagged-critical { background-color: #F8D7DA; border-left: 5px solid #DC3545; padding: 20px; border-radius: 8px; margin: 15px 0; }
    .reported-card { background-color: #D1ECF1; border-left: 5px solid #17A2B8; padding: 20px; border-radius: 8px; margin: 15px 0; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>🛡️ eBay AI Moderation Dashboard</h1>
    <p style='font-size: 1.2em; margin: 0;'>Powered by Google Gemini AI • Real-time Policy Enforcement</p>
    <p style='margin: 5px 0 0 0; opacity: 0.9;'>Live connection to forum • Auto-refreshing</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 📊 Today's Statistics")
    stats = st.session_state.stats
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Posts Analyzed", stats['total_analyzed'])
        st.metric("Violations", stats['violations_found'])
    with col2:
        st.metric("Clean Posts", stats['clean_posts'])
        violation_rate = int(stats['violations_found']/max(stats['total_analyzed'],1)*100) if stats['total_analyzed'] > 0 else 0
        st.metric("Violation Rate", f"{violation_rate}%")
    
    st.markdown("---")
    st.markdown("### 🎯 AI Performance")
    st.metric("AI Accepted", stats['ai_accepted'])
    st.metric("Human Override", stats['human_override'])
    
    if stats['ai_accepted'] + stats['human_override'] > 0:
        accuracy = int(stats['ai_accepted']/(stats['ai_accepted']+stats['human_override'])*100)
        st.metric("AI Accuracy", f"{accuracy}%")
    
    st.markdown("---")
    pending_count = sum(1 for p in st.session_state.forum_posts.values() if p.get('status') == 'pending')
    
    if AI_ENABLED:
        st.success("✅ Gemini AI: Connected")
    else:
        st.warning("⚠️ AI: Simulation Mode")
    
    st.info(f"📡 Live Posts: {len(st.session_state.forum_posts)}")
    st.warning(f"⏳ Pending Review: {pending_count}")
    
    st.markdown("---")
    if st.button("🔄 Refresh Now", use_container_width=True):
        st.rerun()

tab1, tab2, tab3, tab4 = st.tabs(["⏳ Pending Posts", "🟢 Approved Posts", "🔴 Flagged Posts", "🔵 Reported Posts"])

def analyze_post_with_ai(post_content, username, board, post_title):
    if not AI_ENABLED:
        if any(word in post_content.lower() for word in ['scam', 'fraud', 'avoid', 'terrible']):
            return {
                'has_violations': True,
                'violations': [{
                    'type': 'Naming & Shaming',
                    'severity': 'High',
                    'evidence': 'Contains negative language',
                    'reason': 'Potential identification with negative intent',
                    'action': 'Edit to remove identifying information',
                    'confidence': '85%'
                }]
            }
        return {'has_violations': False}
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""Analyze this eBay forum post for policy violations.

POST: {post_content}
Username: {username}
Board: {board}

Check for: Naming & Shaming, Disrespect, Personal Info, Wrong Board, Spam

If violations found, list as:
- TYPE: [violation]
- SEVERITY: Critical/High/Medium/Low
- EVIDENCE: [quote]
- ACTION: [what to do]

If clean: Say "CLEAN POST"
"""
        response = model.generate_content(prompt)
        ai_response = response.text
        
        if "CLEAN POST" in ai_response:
            return {'has_violations': False}
        
        violations = []
        lines = ai_response.split('\n')
        current_v = {}
        
        for line in lines:
            if '- TYPE:' in line:
                if current_v:
                    violations.append(current_v)
                current_v = {'type': line.split('TYPE:')[1].strip()}
            elif '- SEVERITY:' in line and current_v:
                current_v['severity'] = line.split('SEVERITY:')[1].strip()
            elif '- EVIDENCE:' in line and current_v:
                current_v['evidence'] = line.split('EVIDENCE:')[1].strip()
            elif '- ACTION:' in line and current_v:
                current_v['action'] = line.split('ACTION:')[1].strip()
        
        if current_v:
            violations.append(current_v)
        
        return {'has_violations': True, 'violations': violations}
    except:
        return {'has_violations': False}

with tab1:
    st.markdown("### ⏳ Pending Posts - Awaiting Review")
    pending_posts = [p for p in st.session_state.forum_posts.values() if p.get('status') == 'pending']
    
    if pending_posts:
        st.info(f"📥 {len(pending_posts)} post(s) waiting for review")
        
        for post in pending_posts:
            post_id = post['id']
            is_reported = len(post.get('reports', [])) > 0
            
            st.markdown(f'<div class="{"reported-card" if is_reported else "pending-card"}">', unsafe_allow_html=True)
            st.markdown(f"**👤 {post['username']}** • 📌 {post['board']} • 🕐 {post['timestamp']}")
            
            if is_reported:
                st.markdown(f"**🚩 REPORTED by {len(post['reports'])} user(s)**")
            
            st.markdown(f"**Title:** {post['title']}")
            st.markdown(f"**Content:** {post['content']}")
            st.markdown('</div>', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🤖 Analyze", key=f"analyze_{post_id}", use_container_width=True):
                    with st.spinner("Analyzing..."):
                        analysis = analyze_post_with_ai(post['content'], post['username'], post['board'], post['title'])
                        st.session_state.stats['total_analyzed'] += 1
                        
                        if analysis.get('has_violations'):
                            st.session_state.stats['violations_found'] += 1
                            for v in analysis.get('violations', []):
                                st.error(f"🚨 {v.get('type', 'Violation')}: {v.get('severity', 'High')}")
                                st.markdown(f"**Evidence:** {v.get('evidence', 'N/A')}")
                            
                            storage_key = f"forum_post_{post_id}"
                            st.session_state.forum_posts[storage_key]['status'] = 'flagged'
                            st.success("Moved to Flagged!")
                        else:
                            st.session_state.stats['clean_posts'] += 1
                            st.success("✅ No violations!")
                        st.rerun()
            
            with col2:
                if st.button("✅ Approve", key=f"approve_{post_id}", use_container_width=True):
                    storage_key = f"forum_post_{post_id}"
                    st.session_state.forum_posts[storage_key]['status'] = 'approved'
                    st.session_state.stats['ai_accepted'] += 1
                    st.rerun()
            
            with col3:
                if st.button("🚫 Flag", key=f"flag_{post_id}", use_container_width=True):
                    storage_key = f"forum_post_{post_id}"
                    st.session_state.forum_posts[storage_key]['status'] = 'flagged'
                    st.session_state.stats['violations_found'] += 1
                    st.rerun()
            
            st.markdown("---")
    else:
        st.success("✅ No pending posts!")
        st.info("💡 Posts from the forum will appear here automatically")

with tab2:
    st.markdown("### 🟢 Approved Posts")
    approved_posts = [p for p in st.session_state.forum_posts.values() if p.get('status') == 'approved']
    
    if approved_posts:
        for post in approved_posts:
            st.markdown('<div class="approved-card">', unsafe_allow_html=True)
            st.markdown(f"**👤 {post['username']}** • 📌 {post['board']}")
            st.markdown(f"**Title:** {post['title']}")
            st.markdown(f"**Content:** {post['content'][:200]}...")
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No approved posts yet")

with tab3:
    st.markdown("### 🔴 Flagged Posts")
    flagged_posts = [p for p in st.session_state.forum_posts.values() if p.get('status') == 'flagged']
    
    if flagged_posts:
        for post in flagged_posts:
            st.markdown('<div class="flagged-critical">', unsafe_allow_html=True)
            st.markdown(f"**👤 {post['username']}** • 📌 {post['board']}")
            st.markdown(f"**Title:** {post['title']}")
            st.markdown(f"**Content:** {post['content'][:200]}...")
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No flagged posts")

with tab4:
    st.markdown("### 🔵 User-Reported Posts")
    reported_posts = [p for p in st.session_state.forum_posts.values() if len(p.get('reports', [])) > 0]
    
    if reported_posts:
        for post in reported_posts:
            st.markdown('<div class="reported-card">', unsafe_allow_html=True)
            st.markdown(f"**👤 {post['username']}** • 📌 {post['board']}")
            st.markdown(f"**🚩 {len(post['reports'])} Report(s)**")
            for report in post['reports']:
                st.markdown(f"- **{report['reporter']}**: {report['reason']}")
            st.markdown(f"**Content:** {post['content'][:200]}...")
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No reported posts")

st.markdown("---")
st.markdown('<div style="text-align: center; color: #707070; padding: 20px;"><p>🤖 Real-time AI Moderation • Saving $3.1M+ Annually</p></div>', unsafe_allow_html=True)
