import streamlit as st
import PyPDF2
import re
import zipfile
from io import BytesIO
import pandas as pd

st.set_page_config(page_title="PDF Vehicle Renamer", layout="wide")

st.title("🚗 Bulk PDF Renamer (Vehicle Number)")
st.write("Upload PDFs → Auto Rename → Download ZIP")

# ---------------------------
# Clear Button
# ---------------------------
if st.button("🔄 Clear All"):
    st.session_state.clear()
    st.rerun()

# ---------------------------
# File Upload
# ---------------------------
uploaded_files = st.file_uploader(
    "📂 Drag & Drop or Upload PDFs",
    type=["pdf"],
    accept_multiple_files=True
)

# ---------------------------
# Regex Function
# ---------------------------
def extract_vehicle_number(text):
    pattern = r"[A-Z]{2}[\s-]?\d{1,2}[\s-]?[A-Z]{1,3}[\s-]?\d{1,4}"
    match = re.search(pattern, text)
    if match:
        return re.sub(r"[\s-]", "", match.group())
    return None

# ---------------------------
# Main Processing
# ---------------------------
if uploaded_files:

    st.success(f"✅ {len(uploaded_files)} files uploaded")

    progress = st.progress(0)

    zip_buffer = BytesIO()
    preview_data = []
    errors = []
    used_names = set()

    with zipfile.ZipFile(zip_buffer, "w") as zip_file:

        for i, file in enumerate(uploaded_files):

            try:
                # ---------------------------
                # File size validation (5MB)
                # ---------------------------
                if file.size > 5 * 1024 * 1024:
                    errors.append((file.name, "File too large (>5MB)"))
                    continue

                pdf_reader = PyPDF2.PdfReader(file)
                text = ""

                for page in pdf_reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted

                # ---------------------------
                # Detect scanned PDF
                # ---------------------------
                if not text.strip():
                    errors.append((file.name, "No text found (Scanned PDF?)"))
                    continue

                vehicle_no = extract_vehicle_number(text)

                if vehicle_no:
                    new_name = f"{vehicle_no}.pdf"
                else:
                    new_name = f"NOT_FOUND_{i}.pdf"

                # ---------------------------
                # Handle duplicates
                # ---------------------------
                if new_name in used_names:
                    new_name = f"{vehicle_no}_{i}.pdf"

                used_names.add(new_name)

                # ---------------------------
                # FIX: Reset pointer
                # ---------------------------
                file_bytes = file.getvalue()

                zip_file.writestr(new_name, file_bytes)

                preview_data.append((file.name, new_name))

            except Exception as e:
                errors.append((file.name, str(e)))

            # ---------------------------
            # Progress update
            # ---------------------------
            progress.progress((i + 1) / len(uploaded_files))

    st.success("🎉 Processing Complete!")

    # ---------------------------
    # Preview Section
    # ---------------------------
    st.subheader("📋 Rename Preview")
    preview_df = pd.DataFrame(preview_data, columns=["Original Name", "Renamed To"])
    st.dataframe(preview_df, use_container_width=True)

    # ---------------------------
    # Download ZIP
    # ---------------------------
    st.download_button(
        label="⬇️ Download All Renamed PDFs (ZIP)",
        data=zip_buffer.getvalue(),
        file_name="Renamed_PDFs.zip",
        mime="application/zip"
    )

    # ---------------------------
    # Download Report
    # ---------------------------
    st.download_button(
        label="📊 Download CSV Report",
        data=preview_df.to_csv(index=False),
        file_name="Rename_Report.csv",
        mime="text/csv"
    )

    # ---------------------------
    # Error Display
    # ---------------------------
    if errors:
        st.error("⚠️ Some files could not be processed")
        error_df = pd.DataFrame(errors, columns=["File Name", "Issue"])
        st.dataframe(error_df, use_container_width=True)