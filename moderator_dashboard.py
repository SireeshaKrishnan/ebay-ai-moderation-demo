import streamlit as st
import pandas as pd
import re
from datetime import datetime, timedelta

# ================================
# PAGE CONFIG
# ================================

st.set_page_config(
    page_title="eBay AI Moderation Dashboard",
    page_icon="🛡️",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
.approved-section {
    background-color: #d4edda !important;
    border-left: 5px solid #28a745 !important;
    padding: 15px;
    margin: 10px 0;
    border-radius: 5px;
}

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

.user-profile-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 20px;
    border-radius: 10px;
    margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)

# ================================
# STATS STORAGE
# ================================

def init_stats_storage():
    """Initialize comprehensive stats storage"""
    if 'action_log' not in st.session_state:
        st.session_state.action_log = []
    
    if 'violation_log' not in st.session_state:
        st.session_state.violation_log = []
    
    if 'user_profiles' not in st.session_state:
        st.session_state.user_profiles = {}

def log_moderation_action(post_id, action_type, moderator, username, details=None):
    """Log every moderation action"""
    log_entry = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'date': datetime.now().strftime('%Y-%m-%d'),
        'post_id': post_id,
        'username': username,
        'action_type': action_type,
        'moderator': moderator,
        'details': details or {}
    }
    st.session_state.action_log.append(log_entry)
    update_user_profile(username, 'action', log_entry)
    return log_entry

def log_violation(post_id, username, violation_type, severity, confidence, evidence):
    """Log each violation detected"""
    violation_entry = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'date': datetime.now().strftime('%Y-%m-%d'),
        'post_id': post_id,
        'username': username,
        'violation_type': violation_type,
        'severity': severity,
        'confidence': confidence,
        'evidence': evidence
    }
    st.session_state.violation_log.append(violation_entry)
    update_user_profile(username, 'violation', violation_entry)
    return violation_entry

def update_user_profile(username, event_type, event_data):
    """Update user profile with new events"""
    if username not in st.session_state.user_profiles:
        st.session_state.user_profiles[username] = {
            'username': username,
            'first_seen': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_posts': 0,
            'total_violations': 0,
            'violations': [],
            'actions': [],
            'violation_types': {},
            'severity_counts': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0},
            'status': 'clean'
        }
    
    profile = st.session_state.user_profiles[username]
    
    if event_type == 'post':
        profile['total_posts'] += 1
    
    elif event_type == 'violation':
        profile['total_violations'] += 1
        profile['violations'].append(event_data)
        
        v_type = event_data['violation_type']
        profile['violation_types'][v_type] = profile['violation_types'].get(v_type, 0) + 1
        
        severity = event_data['severity']
        profile['severity_counts'][severity] = profile['severity_counts'].get(severity, 0) + 1
        
        if profile['severity_counts']['critical'] > 0 or profile['total_violations'] >= 5:
            profile['status'] = 'flagged'
        elif profile['total_violations'] >= 2:
            profile['status'] = 'warning'
    
    elif event_type == 'action':
        profile['actions'].append(event_data)
        if event_data['action_type'] == 'banned':
            profile['status'] = 'banned'

def get_user_profile(username):
    """Get complete user profile"""
    return st.session_state.user_profiles.get(username, None)

def get_stats_for_period(start_date, end_date):
    """Get comprehensive stats for date range"""
    
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    actions_in_period = [
        a for a in st.session_state.action_log 
        if start_str <= a['date'] <= end_str
    ]
    
    violations_in_period = [
        v for v in st.session_state.violation_log
        if start_str <= v['date'] <= end_str
    ]
    
    stats = {
        'total_actions': len(actions_in_period),
        'total_violations': len(violations_in_period),
        
        # Action breakdown
        'analyzed': len([a for a in actions_in_period if a['action_type'] == 'analyzed']),
        'edited': len([a for a in actions_in_period if a['action_type'] == 'edited']),
        'removed': len([a for a in actions_in_period if a['action_type'] == 'removed']),
        'approved': len([a for a in actions_in_period if a['action_type'] == 'approved']),
        'no_action_required': len([a for a in actions_in_period if a['action_type'] == 'no_action_required']),
        'overridden': len([a for a in actions_in_period if a['action_type'] == 'overridden']),
        'moved': len([a for a in actions_in_period if a['action_type'] == 'moved']),
        'locked': len([a for a in actions_in_period if a['action_type'] == 'locked']),
        'merged': len([a for a in actions_in_period if a['action_type'] == 'merged']),
        'banned': len([a for a in actions_in_period if a['action_type'] == 'banned']),
        'warned': len([a for a in actions_in_period if a['action_type'] == 'warned']),
        
        # Violation breakdown
        'pii_violations': len([v for v in violations_in_period if 'PII' in v['violation_type']]),
        'naming_violations': len([v for v in violations_in_period if 'Naming' in v['violation_type']]),
        'disrespect_violations': len([v for v in violations_in_period if 'Disrespect' in v['violation_type']]),
        'wrong_board_violations': len([v for v in violations_in_period if 'Wrong Board' in v['violation_type']]),
        'off_topic_violations': len([v for v in violations_in_period if 'Off-Topic' in v['violation_type']]),
        'spam_violations': len([v for v in violations_in_period if 'Spam' in v['violation_type']]),
        'fee_avoidance_violations': len([v for v in violations_in_period if 'Fee' in v['violation_type']]),
        'duplicate_violations': len([v for v in violations_in_period if 'Duplicate' in v['violation_type']]),
        'moderation_discussion_violations': len([v for v in violations_in_period if 'Moderation' in v['violation_type']]),
        'policy_breach_violations': len([v for v in violations_in_period if 'Policy Breach' in v['violation_type']]),
        'necropost_violations': len([v for v in violations_in_period if 'Necropost' in v['violation_type']]),
        'advertising_violations': len([v for v in violations_in_period if 'Advertising' in v['violation_type']]),
        'other_violations': len([v for v in violations_in_period if 'Other' in v['violation_type']]),
        
        # Severity breakdown
        'critical': len([v for v in violations_in_period if v['severity'] == 'critical']),
        'high': len([v for v in violations_in_period if v['severity'] == 'high']),
        'medium': len([v for v in violations_in_period if v['severity'] == 'medium']),
        'low': len([v for v in violations_in_period if v['severity'] == 'low']),
    }
    
    return stats

# ================================
# ULTRA-STRICT AI ANALYSIS
# ================================

def analyze_post_ultra_strict(content, post_id, board, username):
    """Ultra-strict policy analysis"""
    
    result = {
        "post_id": post_id,
        "overall_status": "assured",
        "confidence": 95,
        "priority": "low",
        "violations_detected": [],
        "recommended_action": "none"
    }
    
    violations = []
    highest_priority = "low"
    max_confidence = 0
    
    # PII Detection
    pii_patterns = {
        "Phone": r'\b(0[1-9]\d{8,9}|\+44\s?\d{10}|0[2-4]\d{8}|\+61\s?\d{9})\b',
        "Email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "Address": r'\b[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}\b'
    }
    
    for pii_type, pattern in pii_patterns.items():
        match = re.search(pattern, content, re.IGNORECASE if pii_type == "Address" else 0)
        if match:
            violations.append({
                "type": f"PII - {pii_type}",
                "confidence": 100,
                "evidence": match.group(),
                "policy": "Contact Information Sharing Policy",
                "severity": "critical"
            })
            highest_priority = "critical"
            max_confidence = 100
            log_violation(post_id, username, f"PII - {pii_type}", "critical", 100, match.group())
            break
    
    # Naming & Shaming
    negative_words = ['scam', 'scammer', 'fraud', 'terrible', 'awful', 'worst', 'avoid', 'cheat']
    content_lower = content.lower()
    
    if any(word in content_lower for word in negative_words):
        if re.search(r'\b(?:seller|buyer)\s+[A-Za-z0-9_-]{3,20}\b', content, re.IGNORECASE):
            violations.append({
                "type": "Naming and Shaming",
                "confidence": 94,
                "evidence": "Username with negative context",
                "policy": "Board Usage Policy",
                "severity": "high"
            })
            if highest_priority in ["low", "medium"]:
                highest_priority = "high"
            max_confidence = max(max_confidence, 94)
            log_violation(post_id, username, "Naming and Shaming", "high", 94, "Username with negative context")
    
    # Disrespect - Profanity
    profanity = [r'\bf[\*\@]ck', r'\bsh[\*\!]t', r'\bd[\@\*]mn', r'\bb[\*\!]tch']
    for pattern in profanity:
        if re.search(pattern, content_lower):
            violations.append({
                "type": "Disrespect - Profanity",
                "confidence": 98,
                "evidence": "Profane language",
                "policy": "Board Usage Policy",
                "severity": "medium"
            })
            if highest_priority == "low":
                highest_priority = "medium"
            max_confidence = max(max_confidence, 98)
            log_violation(post_id, username, "Disrespect - Profanity", "medium", 98, "Profane language")
            break
    
    # Disrespect - Insults
    insults = ['idiot', 'stupid', 'dumb', 'moron', 'fool']
    for insult in insults:
        if insult in content_lower:
            violations.append({
                "type": "Disrespect - Insult",
                "confidence": 96,
                "evidence": f"Contains: '{insult}'",
                "policy": "Board Usage Policy",
                "severity": "high"
            })
            if highest_priority in ["low", "medium"]:
                highest_priority = "high"
            max_confidence = max(max_confidence, 96)
            log_violation(post_id, username, "Disrespect - Insult", "high", 96, f"Contains: '{insult}'")
            break
    
    # Spam
    spam_domains = ['amazon.com', 'amazon.co.uk', 'etsy.com']
    for domain in spam_domains:
        if domain in content_lower:
            violations.append({
                "type": "Spam - External Link",
                "confidence": 100,
                "evidence": f"Link to: {domain}",
                "policy": "Board Usage Policy",
                "severity": "high"
            })
            highest_priority = "high"
            max_confidence = 100
            log_violation(post_id, username, "Spam - External Link", "high", 100, f"Link to: {domain}")
            break
    
    if violations:
        result["overall_status"] = "flagged"
        result["violations_detected"] = violations
        result["confidence"] = max_confidence
        result["priority"] = highest_priority
        result["recommended_action"] = "edit"
    
    log_moderation_action(post_id, "analyzed", "AI System", username, {
        'status': result['overall_status'],
        'violations_found': len(violations)
    })
    
    return result

# ================================
# SESSION STATE INITIALIZATION
# ================================

init_stats_storage()

if 'forum_posts' not in st.session_state:
    st.session_state.forum_posts = {}

if 'ebay_forum_posts_v1' not in st.session_state:
    st.session_state['ebay_forum_posts_v1'] = {}

if 'viewing_user_profile' not in st.session_state:
    st.session_state.viewing_user_profile = None

# Sync with forum app and AUTO-ANALYZE new posts
if 'ebay_forum_posts_v1' in st.session_state and st.session_state['ebay_forum_posts_v1']:
    st.session_state.forum_posts = st.session_state['ebay_forum_posts_v1']
    
    # AUTO-ANALYZE: Check for any unanalyzed posts and analyze them automatically
    for post_key, post in st.session_state.forum_posts.items():
        if not post.get('ai_analyzed', False):
            # Automatically analyze this post
            analysis = analyze_post_ultra_strict(
                post['content'], 
                post['id'], 
                post.get('board', 'Unknown'), 
                post['username']
            )
            
            # Update post with analysis results
            st.session_state.forum_posts[post_key]['ai_analyzed'] = True
            st.session_state.forum_posts[post_key]['overall_status'] = analysis['overall_status']
            st.session_state.forum_posts[post_key]['confidence'] = analysis['confidence']
            st.session_state.forum_posts[post_key]['priority'] = analysis['priority']
            st.session_state.forum_posts[post_key]['violations_detected'] = analysis['violations_detected']
            
            # Also update in ebay_forum_posts_v1
            if post_key in st.session_state['ebay_forum_posts_v1']:
                st.session_state['ebay_forum_posts_v1'][post_key]['ai_analyzed'] = True
                st.session_state['ebay_forum_posts_v1'][post_key]['overall_status'] = analysis['overall_status']
                st.session_state['ebay_forum_posts_v1'][post_key]['confidence'] = analysis['confidence']
                st.session_state['ebay_forum_posts_v1'][post_key]['priority'] = analysis['priority']
                st.session_state['ebay_forum_posts_v1'][post_key]['violations_detected'] = analysis['violations_detected']
            
            update_user_profile(post['username'], 'post', {})

# ================================
# USER PROFILE VIEW
# ================================

def show_user_profile(username):
    """Display detailed user profile"""
    profile = get_user_profile(username)
    
    if not profile:
        st.warning(f"No profile found for user: {username}")
        return
    
    st.markdown(f"""
    <div class="user-profile-card">
        <h2>👤 User Profile: {username}</h2>
        <p><strong>Member Since:</strong> {profile['first_seen']}</p>
        <p><strong>Status:</strong> {profile['status'].upper()}</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Posts", profile['total_posts'])
    col2.metric("Total Violations", profile['total_violations'])
    col3.metric("🚨 Critical", profile['severity_counts']['critical'])
    col4.metric("🔴 High", profile['severity_counts']['high'])
    
    st.markdown("---")
    
    # Violation History
    st.subheader("⚠️ Violation History")
    
    if profile['violations']:
        st.warning(f"This user has {len(profile['violations'])} violation(s) on record")
        
        st.markdown("### By Type:")
        for v_type, count in profile['violation_types'].items():
            st.markdown(f"**{v_type}:** {count} occurrence(s)")
        
        st.markdown("---")
        
        st.markdown("### Detailed Violations:")
        for i, v in enumerate(reversed(profile['violations'][-10:]), 1):
            severity_emoji = {"critical": "🚨", "high": "🔴", "medium": "🟠", "low": "⚪"}
            emoji = severity_emoji.get(v['severity'], "⚪")
            
            with st.expander(f"{emoji} {v['timestamp']} - {v['violation_type']}"):
                st.markdown(f"**Post ID:** {v['post_id']}")
                st.markdown(f"**Severity:** {v['severity'].upper()}")
                st.markdown(f"**Confidence:** {v['confidence']}%")
                st.markdown(f"**Evidence:** {v['evidence']}")
    else:
        st.success("✅ No violations on record - Clean user!")
    
    st.markdown("---")
    
    # Action History
    st.subheader("🔧 Moderation Actions Taken")
    
    if profile['actions']:
        for action in reversed(profile['actions'][-5:]):
            st.markdown(f"**{action['timestamp']}** - {action['action_type'].upper()} by {action['moderator']}")
    else:
        st.info("No moderation actions taken yet")
    
    st.markdown("---")
    
    if st.button("← Back to Dashboard", use_container_width=True):
        st.session_state.viewing_user_profile = None
        st.rerun()

# ================================
# MAIN DASHBOARD
# ================================

st.title("🛡️ eBay Community AI Moderation Dashboard")
st.markdown("**Ultra-Strict Policy Engine | Real-Time Auto-Classification | Complete Stats Tracking**")

# Sync status with auto-analyze indicator
if st.session_state.forum_posts:
    analyzed_count = len([p for p in st.session_state.forum_posts.values() if p.get('ai_analyzed')])
    total_count = len(st.session_state.forum_posts)
    st.success(f"✨ LIVE MODERATION: {total_count} posts loaded | {analyzed_count} analyzed | Auto-classification active")
else:
    st.warning("📡 No posts in queue | Waiting for new posts from Forum App")
    st.info("👉 **To test:** Open the Forum App in another tab and submit a post. Then click 'Refresh' here to see it analyzed automatically.")

st.markdown("---")

# Control buttons
col_ref1, col_ref2, col_ref3 = st.columns([4, 1, 1])

with col_ref2:
    auto_refresh = st.checkbox("🔄 Auto", value=False, help="Auto-refresh every 3 seconds")

with col_ref3:
    if st.button("🔄 Refresh", use_container_width=True):
        if 'ebay_forum_posts_v1' in st.session_state:
            st.session_state.forum_posts = st.session_state['ebay_forum_posts_v1']
        st.rerun()

# Auto-refresh functionality
if auto_refresh:
    import time
    time.sleep(3)
    st.rerun()

# ================================
# SIDEBAR STATS
# ================================

with st.sidebar:
    st.header("📊 Stats Query")
    
    quick_filter = st.selectbox(
        "Time Period",
        ["Today", "Yesterday", "Last 7 Days", "Last 30 Days", "Custom"]
    )
    
    if quick_filter == "Today":
        start_date = datetime.now().replace(hour=0, minute=0, second=0)
        end_date = datetime.now()
    elif quick_filter == "Yesterday":
        start_date = (datetime.now() - timedelta(days=1)).replace(hour=0, minute=0)
        end_date = (datetime.now() - timedelta(days=1)).replace(hour=23, minute=59)
    elif quick_filter == "Last 7 Days":
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
    elif quick_filter == "Last 30 Days":
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
    else:
        start_date = st.date_input("Start", value=datetime.now() - timedelta(days=7))
        end_date = st.date_input("End", value=datetime.now())
    
    period_stats = get_stats_for_period(start_date, end_date)
    
    st.markdown("---")
    st.subheader("📈 Period Summary")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Actions", period_stats['total_actions'])
    with col2:
        st.metric("Violations", period_stats['total_violations'])
    
    st.markdown("---")
    st.subheader("🔧 Actions")
    
    st.markdown(f"🤖 **Analyzed:** {period_stats['analyzed']}")
    st.markdown(f"✅ **Approved:** {period_stats['no_action_required']}")
    st.markdown(f"✏️ **Edited:** {period_stats['edited']}")
    st.markdown(f"🗑️ **Removed:** {period_stats['removed']}")
    st.markdown(f"🚫 **Banned:** {period_stats['banned']}")
    
    st.markdown("---")
    st.subheader("⚠️ Violations")
    
    st.markdown(f"🚨 **PII:** {period_stats['pii_violations']}")
    st.markdown(f"👤 **Naming:** {period_stats['naming_violations']}")
    st.markdown(f"😠 **Disrespect:** {period_stats['disrespect_violations']}")
    st.markdown(f"📧 **Spam:** {period_stats['spam_violations']}")
    st.markdown(f"❓ **Other:** {period_stats['other_violations']}")
    
    st.markdown("---")
    st.subheader("🎯 By Severity")
    
    st.markdown(f"🚨 **Critical:** {period_stats['critical']}")
    st.markdown(f"🔴 **High:** {period_stats['high']}")
    st.markdown(f"🟠 **Medium:** {period_stats['medium']}")
    st.markdown(f"⚪ **Low:** {period_stats['low']}")

# ================================
# MAIN VIEW
# ================================

if st.session_state.viewing_user_profile:
    show_user_profile(st.session_state.viewing_user_profile)

else:
    # Stats Display
    all_posts = list(st.session_state.forum_posts.values())
    ai_approved = [p for p in all_posts if p.get('ai_analyzed') and p.get('overall_status') == 'assured']
    user_reported = [p for p in all_posts if len(p.get('reports', [])) > 0]
    ai_flagged = [p for p in all_posts if p.get('ai_analyzed') and p.get('overall_status') == 'flagged']
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Posts", len(all_posts))
    col2.metric("✅ AI Approved", len(ai_approved), delta=f"{len(ai_approved)}", delta_color="normal")
    col3.metric("👤 User Reported", len(user_reported), delta=f"{len(user_reported)}" if len(user_reported) > 0 else "0", delta_color="off")
    col4.metric("🚨 AI Flagged", len(ai_flagged), delta=f"{len(ai_flagged)}" if len(ai_flagged) > 0 else "0", delta_color="inverse")
    
    # Show classification status
    if all_posts:
        analyzed_pct = (len([p for p in all_posts if p.get('ai_analyzed')]) / len(all_posts)) * 100
        st.progress(analyzed_pct / 100)
        st.caption(f"📊 Classification Status: {analyzed_pct:.0f}% analyzed and auto-sorted")
    
    st.markdown("---")
    
    # Add info banner
    st.info("🤖 **AUTO-CLASSIFICATION ACTIVE:** Posts are automatically analyzed and sorted into columns below")
    
    st.markdown("---")
    
    # Three Column Layout
    col_approved, col_reported, col_flagged = st.columns(3)
    
    with col_approved:
        st.subheader("✅ AI Approved")
        st.caption(f"{len(ai_approved)} posts • Auto-classified as clean")
        
        if ai_approved:
            for post in ai_approved[:10]:
                st.markdown(f"""
                <div class="approved-section">
                    <strong>#{post['id'][:8]}</strong> | {post.get('board', 'Unknown')}<br>
                    👤 {post['username']}<br>
                    🕒 {post['timestamp']}<br>
                    📋 <strong>{post.get('title', 'Untitled')}</strong><br><br>
                    <em>{post['content'][:100]}...</em><br><br>
                    ✅ {post.get('confidence', 95)}% Confidence • No violations detected
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"👤 View Profile", key=f"profile_a_{post['id']}", use_container_width=True):
                    st.session_state.viewing_user_profile = post['username']
                    st.rerun()
        else:
            st.success("✅ No approved posts in queue")
    
    with col_reported:
        st.subheader("👤 User Reported")
        st.caption(f"{len(user_reported)} posts • Requires review")
        
        if user_reported:
            for post in sorted(user_reported, key=lambda x: len(x.get('reports', [])), reverse=True)[:10]:
                report_count = len(post['reports'])
                css_class = "user-reported-high" if report_count >= 3 else "user-reported-medium" if report_count >= 2 else "user-reported-low"
                
                st.markdown(f"""
                <div class="{css_class}">
                    <strong>#{post['id'][:8]}</strong> | {post.get('board', 'Unknown')}<br>
                    👤 {post['username']}<br>
                    🕒 {post['timestamp']}<br>
                    📋 <strong>{post.get('title', 'Untitled')}</strong><br><br>
                    <em>{post['content'][:100]}...</em><br><br>
                    🚩 <strong>{report_count} report(s)</strong>
                </div>
                """, unsafe_allow_html=True)
                
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button(f"✅ Approve", key=f"approve_r_{post['id']}", use_container_width=True):
                        log_moderation_action(post['id'], "approved", "Moderator", post['username'])
                        st.success("Approved")
                with col_b:
                    if st.button(f"👤 Profile", key=f"profile_r_{post['id']}", use_container_width=True):
                        st.session_state.viewing_user_profile = post['username']
                        st.rerun()
        else:
            st.success("✅ No user reports in queue")
    
    with col_flagged:
        st.subheader("🚨 AI Flagged")
        st.caption(f"{len(ai_flagged)} posts • Auto-detected violations")
        
        if ai_flagged:
            for post in sorted(ai_flagged, key=lambda x: {'critical':0,'high':1,'medium':2}.get(x.get('priority','low'),3))[:10]:
                priority = post.get('priority', 'low')
                css_class = f"flagged-{priority}"
                emoji = {"critical":"🚨", "high":"🔴", "medium":"🟠"}.get(priority, "⚪")
                
                st.markdown(f"""
                <div class="{css_class}">
                    {emoji} <strong>{priority.upper()} PRIORITY</strong><br>
                    #{post['id'][:8]} | {post.get('board', 'Unknown')}<br>
                    👤 {post['username']}<br>
                    🕒 {post['timestamp']}<br>
                    📋 <strong>{post.get('title', 'Untitled')}</strong><br><br>
                    <strong>Violations Detected:</strong><br>
                """, unsafe_allow_html=True)
                
                for v in post.get('violations_detected', []):
                    st.markdown(f"• {v['type']} ({v['confidence']}%)<br>", unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    if st.button("✅", key=f"accept_{post['id']}", help="Approve (Override AI)"):
                        log_moderation_action(post['id'], "overridden", "Moderator", post['username'])
                        st.success("Override")
                with col_b:
                    if st.button("✏️", key=f"edit_{post['id']}", help="Edit Post"):
                        log_moderation_action(post['id'], "edited", "Moderator", post['username'])
                        st.info("Edited")
                with col_c:
                    if st.button("👤", key=f"profile_f_{post['id']}", help="View User Profile"):
                        st.session_state.viewing_user_profile = post['username']
                        st.rerun()
        else:
            st.success("✅ No violations detected")
    
    st.markdown("---")

st.markdown("---")
st.caption("eBay AI Moderation Dashboard v6.0 | Auto-Classification | Real-Time Analysis | Production Ready")
st.caption("💡 Posts from Forum App are automatically analyzed and classified in real-time")
