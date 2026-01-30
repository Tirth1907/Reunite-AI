import uuid
import json
import base64
import numpy as np
import streamlit as st
from pages.helper.data_models import RegisteredCases
from pages.helper import db_queries
from pages.helper.utils import image_obj_to_numpy, extract_face_encoding
st.set_page_config(page_title="Reunite AI – New Case")
def image_to_base64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")
if "login_status" not in st.session_state or not st.session_state["login_status"]:
    st.write("You need to be logged in as admin to use this page.")
else:
    user = st.session_state.user
    st.title("Create a New Missing Person Record")
    image_col, form_col = st.columns(2)
    image_obj = None
    save_flag = False
    face_encoding = None
    unique_id = None
    with image_col:
        image_obj = st.file_uploader(
            "Upload a clear face photo",
            type=["jpg", "jpeg", "png"],
            key="new_case",
        )
        if image_obj:
            unique_id = str(uuid.uuid4())
            uploaded_file_path = "./resources/" + unique_id + ".jpg"
            with open(uploaded_file_path, "wb") as output_temporary_file:
                output_temporary_file.write(image_obj.read())
            st.image(image_obj, caption="Uploaded image preview")
            with st.spinner("Extracting facial features..."):
                image_numpy = image_obj_to_numpy(image_obj)
                face_encoding = extract_face_encoding(image_numpy)
    if image_obj and face_encoding:
        with form_col.form(key="new_case_form"):
            st.subheader("Basic Information")
            name = st.text_input("Full Name")
            father_name = st.text_input("Father's Name (optional)")
            age = st.number_input("Age", min_value=1, max_value=120, value=10, step=1)
            st.subheader("Contact & Case Details")
            mobile_number = st.text_input("Contact Number of Complainant")
            address = st.text_input("Address")
            adhaar_card = st.text_input("ID Document Number (e.g., Aadhaar)")
            birthmarks = st.text_input("Visible Birth Marks / Identifying Features")
            last_seen = st.text_input("Last Seen Location / Area")
            description = st.text_area("Additional Description (optional)")
            complainant_name = st.text_input("Complainant Name")
            complainant_phone = st.text_input("Complainant Phone Number")
            submit_bt = st.form_submit_button("Save Case")
            # Ensure optional fields have default values (not None)
            new_case_details = RegisteredCases(
                id=unique_id,
                submitted_by=user,
                name=name if name else "Unknown",
                father_name=father_name if father_name else "",
                age=str(age),
                complainant_mobile=mobile_number if mobile_number else "",
                complainant_name=complainant_name if complainant_name else "",
                face_mesh=json.dumps(face_encoding),  # 128-D encoding
                adhaar_card=adhaar_card if adhaar_card else "",
                birth_marks=birthmarks if birthmarks else "",
                address=address if address else "",
                last_seen=last_seen if last_seen else "",
                status="NF",
                matched_with="",
            )
            if submit_bt:
                db_queries.register_new_case(new_case_details)
                save_flag = True
        if save_flag:
            st.success("New case has been saved in Reunite AI.")
    elif image_obj and not face_encoding:
        st.warning(
            "No face was detected in the uploaded image. "
            "Please upload a clearer frontal photo."
        )