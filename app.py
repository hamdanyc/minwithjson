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
        title = st.text_input("Meeting Title", st.session_state.mom_data["Header"]["Title"])
        siri = st.text_input("Serial (Siri)", st.session_state.mom_data["Header"]["Siri"])
        jenis_map = {"agm": 0, "exco": 1}
        jenis_idx = jenis_map.get(st.session_state.mom_data["Header"]["Jenis"], 0)
        jenis = st.selectbox("Meeting Type", ["agm", "exco"], index=jenis_idx)
    with col2:
        tarikh = st.text_input("Date (DD/MM/YYYY)", st.session_state.mom_data["Header"]["Tarikh"])
        masa = st.text_input("Time", st.session_state.mom_data["Header"]["Masa"])
        tempat = st.text_input("Venue", st.session_state.mom_data["Header"]["Tempat"])
    
    if st.button("🔄 Sync Header Info"):
        st.session_state.mom_data["Header"].update({
            "Title": title,
            "Siri": siri,
            "Jenis": jenis,
            "Tarikh": tarikh,
            "Masa": masa,
            "Tempat": tempat
        })
        st.success("Header info updated!")

elif current_stage == 2: # Attendance
    st.header("Stage 3: Attendance Management")
    
    # Load AJK CSV
    ajk_path = "ajk.csv"
    if 'ajk_df' not in st.session_state:
        if os.path.exists(ajk_path):
            st.session_state.ajk_df = pd.read_csv(ajk_path)
        else:
            st.session_state.ajk_df = pd.DataFrame(columns=["Siri", "Nama", "Jawatan", "Kategori", "Singkatan", "Portfolio", "Hadir"])

    st.subheader("Manage AJK List (ajk.csv)")
    edited_ajk = st.data_editor(
        st.session_state.ajk_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Hadir": st.column_config.SelectboxColumn(
                "Hadir",
                options=["Ya", "Tidak"],
                help="Attendance Status"
            )
        },
        key="ajk_editor"
    )

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("💾 Save Changes to ajk.csv"):
            edited_ajk.to_csv(ajk_path, index=False)
            st.session_state.ajk_df = edited_ajk
            st.success("Successfully saved to ajk.csv!")
    
    with col_btn2:
        if st.button("🔄 Sync with Session Attendance"):
            # Update session state mom_data based on edited_ajk
            hadir_list = []
            tidak_hadir_list = []
            
            for _, row in edited_ajk.iterrows():
                record = {
                    "siri": str(row.get('Siri', '')),
                    "nama": str(row.get('Nama', '')),
                    "jawatan": str(row.get('Jawatan', '')),
                    "singkatan": str(row.get('Singkatan', ''))
                }
                if str(row.get('Hadir', '')).strip() == "Ya":
                    hadir_list.append(record)
                else:
                    record["sebab"] = "" # Default empty reason
                    tidak_hadir_list.append(record)
            
            st.session_state.mom_data["Attendance"]["Hadir"] = hadir_list
            st.session_state.mom_data["Attendance"]["Tidak Hadir"] = tidak_hadir_list
            st.success("Session attendance updated!")

    st.divider()
    st.subheader("Verification: Attendance Lists")
    
    tab_hadir, tab_tidak = st.tabs(["✅ Hadir (Present)", "❌ Tidak Hadir (Absent)"])
    
    with tab_hadir:
        if st.session_state.mom_data["Attendance"]["Hadir"]:
            st.table(pd.DataFrame(st.session_state.mom_data["Attendance"]["Hadir"])[["nama", "jawatan", "singkatan"]])
        else:
            st.info("No attendees recorded.")
            
    with tab_tidak:
        if st.session_state.mom_data["Attendance"]["Tidak Hadir"]:
            st.table(pd.DataFrame(st.session_state.mom_data["Attendance"]["Tidak Hadir"])[["nama", "jawatan", "singkatan", "sebab"]])
        else:
            st.info("No absentees recorded.")

elif current_stage == 3: # Matters Arising
    st.header("Stage 4: Matters Arising")
    st.write("Status updates on items from the previous meeting.")
    
    ma_df = pd.DataFrame(st.session_state.mom_data["MattersArising"])
    if ma_df.empty:
        ma_df = pd.DataFrame([{"Perkara": "", "Keputusan": "Pelaksanaan", "Keterangan": ""}])
    
    # Ensure columns exist
    for col in ["Perkara", "Keputusan", "Keterangan"]:
        if col not in ma_df.columns:
            ma_df[col] = ""

    st.info("Tip: Edit the table below and click 'Sync Matters Arising' to save changes to the session.")
    edited_ma = st.data_editor(ma_df, num_rows="dynamic", use_container_width=True, 
                               column_config={
                                   "Keputusan": st.column_config.SelectboxColumn(
                                       "Keputusan",
                                       options=["Selesai", "Dilanjutkan", "Tangguh", "Batal", "Pelaksanaan"]
                                   )
                               }, key="ma_editor_stable")
    
    if st.button("🔄 Sync Matters Arising"):
        st.session_state.mom_data["MattersArising"] = edited_ma.to_dict('records')
        st.success("Matters Arising updated in session!")

elif current_stage == 4: # Main Agenda
    st.header("Stage 5: Main Agenda Items")
    
    st.subheader("Chairman's Welcome Note")
    c_perkara = st.text_input("Title (Agenda 1)", st.session_state.mom_data["ChairmanAddress"].get("Perkara", "UCAPAN PEMBUKAAN OLEH PRESIDEN"))
    c_keterangan = st.text_area("Content (Agenda 1)", st.session_state.mom_data["ChairmanAddress"].get("Keterangan", ""), height=200)
    
    st.divider()
    st.subheader("Confirmation of Previous Minutes")
    a_perkara = st.text_input("Title (Agenda 2)", st.session_state.mom_data["ApprovalOfPrevMinutes"].get("Perkara", "MENGESAHKAN MINIT MESYUARAT JAWATANKUASA SIRI ..."))
    a_keterangan = st.text_area("Content (Agenda 2)", st.session_state.mom_data["ApprovalOfPrevMinutes"].get("Keterangan", ""), height=100)
    
    st.divider()
    st.subheader("Financial & Membership Reports")
    
    col_rep1, col_rep2 = st.columns(2)
    with col_rep1:
        st.write("**Financial Report**")
        f_perkara = st.text_input("Title (Agenda 4)", st.session_state.mom_data["Reports"]["Financial"].get("Perkara", "LAPORAN KEWANGAN BERAKHIR"))
        f_keterangan = st.text_area("Content (Agenda 4)", st.session_state.mom_data["Reports"]["Financial"].get("Keterangan", ""), height=150)
        
    with col_rep2:
        st.write("**Membership Report**")
        m_perkara = st.text_input("Title (Agenda 5)", st.session_state.mom_data["Reports"]["Membership"].get("Perkara", "LAPORAN KEAHLIAN BERAKHIR"))
        m_keterangan = st.text_area("Content (Agenda 5)", st.session_state.mom_data["Reports"]["Membership"].get("Keterangan", ""), height=150)

    if st.button("🔄 Sync Main Agenda Items"):
        st.session_state.mom_data["ChairmanAddress"]["Perkara"] = c_perkara
        st.session_state.mom_data["ChairmanAddress"]["Keterangan"] = c_keterangan
        st.session_state.mom_data["ApprovalOfPrevMinutes"]["Perkara"] = a_perkara
        st.session_state.mom_data["ApprovalOfPrevMinutes"]["Keterangan"] = a_keterangan
        st.session_state.mom_data["Reports"]["Financial"]["Perkara"] = f_perkara
        st.session_state.mom_data["Reports"]["Financial"]["Keterangan"] = f_keterangan
        st.session_state.mom_data["Reports"]["Membership"]["Perkara"] = m_perkara
        st.session_state.mom_data["Reports"]["Membership"]["Keterangan"] = m_keterangan
        st.success("Main Agenda items updated!")

elif current_stage == 5: # New Matters
    st.header("Stage 6: New Matters & Decisions")
    
    # 1. Normalize data structure if it has old keys (one-time migration)
    nm_raw = st.session_state.mom_data.get("NewMatters", [])
    if nm_raw and isinstance(nm_raw[0], dict) and ("item" in nm_raw[0] or "keputusan" in nm_raw[0]):
        normalized = []
        for entry in nm_raw:
            normalized.append({
                "Perkara": entry.get("Perkara", entry.get("item", "")),
                "Keterangan": entry.get("Keterangan", ""),
                "Keputusan": entry.get("Keputusan", entry.get("keputusan", ""))
            })
        st.session_state.mom_data["NewMatters"] = normalized

    # 2. Build DataFrame from stable session state
    nm_df = pd.DataFrame(st.session_state.mom_data.get("NewMatters", []))
    if nm_df.empty:
        nm_df = pd.DataFrame([{"Perkara": "", "Keterangan": "", "Keputusan": ""}])
    
    # Ensure all columns exist
    for col in ["Perkara", "Keterangan", "Keputusan"]:
        if col not in nm_df.columns:
            nm_df[col] = ""
    
    st.write("Tip: To delete a row, select it using the checkbox on the left and press 'Delete' on your keyboard.")
    edited_nm = st.data_editor(nm_df, num_rows="dynamic", use_container_width=True, 
                               column_config={
                                   "Perkara": st.column_config.TextColumn("Perkara", width="medium"),
                                   "Keterangan": st.column_config.TextColumn("Keterangan", width="large"),
                                   "Keputusan": st.column_config.TextColumn("Keputusan", width="medium")
                               }, key="nm_editor_stable") 
    
    # 3. Save back to session state via Sync button
    if st.button("🔄 Sync New Matters"):
        st.session_state.mom_data["NewMatters"] = edited_nm.to_dict('records')
        st.success("New Matters updated in session!")
    
    st.subheader("Final Remarks")
    st.session_state.mom_data["Closing"] = st.text_area("Closing Remarks", st.session_state.mom_data.get("Closing", ""))
    st.session_state.mom_data["Annex"] = st.text_area("Annex (Kembaran) - Paste Markdown Tables", 
                                                    st.session_state.mom_data.get("Annex", ""),
                                                    height=200,
                                                    help="Paste markdown tables that should appear as annexes.")

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
