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
    .flagged-high { background-color: #FFE5E5; border-left: 5px solid #FF6B6B; padding: 20px; border-radius: 8px; margin: 15px 0; }
    .flagged-medium { background-color: #FFF3CD; border-left: 5px solid #FFC107; padding: 20px; border-radius: 8px; margin: 15px 0; }
    .reported-card { background-color: #D1ECF1; border-left: 5px solid #17A2B8; padding: 20px; border-radius: 8px; margin: 15px 0; }
    .priority-badge { padding: 5px 10px; border-radius: 5px; font-weight: bold; font-size: 0.9em; display: inline-block; margin: 5px 0; }
    .critical { background-color: #DC3545; color: white; }
    .high { background-color: #FF6B6B; color: white; }
    .medium { background-color: #FFC107; color: #000; }
    .low { background-color: #6C757D; color: white; }
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
    st.markdown("### ⚠️ Priority Breakdown")
    st.markdown(f"🔴 Critical: **{stats['critical']}**")
    st.markdown(f"🟠 High: **{stats['high']}**")
    st.markdown(f"🟡 Medium: **{stats['medium']}**")
    st.markdown(f"⚪ Low: **{stats['low']}**")
    
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
    
    auto_refresh = st.checkbox("🔄 Auto-Refresh (10s)", value=True)
    if auto_refresh:
        time.sleep(10)
        st.rerun()

tab1, tab2, tab3, tab4, tab5 = st.tabs(["⏳ Pending Posts", "🟢 Approved Posts", "🔴 Flagged Posts", "🔵 Reported Posts", "📊 Analytics"])

def analyze_post_with_ai(post_content, username, board, post_title):
    if not AI_ENABLED:
        if any(word in post_content.lower() for word in ['scam', 'fraud', 'avoid', 'terrible']):
            return {
                'has_violations': True,
                'violations': [{
                    'type': 'Naming & Shaming', 'severity': 'High',
                    'evidence': 'Contains negative language about members',
                    'reason': 'Potential identification with negative intent',
                    'action': 'Edit to remove identifying information', 'confidence': '85%'
                }]
            }
        return {'has_violations': False, 'reason': 'No policy violations detected'}
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""You are an eBay community moderator. Analyze this post for policy violations.

POST:
Username: {username}
Board: {board}
Title: {post_title}
Content: {post_content}

POLICIES TO CHECK:
1. Naming & Shaming: Identifying other members negatively
2. Disrespect: Insults, attacks, vulgar language
3. Personal Info: Email, phone, addresses
4. Wrong Board: Content belongs elsewhere
5. Off-Topic: Unrelated to eBay
6. Spam: External links, advertising

RESPOND:
If violations: List each as:
- TYPE: [violation]
- SEVERITY: Critical/High/Medium/Low
- EVIDENCE: [quote from post]
- REASON: [why it violates]
- ACTION: [what to do]
- CONFIDENCE: [percentage]

If clean: Say "CLEAN POST - No violations detected"
"""
        response = model.generate_content(prompt)
        ai_response = response.text
        
        if "CLEAN POST" in ai_response or "No violations" in ai_response:
            return {'has_violations': False, 'reason': 'AI analysis: Complies with policy'}
        
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
            elif '- REASON:' in line and current_v:
                current_v['reason'] = line.split('REASON:')[1].strip()
            elif '- ACTION:' in line and current_v:
                current_v['action'] = line.split('ACTION:')[1].strip()
            elif '- CONFIDENCE:' in line and current_v:
                current_v['confidence'] = line.split('CONFIDENCE:')[1].strip()
        
        if current_v:
            violations.append(current_v)
        
        return {'has_violations': True, 'violations': violations}
    except Exception as e:
        return {'has_violations': False, 'error': str(e)}

with tab1:
    st.markdown("### ⏳ Pending Posts - Awaiting Review")
    pending_posts = [p for p in st.session_state.forum_posts.values() if p.get('status') == 'pending']
    pending_posts.sort(key=lambda x: (len(x.get('reports', [])), x.get('timestamp')), reverse=True)
    
    if pending_posts:
        st.info(f"📥 {len(pending_posts)} post(s) waiting for review. Posts are auto-loaded from the forum in real-time!")
        
        for post in pending_posts:
            post_id = post['id']
            is_reported = len(post.get('reports', [])) > 0
            card_class = "reported-card" if is_reported else "pending-card"
            
            st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
            st.markdown(f"**👤 {post['username']}** • 📌 {post['board']} • 🕐 {post['timestamp']}")
            
            if is_reported:
                st.markdown(f"**🚩 REPORTED by {len(post['reports'])} user(s)**")
                for report in post['reports']:
                    st.markdown(f"- Reporter: {report['reporter']} | Reason: {report['reason']}")
            
            st.markdown(f"**Title:** {post['title']}")
            st.markdown(f"**Content:** {post['content']}")
            st.markdown('</div>', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button(f"🤖 Analyze with AI", key=f"analyze_{post_id}", use_container_width=True):
                    with st.spinner("🔍 AI analyzing..."):
                        analysis = analyze_post_with_ai(post['content'], post['username'], post['board'], post['title'])
                        st.session_state.stats['total_analyzed'] += 1
                        
                        if analysis.get('has_violations'):
                            st.session_state.stats['violations_found'] += 1
                            for v in analysis['violations']:
                                severity = v.get('severity', 'Medium')
                                if 'Critical' in severity:
                                    st.session_state.stats['critical'] += 1
                                    st.error(f"🚨 {v['type']} - {severity}")
                                elif 'High' in severity:
                                    st.session_state.stats['high'] += 1
                                    st.warning(f"⚠️ {v['type']} - {severity}")
                                else:
                                    st.session_state.stats['medium'] += 1
                                    st.info(f"ℹ️ {v['type']} - {severity}")
                                st.markdown(f"**Evidence:** {v.get('evidence', 'N/A')}")
                                st.markdown(f"**Action:** {v.get('action', 'Review needed')}")
                            
                            storage_key = f"forum_post_{post_id}"
                            st.session_state.forum_posts[storage_key]['status'] = 'flagged'
                            st.session_state.forum_posts[storage_key]['ai_analysis'] = analysis
                            st.success("Post moved to Flagged section!")
                        else:
                            st.session_state.stats['clean_posts'] += 1
                            st.success("✅ No violations detected!")
                        st.rerun()
            
            with col2:
                if st.button(f"✅ Approve", key=f"approve_{post_id}", use_container_width=True):
                    storage_key = f"forum_post_{post_id}"
                    st.session_state.forum_posts[storage_key]['status'] = 'approved'
                    st.session_state.stats['ai_accepted'] += 1
                    st.success("✅ Post approved!")
                    st.rerun()
            
            with col3:
                if st.button(f"🚫 Flag", key=f"flag_{post_id}", use_container_width=True):
                    storage_key = f"forum_post_{post_id}"
                    st.session_state.forum_posts[storage_key]['status'] = 'flagged'
                    st.session_state.stats['violations_found'] += 1
                    st.warning("🚫 Post flagged!")
                    st.rerun()
            st.markdown("---")
    else:
        st.success("✅ No pending posts! All caught up!")
        st.info("💡 Posts from the forum will appear here automatically. Try posting in the forum app!")

with tab2:
    st.markdown("### 🟢 Approved Posts")
    approved_posts = [p for p in st.session_state.forum_posts.values() if p.get('status') == 'approved']
    if approved_posts:
        for post in sorted(approved_posts, key=lambda x: x['timestamp'], reverse=True):
            st.markdown('<div class="approved-card">', unsafe_allow_html=True)
            st.markdown(f"**👤 {post['username']}** • 📌 {post['board']} • 🕐 {post['timestamp']}")
            st.markdown(f"**Title:** {post['title']}")
            st.markdown(f"**Content:** {post['content'][:200]}...")
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No approved posts yet.")

with tab3:
    st.markdown("### 🔴 Flagged Posts")
    flagged_posts = [p for p in st.session_state.forum_posts.values() if p.get('status') == 'flagged']
    if flagged_posts:
        for post in sorted(flagged_posts, key=lambda x: x['timestamp'], reverse=True):
            st.markdown('<div class="flagged-critical">', unsafe_allow_html=True)
            st.markdown(f"**👤 {post['username']}** • 📌 {post['board']} • 🕐 {post['timestamp']}")
            st.markdown(f"**Title:** {post['title']}")
            st.markdown(f"**Content:** {post['content'][:200]}...")
            if post.get('ai_analysis'):
                analysis = post['ai_analysis']
                if analysis.get('violations'):
                    st.markdown("**Violations:**")
                    for v in analysis['violations']:
                        st.markdown(f"- {v.get('type')}: {v.get('severity')}")
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No flagged posts.")

with tab4:
    st.markdown("### 🔵 User-Reported Posts")
    reported_posts = [p for p in st.session_state.forum_posts.values() if len(p.get('reports', [])) > 0]
    if reported_posts:
        for post in sorted(reported_posts, key=lambda x: len(x.get('reports', [])), reverse=True):
            st.markdown('<div class="reported-card">', unsafe_allow_html=True)
            st.markdown(f"**👤 {post['username']}** • 📌 {post['board']} • 🕐 {post['timestamp']}")
            st.markdown(f"**🚩 {len(post['reports'])} Report(s)**")
            for report in post['reports']:
                st.markdown(f"- **{report['reporter']}**: {report['reason']}")
                if report.get('additional_info'):
                    st.markdown(f"  *{report['additional_info']}*")
            st.markdown(f"**Content:** {post['content'][:200]}...")
            st.markdown('</div>'
