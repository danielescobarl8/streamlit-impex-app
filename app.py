import streamlit as st
import pandas as pd
import io

def process_files(product_data_file, master_data_file):
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
        "CATALOG_VERSION": "SBCColombiaProductCatalog",
        "APPROVAL_STATUS": "approved"
    }).drop_duplicates()

    assignment_impex = additional_pids[["PID"]].rename(columns={"PID": "SKU"})
    assignment_impex["STOREFRONT_CODE"] = "SBCColombia"

    approval_impex_output = io.StringIO()
    approval_impex.to_csv(approval_impex_output, sep="|", index=False)
    approval_impex_content = approval_impex_output.getvalue()

    assignment_impex_output = io.StringIO()
    assignment_impex.to_csv(assignment_impex_output, sep="|", index=False)
    assignment_impex_content = assignment_impex_output.getvalue()

    return approval_impex_content, assignment_impex_content

st.title("Approval & Assignment Impex Generator")
product_data_file = st.file_uploader("Upload Product Data File (TXT)", type="txt")
master_data_file = st.file_uploader("Upload MASTER DATAFEED (Excel)", type=["xls", "xlsx"])

if st.button("Generate Impex Files"):
    if product_data_file and master_data_file:
        approval_impex_content, assignment_impex_content = process_files(product_data_file, master_data_file)
        st.download_button("Download Approval Impex", approval_impex_content, "Approval_Impex.txt", "text/plain")
        st.download_button("Download Assignment Impex", assignment_impex_content, "Assignment_Impex.txt", "text/plain")
    else:
        st.error("Please upload both files before processing.")
