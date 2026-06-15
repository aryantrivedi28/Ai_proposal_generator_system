"""Production-Ready Web Interface for AI Proposal Generator"""

import streamlit as st
import sys
from pathlib import Path
import json
from datetime import datetime
import pandas as pd
import plotly.express as px

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.pipeline import ProposalPipeline
from src.cost_tracker import CostTracker
from src.database import ProposalDatabase

# Page configuration
st.set_page_config(
    page_title="AI Proposal Generator - Production Suite",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for production styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 1rem;
        color: white;
        text-align: center;
    }
    .stButton > button {
        width: 100%;
    }
    .export-options {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'proposal_generated' not in st.session_state:
    st.session_state.proposal_generated = False
if 'current_proposal' not in st.session_state:
    st.session_state.current_proposal = None
if 'pipeline' not in st.session_state:
    st.session_state.pipeline = ProposalPipeline()
if 'db' not in st.session_state:
    st.session_state.db = ProposalDatabase()
if 'cost_tracker' not in st.session_state:
    st.session_state.cost_tracker = CostTracker()

# Header
st.markdown('<p class="main-header">🤖 AI Proposal Generator</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Enterprise-Grade Proposal Automation with OpenAI GPT-4o</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("## 📊 System Dashboard")
    st.markdown("---")
    
    # API Status
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        st.success("✅ OpenAI API: Connected")
    else:
        st.error("❌ OpenAI API: Key missing")
        st.info("Add OPENAI_API_KEY to .env file")
    
    st.markdown("---")
    
    # Cost Summary
    st.markdown("### 💰 Cost Summary")
    cost_summary = st.session_state.cost_tracker.get_summary()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Today", f"${cost_summary['today']:.4f}")
    with col2:
        st.metric("This Month", f"${cost_summary['this_month']:.2f}")
    
    # Budget progress
    budget_percent = (cost_summary['this_month'] / cost_summary['budget_total']) * 100
    st.progress(min(budget_percent / 100, 1.0))
    st.caption(f"Budget: ${cost_summary['this_month']:.2f} / ${cost_summary['budget_total']}")
    
    if cost_summary['alerts']:
        st.warning(cost_summary['alerts'][0])
    
    st.markdown("---")
    
    # Database Stats
    st.markdown("### 📊 Database Stats")
    stats = st.session_state.db.get_statistics()
    st.metric("Total Proposals", stats['total_proposals'])
    st.metric("Total Cost", f"${stats['total_cost_usd']:.2f}")
    st.metric("Avg per Proposal", f"${stats['average_cost']:.4f}")
    
    st.markdown("---")
    
    # Tips
    st.markdown("### 💡 Pro Tips")
    st.markdown("""
    - ✅ Include specific dates and numbers
    - ✅ Mention budget ranges clearly
    - ✅ List all requirements explicitly
    - ✅ Use Google Docs for team editing
    - ✅ Track costs in Analytics tab
    """)
    
    st.markdown("---")
    st.markdown("### 📁 Output Location")
    st.code("outputs/proposals/")

# Main tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📝 Generate Proposal", 
    "📊 Analytics", 
    "🗄️ History", 
    "⚙️ Settings",
    "📚 Help"
])

# ============================================
# TAB 1: Generate Proposal
# ============================================
with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📝 Step 1: Enter Transcript")
        
        # Input method selection
        input_method = st.radio(
            "Choose input method:",
            ["📋 Paste Text", "📁 Upload File", "✨ Use Sample"],
            horizontal=True,
            key="input_method"
        )
        
        transcript_text = ""
        
        if input_method == "📋 Paste Text":
            transcript_text = st.text_area(
                "Paste your meeting transcript here:",
                height=300,
                placeholder="Example:\nClient: We need a proposal for our conference...\nAgent: When is the event?\nClient: March 15th, 2024...",
                key="paste_input"
            )
        
        elif input_method == "📁 Upload File":
            uploaded_file = st.file_uploader(
                "Upload transcript file",
                type=['txt', 'vtt', 'json', 'md'],
                help="Upload a text file containing the transcript",
                key="file_upload"
            )
            if uploaded_file:
                transcript_text = uploaded_file.read().decode('utf-8')
                st.success(f"✅ Loaded: {uploaded_file.name}")
        
        else:  # Sample
            sample_transcript = """Meeting with Sarah Johnson from Green Events about their annual corporate gala.

Sarah: We're planning our 10th anniversary gala. Expecting about 300-350 guests.
Agent: Congratulations! When is the event?
Sarah: June 15, 2024 at the Grand Plaza Hotel.
Agent: What's your budget range?
Sarah: Around $45,000-50,000 for everything.
Agent: What services do you need?
Sarah: Full event planning, catering, entertainment, decor, and AV.
Agent: Any special requirements?
Sarah: Yes, we need a photo booth and live band. Also dietary accommodations for gluten-free and vegan guests.
Agent: Perfect, I'll prepare the proposal with these details."""

            transcript_text = st.text_area(
                "Sample transcript (you can edit it):",
                value=sample_transcript,
                height=300,
                key="sample_input"
            )
        
        # Export options
        st.markdown("### 📤 Step 2: Export Options")
        
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            export_to_google = st.checkbox(
                "🌐 Google Docs",
                help="Upload to Google Docs for collaborative editing",
                value=False
            )
        with col_b:
            export_to_pdf = st.checkbox(
                "📑 PDF Export",
                help="Generate PDF version for clients",
                value=False
            )
        with col_c:
            save_to_db = st.checkbox(
                "💾 Save to Database",
                help="Store proposal in database for history",
                value=True
            )
        
        # Generate button
        if st.button("🚀 Generate Proposal", type="primary", use_container_width=True):
            if transcript_text.strip():
                with st.spinner("🤖 AI is analyzing the transcript and generating your proposal..."):
                    try:
                        # Process the transcript with selected options
                        result = st.session_state.pipeline.process(
                            transcript_text,
                            transcript_name="web_input",
                            export_to_google=export_to_google,
                            export_to_pdf=export_to_pdf
                        )
                        
                        st.session_state.current_proposal = result
                        st.session_state.proposal_generated = True
                        
                        # Save to database if selected
                        if save_to_db:
                            st.session_state.db.save_proposal(result)
                        
                        st.markdown('<div class="success-box">', unsafe_allow_html=True)
                        st.success(f"✅ Proposal Generated Successfully!")
                        st.markdown(f"**Proposal ID:** `{result['proposal_id']}`")
                        st.markdown(f"**Saved to:** `{result['docx_path']}`")
                        
                        if result.get('google_docs_url'):
                            st.markdown(f"**🌐 Google Docs:** [Open in Google Docs]({result['google_docs_url']})")
                        if result.get('pdf_path'):
                            st.markdown(f"**📑 PDF:** `{result['pdf_path']}`")
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                    except Exception as e:
                        st.error(f"❌ Error generating proposal: {str(e)}")
            else:
                st.warning("⚠️ Please enter some transcript text")
    
    with col2:
        st.markdown("### 📊 Step 3: Review Extracted Data")
        
        if st.session_state.proposal_generated and st.session_state.current_proposal:
            data = st.session_state.current_proposal.get('extracted_data', {})
            
            # Display extracted information
            st.markdown('<div class="info-box">', unsafe_allow_html=True)
            
            # Client Info
            st.markdown("**🏢 Client Information**")
            st.markdown(f"• **Name:** {data.get('client_name') or '—'}")
            st.markdown(f"• **Contact:** {data.get('contact_person') or '—'}")
            st.markdown(f"• **Email:** {data.get('email') or '—'}")
            st.markdown(f"• **Phone:** {data.get('phone') or '—'}")
            
            st.markdown("---")
            
            # Event Info
            st.markdown("**🎯 Event Details**")
            st.markdown(f"• **Type:** {data.get('proposal_type') or '—'}")
            st.markdown(f"• **Event:** {data.get('event_name') or '—'}")
            st.markdown(f"• **Date:** {data.get('event_date') or '—'}")
            st.markdown(f"• **Venue:** {data.get('venue') or '—'}")
            st.markdown(f"• **Guests:** {data.get('guest_count') or '—'}")
            
            st.markdown("---")
            
            # Financial
            st.markdown("**💰 Budget**")
            st.markdown(f"• **Budget Range:** {data.get('budget') or '—'}")
            st.markdown(f"• **Est. Cost:** {data.get('estimated_cost') or '—'}")
            
            # Services
            if data.get('services_requested'):
                st.markdown("---")
                st.markdown("**🛠️ Services Requested**")
                for service in data['services_requested'][:4]:
                    st.markdown(f"• {service}")
            
            # Special Requirements
            if data.get('special_requirements'):
                st.markdown("---")
                st.markdown("**⚠️ Special Requirements**")
                for req in data['special_requirements'][:3]:
                    st.markdown(f"• {req}")
            
            # Key Notes
            if data.get('key_notes'):
                st.markdown("---")
                st.markdown("**📝 Key Notes**")
                for note in data['key_notes'][:3]:
                    st.markdown(f"• {note[:100]}...")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Download buttons
            st.markdown("### 📥 Downloads")
            
            col_d1, col_d2 = st.columns(2)
            
            with col_d1:
                if st.session_state.current_proposal.get('docx_path'):
                    docx_path = Path(st.session_state.current_proposal['docx_path'])
                    if docx_path.exists():
                        with open(docx_path, 'rb') as f:
                            st.download_button(
                                label="📄 Download DOCX",
                                data=f,
                                file_name=docx_path.name,
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                use_container_width=True
                            )
            
            with col_d2:
                if st.session_state.current_proposal.get('pdf_path'):
                    pdf_path = Path(st.session_state.current_proposal['pdf_path'])
                    if pdf_path.exists():
                        with open(pdf_path, 'rb') as f:
                            st.download_button(
                                label="📑 Download PDF",
                                data=f,
                                file_name=pdf_path.name,
                                mime="application/pdf",
                                use_container_width=True
                            )
        else:
            st.info("👈 Generate a proposal to see extracted information here")

# ============================================
# TAB 2: Analytics Dashboard
# ============================================
with tab2:
    st.markdown("### 📊 Cost & Usage Analytics")
    
    # Get cost summary
    cost_summary = st.session_state.cost_tracker.get_summary()
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Today's Cost", f"${cost_summary['today']:.4f}")
    with col2:
        st.metric("This Week", f"${cost_summary['this_week']:.4f}")
    with col3:
        st.metric("This Month", f"${cost_summary['this_month']:.2f}")
    with col4:
        st.metric("Avg per Proposal", f"${cost_summary['average_per_proposal']:.4f}")
    
    # Budget progress
    st.markdown("### 💰 Monthly Budget Progress")
    budget_percent = (cost_summary['this_month'] / cost_summary['budget_total']) * 100
    st.progress(min(budget_percent / 100, 1.0))
    
    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        st.metric("Used", f"${cost_summary['this_month']:.2f}")
    with col_b2:
        st.metric("Remaining", f"${cost_summary['remaining_budget']:.2f}")
    with col_b3:
        st.metric("Budget Total", f"${cost_summary['budget_total']}")
    
    # Cost trend chart
    st.markdown("### 📈 Cost Trend (Last 7 Days)")
    
    # Get daily costs for last 7 days
    from datetime import datetime, timedelta
    dates = []
    costs = []
    
    for i in range(6, -1, -1):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        dates.append(date)
        costs.append(st.session_state.cost_tracker.daily_usage.get(date, 0))
    
    chart_data = pd.DataFrame({"Date": dates, "Cost ($)": costs})
    st.line_chart(chart_data, x="Date", y="Cost ($)", use_container_width=True)
    
    # Cost by proposal type
    st.markdown("### 📊 Proposals by Type")
    stats = st.session_state.db.get_statistics()
    
    if stats['by_type']:
        type_data = pd.DataFrame([
            {"Type": k.capitalize(), "Count": v} 
            for k, v in stats['by_type'].items()
        ])
        st.bar_chart(type_data.set_index("Type"), use_container_width=True)
    else:
        st.info("Generate proposals to see type distribution")
    
    # Cost saving tips
    st.markdown("### 💡 Cost Optimization Tips")
    st.info("""
    - **GPT-4o-mini** costs 90% less than GPT-4
    - Each proposal typically costs **$0.01-0.03**
    - 1,000 proposals = ~**$20-30** total
    - Use batch processing for bulk savings
    - Enable PDF export only when needed
    """)
    
    # Alerts
    if cost_summary['alerts']:
        st.warning(cost_summary['alerts'][0])

# ============================================
# TAB 3: Proposal History
# ============================================
with tab3:
    st.markdown("### 🗄️ Proposal History")
    
    # Search and filter
    col_s1, col_s2 = st.columns([3, 1])
    with col_s1:
        search_query = st.text_input("🔍 Search by client or event name", placeholder="Type to search...")
    with col_s2:
        st.markdown("<br>", unsafe_allow_html=True)
        refresh = st.button("🔄 Refresh", use_container_width=True)
    
    # Get proposals
    if search_query:
        proposals = st.session_state.db.search_proposals(search_query)
    else:
        proposals = st.session_state.db.get_all_proposals(limit=50)
    
    if proposals:
        st.markdown(f"**Found {len(proposals)} proposals**")
        
        # Display as table
        for prop in proposals:
            with st.expander(f"📄 {prop['proposal_id']} - {prop.get('client_name', 'Unknown Client')}"):
                col_e1, col_e2, col_e3 = st.columns(3)
                
                with col_e1:
                    st.markdown("**Event Details**")
                    st.markdown(f"• **Event:** {prop.get('event_name', '—')}")
                    st.markdown(f"• **Date:** {prop.get('event_date', '—')}")
                    st.markdown(f"• **Type:** {prop.get('proposal_type', '—')}")
                    st.markdown(f"• **Guests:** {prop.get('guest_count', '—')}")
                
                with col_e2:
                    st.markdown("**Financial**")
                    st.markdown(f"• **Budget:** {prop.get('budget', '—')}")
                    st.markdown(f"• **API Cost:** ${prop.get('cost_usd', 0):.4f}")
                
                with col_e3:
                    st.markdown("**Actions**")
                    # Download buttons
                    if prop.get('docx_path') and Path(prop['docx_path']).exists():
                        with open(prop['docx_path'], 'rb') as f:
                            st.download_button(
                                label="📄 Download DOCX",
                                data=f,
                                file_name=Path(prop['docx_path']).name,
                                key=f"download_{prop['proposal_id']}"
                            )
                    
                    if prop.get('google_docs_url'):
                        st.markdown(f"[🌐 Open in Google Docs]({prop['google_docs_url']})")
    else:
        st.info("No proposals found. Generate your first proposal!")
    
    # Export history
    st.markdown("---")
    if st.button("📊 Export All History (JSON)", use_container_width=True):
        all_proposals = st.session_state.db.get_all_proposals(limit=1000)
        export_path = f"outputs/history_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        Path("outputs").mkdir(exist_ok=True)
        with open(export_path, 'w') as f:
            json.dump(all_proposals, f, indent=2, default=str)
        st.success(f"Exported to {export_path}")

# ============================================
# TAB 4: Settings
# ============================================
with tab4:
    st.markdown("### ⚙️ System Settings")
    
    col_s1, col_s2 = st.columns(2)
    
    with col_s1:
        st.markdown("#### 💰 Budget Settings")
        monthly_budget = st.number_input(
            "Monthly Budget (USD)",
            min_value=10.0,
            max_value=1000.0,
            value=50.0,
            step=10.0,
            help="Set your monthly OpenAI API budget"
        )
        
        alert_threshold = st.slider(
            "Alert Threshold",
            min_value=0,
            max_value=100,
            value=80,
            step=10,
            help="Percentage of budget that triggers alert"
        )
        
        if st.button("💾 Save Budget Settings"):
            # Update cost tracker budget
            st.session_state.cost_tracker.monthly_budget = monthly_budget
            st.success("✅ Budget settings saved!")
    
    with col_s2:
        st.markdown("#### 🎨 Output Settings")
        company_name = st.text_input("Company Name", value="Your Company Name")
        default_export = st.selectbox(
            "Default Export Format",
            ["DOCX Only", "DOCX + PDF", "DOCX + Google Docs", "All Formats"]
        )
        
        st.markdown("#### 🔧 Advanced")
        enable_batch_processing = st.checkbox("Enable Batch Processing", value=True)
        enable_cost_tracking = st.checkbox("Enable Cost Tracking", value=True)
    
    st.markdown("---")
    st.markdown("### 🗑️ Data Management")
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        if st.button("🗄️ Export Database", use_container_width=True):
            export_data = st.session_state.db.get_all_proposals(limit=10000)
            export_path = f"outputs/db_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            Path("outputs").mkdir(exist_ok=True)
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            st.success(f"✅ Exported to {export_path}")
    
    with col_d2:
        if st.button("🧹 Clear Old Logs", use_container_width=True):
            # Clear logs older than 30 days
            import time
            log_path = Path("logs")
            if log_path.exists():
                cutoff = time.time() - (30 * 24 * 3600)
                for log_file in log_path.glob("*.log*"):
                    if log_file.stat().st_mtime < cutoff:
                        log_file.unlink()
                st.success("✅ Old logs cleared")

# ============================================
# TAB 5: Help & Documentation
# ============================================
with tab5:
    st.markdown("### 📚 User Guide")
    
    with st.expander("🚀 Quick Start Guide", expanded=True):
        st.markdown("""
        **Step 1:** Enter your meeting transcript in the Generate tab
        - Paste text, upload file, or use the sample
        - Include key details: dates, budget, services
        
        **Step 2:** Choose export options
        - DOCX: Editable in Microsoft Word
        - PDF: For client delivery
        - Google Docs: Collaborative editing
        
        **Step 3:** Click Generate and review
        - AI extracts all key information
        - Review extracted data on the right
        - Download your proposal
        """)
    
    with st.expander("📝 Tips for Best Results"):
        st.markdown("""
        ✅ **DO:**
        - Include specific dates and numbers
        - Mention budget ranges clearly
        - List all requirements explicitly
        - State client and event names clearly
        
        ❌ **DON'T:**
        - Use vague language
        - Skip important details
        - Forget to mention guest counts
        - Leave out budget information
        """)
    
    with st.expander("🔧 Troubleshooting"):
        st.markdown("""
        | Issue | Solution |
        |-------|----------|
        | API Key Error | Check .env file has OPENAI_API_KEY |
        | Proposal not generating | Check internet connection |
        | Google Docs fails | Complete OAuth setup first |
        | PDF export fails | Install reportlab: `pip install reportlab` |
        | Cost tracking not showing | Generate at least one proposal |
        """)
    
    with st.expander("📊 Understanding Costs"):
        st.markdown("""
        **Cost Breakdown per Proposal:**
        - GPT-4o-mini: ~$0.01-0.03 per proposal
        - Includes: Extraction + Content generation
        - 1,000 proposals = ~$20-30 total
        
        **Free Features:**
        - DOCX generation
        - Local processing
        - Database storage
        - All templates
        """)
    
    with st.expander("🔐 API Key Setup"):
        st.markdown("""
        1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
        2. Sign up or log in
        3. Click "Create new secret key"
        4. Copy the key (starts with `sk-...`)
        5. Add to `.env` file:
        """)