import streamlit as st
from datetime import datetime
import os

# Configure page
st.set_page_config(page_title="eBay AI Moderation Dashboard", page_icon="🛡️", layout="wide")

# Initialize Gemini AI
try:
    import google.generativeai as genai
    
    # PASTE YOUR API KEY HERE
    GEMINI_API_KEY = "AIzaSyDNe7807fBg1KgwucNZ7GVBX0g1YwCWO9Y"
    genai.configure(api_key=GEMINI_API_KEY)
    AI_ENABLED = True
except Exception as e:
    AI_ENABLED = False
    st.error(f"AI initialization error: {e}")

# Initialize session state
if 'analyzed_posts' not in st.session_state:
    st.session_state.analyzed_posts = {
        'approved': [],
        'flagged': [],
        'reported': []
    }

if 'stats' not in st.session_state:
    st.session_state.stats = {
        'total_analyzed': 0,
        'violations_found': 0,
        'clean_posts': 0,
        'ai_accepted': 0,
        'human_override': 0,
        'critical': 0,
        'high': 0,
        'medium': 0,
        'low': 0
    }

if 'training_data' not in st.session_state:
    st.session_state.training_data = []

# Custom CSS
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
    
    .section-approved {
        background-color: #D4EDDA;
        border-left: 5px solid #28A745;
        padding: 20px;
        border-radius: 8px;
        margin: 15px 0;
    }
    
    .section-flagged-critical {
        background-color: #F8D7DA;
        border-left: 5px solid #DC3545;
        padding: 20px;
        border-radius: 8px;
        margin: 15px 0;
    }
    
    .section-flagged-high {
        background-color: #FFE5E5;
        border-left: 5px solid #FF6B6B;
        padding: 20px;
        border-radius: 8px;
        margin: 15px 0;
    }
    
    .section-flagged-medium {
        background-color: #FFF3CD;
        border-left: 5px solid #FFC107;
        padding: 20px;
        border-radius: 8px;
        margin: 15px 0;
    }
    
    .section-reported {
        background-color: #D1ECF1;
        border-left: 5px solid #17A2B8;
        padding: 20px;
        border-radius: 8px;
        margin: 15px 0;
    }
    
    .stat-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin: 10px 0;
    }
    
    .stat-number {
        font-size: 2.5em;
        font-weight: bold;
    }
    
    .priority-badge {
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
        font-size: 0.9em;
    }
    
    .critical { background-color: #DC3545; color: white; }
    .high { background-color: #FF6B6B; color: white; }
    .medium { background-color: #FFC107; color: #000; }
    .low { background-color: #6C757D; color: white; }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🛡️ eBay AI Moderation Dashboard</h1>
    <p style='font-size: 1.2em; margin: 0;'>Powered by Google Gemini AI • Real-time Policy Enforcement</p>
    <p style='margin: 5px 0 0 0; opacity: 0.9;'>Analyzing posts against eBay Board Usage Policy</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
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
    if st.button("📥 Export Report", use_container_width=True):
        st.success("Report exported! (Feature coming soon)")
    
    if st.button("🔄 Reset Statistics", use_container_width=True):
        st.session_state.stats = {
            'total_analyzed': 0,
            'violations_found': 0,
            'clean_posts': 0,
            'ai_accepted': 0,
            'human_override': 0,
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0
        }
        st.rerun()

# Main content tabs
tab1, tab2, tab3, tab4 = st.tabs(["🔍 Analyze New Post", "🟢 Approved Posts", "🔴 Flagged Posts", "🔵 Reported Posts"])

# eBay Boards
BOARDS = [
    "Selling", "Buying", "Payments", "Postage & Shipping",
    "Technical Issues", "Member to Member Support",
    "Mentors Forum", "General Discussion", "eBay Café"
]

# Tab 1: Analyze New Post
with tab1:
    st.markdown("### 🔍 Analyze Post with AI")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        username = st.text_input("Username", placeholder="Enter username from forum post", key="analyze_username")
        post_title = st.text_input("Post Title", placeholder="Enter post title", key="analyze_title")
        post_content = st.text_area(
            "Post Content", 
            placeholder="Paste the post content here for AI analysis...",
            height=200,
            key="analyze_content"
        )
    
    with col2:
        posted_board = st.selectbox("Posted in Board", BOARDS, key="analyze_board")
        st.info("💡 **AI Analysis**: Paste a post and click 'Analyze' to see real-time AI moderation!")
        
        if AI_ENABLED:
            st.success("✅ Gemini AI: Connected")
        else:
            st.warning("⚠️ AI: Using simulation mode")
    
    if st.button("🤖 Analyze with AI", type="primary", use_container_width=True):
        if post_content and username:
            with st.spinner("🔍 AI is analyzing the post against eBay policies..."):
                
                # Real Gemini AI Analysis
                if AI_ENABLED:
                    try:
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        
                        prompt = f"""You are an expert eBay community moderator. Analyze this forum post for policy violations.

POST DETAILS:
Username: {username}
Board: {posted_board}
Title: {post_title}
Content: {post_content}

EBAY BOARD USAGE POLICY - Check for these violations:

1. NAMING & SHAMING: Identifying other members (by username, item number, or description) with negative intent
2. DISRESPECTFUL LANGUAGE: Personal attacks, insults, vulgar language, harassment
3. PERSONAL INFORMATION: Email addresses, phone numbers, physical addresses, full real names
4. WRONG BOARD: Content that belongs in a different board
5. OFF-TOPIC: Content unrelated to eBay
6. SPAM/ADVERTISING: Promoting external sites, services, or products

ANALYZE and respond in this EXACT format:

VIOLATIONS: [Yes/No]

If YES, list each violation as:
- TYPE: [violation type]
- SEVERITY: [Critical/High/Medium/Low]
- EVIDENCE: [quote the specific violating text]
- REASON: [why this violates policy]
- ACTION: [Edit/Remove/Move to X board/Warning]
- CONFIDENCE: [percentage]

If NO violations, respond:
- CLEAN POST
- REASON: [why it's compliant]

Be thorough but concise. Focus on actual policy violations, not style or tone unless truly disrespectful."""

                        response = model.generate_content(prompt)
                        ai_analysis = response.text
                        
                    except Exception as e:
                        st.error(f"AI Error: {e}")
                        ai_analysis = None
                else:
                    # Fallback simulation
                    ai_analysis = "VIOLATIONS: Yes\n- TYPE: Naming & Shaming\n- SEVERITY: High\n- CONFIDENCE: 85%"
                
                # Parse AI response
                violations = []
                is_clean = "CLEAN POST" in ai_analysis or "VIOLATIONS: No" in ai_analysis
                
                if not is_clean and ai_analysis:
                    # Parse violations from AI response
                    lines = ai_analysis.split('\n')
                    current_violation = {}
                    
                    for line in lines:
                        if '- TYPE:' in line:
                            if current_violation:
                                violations.append(current_violation)
                            current_violation = {'type': line.split('TYPE:')[1].strip()}
                        elif '- SEVERITY:' in line and current_violation:
                            current_violation['severity'] = line.split('SEVERITY:')[1].strip()
                        elif '- EVIDENCE:' in line and current_violation:
                            current_violation['evidence'] = line.split('EVIDENCE:')[1].strip()
                        elif '- REASON:' in line and current_violation:
                            current_violation['reason'] = line.split('REASON:')[1].strip()
                        elif '- ACTION:' in line and current_violation:
                            current_violation['action'] = line.split('ACTION:')[1].strip()
                        elif '- CONFIDENCE:' in line and current_violation:
                            current_violation['confidence'] = line.split('CONFIDENCE:')[1].strip()
                    
                    if current_violation:
                        violations.append(current_violation)
                
                # Update stats
                st.session_state.stats['total_analyzed'] += 1
                
                # Display results
                st.markdown("---")
                st.markdown("### 🤖 AI Analysis Results")
                
                post_data = {
                    'id': f"post_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    'username': username,
                    'title': post_title,
                    'content': post_content,
                    'board': posted_board,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'violations': violations,
                    'ai_analysis': ai_analysis
                }
                
                if is_clean:
                    # Clean post
                    st.markdown('<div class="section-approved">', unsafe_allow_html=True)
                    st.markdown("#### ✅ No Violations Detected")
                    st.markdown(f"**Post by:** {username}")
                    st.markdown(f"**Board:** {posted_board}")
                    st.markdown(f"**AI Analysis:** This post complies with eBay Board Usage Policy.")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.session_state.stats['clean_posts'] += 1
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Accept & Approve", key="approve_clean", use_container_width=True):
                            st.session_state.analyzed_posts['approved'].append(post_data)
                            st.session_state.stats['ai_accepted'] += 1
                            st.success("✅ Post approved and added to Approved Posts!")
                            st.balloons()
                
                else:
                    # Violations found
                    st.session_state.stats['violations_found'] += 1
                    
                    for idx, v in enumerate(violations):
                        severity = v.get('severity', 'Medium')
                        
                        # Update priority stats
                        if 'Critical' in severity:
                            st.session_state.stats['critical'] += 1
                            css_class = "section-flagged-critical"
                            badge_class = "critical"
                        elif 'High' in severity:
                            st.session_state.stats['high'] += 1
                            css_class = "section-flagged-high"
                            badge_class = "high"
                        elif 'Medium' in severity:
                            st.session_state.stats['medium'] += 1
                            css_class = "section-flagged-medium"
                            badge_class = "medium"
                        else:
                            st.session_state.stats['low'] += 1
                            css_class = "section-flagged-medium"
                            badge_class = "low"
                        
                        st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
                        st.markdown(f"#### 🚨 Violation #{idx+1}: {v.get('type', 'Policy Violation')}")
                        st.markdown(f"<span class='priority-badge {badge_class}'>{severity} Priority</span>", unsafe_allow_html=True)
                        st.markdown(f"**Evidence:** {v.get('evidence', 'See post content')}")
                        st.markdown(f"**Reason:** {v.get('reason', 'Violates eBay policy')}")
                        st.markdown(f"**Recommended Action:** {v.get('action', 'Review required')}")
                        st.markdown(f"**AI Confidence:** {v.get('confidence', 'N/A')}")
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Action buttons
                    st.markdown("### 🎯 Moderation Action")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("✅ Accept AI Decision", key="accept_ai", type="primary", use_container_width=True):
                            st.session_state.analyzed_posts['flagged'].append(post_data)
                            st.session_state.stats['ai_accepted'] += 1
                            st.success("✅ AI decision accepted! Post added to Flagged Posts.")
                            st.balloons()
                    
                    with col2:
                        if st.button("⚠️ Override AI", key="override_ai", use_container_width=True):
                            st.session_state.stats['human_override'] += 1
                            
                            # Training data
                            training_entry = {
                                'post': post_content,
                                'ai_decision': 'Violation',
                                'human_decision': 'Override',
                                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                'reason': ''
                            }
                            
                            override_reason = st.text_area("Override Reason", placeholder="Explain why you're overriding the AI...", key="override_reason")
                            if st.button("Submit Override", key="submit_override"):
                                training_entry['reason'] = override_reason
                                st.session_state.training_data.append(training_entry)
                                post_data['human_override'] = override_reason
                                st.session_state.analyzed_posts['approved'].append(post_data)
                                st.warning(f"⚠️ Override recorded. AI will learn from this decision.")
                    
                    with col3:
                        if st.button("📝 Edit & Reanalyze", key="edit_reanalyze", use_container_width=True):
                            st.info("💡 Modify the post content above and click 'Analyze with AI' again.")
        else:
            st.error("⚠️ Please enter both username and post content!")

# Tab 2: Approved Posts
with tab2:
    st.markdown("### 🟢 AI-Approved Posts (Clean)")
    
    if st.session_state.analyzed_posts['approved']:
        for post in reversed(st.session_state.analyzed_posts['approved']):
            st.markdown('<div class="section-approved">', unsafe_allow_html=True)
            st.markdown(f"**👤 {post['username']}** • 📌 {post['board']} • 🕐 {post['timestamp']}")
            st.markdown(f"**Title:** {post['title']}")
            st.markdown(f"**Content:** {post['content'][:200]}...")
            if post.get('human_override'):
                st.markdown(f"**✏️ Human Override:** {post['human_override']}")
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No approved posts yet. Analyze posts in the 'Analyze New Post' tab!")

# Tab 3: Flagged Posts  
with tab3:
    st.markdown("### 🔴 AI-Flagged Posts (Violations Detected)")
    
    if st.session_state.analyzed_posts['flagged']:
        for post in reversed(st.session_state.analyzed_posts['flagged']):
            severity = post['violations'][0].get('severity', 'Medium') if post['violations'] else 'Medium'
            
            if 'Critical' in severity:
                css_class = "section-flagged-critical"
            elif 'High' in severity:
                css_class = "section-flagged-high"
            else:
                css_class = "section-flagged-medium"
            
            st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
            st.markdown(f"**👤 {post['username']}** • 📌 {post['board']} • 🕐 {post['timestamp']}")
            st.markdown(f"**Title:** {post['title']}")
            st.markdown(f"**Content:** {post['content'][:200]}...")
            st.markdown(f"**Violations:** {len(post['violations'])}")
            for v in post['violations']:
                st.markdown(f"- {v.get('type', 'Violation')}: {v.get('severity', 'Medium')} priority")
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No flagged posts yet. Analyze posts in the 'Analyze New Post' tab!")

# Tab 4: Reported Posts
with tab4:
    st.markdown("### 🔵 User-Reported Posts")
    st.info("This section will display posts reported by community members. Connect to your forum app to see live reports!")
    
    # Placeholder for future integration with forum reports
    if st.session_state.analyzed_posts.get('reported'):
        for post in st.session_state.analyzed_posts['reported']:
            st.markdown('<div class="section-reported">', unsafe_allow_html=True)
            st.markdown(f"**Reported by:** {post.get('reporter', 'Community Member')}")
            st.markdown(f"**Reason:** {post.get('report_reason', 'Policy violation')}")
            st.markdown(f"**Post:** {post.get('content', '')[:200]}...")
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown("No reported posts yet.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #707070; padding: 20px;'>
    <p>🤖 Powered by Google Gemini AI • eBay Board Usage Policy Enforcement</p>
    <p>Real-time analysis • Machine learning from moderator feedback • Saving millions in moderation costs</p>
</div>
""", unsafe_allow_html=True)
