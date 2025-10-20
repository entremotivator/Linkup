import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import json
from collections import defaultdict

# Page configuration
st.set_page_config(
    page_title="LinkedIn Chat Viewer",
    page_icon="💬",
    layout="wide"
)

# Custom CSS for better card styling
st.markdown("""
<style>
    .contact-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 25px;
        border-radius: 15px;
        color: white;
        margin-bottom: 15px;
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        transition: transform 0.2s;
        cursor: pointer;
    }
    .contact-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    }
    .message-received {
        background: #f8f9fa;
        padding: 18px;
        border-radius: 15px 15px 15px 5px;
        margin-bottom: 15px;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08);
    }
    .message-sent {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 18px;
        border-radius: 15px 15px 5px 15px;
        margin-bottom: 15px;
        color: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08);
        margin-left: 40px;
    }
    .stat-box {
        background: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        text-align: center;
        border-top: 4px solid #667eea;
    }
    .stat-number {
        font-size: 2.5em;
        font-weight: bold;
        color: #667eea;
    }
    .stat-label {
        color: #666;
        font-size: 0.9em;
        margin-top: 5px;
    }
    .contact-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 30px;
        border-radius: 15px;
        color: white;
        margin-bottom: 25px;
    }
    .message-time {
        font-size: 0.85em;
        opacity: 0.7;
    }
    .linkedin-badge {
        background: rgba(255,255,255,0.2);
        padding: 5px 12px;
        border-radius: 20px;
        display: inline-block;
        margin-top: 10px;
        font-size: 0.9em;
    }
    .search-box {
        margin-bottom: 20px;
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
                'messages': []
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
        else:
            # This is their message
            contact_url = sender_url if sender_url else lead_url
        
        if contact_url in contacts:
            contacts[contact_url]['messages'].append(row)
    
    return contacts

def main():
    st.title("💬 LinkedIn Chat History Viewer")
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
                st.markdown(f"""
                **👤 My Profile:**  
                {MY_PROFILE['name']}  
                [View LinkedIn]({MY_PROFILE['url']})
                """)
                
                # Refresh button
                if st.button("🔄 Refresh Data", use_container_width=True):
                    st.cache_data.clear()
                    st.rerun()
        else:
            st.warning("⚠️ Please upload your service account JSON file to continue")
            st.info("""
            **Steps to get Service Account JSON:**
            1. Go to Google Cloud Console
            2. Enable Google Sheets API & Google Drive API
            3. Create Service Account
            4. Download JSON key
            5. Share the spreadsheet with the service account email
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
            <div class="stat-label">Contacts</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        my_messages = sum(1 for _, row in df.iterrows() if is_me(row.get('sender_name', ''), row.get('sender_linkedin_url', '')))
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-number">{my_messages}</div>
            <div class="stat-label">Messages Sent</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        received_messages = len(df) - my_messages
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-number">{received_messages}</div>
            <div class="stat-label">Messages Received</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # View Selection
    view_mode = st.radio(
        "Select View",
        ["📇 All Contacts", "👤 Contact Details", "📝 All Messages"],
        horizontal=True
    )
    
    if view_mode == "📇 All Contacts":
        show_all_contacts(contacts)
    elif view_mode == "👤 Contact Details":
        show_individual_contact(contacts)
    else:
        show_all_messages(df)

def show_all_contacts(contacts):
    """Display all contacts in card format"""
    st.header("📇 All Contacts")
    
    if not contacts:
        st.info("No contacts found.")
        return
    
    # Search filter
    search = st.text_input("🔍 Search contacts", "", key="contact_search")
    
    # Filter contacts
    filtered_contacts = {
        url: info for url, info in contacts.items()
        if not search or search.lower() in info['name'].lower()
    }
    
    # Display in columns
    cols = st.columns(2)
    
    for idx, (url, info) in enumerate(filtered_contacts.items()):
        col = cols[idx % 2]
        
        message_count = len(info['messages'])
        last_message = info['messages'][-1] if info['messages'] else {}
        last_date = last_message.get('date', '')
        last_time = last_message.get('time', '')
        
        with col:
            st.markdown(f"""
            <div class="contact-card">
                <h2>👤 {info['name']}</h2>
                <p style="font-size: 1.2em;"><strong>💬 {message_count}</strong> messages</p>
                <p><strong>Last Contact:</strong> {last_date} {last_time}</p>
                <div class="linkedin-badge">
                    <a href="{url}" target="_blank" style="color: white; text-decoration: none;">
                        🔗 View LinkedIn Profile
                    </a>
                </div>
            </div>
            """, unsafe_allow_html=True)

def show_individual_contact(contacts):
    """Display messages for a specific contact"""
    st.header("👤 Contact Conversation")
    
    if not contacts:
        st.info("No contacts found.")
        return
    
    # Contact selection
    contact_options = {info['name']: url for url, info in contacts.items()}
    
    selected_name = st.selectbox(
        "Select a contact",
        options=list(contact_options.keys())
    )
    
    selected_url = contact_options[selected_name]
    contact_info = contacts[selected_url]
    
    # Display contact header
    message_count = len(contact_info['messages'])
    st.markdown(f"""
    <div class="contact-header">
        <h2>👤 {contact_info['name']}</h2>
        <p style="font-size: 1.1em;">💬 {message_count} messages in conversation</p>
        <div class="linkedin-badge">
            <a href="{contact_info['url']}" target="_blank" style="color: white; text-decoration: none;">
                🔗 View LinkedIn Profile
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 💬 Conversation")
    
    # Sort messages by date and time
    messages = sorted(
        contact_info['messages'],
        key=lambda x: (x.get('date', ''), x.get('time', ''))
    )
    
    # Display messages
    for msg in messages:
        sender_name = msg.get('sender_name', '')
        sender_url = msg.get('sender_linkedin_url', '')
        message = msg.get('message', '')
        date = msg.get('date', '')
        time = msg.get('time', '')
        shared_content = msg.get('shared_content', '')
        
        is_my_message = is_me(sender_name, sender_url)
        
        if is_my_message:
            # My message (right-aligned, colored)
            st.markdown(f"""
            <div class="message-sent">
                <strong>Me</strong> <span class="message-time">• {date} {time}</span>
                <p style="margin-top: 10px;">{message}</p>
                {f'<p style="opacity: 0.8; margin-top: 5px;"><em>📎 {shared_content}</em></p>' if shared_content else ''}
            </div>
            """, unsafe_allow_html=True)
        else:
            # Their message (left-aligned)
            st.markdown(f"""
            <div class="message-received">
                <strong>{sender_name}</strong> <span class="message-time">• {date} {time}</span>
                <p style="margin-top: 10px; color: #333;">{message}</p>
                {f'<p style="color: #666; margin-top: 5px;"><em>📎 {shared_content}</em></p>' if shared_content else ''}
            </div>
            """, unsafe_allow_html=True)

def show_all_messages(df):
    """Display all messages in chronological order"""
    st.header("📝 All Messages")
    
    # Search filter
    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input("🔍 Search messages", "", key="message_search")
    with col2:
        show_only = st.selectbox("Filter", ["All", "Sent", "Received"])
    
    # Filter messages
    filtered_df = df.copy()
    
    if search:
        filtered_df = filtered_df[filtered_df['message'].str.contains(search, case=False, na=False)]
    
    if show_only == "Sent":
        filtered_df = filtered_df[filtered_df.apply(
            lambda x: is_me(x.get('sender_name', ''), x.get('sender_linkedin_url', '')), axis=1
        )]
    elif show_only == "Received":
        filtered_df = filtered_df[~filtered_df.apply(
            lambda x: is_me(x.get('sender_name', ''), x.get('sender_linkedin_url', '')), axis=1
        )]
    
    # Sort by date and time
    if 'date' in filtered_df.columns and 'time' in filtered_df.columns:
        filtered_df = filtered_df.sort_values(['date', 'time'], ascending=[False, False])
    
    st.markdown(f"**Showing {len(filtered_df)} messages**")
    st.markdown("---")
    
    # Display messages
    for idx, row in filtered_df.iterrows():
        sender_name = row.get('sender_name', 'Unknown')
        sender_url = row.get('sender_linkedin_url', '')
        message = row.get('message', '')
        date = row.get('date', '')
        time = row.get('time', '')
        shared_content = row.get('shared_content', '')
        
        is_my_message = is_me(sender_name, sender_url)
        display_name = "Me" if is_my_message else sender_name
        
        message_class = "message-sent" if is_my_message else "message-received"
        
        st.markdown(f"""
        <div class="{message_class}">
            <strong>{display_name}</strong> <span class="message-time">• {date} {time}</span>
            {f' • <a href="{sender_url}" target="_blank" style="color: inherit;">LinkedIn</a>' if sender_url and not is_my_message else ''}
            <p style="margin-top: 10px;">{message}</p>
            {f'<p style="opacity: 0.8; margin-top: 5px;"><em>📎 {shared_content}</em></p>' if shared_content else ''}
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
