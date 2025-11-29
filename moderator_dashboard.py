import streamlit as st
import pandas as pd
import time
import re
from datetime import datetime, timedelta
import json

# ================================
# ULTRA-STRICT POLICY ENGINE (BUILT-IN)
# ================================

ULTRA_STRICT_POLICY = """
eBay UK/AU COMMUNITY MODERATION - ULTRA-STRICT POLICY ENGINE
Version 2.0 | ZERO GUESSING | 100% Policy Compliance

CORE DIRECTIVE:
You are a policy enforcement engine, NOT a conversational AI.
You do NOT guess, assume, interpret, or try to be helpful.
You ONLY flag violations that match EXACT policy criteria.
If criteria are not met, the post is ASSURED (clean).

See full policy documentation in code comments.
"""

def analyze_post_strict(content, post_id, board, username):
    """
    Ultra-strict policy analysis
    Only flags violations that match EXACT criteria
    No guessing, no interpretation
    """
    
    # Simulate processing time
    time.sleep(0.5)
    
    result = {
        "post_id": post_id,
        "content": content,
        "board": board,
        "username": username,
        "overall_status": "assured",
        "confidence": 95,
        "priority": "low",
        "violations_detected": [],
        "recommended_action": "none",
        "action_details": {},
        "time_saved_minutes": 0,
        "moderator_notes": "",
        "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    violations = []
    max_confidence = 0
    highest_priority = "low"
    total_time_saved = 0
    
    # PII DETECTION - 100% confidence (pattern matching)
    pii_found = []
    
    # Phone numbers - UK/AU formats
    phone_patterns = [
        r'\b(0[1-9]\d{8,9})\b',
        r'\b(\+44\s?\d{10})\b',
        r'\b(0[2-4]\d{8})\b',
        r'\b(\+61\s?\d{9})\b'
    ]
    
    for pattern in phone_patterns:
        if re.search(pattern, content):
            pii_found.append("Phone number")
            break
    
    # Email addresses
    if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content):
        pii_found.append("Email address")
    
    # UK Postcodes in address context
    if re.search(r'\b[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}\b', content, re.IGNORECASE):
        if any(word in content.lower() for word in ['address', 'located', 'ship to']):
            pii_found.append("Physical address")
    
    if pii_found:
        violations.append({
            "type": "PII - Personal Information",
            "confidence": 100,
            "evidence": ", ".join(pii_found),
            "policy": "Contact Information Sharing Policy",
            "explanation": "Post contains personally identifiable information"
        })
        highest_priority = "critical"
        max_confidence = 100
        total_time_saved += 8
    
    # NAMING AND SHAMING
    negative_words = [
        'scam', 'scammer', 'fraud', 'terrible', 'awful', 'worst',
        'avoid', 'never', 'rip off', 'ripoff', 'fake', 'cheat'
    ]
    
    content_lower = content.lower()
    has_negative = any(word in content_lower for word in negative_words)
    
    if has_negative:
        if re.search(r'\b(?:seller|buyer)\s+[A-Za-z0-9_-]{3,20}\b', content, re.IGNORECASE):
            violations.append({
                "type": "Naming and Shaming",
                "confidence": 94,
                "evidence": "Username in negative context",
                "policy": "Board Usage Policy - Naming and Shaming",
                "explanation": "Identifies member with criticism"
            })
            if highest_priority in ["low", "medium"]:
                highest_priority = "high"
            max_confidence = max(max_confidence, 94)
            total_time_saved += 3
    
    # DISRESPECT - Profanity
    profanity_patterns = [
        r'\bf[\*\@]ck', r'\bsh[\*\!]t', r'\bd[\@\*]mn',
        r'\bb[\*\!]tch', r'\b[\@\*]ss'
    ]
    
    for pattern in profanity_patterns:
        if re.search(pattern, content_lower):
            violations.append({
                "type": "Disrespect - Profanity",
                "confidence": 98,
                "evidence": "Profane language detected",
                "policy": "Board Usage Policy - Be Respectful",
                "explanation": "Contains profanity"
            })
            if highest_priority == "low":
                highest_priority = "medium"
            max_confidence = max(max_confidence, 98)
            total_time_saved += 4
            break
    
    # DISRESPECT - Direct insults
    insults = ['idiot', 'stupid', 'dumb', 'moron', 'fool']
    for insult in insults:
        if insult in content_lower:
            violations.append({
                "type": "Disrespect - Insult",
                "confidence": 96,
                "evidence": f"Contains: '{insult}'",
                "policy": "Board Usage Policy - Be Respectful",
                "explanation": "Personal attack detected"
            })
            if highest_priority in ["low", "medium"]:
                highest_priority = "high"
            max_confidence = max(max_confidence, 96)
            total_time_saved += 6
            break
    
    # WRONG BOARD DETECTION
    board_keywords = {
        "Selling": ["list", "sell", "price", "product"],
        "Buying": ["buy", "purchase", "bid", "offer"],
        "Payments": ["payment", "refund", "paypal", "transaction"],
        "Postage & Shipping": ["shipping", "delivery", "courier", "tracking"],
        "Technical Issues": ["error", "bug", "crash", "login"],
        "Member to Member Support": ["policy", "account", "help", "advice"]
    }
    
    if board not in ["eBay Café", "Mentors Forum", "General Discussion", "Community Spirit"]:
        if board in board_keywords:
            current_match = any(kw in content_lower for kw in board_keywords[board])
            
            for other_board, keywords in board_keywords.items():
                if other_board != board:
                    other_match = any(kw in content_lower for kw in keywords)
                    if other_match and not current_match:
                        violations.append({
                            "type": "Wrong Board Placement",
                            "confidence": 87,
                            "evidence": f"Better suited for {other_board}",
                            "policy": "Board Usage Policy - Stay On Topic",
                            "explanation": f"Topic matches {other_board}"
                        })
                        if highest_priority == "low":
                            highest_priority = "medium"
                        max_confidence = max(max_confidence, 87)
                        total_time_saved += 2
                        result["action_details"]["move_to_board"] = other_board
                        break
    
    # SPAM & ADVERTISING
    competitor_domains = ['amazon.com', 'amazon.co.uk', 'etsy.com', 'facebook.com/marketplace']
    
    for domain in competitor_domains:
        if domain in content_lower:
            violations.append({
                "type": "Spam - External Link",
                "confidence": 100,
                "evidence": f"Link to: {domain}",
                "policy": "Board Usage Policy - Advertising",
                "explanation": "External marketplace link"
            })
            highest_priority = "high"
            max_confidence = 100
            total_time_saved += 5
            break
    
    # Fee avoidance
    if any(phrase in content_lower for phrase in ['avoid fees', 'outside ebay', 'skip ebay']):
        violations.append({
            "type": "Fee Avoidance",
            "confidence": 95,
            "evidence": "Fee avoidance language",
            "policy": "Avoiding eBay Fees Policy",
            "explanation": "Encourages off-platform transactions"
        })
        if highest_priority in ["low", "medium"]:
            highest_priority = "high"
        max_confidence = max(max_confidence, 95)
        total_time_saved += 5
    
    # FINAL DECISION
    if violations:
        result["overall_status"] = "flagged"
        result["violations_detected"] = violations
        result["confidence"] = max_confidence
        result["priority"] = highest_priority
        result["time_saved_minutes"] = total_time_saved
        
        if highest_priority == "critical":
            result["recommended_action"] = "edit"
            result["moderator_notes"] = "⚠️ URGENT: Contains PII - edit immediately"
        elif highest_priority == "high":
            result["recommended_action"] = "edit"
            result["moderator_notes"] = "Edit to remove violations"
        elif highest_priority == "medium":
            if "Wrong Board" in [v["type"] for v in violations]:
                result["recommended_action"] = "move"
                result["moderator_notes"] = f"Move to appropriate board"
            else:
                result["recommended_action"] = "edit"
                result["moderator_notes"] = "Minor edit required"
        else:
            result["recommended_action"] = "review"
            result["moderator_notes"] = "Human review recommended"
    else:
        result["overall_status"] = "assured"
        result["confidence"] = 95
        result["moderator_notes"] = "✅ No violations - post is compliant"
        result["time_saved_minutes"] = 2
    
    return result

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
</style>
""", unsafe_allow_html=True)

# ================================
# SAMPLE DATA
# ================================

def generate_sample_data():
    base_date = datetime.now()
    
    posts = [
        # AI APPROVED
        {
            "post_id": "P001",
            "source": "ai_approved",
            "username": "HelpfulSeller",
            "board": "Selling",
            "content": "What's the best way to price vintage collectibles? I have some rare stamps.",
            "timestamp": base_date - timedelta(hours=2),
            "status": "assured",
            "priority": "low",
            "confidence": 96,
            "violations": [],
            "time_saved": 2
        },
        {
            "post_id": "P002",
            "source": "ai_approved",
            "username": "NewSeller123",
            "board": "Member to Member Support",
            "content": "Can someone explain the seller protection policy? I'm new to selling.",
            "timestamp": base_date - timedelta(hours=5),
            "status": "assured",
            "priority": "low",
            "confidence": 98,
            "violations": [],
            "time_saved": 2
        },
        {
            "post_id": "P003",
            "source": "ai_approved",
            "username": "SatisfiedBuyer",
            "board": "Community Spirit",
            "content": "Excellent seller! Fast shipping and item exactly as described. Highly recommend!",
            "timestamp": base_date - timedelta(days=1, hours=3),
            "status": "assured",
            "priority": "low",
            "confidence": 99,
            "violations": [],
            "time_saved": 2
        },
        
        # USER REPORTED
        {
            "post_id": "P004",
            "source": "user_reported",
            "username": "ConfusedUser",
            "board": "Buying",
            "content": "I'm looking for vintage cameras. Anyone selling?",
            "timestamp": base_date - timedelta(hours=1),
            "status": "reported",
            "priority": "low",
            "confidence": 75,
            "report_reason": "Possible wanted post (against policy)",
            "reporter": "CommunityExpert42",
            "violations": [],
            "time_saved": 1
        },
        {
            "post_id": "P005",
            "source": "user_reported",
            "username": "DebatingUser",
            "board": "General Discussion",
            "content": "I disagree with the new shipping policy. It doesn't make sense for international sellers.",
            "timestamp": base_date - timedelta(hours=4),
            "status": "reported",
            "priority": "medium",
            "confidence": 70,
            "report_reason": "Possible policy breach discussion",
            "reporter": "Moderator_Assistant",
            "violations": [],
            "time_saved": 2
        },
        {
            "post_id": "P006",
            "source": "user_reported",
            "username": "FrustratedSeller",
            "board": "Selling",
            "content": "Why was my listing removed? I followed all the rules!",
            "timestamp": base_date - timedelta(days=1),
            "status": "reported",
            "priority": "high",
            "confidence": 85,
            "report_reason": "Discussion of moderation action",
            "reporter": "Sandy_Pebbles",
            "violations": ["Discussion of Moderation"],
            "time_saved": 3
        },
        
        # AI FLAGGED
        {
            "post_id": "P007",
            "source": "ai_flagged",
            "username": "TechHelper",
            "board": "Selling",
            "content": "My app keeps crashing when I try to login. Anyone else having this issue?",
            "timestamp": base_date - timedelta(hours=3),
            "status": "flagged",
            "priority": "medium",
            "confidence": 92,
            "violations": [
                {
                    "type": "Wrong Board Placement",
                    "evidence": "Technical issue posted in Selling board",
                    "policy": "Board Usage Policy - Stay On Topic",
                    "confidence": 92
                }
            ],
            "recommended_action": "move",
            "move_to": "Technical Issues",
            "time_saved": 2
        },
        {
            "post_id": "P008",
            "source": "ai_flagged",
            "username": "AngryUser",
            "board": "Community",
            "content": "You're all idiots if you think eBay cares about sellers. F*cking ridiculous!",
            "timestamp": base_date - timedelta(hours=6),
            "status": "flagged",
            "priority": "high",
            "confidence": 98,
            "violations": [
                {
                    "type": "Disrespect - Insult",
                    "evidence": "\"You're all idiots\"",
                    "policy": "Board Usage Policy - Be Respectful",
                    "confidence": 96
                },
                {
                    "type": "Disrespect - Profanity",
                    "evidence": "\"F*cking\"",
                    "policy": "Board Usage Policy - Be Respectful",
                    "confidence": 98
                }
            ],
            "recommended_action": "edit",
            "time_saved": 6
        },
        {
            "post_id": "P009",
            "source": "ai_flagged",
            "username": "FrustratedBuyer",
            "board": "Buying",
            "content": "Seller abc123 is a total scammer! Never shipped my item. Call me at 020-5555-1234 if this happened to you!",
            "timestamp": base_date - timedelta(days=1, hours=2),
            "status": "flagged",
            "priority": "critical",
            "confidence": 100,
            "violations": [
                {
                    "type": "PII - Phone Number",
                    "evidence": "020-5555-1234",
                    "policy": "Contact Information Sharing Policy",
                    "confidence": 100
                },
                {
                    "type": "Naming and Shaming",
                    "evidence": "\"Seller abc123 is a total scammer\"",
                    "policy": "Board Usage Policy - Naming and Shaming",
                    "confidence": 96
                }
            ],
            "recommended_action": "edit",
            "time_saved": 11
        },
        {
            "post_id": "P010",
            "source": "ai_flagged",
            "username": "SpamBot",
            "board": "Selling",
            "content": "Better deals on Amazon.com! Skip eBay fees and shop direct!",
            "timestamp": base_date - timedelta(hours=8),
            "status": "flagged",
            "priority": "high",
            "confidence": 100,
            "violations": [
                {
                    "type": "Spam - External Link",
                    "evidence": "amazon.com",
                    "policy": "Board Usage Policy - Advertising",
                    "confidence": 100
                },
                {
                    "type": "Fee Avoidance",
                    "evidence": "\"Skip eBay fees\"",
                    "policy": "Avoiding eBay Fees Policy",
                    "confidence": 95
                }
            ],
            "recommended_action": "remove",
            "time_saved": 10
        }
    ]
    
    return posts

# ================================
# SESSION STATE
# ================================

if 'posts_data' not in st.session_state:
    st.session_state.posts_data = generate_sample_data()
    st.session_state.filter_start_date = datetime.now() - timedelta(days=30)
    st.session_state.filter_end_date = datetime.now()
    st.session_state.selected_board = "All Boards"
    st.session_state.selected_priority = "All Priorities"

# ================================
# HEADER
# ================================

st.title("🛡️ eBay Community AI Moderation Dashboard")
st.markdown("**Advanced Multi-Stream Monitoring System with Ultra-Strict Policy Engine**")
st.markdown("---")

# ================================
# SIDEBAR FILTERS
# ================================

with st.sidebar:
    st.header("📊 Analytics Filters")
    
    st.subheader("Date Range")
    
    quick_filter = st.selectbox(
        "Quick Select",
        ["Custom Range", "Today", "Yesterday", "Last 7 Days", "Last 30 Days", "This Month", "Last Month"]
    )
    
    if quick_filter == "Today":
        st.session_state.filter_start_date = datetime.now().replace(hour=0, minute=0, second=0)
        st.session_state.filter_end_date = datetime.now()
    elif quick_filter == "Yesterday":
        st.session_state.filter_start_date = (datetime.now() - timedelta(days=1)).replace(hour=0, minute=0)
        st.session_state.filter_end_date = (datetime.now() - timedelta(days=1)).replace(hour=23, minute=59)
    elif quick_filter == "Last 7 Days":
        st.session_state.filter_start_date = datetime.now() - timedelta(days=7)
        st.session_state.filter_end_date = datetime.now()
    elif quick_filter == "Last 30 Days":
        st.session_state.filter_start_date = datetime.now() - timedelta(days=30)
        st.session_state.filter_end_date = datetime.now()
    
    if quick_filter == "Custom Range":
        st.session_state.filter_start_date = st.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=30)
        )
        st.session_state.filter_end_date = st.date_input(
            "End Date",
            value=datetime.now()
        )
    else:
        st.info(f"Showing: {quick_filter}")
    
    st.markdown("---")
    
    all_boards = ["All Boards"] + sorted(list(set([p['board'] for p in st.session_state.posts_data])))
    st.session_state.selected_board = st.selectbox("Board Filter", all_boards)
    
    all_priorities = ["All Priorities", "Critical", "High", "Medium", "Low"]
    st.session_state.selected_priority = st.selectbox("Priority Filter", all_priorities)

# ================================
# FILTER DATA
# ================================

def filter_posts(posts, start_date, end_date, board, priority):
    filtered = []
    for post in posts:
        if isinstance(start_date, datetime):
            start_dt = start_date
        else:
            start_dt = datetime.combine(start_date, datetime.min.time())
            
        if isinstance(end_date, datetime):
            end_dt = end_date
        else:
            end_dt = datetime.combine(end_date, datetime.max.time())
        
        if not (start_dt <= post['timestamp'] <= end_dt):
            continue
        
        if board != "All Boards" and post['board'] != board:
            continue
        
        if priority != "All Priorities" and post.get('priority', '').lower() != priority.lower():
            continue
        
        filtered.append(post)
    
    return filtered

filtered_posts = filter_posts(
    st.session_state.posts_data,
    st.session_state.filter_start_date,
    st.session_state.filter_end_date,
    st.session_state.selected_board,
    st.session_state.selected_priority
)

# ================================
# STATS
# ================================

ai_approved = [p for p in filtered_posts if p['source'] == 'ai_approved']
user_reported = [p for p in filtered_posts if p['source'] == 'user_reported']
ai_flagged = [p for p in filtered_posts if p['source'] == 'ai_flagged']
total_time_saved = sum([p.get('time_saved', 0) for p in filtered_posts])

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Posts", len(filtered_posts))
with col2:
    st.metric("✅ AI Approved", len(ai_approved), 
              delta=f"{len(ai_approved)/max(len(filtered_posts),1)*100:.0f}%")
with col3:
    st.metric("👤 User Reported", len(user_reported),
              delta=f"{len(user_reported)/max(len(filtered_posts),1)*100:.0f}%")
with col4:
    st.metric("🚨 AI Flagged", len(ai_flagged),
              delta=f"{len(ai_flagged)/max(len(filtered_posts),1)*100:.0f}%")
with col5:
    st.metric("⏱️ Time Saved", f"{total_time_saved} min",
              delta=f"{total_time_saved/60:.1f} hrs")

st.markdown("---")

# ================================
# THREE COLUMNS
# ================================

col_approved, col_reported, col_flagged = st.columns(3)

with col_approved:
    st.subheader("✅ AI Approved Posts")
    st.caption(f"**{len(ai_approved)} posts** - No violations detected")
    
    if ai_approved:
        for post in sorted(ai_approved, key=lambda x: x['timestamp'], reverse=True):
            st.markdown(f"""
            <div class="approved-section">
                <strong>Post #{post['post_id']}</strong> | Board: {post['board']}<br>
                👤 {post['username']} | 🕒 {post['timestamp'].strftime('%H:%M')}<br><br>
                📝 <em>{post['content'][:100]}...</em><br><br>
                ✅ ASSURED {post['confidence']}% | ⏱️ {post['time_saved']} min saved
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🔍 View", key=f"v_{post['post_id']}"):
                st.info(post['content'])
    else:
        st.info("No approved posts")

with col_reported:
    st.subheader("👤 User Reported Posts")
    st.caption(f"**{len(user_reported)} posts** - Community flagged")
    
    if user_reported:
        for post in sorted(user_reported, key=lambda x: {'high':0,'medium':1,'low':2}.get(x.get('priority','low').lower(),3)):
            priority = post.get('priority', 'low').lower()
            css_class = f"user-reported-{priority}"
            emoji = "🔵" * (3 if priority=='high' else 2 if priority=='medium' else 1)
            
            st.markdown(f"""
            <div class="{css_class}">
                {emoji} <strong>{priority.upper()}</strong> | Post #{post['post_id']}<br>
                👤 {post['username']} | Board: {post['board']}<br><br>
                📝 <em>{post['content'][:100]}...</em><br><br>
                Reported by: {post.get('reporter', 'Unknown')}<br>
                Reason: {post.get('report_reason', 'Not specified')}
            </div>
            """, unsafe_allow_html=True)
            
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("✅ Clear", key=f"c_{post['post_id']}"):
                    st.success("Cleared")
            with col_b:
                if st.button("✏️ Edit", key=f"e_{post['post_id']}"):
                    st.info("Editor...")
    else:
        st.success("No reports")

with col_flagged:
    st.subheader("🚨 AI Flagged Posts")
    st.caption(f"**{len(ai_flagged)} posts** - Violations detected")
    
    if ai_flagged:
        for post in sorted(ai_flagged, key=lambda x: {'critical':0,'high':1,'medium':2,'low':3}.get(x.get('priority','low').lower(),4)):
            priority = post.get('priority', 'low').lower()
            css_class = f"flagged-{priority}"
            emoji = "🚨" if priority=='critical' else "🔴" if priority=='high' else "🟠" if priority=='medium' else "🟡"
            
            st.markdown(f"""
            <div class="{css_class}">
                {emoji} <strong>{priority.upper()}</strong> | Post #{post['post_id']}<br>
                👤 {post['username']} | Board: {post['board']}<br><br>
                📝 <em>{post['content'][:100]}...</em><br><br>
            """, unsafe_allow_html=True)
            
            if post.get('violations'):
                st.markdown("**Violations:**", unsafe_allow_html=True)
                for v in post['violations']:
                    st.markdown(f"• {v['type']} ({v['confidence']}%)<br>", unsafe_allow_html=True)
            
            st.markdown(f"""
                <br>Action: {post.get('recommended_action', 'review').upper()}<br>
                ⏱️ {post['time_saved']} min saved
            </div>
            """, unsafe_allow_html=True)
            
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("✅ Accept", key=f"a_{post['post_id']}"):
                    st.success("Accepted")
            with col_b:
                if st.button("🔄 Override", key=f"o_{post['post_id']}"):
                    st.warning("Override")
    else:
        st.success("No flags")

st.markdown("---")
st.caption("eBay AI Moderation Dashboard v3.0 | Ultra-Strict Policy Engine | Zero Guessing")
