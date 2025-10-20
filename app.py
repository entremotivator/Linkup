import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import json

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
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin-bottom: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .message-card {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
        border-left: 4px solid #667eea;
    }
    .sender-card {
        background: #e3f2fd;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
        border-left: 4px solid #2196f3;
    }
    .stat-box {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Google Sheets Configuration
SPREADSHEET_ID = "1klm60YFXSoV510S4igv5LfREXeykDhNA5Ygq7HNFN0I"
SHEET_NAME = "linkedin_chat_history_advanced 2"

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
                
                # Refresh button
                if st.button("🔄 Refresh Data"):
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
    
    # Display Statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="stat-box">', unsafe_allow_html=True)
        st.metric("Total Messages", len(df))
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="stat-box">', unsafe_allow_html=True)
        unique_contacts = df['lead_linkedin_url'].nunique() if 'lead_linkedin_url' in df.columns else 0
        st.metric("Unique Contacts", unique_contacts)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="stat-box">', unsafe_allow_html=True)
        unique_senders = df['sender_name'].nunique() if 'sender_name' in df.columns else 0
        st.metric("Unique Senders", unique_senders)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="stat-box">', unsafe_allow_html=True)
        sessions = df['sessionId'].nunique() if 'sessionId' in df.columns else 0
        st.metric("Chat Sessions", sessions)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # View Selection
    view_mode = st.radio(
        "Select View",
        ["All Contacts", "Individual Contact", "All Messages"],
        horizontal=True
    )
    
    if view_mode == "All Contacts":
        show_all_contacts(df)
    elif view_mode == "Individual Contact":
        show_individual_contact(df)
    else:
        show_all_messages(df)

def show_all_contacts(df):
    """Display all contacts in card format"""
    st.header("📇 All Contacts")
    
    # Group by lead_linkedin_url
    if 'lead_linkedin_url' not in df.columns:
        st.error("Column 'lead_linkedin_url' not found in data")
        return
    
    grouped = df.groupby('lead_linkedin_url').agg({
        'sender_name': lambda x: x.iloc[0] if len(x) > 0 else 'Unknown',
        'message': 'count',
        'date': lambda x: x.iloc[-1] if len(x) > 0 else '',
        'time': lambda x: x.iloc[-1] if len(x) > 0 else '',
        'sessionId': lambda x: x.iloc[0] if len(x) > 0 else ''
    }).reset_index()
    
    grouped.columns = ['LinkedIn URL', 'Name', 'Message Count', 'Last Date', 'Last Time', 'Session ID']
    
    # Display in columns
    cols = st.columns(2)
    
    for idx, row in grouped.iterrows():
        col = cols[idx % 2]
        
        with col:
            st.markdown(f"""
            <div class="contact-card">
                <h3>👤 {row['Name']}</h3>
                <p><strong>Messages:</strong> {row['Message Count']}</p>
                <p><strong>Last Contact:</strong> {row['Last Date']} {row['Last Time']}</p>
                <p><strong>LinkedIn:</strong> <a href="{row['LinkedIn URL']}" target="_blank" style="color: white;">View Profile</a></p>
            </div>
            """, unsafe_allow_html=True)

def show_individual_contact(df):
    """Display messages for a specific contact"""
    st.header("👤 Individual Contact View")
    
    if 'lead_linkedin_url' not in df.columns:
        st.error("Column 'lead_linkedin_url' not found in data")
        return
    
    # Contact selection
    contacts = df['lead_linkedin_url'].unique()
    
    # Create a mapping of names to URLs
    contact_names = {}
    for url in contacts:
        name = df[df['lead_linkedin_url'] == url]['sender_name'].iloc[0] if len(df[df['lead_linkedin_url'] == url]) > 0 else url
        contact_names[f"{name} ({url})"] = url
    
    selected_contact_display = st.selectbox(
        "Select a contact",
        options=list(contact_names.keys())
    )
    
    selected_contact = contact_names[selected_contact_display]
    
    # Filter messages for selected contact
    contact_messages = df[df['lead_linkedin_url'] == selected_contact].copy()
    
    if contact_messages.empty:
        st.warning("No messages found for this contact")
        return
    
    # Display contact info
    st.markdown(f"""
    <div class="contact-card">
        <h3>Contact Information</h3>
        <p><strong>LinkedIn:</strong> <a href="{selected_contact}" target="_blank" style="color: white;">View Profile</a></p>
        <p><strong>Total Messages:</strong> {len(contact_messages)}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 💬 Message History")
    
    # Sort by date and time
    contact_messages = contact_messages.sort_values(['date', 'time'], ascending=[True, True])
    
    # Display messages
    for idx, row in contact_messages.iterrows():
        sender = row.get('sender_name', 'Unknown')
        message = row.get('message', '')
        date = row.get('date', '')
        time = row.get('time', '')
        shared_content = row.get('shared_content', '')
        
        # Different styling for different senders
        card_class = "sender-card" if sender != "Kolin Simon" else "message-card"
        
        st.markdown(f"""
        <div class="{card_class}">
            <strong>{sender}</strong> • <small>{date} {time}</small>
            <p style="margin-top: 10px; color: #333;">{message}</p>
            {f'<p style="color: #666;"><em>Shared: {shared_content}</em></p>' if shared_content else ''}
        </div>
        """, unsafe_allow_html=True)

def show_all_messages(df):
    """Display all messages in chronological order"""
    st.header("📝 All Messages")
    
    # Add search filter
    search = st.text_input("🔍 Search messages", "")
    
    # Filter by search
    if search:
        df = df[df['message'].str.contains(search, case=False, na=False)]
    
    # Sort by date and time
    if 'date' in df.columns and 'time' in df.columns:
        df = df.sort_values(['date', 'time'], ascending=[False, False])
    
    # Display messages
    for idx, row in df.iterrows():
        sender = row.get('sender_name', 'Unknown')
        message = row.get('message', '')
        date = row.get('date', '')
        time = row.get('time', '')
        linkedin_url = row.get('sender_linkedin_url', row.get('lead_linkedin_url', ''))
        
        st.markdown(f"""
        <div class="message-card">
            <strong>{sender}</strong> • <small>{date} {time}</small>
            {f' • <a href="{linkedin_url}" target="_blank">LinkedIn</a>' if linkedin_url else ''}
            <p style="margin-top: 10px; color: #333;">{message}</p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
