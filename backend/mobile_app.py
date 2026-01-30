import requests
import streamlit as st

# Helper for API calls
API_BASE_URL = "http://localhost:8000"

def get_api_url(path):
    return f"{API_BASE_URL}{path}"

st.set_page_config(
    page_title="Reunite AI – Public Portal",
    initial_sidebar_state="collapsed",
)
st.title("Reunite AI – Public Portal")
def show_not_found_cases():
    """Public view: list all currently 'Not Found' registered cases."""
    st.subheader("Currently Missing People")
    # TODO: Migrate to API call if needed, but direct DB read for browsing is okay for now
    # to minimize changes. Focusing on WRITES first.
    from pages.helper import db_queries
    cases = db_queries.fetch_all_not_found_registered_cases()
    if not cases:
        st.info("There are no open cases at the moment.")
        return
    for case in cases:
        case = list(case)
        case_id = str(case.pop(0))
        name, age, status, last_seen, birth_marks = case
        info_col, image_col = st.columns([2, 1])
        info_col.write(f"**Name:** {name}")
        info_col.write(f"**Age:** {age}")
        info_col.write(f"**Last seen:** {last_seen}")
        info_col.write(f"**Birth marks / identifiers:** {birth_marks}")
        info_col.write(f"**Status:** {'Not Found' if status == 'NF' else 'Found'}")
        info_col.caption(f"Case ID: {case_id}")
        try:
            image_col.image(
                "./resources/" + case_id + ".jpg",
                caption="Registered photo",
                use_container_width=True,
            )
        except Exception:
            image_col.warning("No photo available.")
        st.write("---")
def show_submit_sighting():
    """Public view: submit a new sighting."""
    st.subheader("Submit a Sighting")
    
    st.info(
        "📸 **Tip for better matching:** Try to get a clear photo of the person's face. "
        "The system can match faces even from a distance, but clearer photos work better."
    )
    image_col, form_col = st.columns(2)
    image_obj = None

    with image_col:
        image_obj = st.file_uploader(
            "Upload a photo of the person you saw",
            type=["jpg", "jpeg", "png"],
            key="user_submission",
        )
        if image_obj:
            st.image(image_obj, width=220)

    if image_obj:
        with form_col.form(key="new_user_submission"):
            location = st.text_input("Where did you see this person?")
            mobile = st.text_input("Your mobile number")
            birth_marks = st.text_input("Any visible marks / details?")
            submitted_by = st.text_input("Your name (optional)")
            email = st.text_input("Your email (optional)")
            
            submit_bt = st.form_submit_button("Send Report")
            
            if submit_bt:
                if not location or not mobile:
                    st.error("Location and Mobile number are required.")
                else:
                    with st.spinner("Submitting report and analyzing image..."):
                        try:
                            # Prepare form data
                            files = {"photo": ("photo.jpg", image_obj.getvalue(), "image/jpeg")}
                            data = {
                                "location": location,
                                "mobile": mobile,
                                "birth_marks": birth_marks,
                                "submitted_by": submitted_by if submitted_by else "Anonymous",
                                "email": email,
                            }
                            
                            # Call API
                            response = requests.post(get_api_url("/api/v1/public"), data=data, files=files)
                            
                            if response.status_code == 200:
                                result = response.json()
                                st.success("Thank you. Your report has been recorded.")
                                st.info(f"Report ID: **{result['id']}**\nPlease save this ID.")
                            elif response.status_code == 400:
                                st.error(f"Error: {response.json().get('detail', 'Bad Request')}")
                            else:
                                st.error(f"Server Error: {response.status_code}")
                                
                        except Exception as e:
                            st.error(f"Connection failed: {e}")
def show_check_sighting_status():
    """Public view: check status of a previously submitted sighting."""
    st.subheader("Check Sighting Status")
    sighting_id = st.text_input(
        "Enter your sighting reference ID",
        help="This ID was shown to you right after submitting your report.",
    )
    if st.button("Check status"):
        if not sighting_id:
            st.warning("Please enter a valid reference ID.")
            return
        # Use helper for getting basic status from DB (or migrate to API status check later)
        from pages.helper import db_queries
        submission = db_queries.get_public_submission_basic(sighting_id)
        if not submission:
            st.error("No report found with that reference ID.")
            return
        sid, status, location, birth_marks, submitted_on = submission
        status_text = "Not Found / Under review" if status == "NF" else "Matched / Found"
        st.write(f"**Report ID:** {sid}")
        st.write(f"**Status:** {status_text}")
        st.write(f"**Reported location:** {location}")
        st.write(f"**Details:** {birth_marks}")
        st.write(f"**Submitted on:** {submitted_on}")
        if status == "F":
            from pages.helper import db_queries
            matched_case = db_queries.get_matched_registered_case_for_public_id(sighting_id)
            if matched_case:
                case_id, name, age, last_seen, case_birth_marks = matched_case
                st.write("---")
                st.write("### Matched with registered case")
                st.write(f"**Case ID:** {case_id}")
                st.write(f"**Name:** {name}")
                st.write(f"**Age:** {age}")
                st.write(f"**Last seen:** {last_seen}")
                st.write(f"**Birth marks / identifiers:** {case_birth_marks}")
                try:
                    st.image(
                        "./resources/" + case_id + ".jpg",
                        caption="Registered case photo",
                        width=200,
                        use_container_width=False,
                    )
                except Exception:
                    st.warning("Could not load registered case photo.")
            else:
                st.info(
                    "This report has been marked as 'Found', but no linked "
                    "registered case was located in the system."
                )
# --------- Main navigation for public user ---------
page = st.sidebar.radio(
    "What would you like to do?",
    [
        "Browse missing people",
        "Submit a sighting",
        "Check my sighting status",
    ],
)
if page == "Browse missing people":
    show_not_found_cases()
elif page == "Submit a sighting":
    show_submit_sighting()
elif page == "Check my sighting status":
    show_check_sighting_status()