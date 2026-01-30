import streamlit as st

st.set_page_config(page_title="Reunite AI – Help")

st.title("Help & Documentation")

st.markdown("""
## How Reunite AI Works

Reunite AI uses **facial recognition technology** to help find missing persons by matching 
registered cases with public sightings.

---

### For Administrators

#### Register New Case
1. Upload a clear, frontal photo of the missing person
2. Fill in the person's details (name, age, last seen location, etc.)
3. The system extracts facial features automatically
4. Click "Save Case" to register

#### View All Cases
- View all your registered cases
- Filter by status (Found / Not Found)
- Select and delete multiple cases
- See matched public sightings

#### Run Matching
- Click "Refresh & Run Matching" to find matches
- The system compares all public sightings against registered cases
- Matches are shown with confidence levels
- Confirm matches to update case status

---

### For Public Users (Mobile App)

#### Browse Missing People
- View all currently missing persons
- See photos and details

#### Submit a Sighting
1. Take or upload a photo of someone you think might be missing
2. Enter the location where you saw them
3. Provide your contact details
4. Submit the report

**Tips for better matching:**
- Get as clear a photo as possible
- Front-facing photos work best
- Even distant photos can work - the system is designed to handle them

#### Check Sighting Status
- Use your reference ID to check if your sighting matched any registered case

---

### Technical Notes
- **Face Recognition**: Uses advanced AI to create a 128-dimensional "fingerprint" of each face
- **Matching Tolerance**: The system allows for some variation in angles, lighting, and distance
- **Privacy**: Photos are stored securely and only used for matching purposes

---

### Contact Support
For technical issues or questions, contact: admin@reuniteai.demo
""")