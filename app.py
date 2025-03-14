import streamlit as st
import pandas as pd
import io
import os

# Secure Password Option (set password in Render environment variables)
PASSWORD = os.getenv("APP_PASSWORD", "1974")

# Session state to track login status
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Login form
if not st.session_state.logged_in:
    st.title("Login Required")
    user_password = st.text_input("Enter Password:", type="password")
    if st.button("Login"):
        if user_password == PASSWORD:
            st.session_state.logged_in = True
            st.rerun()  # ✅ Fixed: Use st.rerun() instead of st.experimental_rerun()
        else:
            st.error("Incorrect password. Please try again.")

# Show app only if logged in
if st.session_state.logged_in:
    # Country options and replacements
    country_options = {
        "Brazil": "Brazil",
        "Chile": "Chile",
        "Mexico": "Mexico",
        "Colombia": "Colombia",
        "Argentina": "Argentina"
    }

    # Streamlit UI
    st.title("Approval & Assignment Impex Generator")

    # Country selection dropdown
    selected_country = st.selectbox("Select Country:", list(country_options.keys()))

    # File Uploaders with Instructions
    st.subheader("Upload Product Data File (TXT)")
    st.write("📌 **Instructions:** Add the most recently downloaded datafeed from your country. "
             "Filter out archived products. Filter only for bikes in the column **PRODUCT_TYPE**. "
             "Load a **TXT File** type.")
    product_data_file = st.file_uploader("Choose a TXT file", type="txt")

    st.subheader("Upload MASTER DATAFEED (Excel)")
    st.write("📌 **Instructions:** Add a **USA recent Datafeed** for comparison. "
             "Only keep up to column **AG** and filter for **PRODUCT_TYPE** equals **BIKE**.")
    master_data_file = st.file_uploader("Choose an Excel file", type=["xls", "xlsx"])

    # Use session state to keep files available after processing
    if "approval_impex_content" not in st.session_state:
        st.session_state.approval_impex_content = None
    if "assignment_impex_content" not in st.session_state:
        st.session_state.assignment_impex_content = None

    def process_files(product_data_file, master_data_file, country):
        product_data = pd.read_csv(product_data_file, sep="\t")
        master_data = pd.read_excel(master_data_file)

        eligible_products = product_data[
            (product_data["BASE_APPROVED"] == True) &
            (product_data["COLOR_APPROVED"] == True) &
            (product_data["SKU_APPROVED"] == True) &
            (product_data["ECOM_ENABLED"] == True)
        ]

        eligible_color_ids = eligible_products["COLOR_ID"].unique()
        approved_products = product_data[product_data["COLOR_ID"].isin(eligible_color_ids)]
        additional_pids = master_data[master_data["COLOR_ID"].isin(eligible_color_ids)]

        approval_impex = pd.DataFrame({
            "SKU": pd.concat([approved_products["PID"], additional_pids["PID"]], ignore_index=True),
            "Base Product ID": pd.concat([approved_products["MPL_PRODUCT_ID"], additional_pids["MPL_PRODUCT_ID"]], ignore_index=True),
            "CATALOG_VERSION": f"SBC{country}ProductCatalog",
            "APPROVAL_STATUS": "approved"
        }).drop_duplicates()

        assignment_impex = additional_pids[["PID"]].rename(columns={"PID": "SKU"})
        assignment_impex["STOREFRONT_CODE"] = f"SBC{country}"

        # Convert to pipe-separated format for download
        approval_impex_output = io.StringIO()
        approval_impex.to_csv(approval_impex_output, sep="|", index=False)
        approval_impex_content = approval_impex_output.getvalue()

        assignment_impex_output = io.StringIO()
        assignment_impex.to_csv(assignment_impex_output, sep="|", index=False)
        assignment_impex_content = assignment_impex_output.getvalue()

        return approval_impex_content, assignment_impex_content

    if st.button("Generate Impex Files"):
        if product_data_file and master_data_file:
            approval_impex_content, assignment_impex_content = process_files(
                product_data_file, master_data_file, country_options[selected_country]
            )

            # Store files in session state
            st.session_state.approval_impex_content = approval_impex_content
            st.session_state.assignment_impex_content = assignment_impex_content

            st.success(f"Files have been generated for {selected_country}! Download below.")

    # Show download buttons only if files exist in session state
    if st.session_state.approval_impex_content:
        st.download_button(
            "Download Approval Impex",
            st.session_state.approval_impex_content,
            "Approval_Impex.txt",
            "text/plain"
        )

    if st.session_state.assignment_impex_content:
        st.download_button(
            "Download Assignment Impex",
            st.session_state.assignment_impex_content,
            "Assignment_Impex.txt",
            "text/plain"
        )
