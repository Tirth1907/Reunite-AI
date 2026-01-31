
from sqlmodel import create_engine, Session, select

from pages.helper.data_models import RegisteredCases, PublicSubmissions

sqlite_url = "sqlite:///sqlite_database.db"
engine = create_engine(sqlite_url)



import logging
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_db():
    """Create tables if they do not already exist."""
    try:
        RegisteredCases.__table__.create(engine)
        PublicSubmissions.__table__.create(engine)
    except Exception:
        # Tables already exist – ignore
        pass


def register_new_case(case_details: RegisteredCases):
    """Insert a new registered case."""
    # create_db()
    with Session(engine) as session:
        session.add(case_details)
        session.commit()


def fetch_registered_cases(submitted_by: str, status: str):
    """
    Fetch registered cases for a particular admin user, filtered by status.
    Status: "All" | "Found" | "Not Found"
    """
    if status == "All":
        status_list = ["F", "NF"]
    elif status == "Found":
        status_list = ["F"]
    elif status == "Not Found":
        status_list = ["NF"]
    else:
        status_list = ["F", "NF"]

    # create_db()
    with Session(engine) as session:
        result = session.exec(
            select(
                RegisteredCases.id,
                RegisteredCases.name,
                RegisteredCases.age,
                RegisteredCases.status,
                RegisteredCases.last_seen,
                RegisteredCases.matched_with,
                RegisteredCases.complainant_mobile,
                RegisteredCases.birth_marks,
                RegisteredCases.father_name,
                RegisteredCases.address,
                RegisteredCases.complainant_name,
                RegisteredCases.submitted_on,
            )
            .where(RegisteredCases.submitted_by == submitted_by)
            .where(RegisteredCases.status.in_(status_list))
            .order_by(RegisteredCases.submitted_on.desc())
        ).all()
        return result


def fetch_all_not_found_registered_cases():
    """
    Fetch ALL registered cases across all admins where status is 'NF'.

    Used in the PUBLIC app to list all currently missing people.
    """
    # create_db()
    with Session(engine) as session:
        result = session.exec(
            select(
                RegisteredCases.id,
                RegisteredCases.name,
                RegisteredCases.age,
                RegisteredCases.status,
                RegisteredCases.last_seen,
                RegisteredCases.birth_marks,
                RegisteredCases.father_name,
                RegisteredCases.address,
                RegisteredCases.complainant_name,
                RegisteredCases.complainant_mobile,
                RegisteredCases.submitted_on,
            )
            .where(RegisteredCases.status == "NF")
            .order_by(RegisteredCases.submitted_on.desc())
        ).all()
        return result


def fetch_all_registered_cases():
    """
    Fetch ALL registered cases across all admins (both Found and Not Found).
    
    Used in web app to list all cases regardless of status.
    """
    # create_db()
    with Session(engine) as session:
        result = session.exec(
            select(
                RegisteredCases.id,
                RegisteredCases.name,
                RegisteredCases.age,
                RegisteredCases.status,
                RegisteredCases.last_seen,
                RegisteredCases.birth_marks,
                RegisteredCases.father_name,
                RegisteredCases.address,
                RegisteredCases.complainant_name,
                RegisteredCases.complainant_mobile,
                RegisteredCases.submitted_on,
            )
            .order_by(RegisteredCases.submitted_on.desc())
        ).all()
        return result


def fetch_public_cases(train_data: bool, status: str):
    """
    Fetch public submissions.

    If train_data=True, returns only ID + face_mesh (for model/matching).
    Otherwise returns details for admin view.
    """
    # create_db()
    if train_data:
        with Session(engine) as session:
            query = select(PublicSubmissions.id, PublicSubmissions.face_mesh)
            if status != "All":
                query = query.where(PublicSubmissions.status == status)
            
            result = session.exec(query).all()
            return result

    with Session(engine) as session:
        query = select(
            PublicSubmissions.id,
            PublicSubmissions.status,
            PublicSubmissions.location,
            PublicSubmissions.mobile,
            PublicSubmissions.birth_marks,
            PublicSubmissions.submitted_on,
            PublicSubmissions.submitted_by,
        )
        if status != "All":
            query = query.where(PublicSubmissions.status == status)
            
        result = session.exec(
            query.order_by(PublicSubmissions.submitted_on.desc())
        ).all()
        return result


def get_not_confirmed_registered_cases(submitted_by: str):
    """
    Returns all registered cases for the given admin.
    Used for model training where only 'NF' might be required.
    """
    # create_db()
    with Session(engine) as session:
        result = session.exec(
            select(RegisteredCases).where(RegisteredCases.submitted_by == submitted_by)
        ).all()
        return result


def get_training_data(submitted_by: str):
    """Return IDs and face_mesh for 'NF' cases submitted by a specific admin."""
    # create_db()
    with Session(engine) as session:
        result = session.exec(
            select(RegisteredCases.id, RegisteredCases.face_mesh)
            .where(RegisteredCases.submitted_by == submitted_by)
            .where(RegisteredCases.status == "NF")
        ).all()
        return result


def new_public_case(public_case_details: PublicSubmissions):
    """Insert a new public sighting/submission."""
    # create_db()
    with Session(engine) as session:
        session.add(public_case_details)
        session.commit()


def get_public_case_detail(case_id: str):
    """Return detailed info about a public submission for admin matching view."""
    # create_db()
    with Session(engine) as session:
        result = session.exec(
            select(
                PublicSubmissions.location,
                PublicSubmissions.submitted_by,
                PublicSubmissions.mobile,
                PublicSubmissions.birth_marks,
            ).where(PublicSubmissions.id == case_id)
        ).all()
        return result


def get_public_submission_basic(case_id: str):
    """
    Return basic info + status of a public submission.

    Used in public app 'Check my submission'.
    """
    # create_db()
    with Session(engine) as session:
        return session.exec(
            select(
                PublicSubmissions.id,
                PublicSubmissions.status,
                PublicSubmissions.location,
                PublicSubmissions.birth_marks,
                PublicSubmissions.submitted_on,
            ).where(PublicSubmissions.id == case_id)
        ).first()


def get_registered_case_detail(case_id: str):
    """Return key fields of a registered case for display."""
    # create_db()
    with Session(engine) as session:
        result = session.exec(
            select(
                RegisteredCases.name,
                RegisteredCases.complainant_mobile,
                RegisteredCases.age,
                RegisteredCases.last_seen,
                RegisteredCases.birth_marks,
                RegisteredCases.father_name,
                RegisteredCases.address,
                RegisteredCases.complainant_name,
                RegisteredCases.submitted_on,
                RegisteredCases.status,
                RegisteredCases.submitted_by,
            ).where(RegisteredCases.id == case_id)
        ).all()
        return result


def get_matched_registered_case_for_public_id(public_case_id: str):
    """
    Given a public submission ID, find the registered case that was matched with it.
    """
    # create_db()
    with Session(engine) as session:
        return session.exec(
            select(
                RegisteredCases.id,
                RegisteredCases.name,
                RegisteredCases.age,
                RegisteredCases.last_seen,
                RegisteredCases.birth_marks,
            ).where(RegisteredCases.matched_with == str(public_case_id))
        ).first()


def list_public_cases():
    # create_db()
    with Session(engine) as session:
        result = session.exec(select(PublicSubmissions)).all()
        return result


def update_found_status(register_case_id: str, public_case_id: str):
    """
    Mark a registered case and a public submission as 'Found' and link them.
    """
    # create_db()
    with Session(engine) as session:
        registered_case_details = session.exec(
            select(RegisteredCases).where(RegisteredCases.id == str(register_case_id))
        ).one()
        registered_case_details.status = "F"
        registered_case_details.matched_with = str(public_case_id)

        public_case_details = session.exec(
            select(PublicSubmissions).where(PublicSubmissions.id == str(public_case_id))
        ).one()
        public_case_details.status = "F"

        session.add(registered_case_details)
        session.add(public_case_details)
        session.commit()


def update_matched_with(registered_case_id: str, public_case_id: str):
    """
    Update a registered case with the ID of a matching public submission.
    Does NOT change status to 'F' yet, just links them.
    """
    with Session(engine) as session:
        statement = select(RegisteredCases).where(RegisteredCases.id == str(registered_case_id))
        registered_case = session.exec(statement).one_or_none()
        
        if registered_case:
            old_val = registered_case.matched_with
            registered_case.matched_with = str(public_case_id)
            session.add(registered_case)
            session.commit()
            logger.info(f"[VERIFICATION] DB: Updated RegisteredCase {registered_case_id} matched_with: {old_val} -> {public_case_id}")
        else:
            logger.error(f"[VERIFICATION] DB: RegisteredCase {registered_case_id} NOT found for update.")


def get_registered_cases_count(submitted_by: str, status: str):
    # create_db()
    with Session(engine) as session:
        result = session.exec(
            select(RegisteredCases)
            .where(RegisteredCases.submitted_by == submitted_by)
            .where(RegisteredCases.status == status)
        ).all()
        return result


def delete_registered_case(case_id: str):
    """
    Delete a registered case (admin clean-up of unwanted / test entries).
    """
    # create_db()
    with Session(engine) as session:
        case = session.get(RegisteredCases, case_id)
        if case:
            session.delete(case)
            session.commit()


def delete_public_case(case_id: str):
    """
    Delete a public submission (admin clean-up of unwanted / test entries).
    """
    # create_db()
    with Session(engine) as session:
        case = session.get(PublicSubmissions, case_id)
        if case:
            session.delete(case)
            session.commit()