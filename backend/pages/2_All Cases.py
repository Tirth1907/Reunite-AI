

import os
import streamlit as st
from pages.helper import db_queries


st.set_page_config(page_title="Reunite AI – All Cases")


def delete_case_with_image(case_id: str, is_public: bool = False):
    """Delete a case and its associated image file."""
    # Delete from database
    if is_public:
        db_queries.delete_public_case(case_id)
    else:
        db_queries.delete_registered_case(case_id)
    
    # Delete associated image
    image_path = f"./resources/{case_id}.jpg"
    if os.path.exists(image_path):
        try:
            os.remove(image_path)
        except OSError as e:
            st.warning(f"Could not delete image file: {e}")


def case_viewer(case, selected_cases: set):
    """
    Display a single registered case with checkbox for selection.
    """
    case = list(case)
    case_id = str(case.pop(0))
    matched_with_id = case.pop(4)
    phone = case.pop()
    matched_with_details = None

    if matched_with_id:
        try:
            matched_with_id = str(matched_with_id).replace("{", "").replace("}", "")
        except Exception:
            matched_with_id = None

    if matched_with_id:
        matched_with_details = db_queries.get_public_case_detail(matched_with_id)

    # Checkbox for selection
    col_check, data_col, image_col, action_col = st.columns([0.5, 2, 1.5, 2])
    
    is_selected = col_check.checkbox("", key=f"select_{case_id}", value=case_id in selected_cases)
    if is_selected:
        selected_cases.add(case_id)
    elif case_id in selected_cases:
        selected_cases.discard(case_id)

    for label, value in zip(["Name", "Age", "Status", "Last Seen"], case):
        if label == "Status":
            value = "Found" if value == "F" else "Not Found"
        data_col.write(f"**{label}:** {value}")
    data_col.write(f"**Contact:** {phone}")

    try:
        image_col.image(
            "./resources/" + case_id + ".jpg",
            width=120,
            use_container_width=False,
        )
    except Exception:
        image_col.warning("No image available.")

    if matched_with_details:
        loc, submitted_by, mobile, birth_marks = matched_with_details[0]
        action_col.write("**Matched public report:**")
        action_col.write(f"- Location: {loc}")
        action_col.write(f"- Submitted by: {submitted_by}")
        action_col.write(f"- Mobile: {mobile}")
        action_col.write(f"- Birth marks: {birth_marks}")

    if action_col.button("Delete", key=f"delete_{case_id}"):
        delete_case_with_image(case_id, is_public=False)
        st.success("Case deleted.")
        st.rerun()

    st.write("---")
    
    return is_selected


def public_case_viewer(case: list, selected_public_cases: set) -> None:
    """Display a public submission in the admin view with delete option."""
    case = list(case)
    case_id = str(case.pop(0))

    # Checkbox for selection
    col_check, data_col, image_col, action_col = st.columns([0.5, 2, 1.5, 2])
    
    is_selected = col_check.checkbox("", key=f"select_pub_{case_id}", value=case_id in selected_public_cases)
    if is_selected:
        selected_public_cases.add(case_id)
    elif case_id in selected_public_cases:
        selected_public_cases.discard(case_id)
    
    for text, value in zip(
        ["Status", "Location", "Mobile", "Birth Marks", "Submitted on", "Submitted by"],
        case,
    ):
        if text == "Status":
            value = "Found" if value == "F" else "Not Found"
        data_col.write(f"**{text}:** {value}")

    try:
        image_col.image(
            "./resources/" + case_id + ".jpg",
            width=120,
            use_container_width=False,
        )
    except Exception:
        image_col.warning("Couldn't load image for this submission.")

    # Add delete button for public submissions
    if action_col.button("Delete", key=f"delete_pub_{case_id}"):
        delete_case_with_image(case_id, is_public=True)
        st.success("Public submission deleted.")
        st.rerun()

    st.write("---")


# Initialize session state for selected cases
if "selected_cases" not in st.session_state:
    st.session_state.selected_cases = set()

if "selected_public_cases" not in st.session_state:
    st.session_state.selected_public_cases = set()


if "login_status" not in st.session_state or not st.session_state["login_status"]:
    st.write("You need to be logged in as admin to use this page.")
else:
    user = st.session_state.user

    st.title("Your Registered Cases & Public Reports")

    status_col, date_col = st.columns(2)
    status = status_col.selectbox(
        "Show",
        options=["All", "Not Found", "Found", "Public Submissions"],
    )
    _ = date_col.date_input("Filter by date (not applied yet)")

    st.write("---")
    
    # Bulk delete controls for REGISTERED cases
    if status != "Public Submissions":
        bulk_col1, bulk_col2, bulk_col3 = st.columns([1, 1, 2])
        
        if bulk_col1.button("Select All"):
            cases_data = db_queries.fetch_registered_cases(user, status)
            st.session_state.selected_cases = {str(case[0]) for case in cases_data}
            st.rerun()
        
        if bulk_col2.button("Clear Selection"):
            st.session_state.selected_cases = set()
            st.rerun()
        
        if st.session_state.selected_cases:
            bulk_col3.warning(f"{len(st.session_state.selected_cases)} case(s) selected")
            if bulk_col3.button("🗑️ Delete Selected", type="primary"):
                for case_id in list(st.session_state.selected_cases):
                    delete_case_with_image(case_id, is_public=False)
                st.session_state.selected_cases = set()
                st.success("Selected cases deleted!")
                st.rerun()
        
        st.write("---")
        
        cases_data = db_queries.fetch_registered_cases(user, status)
        for case in cases_data:
            case_viewer(case, st.session_state.selected_cases)
    
    # Bulk delete controls for PUBLIC SUBMISSIONS
    else:
        bulk_col1, bulk_col2, bulk_col3 = st.columns([1, 1, 2])
        
        if bulk_col1.button("Select All"):
            cases_data = db_queries.fetch_public_cases(False, status="NF")
            st.session_state.selected_public_cases = {str(case[0]) for case in cases_data}
            st.rerun()
        
        if bulk_col2.button("Clear Selection"):
            st.session_state.selected_public_cases = set()
            st.rerun()
        
        if st.session_state.selected_public_cases:
            bulk_col3.warning(f"{len(st.session_state.selected_public_cases)} submission(s) selected")
            if bulk_col3.button("🗑️ Delete Selected", type="primary"):
                for case_id in list(st.session_state.selected_public_cases):
                    delete_case_with_image(case_id, is_public=True)
                st.session_state.selected_public_cases = set()
                st.success("Selected public submissions deleted!")
                st.rerun()
        
        st.write("---")
        
        cases_data = db_queries.fetch_public_cases(False, status="NF")
        for case in cases_data:
            public_case_viewer(case, st.session_state.selected_public_cases)
