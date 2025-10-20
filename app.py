import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import json
from collections import defaultdict
import plotly.express as px
import plotly.graph_objects as go

# Page configuration
st.set_page_config(
    page_title="LinkedIn Chat Viewer",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better card styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        background: #f5f7fa;
    }
    
    .contact-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 30px;
        border-radius: 20px;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        transition: all 0.3s ease;
        cursor: pointer;
        position: relative;
        overflow: hidden;
    }
    
    .contact-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 100%);
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .contact-card:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: 0 15px 40px rgba(102, 126, 234, 0.4);
    }
    
    .contact-card:hover::before {
        opacity: 1;
    }
    
    .contact-name {
        font-size: 1.8em;
        font-weight: 700;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .contact-stats {
        display: flex;
        gap: 20px;
        margin-top: 15px;
        flex-wrap: wrap;
    }
    
    .contact-stat-item {
        background: rgba(255,255,255,0.15);
        padding: 8px 15px;
        border-radius: 10px;
        font-size: 0.95em;
    }
    
    .message-received {
        background: white;
        padding: 25px;
        border-radius: 20px 20px 20px 5px;
        margin-bottom: 20px;
        border-left: 5px solid #667eea;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        transition: all 0.2s ease;
    }
    
    .message-received:hover {
        box-shadow: 0 6px 20px rgba(0,0,0,0.12);
        transform: translateX(5px);
    }
    
    .message-sent {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 25px;
        border-radius: 20px 20px 5px 20px;
        margin-bottom: 20px;
        color: white;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        margin-left: 60px;
        transition: all 0.2s ease;
    }
    
    .message-sent:hover {
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        transform: translateX(-5px);
    }
    
    .message-card-all {
        background: white;
        padding: 32px;
        border-radius: 20px;
        margin-bottom: 24px;
        box-shadow: 0 2px 16px rgba(0,0,0,0.08);
        border: 1px solid #e1e4e8;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .message-card-all::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        width: 5px;
        height: 100%;
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
        transform: scaleY(0);
        transition: transform 0.3s ease;
    }
    
    .message-card-all:hover {
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.15);
        transform: translateY(-3px);
        border-color: #667eea;
    }
    
    .message-card-all:hover::before {
        transform: scaleY(1);
    }
    
    .message-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 20px;
        padding-bottom: 18px;
        border-bottom: 2px solid #f5f7fa;
    }
    
    .message-sender {
        font-size: 1.25em;
        font-weight: 700;
        color: #1a1a2e;
        display: flex;
        align-items: center;
        gap: 12px;
        letter-spacing: -0.02em;
    }
    
    .message-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 6px 14px;
        border-radius: 14px;
        font-size: 0.7em;
        font-weight: 600;
        letter-spacing: 0.3px;
        text-transform: uppercase;
    }
    
    .message-timestamp {
        color: #6b7280;
        font-size: 0.95em;
        display: flex;
        align-items: center;
        gap: 6px;
        font-weight: 500;
    }
    
    .message-content {
        color: #2d3748;
        font-size: 1.08em;
        line-height: 1.75;
        margin: 20px 0;
        white-space: pre-wrap;
        word-wrap: break-word;
        font-weight: 400;
    }
    
    .message-footer {
        display: flex;
        flex-wrap: wrap;
        gap: 20px;
        margin-top: 20px;
        padding-top: 18px;
        border-top: 2px solid #f5f7fa;
        font-size: 0.92em;
        color: #6b7280;
        align-items: center;
    }
    
    .linkedin-link {
        color: #667eea;
        text-decoration: none;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 5px;
        transition: all 0.2s ease;
    }
    
    .linkedin-link:hover {
        color: #764ba2;
        gap: 8px;
    }
    
    .stat-box {
        background: white;
        padding: 30px;
        border-radius: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        text-align: center;
        border-top: 5px solid #667eea;
        transition: all 0.3s ease;
    }
    
    .stat-box:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.12);
    }
    
    .stat-number {
        font-size: 3em;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .stat-label {
        color: #5f6368;
        font-size: 1em;
        margin-top: 8px;
        font-weight: 500;
        letter-spacing: 0.5px;
    }
    
    .contact-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 40px;
        border-radius: 20px;
        color: white;
        margin-bottom: 30px;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }
    
    .message-time {
        font-size: 0.85em;
        opacity: 0.8;
    }
    
    .linkedin-badge {
        background: rgba(255,255,255,0.2);
        padding: 8px 16px;
        border-radius: 25px;
        display: inline-block;
        margin-top: 15px;
        font-size: 0.95em;
        transition: all 0.3s ease;
    }
    
    .linkedin-badge:hover {
        background: rgba(255,255,255,0.3);
        transform: scale(1.05);
    }
    
    .shared-content-badge {
        background: #f0f2f5;
        color: #5f6368;
        padding: 8px 14px;
        border-radius: 8px;
        font-size: 0.85em;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        margin-top: 10px;
    }
    
    .profile-badge {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 1.5em;
        font-weight: 700;
        margin-right: 15px;
    }
    
    .conversation-date-divider {
        text-align: center;
        color: #5f6368;
        font-size: 0.9em;
        margin: 30px 0;
        position: relative;
    }
    
    .conversation-date-divider::before,
    .conversation-date-divider::after {
        content: '';
        position: absolute;
        top: 50%;
        width: 40%;
        height: 1px;
        background: #e8eaed;
    }
    
    .conversation-date-divider::before {
        left: 0;
    }
    
    .conversation-date-divider::after {
        right: 0;
    }
    
    .no-data-message {
        text-align: center;
        padding: 60px;
        color: #5f6368;
        font-size: 1.2em;
    }
</style>
""", unsafe_allow_html=True)

# Google Sheets Configuration
SPREADSHEET_ID = "1klm60YFXSoV510S4igv5LfREXeykDhNA5Ygq7HNFN0I"
SHEET_NAME = "linkedin_chat_history_advanced 2"

# My profile information
MY_PROFILE = {
    "name": "Donmenico Hudson",
    "url": "https://www.linkedin.com/in/donmenicohudson/"
}

@st.cache_resource
def init_google_sheets(credentials_json):
    """Initialize Google Sheets connection with service account"""
    try:
        credentials_dict = json.loads(credentials_json)
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets.readonly',
            'https://www.googleapis.com/auth/drive.readonly'
        ]
        credentials = Credentials.from_service_account_info(
            credentials_dict, 
            scopes=scopes
        )
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.error(f"Error initializing Google Sheets: {str(e)}")
        return None

@st.cache_data(ttl=60)
def load_data(_client):
    """Load data from Google Sheets with caching"""
    try:
        spreadsheet = _client.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet(SHEET_NAME)
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

def is_me(sender_name, sender_url):
    """Check if the sender is me"""
    if not sender_name or not isinstance(sender_name, str):
        return False
    return (
        MY_PROFILE["name"].lower() in sender_name.lower() or
        (sender_url and MY_PROFILE["url"].lower() in str(sender_url).lower())
    )

def get_initials(name):
    """Get initials from name"""
    if not name:
        return "?"
    parts = name.split()
    if len(parts) >= 2:
        return f"{parts[0][0]}{parts[1][0]}".upper()
    return name[0].upper()

def get_contact_info(df):
    """Extract unique contacts (excluding myself)"""
    contacts = {}
    
    for idx, row in df.iterrows():
        sender_name = row.get('sender_name', '')
        sender_url = row.get('sender_linkedin_url', '')
        lead_name = row.get('lead_name', '')
        lead_url = row.get('lead_linkedin_url', '')
        
        # Skip if this is me
        if is_me(sender_name, sender_url):
            continue
        
        # Determine contact info
        contact_url = sender_url if sender_url else lead_url
        contact_name = sender_name if sender_name else lead_name
        
        if contact_url and contact_url not in contacts:
            contacts[contact_url] = {
                'name': contact_name,
                'url': contact_url,
                'messages': [],
                'last_contact': None,
                'received_count': 0,
                'sent_count': 0
            }
    
    # Collect all messages per contact
    for idx, row in df.iterrows():
        sender_name = row.get('sender_name', '')
        sender_url = row.get('sender_linkedin_url', '')
        lead_url = row.get('lead_linkedin_url', '')
        
        # Find which contact this message belongs to
        contact_url = None
        if is_me(sender_name, sender_url):
            # This is my message, find the recipient
            contact_url = lead_url
            if contact_url in contacts:
                contacts[contact_url]['sent_count'] += 1
        else:
            # This is their message
            contact_url = sender_url if sender_url else lead_url
            if contact_url in contacts:
                contacts[contact_url]['received_count'] += 1
        
        if contact_url in contacts:
            contacts[contact_url]['messages'].append(row)
            contacts[contact_url]['last_contact'] = f"{row.get('date', '')} {row.get('time', '')}"
    
    return contacts

def create_message_chart(df):
    """Create a message activity chart"""
    if df.empty or 'date' not in df.columns:
        return None
    
    # Count messages by date
    message_counts = df['date'].value_counts().sort_index()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=message_counts.index,
        y=message_counts.values,
        mode='lines+markers',
        line=dict(color='#667eea', width=3),
        marker=dict(size=8, color='#764ba2'),
        fill='tozeroy',
        fillcolor='rgba(102, 126, 234, 0.2)'
    ))
    
    fig.update_layout(
        title="Message Activity Over Time",
        xaxis_title="Date",
        yaxis_title="Messages",
        template="plotly_white",
        height=300,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig

def main():
    st.title("💬 LinkedIn Chat History Analytics")
    st.markdown("**Professional conversation management and insights**")
    st.markdown("---")
    
    # Service Account Authentication
    with st.sidebar:
        st.header("🔐 Authentication")
        
        uploaded_file = st.file_uploader(
            "Upload Service Account JSON",
            type=['json'],
            help="Upload your Google Service Account credentials JSON file"
        )
        
        if uploaded_file is not None:
            credentials_json = uploaded_file.read().decode('utf-8')
            client = init_google_sheets(credentials_json)
            
            if client:
                st.success("✅ Connected to Google Sheets!")
                
                # My Profile Info
                st.markdown("---")
                st.markdown("### 👤 Your Profile")
                st.markdown(f"""
                **{MY_PROFILE['name']}**  
                [View LinkedIn Profile →]({MY_PROFILE['url']})
                """)
                
                st.markdown("---")
                
                # Refresh button
                if st.button("🔄 Refresh Data", use_container_width=True):
                    st.cache_data.clear()
                    st.rerun()
                
                st.markdown("---")
                st.markdown("### 📊 Quick Stats")
        else:
            st.warning("⚠️ Please upload your service account JSON file to continue")
            st.info("""
            **Setup Instructions:**
            
            1. **Google Cloud Console**
               - Go to console.cloud.google.com
               - Create new project
            
            2. **Enable APIs**
               - Google Sheets API
               - Google Drive API
            
            3. **Service Account**
               - Create service account
               - Download JSON key
            
            4. **Share Spreadsheet**
               - Share with service account email
               - Grant "Viewer" access
            
            5. **Upload JSON**
               - Use the uploader above
            """)
            return
    
    # Load data
    df = load_data(client)
    
    if df.empty:
        st.warning("No data found. Please check your spreadsheet and permissions.")
        return
    
    # Get contact information
    contacts = get_contact_info(df)
    
    # Display Statistics
    st.markdown("### 📈 Overview Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-number">{len(df)}</div>
            <div class="stat-label">Total Messages</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-number">{len(contacts)}</div>
            <div class="stat-label">Active Contacts</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        my_messages = sum(1 for _, row in df.iterrows() if is_me(row.get('sender_name', ''), row.get('sender_linkedin_url', '')))
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-number">{my_messages}</div>
            <div class="stat-label">Sent by You</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        received_messages = len(df) - my_messages
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-number">{received_messages}</div>
            <div class="stat-label">Received</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Message activity chart
    with st.expander("📊 View Message Activity Chart", expanded=False):
        chart = create_message_chart(df)
        if chart:
            st.plotly_chart(chart, use_container_width=True)
    
    st.markdown("---")
    
    # View Selection with better styling
    st.markdown("### 🔍 Select View Mode")
    view_mode = st.radio(
        "",
        ["📇 All Contacts", "👤 Contact Conversation", "📝 All Messages"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    if view_mode == "📇 All Contacts":
        show_all_contacts(contacts)
    elif view_mode == "👤 Contact Conversation":
        show_individual_contact(contacts)
    else:
        show_all_messages(df)

def show_all_contacts(contacts):
    """Display all contacts in card format"""
    st.header("📇 All Contacts")
    st.markdown("*Click on any contact card to view their profile*")
    st.markdown("")
    
    if not contacts:
        st.markdown('<div class="no-data-message">📭 No contacts found.</div>', unsafe_allow_html=True)
        return
    
    # Search and sort filters
    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input("🔍 Search contacts by name", "", key="contact_search")
    with col2:
        sort_by = st.selectbox("Sort by", ["Name", "Messages", "Recent"])
    
    # Filter contacts
    filtered_contacts = {
        url: info for url, info in contacts.items()
        if not search or search.lower() in info['name'].lower()
    }
    
    # Sort contacts
    if sort_by == "Messages":
        filtered_contacts = dict(sorted(
            filtered_contacts.items(),
            key=lambda x: len(x[1]['messages']),
            reverse=True
        ))
    elif sort_by == "Name":
        filtered_contacts = dict(sorted(
            filtered_contacts.items(),
            key=lambda x: x[1]['name']
        ))
    
    st.markdown(f"**Showing {len(filtered_contacts)} contacts**")
    st.markdown("")
    
    # Display in columns
    cols = st.columns(2)
    
    for idx, (url, info) in enumerate(filtered_contacts.items()):
        col = cols[idx % 2]
        
        message_count = len(info['messages'])
        initials = get_initials(info['name'])
        
        with col:
            st.markdown(f"""
            <div class="contact-card">
                <div style="display: flex; align-items: center; margin-bottom: 20px;">
                    <div class="profile-badge">{initials}</div>
                    <div>
                        <div class="contact-name">{info['name']}</div>
                    </div>
                </div>
                <div class="contact-stats">
                    <div class="contact-stat-item">
                        💬 <strong>{message_count}</strong> messages
                    </div>
                    <div class="contact-stat-item">
                        📤 <strong>{info['sent_count']}</strong> sent
                    </div>
                    <div class="contact-stat-item">
                        📥 <strong>{info['received_count']}</strong> received
                    </div>
                </div>
                <p style="margin-top: 15px; opacity: 0.9;">
                    <strong>Last Contact:</strong> {info['last_contact']}
                </p>
                <div class="linkedin-badge">
                    <a href="{url}" target="_blank" style="color: white; text-decoration: none;">
                        🔗 View LinkedIn Profile →
                    </a>
                </div>
            </div>
            """, unsafe_allow_html=True)

def show_individual_contact(contacts):
    """Display messages for a specific contact"""
    st.header("👤 Contact Conversation")
    st.markdown("*View detailed conversation history with a specific contact*")
    st.markdown("")
    
    if not contacts:
        st.markdown('<div class="no-data-message">📭 No contacts found.</div>', unsafe_allow_html=True)
        return
    
    # Contact selection
    contact_options = {info['name']: url for url, info in contacts.items()}
    
    selected_name = st.selectbox(
        "Select a contact to view conversation",
        options=list(contact_options.keys())
    )
    
    selected_url = contact_options[selected_name]
    contact_info = contacts[selected_url]
    
    # Display contact header
    message_count = len(contact_info['messages'])
    initials = get_initials(contact_info['name'])
    
    st.markdown(f"""
    <div class="contact-header">
        <div style="display: flex; align-items: center; margin-bottom: 20px;">
            <div class="profile-badge" style="width: 70px; height: 70px; font-size: 2em;">{initials}</div>
            <div>
                <h2 style="margin: 0;">{contact_info['name']}</h2>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">LinkedIn Professional</p>
            </div>
        </div>
        <div style="display: flex; gap: 20px; flex-wrap: wrap;">
            <div style="background: rgba(255,255,255,0.2); padding: 12px 20px; border-radius: 12px;">
                💬 <strong>{message_count}</strong> total messages
            </div>
            <div style="background: rgba(255,255,255,0.2); padding: 12px 20px; border-radius: 12px;">
                📤 <strong>{contact_info['sent_count']}</strong> sent
            </div>
            <div style="background: rgba(255,255,255,0.2); padding: 12px 20px; border-radius: 12px;">
                📥 <strong>{contact_info['received_count']}</strong> received
            </div>
        </div>
        <div class="linkedin-badge">
            <a href="{contact_info['url']}" target="_blank" style="color: white; text-decoration: none;">
                🔗 View LinkedIn Profile →
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 💬 Conversation History")
    
    # Sort messages by date and time
    messages = sorted(
        contact_info['messages'],
        key=lambda x: (x.get('date', ''), x.get('time', ''))
    )
    
    current_date = None
    
    # Display messages
    for msg in messages:
        sender_name = msg.get('sender_name', '')
        sender_url = msg.get('sender_linkedin_url', '')
        message = msg.get('message', '')
        date = msg.get('date', '')
        time = msg.get('time', '')
        shared_content = msg.get('shared_content', '')
        
        # Date divider
        if date and date != current_date:
            st.markdown(f'<div class="conversation-date-divider">{date}</div>', unsafe_allow_html=True)
            current_date = date
        
        is_my_message = is_me(sender_name, sender_url)
        
        if is_my_message:
            # My message (right-aligned, colored)
            st.markdown(f"""
            <div class="message-sent">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <strong>You</strong>
                    <span class="message-time">🕐 {time}</span>
                </div>
                <p style="margin: 0; line-height: 1.6;">{message}</p>
                {f'<div class="shared-content-badge" style="background: rgba(255,255,255,0.2); color: white;">📎 {shared_content}</div>' if shared_content else ''}
            </div>
            """, unsafe_allow_html=True)
        else:
            # Their message (left-aligned)
            st.markdown(f"""
            <div class="message-received">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <strong style="color: #667eea;">{sender_name}</strong>
                    <span class="message-time">🕐 {time}</span>
                </div>
                <p style="margin: 0; color: #333; line-height: 1.6;">{message}</p>
                {f'<div class="shared-content-badge">📎 {shared_content}</div>' if shared_content else ''}
            </div>
            """, unsafe_allow_html=True)

def show_all_messages(df):
    """Display all messages in bulk card format with white background"""
    st.header("📝 All Messages")
    st.markdown("*Complete message archive with advanced filtering*")
    st.markdown("")
    
    # Search and filter controls
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search = st.text_input("🔍 Search in messages", "", key="message_search", placeholder="Type to search...")
    with col2:
        show_only = st.selectbox("Filter by", ["All Messages", "Sent by Me", "Received", "With Attachments"])
    with col3:
        sort_order = st.selectbox("Sort", ["Newest First", "Oldest First"])
    
    # Filter messages
    filtered_df = df.copy()
    
    if search:
        filtered_df = filtered_df[
            filtered_df['message'].str.contains(search, case=False, na=False) |
            filtered_df['sender_name'].str.contains(search, case=False, na=False)
        ]
    
    if show_only == "Sent by Me":
        filtered_df = filtered_df[filtered_df.apply(lambda row: is_me(row.get('sender_name', ''), row.get('sender_linkedin_url', '')), axis=1)]
    elif show_only == "Received":
        filtered_df = filtered_df[filtered_df.apply(lambda row: not is_me(row.get('sender_name', ''), row.get('sender_linkedin_url', '')), axis=1)]
    elif show_only == "With Attachments":
        filtered_df = filtered_df[filtered_df['shared_content'].notna() & (filtered_df['shared_content'] != '')]
    
    # Sort messages
    if 'date' in filtered_df.columns and 'time' in filtered_df.columns:
        filtered_df = filtered_df.sort_values(by=['date', 'time'], ascending=(sort_order == "Oldest First"))
    
    st.markdown(f"**Showing {len(filtered_df)} messages**")
    st.markdown("")
    
    if filtered_df.empty:
        st.markdown('<div class="no-data-message">📭 No messages found matching your filters.</div>', unsafe_allow_html=True)
        return
    
    # Display messages
    for idx, row in filtered_df.iterrows():
        sender_name = row.get('sender_name', 'Unknown')
        sender_url = row.get('sender_linkedin_url', '')
        lead_name = row.get('lead_name', '')
        lead_url = row.get('lead_linkedin_url', '')
        message = row.get('message', '')
        date = row.get('date', '')
        time = row.get('time', '')
        shared_content = row.get('shared_content', '')
        
        # Determine if I sent this message
        is_my_message = is_me(sender_name, sender_url)
        
        # Determine the other person (contact)
        if is_my_message:
            contact_name = lead_name
            contact_url = lead_url
            badge_text = "You"
            badge_style = "background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);"
        else:
            contact_name = sender_name
            contact_url = sender_url
            badge_text = "Received"
            badge_style = "background: #10b981;"
        
        st.markdown(f"""
        <div class="message-card-all">
            <div class="message-header">
                <div>
                    <div class="message-sender">
                        {sender_name}
                        <span class="message-badge" style="{badge_style}">{badge_text}</span>
                    </div>
                </div>
                <div class="message-timestamp">
                    🗓️ {date} • 🕐 {time}
                </div>
            </div>
            
            <div class="message-content">
                {message}
            </div>
            
            <div class="message-footer">
                <span>
                    <strong>Contact:</strong> {contact_name if contact_name else 'N/A'}
                </span>
                {f'<span><strong>📎 Attachment:</strong> {shared_content}</span>' if shared_content else ''}
                {f'<a href="{contact_url}" target="_blank" class="linkedin-link">🔗 View LinkedIn Profile →</a>' if contact_url else ''}
            </div>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
