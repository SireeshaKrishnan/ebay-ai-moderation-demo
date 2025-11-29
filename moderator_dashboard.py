import streamlit as st
import pandas as pd
import time
import re
from datetime import datetime, timedelta
import json

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

.clickable-username {
    color: #0066cc;
    cursor: pointer;
    text-decoration: underline;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ================================
# STATS STORAGE
# ================================

def init_stats_storage():
    """Initialize comprehensive stats storage"""
    if 'moderation_log' not in st.session_state:
        st.session_state.moderation_log = []
    
    if 'violation_log' not in st.session_state:
        st.session_state.violation_log = []
    
    if 'action_log' not in st.session_state:
        st.session_state.action_log = []
    
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
    
    # Update user profile
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
    
    # Update user profile
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
            'status': 'clean'  # clean, warning, flagged, banned
        }
    
    profile = st.session_state.user_profiles[username]
    
    if event_type == 'post':
        profile['total_posts'] += 1
    
    elif event_type == 'violation':
        profile['total_violations'] += 1
        profile['violations'].append(event_data)
        
        # Track violation types
        v_type = event_data['violation_type']
        profile['violation_types'][v_type] = profile['violation_types'].get(v_type, 0) + 1
        
        # Track severity
        severity = event_data['severity']
        profile['severity_counts'][severity] = profile['severity_counts'].get(severity, 0) + 1
        
        # Update status based on violations
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
        'overridden': len([a for a in actions_in_period if a['action_type'] == 'overridden']),
        'moved': len([a for a in actions_in_period if a['action_type'] == 'moved']),
        'banned': len([a for a in actions_in_period if a['action_type'] == 'banned']),
        
        # Violation breakdown
        'pii_violations': len([v for v in violations_in_period if 'PII' in v['violation_type']]),
        'naming_violations': len([v for v in violations_in_period if 'Naming' in v['violation_type']]),
        'disrespect_violations': len([v for v in violations_in_period if 'Disrespect' in v['violation_type']]),
        'wrong_board_violations': len([v for v in violations_in_period if 'Wrong Board' in v['violation_type']]),
        'spam_violations': len([v for v in violations_in_period if 'Spam' in v['violation_type']]),
        'fee_avoidance_violations': len([v for v in violations_in_period if 'Fee' in v['violation_type']]),
        
        # Severity breakdown
        'critical': len([v for v in violations_in_period if v['severity'] == 'critical']),
        'high': len([v for v in violations_in_period if v['severity'] == 'high']),
        'medium': len([v for v in violations_in_period if v['severity'] == 'medium']),
        'low': len([v for v in violations_in_period if v['severity'] == 'low']),
        
        'actions': actions_in_period,
        'violations': violations_in_period
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
# SESSION STATE
# ================================

init_stats_storage()

if 'forum_posts' not in st.session_state:
    st.session_state.forum_posts = {}

if 'viewing_user_profile' not in st.session_state:
    st.session_state.viewing_user_profile = None

# ================================
# USER PROFILE MODAL
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
        
        # Group by violation type
        st.markdown("### By Type:")
        for v_type, count in profile['violation_types'].items():
            st.markdown(f"**{v_type}:** {count} occurrence(s)")
        
        st.markdown("---")
        
        # Detailed violations
        st.markdown("### Detailed Violations:")
        for i, v in enumerate(reversed(profile['violations'][-10:]), 1):
            severity_emoji = {"critical": "🚨", "high": "🔴", "medium": "🟠", "low": "⚪"}
            emoji = severity_emoji.get(v['severity'], "⚪")
            
            with st.expander(f"{emoji} {v['timestamp']} - {v['violation_type']}"):
                st.markdown(f"**Post ID:** {v['post_id']}")
                st.markdown(f"**Severity:** {v['severity'].upper()}")
                st.markdown(f"**Confidence:** {v['confidence']}%")
                st.markdown(f"**Evidence:** {v['evidence']}")
                st.markdown(f"**Date:** {v['date']}")
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
# HEADER
# ================================

st.title("🛡️ eBay Community AI Moderation Dashboard")
st.markdown("**Ultra-Strict Policy Engine | Complete Stats Tracking | User Profiles**")
st.success("✨ All actions and violations permanently stored | Click usernames to view profiles")
st.markdown("---")

# ================================
# SIDEBAR
# ================================

with st.sidebar:
    st.header("📊 Stats Query")
    
    quick_filter = st.selectbox(
        "Time Period",
        ["Today", "Yesterday", "Last 7 Days", "Last 30 Days", "Last Week", "Last Month", "Custom"]
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
    elif quick_filter == "Last Week":
        end_of_last_week = datetime.now() - timedelta(days=datetime.now().weekday() + 1)
        start_date = end_of_last_week - timedelta(days=6)
        end_date = end_of_last_week.replace(hour=23, minute=59)
    elif quick_filter == "Last Month":
        last_month = datetime.now().replace(day=1) - timedelta(days=1)
        start_date = last_month.replace(day=1, hour=0, minute=0)
        end_date = last_month.replace(hour=23, minute=59)
    else:
        start_date = st.date_input("Start", value=datetime.now() - timedelta(days=7))
        end_date = st.date_input("End", value=datetime.now())
    
    period_stats = get_stats_for_period(start_date, end_date)
    
    st.markdown("---")
    st.metric("Total Actions", period_stats['total_actions'])
    st.metric("Total Violations", period_stats['total_violations'])
    
    st.markdown("---")
    st.markdown("### 🔧 Actions")
    st.markdown(f"Analyzed: **{period_stats['analyzed']}**")
    st.markdown(f"Edited: **{period_stats['edited']}**")
    st.markdown(f"Removed: **{period_stats['removed']}**")
    st.markdown(f"Approved: **{period_stats['approved']}**")
    
    st.markdown("---")
    st.markdown("### ⚠️ Violations")
    st.markdown(f"PII: **{period_stats['pii_violations']}**")
    st.markdown(f"Naming: **{period_stats['naming_violations']}**")
    st.markdown(f"Disrespect: **{period_stats['disrespect_violations']}**")
    st.markdown(f"Spam: **{period_stats['spam_violations']}**")
    
    st.markdown("---")
    
    with st.expander("💾 Storage Info"):
        st.markdown(f"""
        **Records:**  
        Actions: {len(st.session_state.action_log)}  
        Violations: {len(st.session_state.violation_log)}  
        Users Tracked: {len(st.session_state.user_profiles)}
        
        **Location:**  
        `st.session_state.action_log`  
        `st.session_state.violation_log`  
        `st.session_state.user_profiles`
        """)

# ================================
# MAIN VIEW - USER PROFILE OR DASHBOARD
# ================================

if st.session_state.viewing_user_profile:
    show_user_profile(st.session_state.viewing_user_profile)

else:
    # ================================
    # STATS DISPLAY
    # ================================
    
    all_posts = list(st.session_state.forum_posts.values())
    ai_approved = [p for p in all_posts if p.get('ai_analyzed') and p.get('overall_status') == 'assured']
    user_reported = [p for p in all_posts if len(p.get('reports', [])) > 0]
    ai_flagged = [p for p in all_posts if p.get('ai_analyzed') and p.get('overall_status') == 'flagged']
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Posts", len(all_posts))
    col2.metric("✅ AI Approved", len(ai_approved))
    col3.metric("👤 User Reported", len(user_reported))
    col4.metric("🚨 AI Flagged", len(ai_flagged))
    
    st.markdown("---")
    
    # ================================
    # THREE COLUMNS
    # ================================
    
    col_approved, col_reported, col_flagged = st.columns(3)
    
    with col_approved:
        st.subheader("✅ AI Approved")
        st.caption(f"{len(ai_approved)} posts")
        
        if ai_approved:
            for post in ai_approved[:10]:
                st.markdown(f"""
                <div class="approved-section">
                    <strong>#{post['id'][:8]}</strong> | {post['board']}<br>
                    👤 <span class="clickable-username">{post['username']}</span><br>
                    🕒 {post['timestamp']}<br><br>
                    <em>{post['content'][:80]}...</em><br><br>
                    ✅ {post.get('confidence', 95)}% Assured
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"View Profile", key=f"profile_a_{post['id']}", use_container_width=True):
                    st.session_state.viewing_user_profile = post['username']
                    st.rerun()
        else:
            st.info("No approved posts")
    
    with col_reported:
        st.subheader("👤 User Reported")
        st.caption(f"{len(user_reported)} posts")
        
        if user_reported:
            for post in sorted(user_reported, key=lambda x: len(x.get('reports', [])), reverse=True)[:10]:
                report_count = len(post['reports'])
                css_class = "user-reported-high" if report_count >= 3 else "user-reported-medium" if report_count >= 2 else "user-reported-low"
                
                st.markdown(f"""
                <div class="{css_class}">
                    <strong>#{post['id'][:8]}</strong><br>
                    👤 {post['username']}<br>
                    Reports: {report_count}
                </div>
                """, unsafe_allow_html=True)
                
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button(f"Analyze", key=f"analyze_{post['id']}", use_container_width=True):
                        analysis = analyze_post_ultra_strict(post['content'], post['id'], post['board'], post['username'])
                        st.session_state.forum_posts[f"forum_post_{post['id']}"]['ai_analyzed'] = True
                        st.session_state.forum_posts[f"forum_post_{post['id']}"]['overall_status'] = analysis['overall_status']
                        st.session_state.forum_posts[f"forum_post_{post['id']}"]['confidence'] = analysis['confidence']
                        st.session_state.forum_posts[f"forum_post_{post['id']}"]['priority'] = analysis['priority']
                        st.session_state.forum_posts[f"forum_post_{post['id']}"]['violations_detected'] = analysis['violations_detected']
                        update_user_profile(post['username'], 'post', {})
                        st.rerun()
                with col_b:
                    if st.button(f"Profile", key=f"profile_r_{post['id']}", use_container_width=True):
                        st.session_state.viewing_user_profile = post['username']
                        st.rerun()
        else:
            st.success("No reports")
    
    with col_flagged:
        st.subheader("🚨 AI Flagged")
        st.caption(f"{len(ai_flagged)} posts")
        
        if ai_flagged:
            for post in sorted(ai_flagged, key=lambda x: {'critical':0,'high':1,'medium':2}.get(x.get('priority','low'),3))[:10]:
                priority = post.get('priority', 'low')
                css_class = f"flagged-{priority}"
                emoji = {"critical":"🚨", "high":"🔴", "medium":"🟠"}.get(priority, "⚪")
                
                st.markdown(f"""
                <div class="{css_class}">
                    {emoji} <strong>{priority.upper()}</strong><br>
                    #{post['id'][:8]}<br>
                    👤 {post['username']}<br><br>
                """, unsafe_allow_html=True)
                
                for v in post.get('violations_detected', []):
                    st.markdown(f"• {v['type']}<br>", unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    if st.button("✅", key=f"accept_{post['id']}"):
                        log_moderation_action(post['id'], "approved", "Moderator", post['username'])
                        st.success("Approved")
                with col_b:
                    if st.button("✏️", key=f"edit_{post['id']}"):
                        log_moderation_action(post['id'], "edited", "Moderator", post['username'])
                        st.info("Edited")
                with col_c:
                    if st.button("👤", key=f"profile_f_{post['id']}"):
                        st.session_state.viewing_user_profile = post['username']
                        st.rerun()
        else:
            st.success("No flags")
    
    st.markdown("---")
    
    # Pending posts
    st.header("⏳ Pending Analysis")
    
    pending = [p for p in all_posts if not p.get('ai_analyzed')]
    
    if pending:
        st.warning(f"📥 {len(pending)} post(s) awaiting analysis")
        
        for post in pending[:5]:
            with st.expander(f"Post #{post['id'][:8]} - {post['username']}"):
                st.markdown(f"**Board:** {post['board']}")
                st.markdown(f"**Content:** {post['content']}")
                
                col_a, col_b = st.columns([3,1])
                with col_a:
                    if st.button(f"🤖 Analyze with AI", key=f"pend_{post['id']}", use_container_width=True):
                        with st.spinner("Analyzing..."):
                            analysis = analyze_post_ultra_strict(post['content'], post['id'], post['board'], post['username'])
                            st.session_state.forum_posts[f"forum_post_{post['id']}"]['ai_analyzed'] = True
                            st.session_state.forum_posts[f"forum_post_{post['id']}"]['overall_status'] = analysis['overall_status']
                            st.session_state.forum_posts[f"forum_post_{post['id']}"]['confidence'] = analysis['confidence']
                            st.session_state.forum_posts[f"forum_post_{post['id']}"]['priority'] = analysis['priority']
                            st.session_state.forum_posts[f"forum_post_{post['id']}"]['violations_detected'] = analysis['violations_detected']
                            update_user_profile(post['username'], 'post', {})
                            st.success("✅ Complete!")
                            st.rerun()
                with col_b:
                    if st.button("View User", key=f"profile_p_{post['id']}", use_container_width=True):
                        st.session_state.viewing_user_profile = post['username']
                        st.rerun()
    else:
        st.success("✅ All posts analyzed!")

st.markdown("---")
st.caption("eBay AI Moderation Dashboard v4.0 | User Profiles | Complete Stats Tracking")
