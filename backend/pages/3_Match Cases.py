

import streamlit as st

from pages.helper import db_queries, match_algo, train_model


def case_viewer(registered_case_id, public_case_id):
    """
    Show basic details of the registered case and mark it as 'Found'
    when a match is confirmed.
    """
    try:
        case_details = db_queries.get_registered_case_detail(registered_case_id)[0]
        data_col, image_col = st.columns(2)

        for label, value in zip(
            ["Name", "Contact", "Age", "Last Seen", "Birth marks"], case_details
        ):
            data_col.write(f"**{label}:** {value}")

        # Update status in DB
        db_queries.update_found_status(registered_case_id, public_case_id)
        st.success(
            "Case status updated to 'Found'. It will now appear under found cases."
        )

        try:
            image_col.image(
                "./resources/" + registered_case_id + ".jpg",
                width=80,
                use_container_width=False,
            )
        except Exception:
            image_col.warning("Could not load image for this case.")

    except Exception as e:
        st.error(f"Something went wrong while processing this match: {str(e)}")


if "login_status" not in st.session_state or not st.session_state["login_status"]:
    st.write("You need to be logged in as admin to use this page.")
else:
    user = st.session_state.user

    st.title("Run Face Matching (Reunite AI)")

    col1, _ = st.columns(2)
    refresh_bt = col1.button("Refresh & Run Matching")
    st.write("---")

    if refresh_bt:
        with st.spinner("Preparing data and training model..."):
            result = train_model.train(user)

        with st.spinner("Searching for possible matches..."):
            matched_ids = match_algo.match()

        if not matched_ids["status"]:
            st.info(matched_ids.get("message", "No match result available."))
        else:
            if not matched_ids["result"]:
                st.info("No potential matches found at the moment.")
            else:
                for matched_id, submitted_case_id in matched_ids["result"].items():
                    case_viewer(matched_id, submitted_case_id[0])
                    st.write("---")
