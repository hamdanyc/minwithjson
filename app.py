import streamlit as st
import os
import json
import base64
import pandas as pd
from mom_logic import initialize_mom_state, ingest_previous_mom, save_mom_to_json
from generate_mom_reportlab import MOMReportLab

st.set_page_config(page_title="MOM Crafter", layout="wide")

# CSS for better UI
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #007bff;
        color: white;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #e9ecef;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #007bff;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if 'mom_data' not in st.session_state:
    st.session_state.mom_data = initialize_mom_state()
if 'current_stage' not in st.session_state:
    st.session_state.current_stage = 0

def next_stage():
    st.session_state.current_stage += 1
def prev_stage():
    st.session_state.current_stage -= 1

st.title("📋 Minutes of Meeting (MOM) Crafter")

# Sidebar for Navigation and Persistence
with st.sidebar:
    st.header("Navigation")
    stages = [
        "1. Initialization",
        "2. Header Info",
        "3. Attendance",
        "4. Matters Arising",
        "5. Main Agenda",
        "6. New Matters",
        "7. Closing & Export"
    ]
    st.session_state.current_stage = st.radio("Go to Stage", range(len(stages)), 
                                              index=st.session_state.current_stage,
                                              format_func=lambda i: stages[i])

    st.divider()
    st.header("Persistence")
    if st.button("Reset Session"):
        st.session_state.mom_data = initialize_mom_state()
        st.session_state.current_stage = 0
        st.rerun()

    exported_json = json.dumps(st.session_state.mom_data, indent=4)
    st.download_button(
        label="Download Current JSON",
        data=exported_json,
        file_name="mom_draft.json",
        mime="application/json"
    )

# Workflow Stages
current_stage = st.session_state.current_stage

if current_stage == 0: # Initialization
    st.header("Stage 1: Initialization")
    st.info("Start a new meeting or load items from a previous minutes to update 'Matters Arising'.")
    
    uploaded_prev = st.file_uploader("Upload Previous MOM JSON (optional)", type=["json"])
    if uploaded_prev:
        try:
            prev_data = json.load(uploaded_prev)
            if st.button("Ingest Previous Minutes"):
                st.session_state.mom_data = ingest_previous_mom(prev_data)
                # Clear editor states to force refresh from new data
                for k in ["hadir_editor", "tidak_editor", "ma_editor", "nm_editor"]:
                    if k in st.session_state:
                         del st.session_state[k]
                st.success("Previous items ingested into 'Matters Arising'!")
                st.rerun()
        except Exception as e:
            st.error(f"Error loading JSON: {e}")

elif current_stage == 1: # Header Info
    st.header("Stage 2: Header Information")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.mom_data["Header"]["Title"] = st.text_input("Meeting Title", st.session_state.mom_data["Header"]["Title"])
        st.session_state.mom_data["Header"]["Siri"] = st.text_input("Serial (Siri)", st.session_state.mom_data["Header"]["Siri"])
        st.session_state.mom_data["Header"]["Jenis"] = st.selectbox("Meeting Type", ["agm", "exco"], 
                                                                    index=0 if st.session_state.mom_data["Header"]["Jenis"] == "agm" else 1)
    with col2:
        st.session_state.mom_data["Header"]["Tarikh"] = st.text_input("Date (DD/MM/YYYY)", st.session_state.mom_data["Header"]["Tarikh"])
        st.session_state.mom_data["Header"]["Masa"] = st.text_input("Time", st.session_state.mom_data["Header"]["Masa"])
        st.session_state.mom_data["Header"]["Tempat"] = st.text_input("Venue", st.session_state.mom_data["Header"]["Tempat"])

elif current_stage == 2: # Attendance
    st.header("Stage 3: Attendance")
    
    col_at1, col_at2 = st.columns([2, 1])
    with col_at2:
        st.subheader("Bulk Import")
        uploaded_csv = st.file_uploader("Upload Attendance CSV (nama, jawatan)", type=["csv"], key="csv_at")
        if uploaded_csv:
            try:
                import pandas as pd
                df_csv = pd.read_csv(uploaded_csv)
                # Normalize columns to lowercase
                df_csv.columns = [c.lower() for c in df_csv.columns]
                if 'nama' in df_csv.columns:
                    # Map to the format we need
                    new_hadir = []
                    new_tidak = []
                    
                    # Convert 'hadir' column to boolean if it exists
                    if 'hadir' in df_csv.columns:
                        # Handle various boolean-like values
                        df_csv['hadir_bool'] = df_csv['hadir'].apply(lambda x: str(x).lower().strip() in ['true', '1', 't', 'yes', 'ya', 'hadir'])
                    else:
                        # Default all to Hadir if column missing
                        df_csv['hadir_bool'] = True
                        
                    for _, row in df_csv.iterrows():
                        record = {
                            "siri": row.get('siri', ''),
                            "nama": row['nama'],
                            "jawatan": row.get('jawatan', ''),
                            "singkatan": row.get('singkatan', '')
                        }
                        if row['hadir_bool']:
                            new_hadir.append(record)
                        else:
                            # Add default empty reason for absence
                            record["sebab"] = ""
                            new_tidak.append(record)
                    
                    if st.button("Append to Attendance Lists"):
                        st.session_state.mom_data["Attendance"]["Hadir"].extend(new_hadir)
                        st.session_state.mom_data["Attendance"]["Tidak Hadir"].extend(new_tidak)
                        st.success(f"Processed CSV: Added {len(new_hadir)} to 'Hadir' and {len(new_tidak)} to 'Tidak Hadir'.")
                else:
                    st.error("CSV must contain a 'nama' column.")
            except Exception as e:
                st.error(f"Error reading CSV: {e}")

    with col_at1:
        st.subheader("Hadir (Present)")
        hadir_df = pd.DataFrame(st.session_state.mom_data["Attendance"]["Hadir"])
        if hadir_df.empty:
            hadir_df = pd.DataFrame([{"siri": "", "nama": "", "jawatan": "", "singkatan": ""}])
        
        edited_hadir = st.data_editor(hadir_df, num_rows="dynamic", use_container_width=True, key="hadir_editor")
        st.session_state.mom_data["Attendance"]["Hadir"] = edited_hadir.to_dict('records')

    st.subheader("Tidak Hadir (Absent with Excuse)")
    tidak_hadir_df = pd.DataFrame(st.session_state.mom_data["Attendance"]["Tidak Hadir"])
    if tidak_hadir_df.empty:
        tidak_hadir_df = pd.DataFrame([{"siri": "", "nama": "", "jawatan": "", "singkatan": "", "sebab": ""}])
    
    edited_tidak = st.data_editor(tidak_hadir_df, num_rows="dynamic", use_container_width=True, key="tidak_editor")
    st.session_state.mom_data["Attendance"]["Tidak Hadir"] = edited_tidak.to_dict('records')

elif current_stage == 3: # Matters Arising
    st.header("Stage 4: Matters Arising")
    st.write("Status updates on items from the previous meeting.")
    
    ma_df = pd.DataFrame(st.session_state.mom_data["MattersArising"])
    if ma_df.empty:
        ma_df = pd.DataFrame([{"item": "", "status": "Ongoing", "outcome": ""}])
    
    # Ensure columns exist
    for col in ["item", "status", "outcome"]:
        if col not in ma_df.columns:
            ma_df[col] = ""

    edited_ma = st.data_editor(ma_df, num_rows="dynamic", use_container_width=True, 
                               column_config={
                                   "status": st.column_config.SelectboxColumn(
                                       "Status",
                                       options=["Done", "Ongoing", "Pending", "Cancelled"]
                                   )
                               }, key="ma_editor")
    st.session_state.mom_data["MattersArising"] = edited_ma.to_dict('records')

elif current_stage == 4: # Main Agenda
    st.header("Stage 5: Main Agenda Items")
    st.session_state.mom_data["ChairmanAddress"] = st.text_area("Chairman's Welcome Note", st.session_state.mom_data.get("ChairmanAddress", ""))
    st.session_state.mom_data["ApprovalOfPrevMinutes"] = st.text_area("Confirmation of Previous Minutes", st.session_state.mom_data.get("ApprovalOfPrevMinutes", ""))
    
    st.subheader("Financial & Membership Reports")
    st.session_state.mom_data["Reports"]["Financial"] = st.text_area("Financial Report", st.session_state.mom_data["Reports"]["Financial"])
    st.session_state.mom_data["Reports"]["Membership"] = st.text_area("Membership Report", st.session_state.mom_data["Reports"]["Membership"])

elif current_stage == 5: # New Matters
    st.header("Stage 6: New Matters & Decisions")
    nm_df = pd.DataFrame(st.session_state.mom_data["NewMatters"])
    if nm_df.empty:
        nm_df = pd.DataFrame([{"item": "", "keputusan": ""}])
    
    edited_nm = st.data_editor(nm_df, num_rows="dynamic", use_container_width=True, key="nm_editor")
    st.session_state.mom_data["NewMatters"] = edited_nm.to_dict('records')

elif current_stage == 6: # Export
    st.header("Stage 7: Finalize & Generate PDF")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Raw Data Preview")
        st.json(st.session_state.mom_data)
    
    with col2:
        st.subheader("Generate Output")
        
        # We need a formal save for the PDF generator
        import tempfile
        import os
        
        if st.button("Generate Formal PDF"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode='w') as f:
                json.dump(st.session_state.mom_data, f)
                tmp_json_path = f.name
            
            output_pdf = tempfile.mktemp(suffix=".pdf")
            try:
                mom = MOMReportLab(tmp_json_path, output_pdf)
                mom.create_pdf()
                
                if os.path.exists(output_pdf):
                    with open(output_pdf, "rb") as f:
                        pdf_bytes = f.read()
                    
                    st.success("PDF Generated Successfully!")
                    
                    # Preview PDF
                    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
                    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
                    st.markdown(pdf_display, unsafe_allow_html=True)
                    
                    st.download_button(
                        label="Download PDF",
                        data=pdf_bytes,
                        file_name=f"MOM_{st.session_state.mom_data['Header']['Siri'].replace('/', '_')}.pdf",
                        mime="application/pdf"
                    )
            except Exception as e:
                st.error(f"PDF Generation failed: {e}")
            finally:
                if 'tmp_json_path' in locals() and os.path.exists(tmp_json_path):
                    os.remove(tmp_json_path)
        
        st.divider()
        st.subheader("Serial Continuity")
        if st.button("Prepare JSON for NEXT Meeting"):
            # Map current session to next session state
            next_session_data = ingest_previous_mom(st.session_state.mom_data)
            next_json = json.dumps(next_session_data, indent=4)
            st.download_button(
                label="Download NEXT Meeting JSON",
                data=next_json,
                file_name="next_meeting_init.json",
                mime="application/json"
            )
            st.info("This JSON contains your current 'New Matters' as 'Matters Arising' for the next session.")

st.divider()
col_prev, col_next = st.columns([1,1])
with col_prev:
    if current_stage > 0:
        if st.button("⬅️ Previous Stage"):
            st.session_state.current_stage -= 1
            st.rerun()
with col_next:
    if current_stage < len(stages) - 1:
        if st.button("Next Stage ➡️"):
            st.session_state.current_stage += 1
            st.rerun()
