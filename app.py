import streamlit as st
import os
import tempfile
import base64
from generate_mom import generate_mom
from generate_mom_reportlab import MOMReportLab


st.set_page_config(page_title="MOM Generator", layout="wide")

st.title("Minutes of Meeting (MOM) Generator")

# Create two columns
col_left, col_right = st.columns([1, 2])

with col_left:
    st.header("Input")
    uploaded_file = st.file_uploader("Upload MOM JSON data", type=["json"])
    
    format_options = {
        "PDF (ReportLab)": "reportlab",
        "PDF (Typst)": "typst",
        "PDF (LaTeX)": "pdf",
        "Word (DOCX)": "docx"
    }

    selected_format_label = st.radio("Output Format", list(format_options.keys()))
    output_format = format_options[selected_format_label]
    
    generate_btn = st.button("Generate MOM")

with col_right:
    st.header("Output View")
    
    if uploaded_file is not None and generate_btn:
        # Save uploaded file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        try:
            with st.spinner(f"Generating {selected_format_label}..."):
                # Map internal format to file extension
                ext = "pdf" if output_format in ["pdf", "typst", "reportlab"] else "docx"
                output_filename = tempfile.mktemp(suffix="." + ext)
                
                if output_format == "reportlab":
                    mom = MOMReportLab(tmp_path, output_filename)
                    mom.create_pdf()
                    # Mock a result object for compatibility with existing check
                    class MockResult:
                        def __init__(self, returncode):
                            self.returncode = returncode
                            self.stdout = ""
                            self.stderr = ""
                    result = MockResult(0)
                else:
                    result = generate_mom(tmp_path, output_format, output_filename)

            
            if result.returncode == 0 and os.path.exists(output_filename):
                st.success(f"Generated {selected_format_label} successfully!")
                
                with open(output_filename, "rb") as f:
                    file_data = f.read()
                
                if ext == "pdf":
                    # Display PDF preview
                    base64_pdf = base64.b64encode(file_data).decode('utf-8')
                    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
                    st.markdown(pdf_display, unsafe_allow_html=True)
                else:
                    st.info("Word document generated. You can download it below.")
                
                st.download_button(
                    label=f"Download {selected_format_label}",
                    data=file_data,
                    file_name=f"MOM.{ext}",
                    mime="application/pdf" if ext == "pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                
                # Cleanup
                if os.path.exists(output_filename):
                    os.remove(output_filename)
            else:
                st.error(f"Failed to generate {output_format.upper()}.")
                with st.expander("Show Detailed Error Output"):
                    st.code(result.stdout + "\n" + result.stderr)
        
        except Exception as e:
            st.error(f"An error occurred: {e}")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    else:
        st.info("Upload a JSON file and click 'Generate MOM' to see the result.")
