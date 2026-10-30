"""
Class Communication Router
Handles Class Resources, Announcements, and Doubts for Faculty and Students.
Enforces ownership access control, input sanitization, rate limiting, and privacy rules.
"""

from datetime import datetime
from typing import List, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from database import get_db
from models import (
    User, ClassModel, ClassEnrollment, Topic, AgentLog,
    ClassResource, ClassAnnouncement, AnnouncementRead,
    ClassDoubt, ClassDoubtReply
)
from schemas import (
    ClassResourceCreate, ClassResourceOut,
    ClassAnnouncementCreate, ClassAnnouncementOut,
    ClassDoubtCreate, ClassDoubtReplyCreate, ClassDoubtReplyOut, ClassDoubtOut
)
from core.security import require_faculty_or_admin, require_role
from core.rate_limiter import enforce_rate_limit
from core.sanitization import (
    validate_plain_text, validate_url,
    validate_resource_type, validate_doubt_visibility
)

router = APIRouter(tags=["class_communication"])


# ==============================================================================
# Helper Access Checkers
# ==============================================================================

def get_class_for_faculty(db: Session, class_id: int, current_user: User) -> ClassModel:
    """
    Returns ClassModel if faculty owns it (or if user is admin).
    If class doesn't exist, is inactive, or belongs to another faculty -> raises 404 (does not leak existence).
    """
    query = db.query(ClassModel).filter(ClassModel.id == class_id, ClassModel.is_active == True)
    if current_user.role != "admin":
        query = query.filter(ClassModel.faculty_id == current_user.id)
    class_obj = query.first()
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    return class_obj


def get_class_for_student(db: Session, class_id: int, current_user: User) -> Tuple[ClassModel, ClassEnrollment]:
    """
    Returns (ClassModel, ClassEnrollment) if student has an 'active' enrollment in the class.
    If class doesn't exist, student not enrolled, or enrollment is 'left' or 'removed' -> raises 404.
    """
    class_obj = db.query(ClassModel).filter(ClassModel.id == class_id, ClassModel.is_active == True).first()
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )

    enrollment = db.query(ClassEnrollment).filter(
        ClassEnrollment.class_id == class_id,
        ClassEnrollment.student_id == current_user.id,
        ClassEnrollment.status == "active"
    ).first()
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found or enrollment is not active"
        )

    return class_obj, enrollment


# ==============================================================================
# FACULTY CLASS RESOURCES
# ==============================================================================

@router.post("/api/faculty/classes/{class_id}/resources", response_model=ClassResourceOut, status_code=status.HTTP_201_CREATED)
def create_class_resource(
    class_id: int,
    payload: ClassResourceCreate,
    current_user: User = Depends(require_faculty_or_admin),
    db: Session = Depends(get_db)
):
    """Faculty creates a class resource. Rate limit: 30 posts/hr."""
    class_obj = get_class_for_faculty(db, class_id, current_user)
    enforce_rate_limit(
        f"comm:faculty:hr:{current_user.id}",
        limit=30,
        window_seconds=3600,
        detail="Hourly post limit exceeded (max 30 posts per hour). Please try again later."
    )

    clean_title = validate_plain_text(payload.title, max_length=150, field_name="Title", required=True)
    clean_desc = validate_plain_text(payload.description, max_length=2000, field_name="Description", allow_newlines=True, required=False) if payload.description else None
    clean_url = validate_url(payload.url, max_length=500)
    clean_type = validate_resource_type(payload.resource_type)

    topic_title = None
    if payload.topic_id is not None:
        topic = db.query(Topic).filter(Topic.id == payload.topic_id, Topic.course_id == class_obj.course_id).first()
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected topic does not belong to the class course."
            )
        topic_title = topic.title

    resource = ClassResource(
        class_id=class_obj.id,
        created_by=current_user.id,
        title=clean_title,
        description=clean_desc,
        url=clean_url,
        resource_type=clean_type,
        topic_id=payload.topic_id,
        created_at=datetime.utcnow(),
        is_deleted=False
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)

    return ClassResourceOut(
        id=resource.id,
        class_id=resource.class_id,
        created_by=resource.created_by,
        title=resource.title,
        description=resource.description,
        url=resource.url,
        resource_type=resource.resource_type,
        topic_id=resource.topic_id,
        topic_title=topic_title,
        created_at=resource.created_at.isoformat(),
        is_deleted=resource.is_deleted
    )


@router.get("/api/faculty/classes/{class_id}/resources", response_model=List[ClassResourceOut])
def get_faculty_class_resources(
    class_id: int,
    current_user: User = Depends(require_faculty_or_admin),
    db: Session = Depends(get_db)
):
    """Faculty lists all active resources for a class."""
    class_obj = get_class_for_faculty(db, class_id, current_user)
    resources = (
        db.query(ClassResource)
        .filter(ClassResource.class_id == class_obj.id, ClassResource.is_deleted == False)
        .order_by(ClassResource.created_at.desc())
        .all()
    )

    result = []
    for r in resources:
        t_title = r.topic.title if r.topic else None
        result.append(ClassResourceOut(
            id=r.id,
            class_id=r.class_id,
            created_by=r.created_by,
            title=r.title,
            description=r.description,
            url=r.url,
            resource_type=r.resource_type,
            topic_id=r.topic_id,
            topic_title=t_title,
            created_at=r.created_at.isoformat(),
            is_deleted=r.is_deleted
        ))
    return result


@router.delete("/api/faculty/classes/{class_id}/resources/{resource_id}")
def delete_class_resource(
    class_id: int,
    resource_id: int,
    current_user: User = Depends(require_faculty_or_admin),
    db: Session = Depends(get_db)
):
    """Faculty soft-deletes a resource. Audited in AgentLog."""
    class_obj = get_class_for_faculty(db, class_id, current_user)
    resource = (
        db.query(ClassResource)
        .filter(ClassResource.id == resource_id, ClassResource.class_id == class_obj.id, ClassResource.is_deleted == False)
        .first()
    )
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

    resource.is_deleted = True
    db.add(AgentLog(
        user_id=current_user.id,
        agent_name="Faculty Portal",
        action="resource_deleted",
        message=f"Faculty {current_user.id} soft-deleted resource '{resource.title}' (id {resource.id}) in class {class_obj.id}.",
        created_at=datetime.utcnow()
    ))
    db.commit()
    return {"message": "Resource deleted successfully"}


# ==============================================================================
# FACULTY ANNOUNCEMENTS
# ==============================================================================

@router.post("/api/faculty/classes/{class_id}/announcements", response_model=ClassAnnouncementOut, status_code=status.HTTP_201_CREATED)
def create_class_announcement(
    class_id: int,
    payload: ClassAnnouncementCreate,
    current_user: User = Depends(require_faculty_or_admin),
    db: Session = Depends(get_db)
):
    """Faculty posts an announcement. Rate limit: 30 posts/hr."""
    class_obj = get_class_for_faculty(db, class_id, current_user)
    enforce_rate_limit(
        f"comm:faculty:hr:{current_user.id}",
        limit=30,
        window_seconds=3600,
        detail="Hourly post limit exceeded (max 30 posts per hour). Please try again later."
    )

    clean_title = validate_plain_text(payload.title, max_length=150, field_name="Title", required=True)
    clean_body = validate_plain_text(payload.body, max_length=2000, field_name="Body", allow_newlines=True, required=True)

    announcement = ClassAnnouncement(
        class_id=class_obj.id,
        created_by=current_user.id,
        title=clean_title,
        body=clean_body,
        pinned=bool(payload.pinned),
        created_at=datetime.utcnow(),
        is_deleted=False
    )
    db.add(announcement)
    db.commit()
    db.refresh(announcement)

    return ClassAnnouncementOut(
        id=announcement.id,
        class_id=announcement.class_id,
        created_by=announcement.created_by,
        title=announcement.title,
        body=announcement.body,
        pinned=announcement.pinned,
        created_at=announcement.created_at.isoformat()
    )


@router.get("/api/faculty/classes/{class_id}/announcements", response_model=List[ClassAnnouncementOut])
def get_faculty_class_announcements(
    class_id: int,
    current_user: User = Depends(require_faculty_or_admin),
    db: Session = Depends(get_db)
):
    """Faculty lists all active announcements for a class (pinned first, then newest)."""
    class_obj = get_class_for_faculty(db, class_id, current_user)
    announcements = (
        db.query(ClassAnnouncement)
        .filter(ClassAnnouncement.class_id == class_obj.id, ClassAnnouncement.is_deleted == False)
        .order_by(ClassAnnouncement.pinned.desc(), ClassAnnouncement.created_at.desc())
        .all()
    )

    return [
        ClassAnnouncementOut(
            id=a.id,
            class_id=a.class_id,
            created_by=a.created_by,
            title=a.title,
            body=a.body,
            pinned=a.pinned,
            created_at=a.created_at.isoformat()
        )
        for a in announcements
    ]


@router.delete("/api/faculty/classes/{class_id}/announcements/{announcement_id}")
def delete_class_announcement(
    class_id: int,
    announcement_id: int,
    current_user: User = Depends(require_faculty_or_admin),
    db: Session = Depends(get_db)
):
    """Faculty soft-deletes an announcement. Audited in AgentLog."""
    class_obj = get_class_for_faculty(db, class_id, current_user)
    announcement = (
        db.query(ClassAnnouncement)
        .filter(ClassAnnouncement.id == announcement_id, ClassAnnouncement.class_id == class_obj.id, ClassAnnouncement.is_deleted == False)
        .first()
    )
    if not announcement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found")

    announcement.is_deleted = True
    db.add(AgentLog(
        user_id=current_user.id,
        agent_name="Faculty Portal",
        action="announcement_deleted",
        message=f"Faculty {current_user.id} soft-deleted announcement '{announcement.title}' (id {announcement.id}) in class {class_obj.id}.",
        created_at=datetime.utcnow()
    ))
    db.commit()
    return {"message": "Announcement deleted successfully"}


@router.patch("/api/faculty/classes/{class_id}/announcements/{announcement_id}/pin", response_model=ClassAnnouncementOut)
def toggle_pin_announcement(
    class_id: int,
    announcement_id: int,
    current_user: User = Depends(require_faculty_or_admin),
    db: Session = Depends(get_db)
):
    """Faculty toggles pinned status of an announcement."""
    class_obj = get_class_for_faculty(db, class_id, current_user)
    announcement = (
        db.query(ClassAnnouncement)
        .filter(ClassAnnouncement.id == announcement_id, ClassAnnouncement.class_id == class_obj.id, ClassAnnouncement.is_deleted == False)
        .first()
    )
    if not announcement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found")

    announcement.pinned = not announcement.pinned
    db.commit()
    db.refresh(announcement)

    return ClassAnnouncementOut(
        id=announcement.id,
        class_id=announcement.class_id,
        created_by=announcement.created_by,
        title=announcement.title,
        body=announcement.body,
        pinned=announcement.pinned,
        created_at=announcement.created_at.isoformat()
    )


# ==============================================================================
# FACULTY DOUBTS & REPLIES
# ==============================================================================

@router.get("/api/faculty/classes/{class_id}/doubts", response_model=List[ClassDoubtOut])
def get_faculty_class_doubts(
    class_id: int,
    status_filter: Optional[str] = Query(None, alias="status"),
    topic_id: Optional[int] = Query(None),
    current_user: User = Depends(require_faculty_or_admin),
    db: Session = Depends(get_db)
):
    """Faculty views doubts for a class with optional status/topic filters."""
    class_obj = get_class_for_faculty(db, class_id, current_user)
    query = db.query(ClassDoubt).filter(ClassDoubt.class_id == class_obj.id)

    if status_filter:
        clean_status = status_filter.strip().lower()
        if clean_status in ("open", "answered", "closed"):
            query = query.filter(ClassDoubt.status == clean_status)

    if topic_id is not None:
        query = query.filter(ClassDoubt.topic_id == topic_id)

    doubts = query.order_by(ClassDoubt.created_at.desc()).all()

    result = []
    for d in doubts:
        author_name = d.student.full_name if d.student and d.student.full_name else "Student"
        topic_title = d.topic.title if d.topic else None

        active_replies = [
            ClassDoubtReplyOut(
                id=rep.id,
                doubt_id=rep.doubt_id,
                author_id=rep.author_id,
                author_name=rep.author.full_name if rep.author and rep.author.full_name else "Instructor",
                author_role=rep.author.role if rep.author else "faculty",
                body=rep.body,
                created_at=rep.created_at.isoformat()
            )
            for rep in d.replies
            if not rep.is_deleted
        ]

        result.append(ClassDoubtOut(
            id=d.id,
            class_id=d.class_id,
            student_id=d.student_id,
            title=d.title,
            body=d.body,
            visibility=d.visibility,
            status=d.status,
            topic_id=d.topic_id,
            topic_title=topic_title,
            created_at=d.created_at.isoformat(),
            author_name=author_name,
            is_my_doubt=False,
            replies=active_replies
        ))
    return result


@router.post("/api/faculty/classes/{class_id}/doubts/{doubt_id}/replies", response_model=ClassDoubtReplyOut, status_code=status.HTTP_201_CREATED)
def reply_to_doubt(
    class_id: int,
    doubt_id: int,
    payload: ClassDoubtReplyCreate,
    current_user: User = Depends(require_faculty_or_admin),
    db: Session = Depends(get_db)
):
    """Faculty replies to a student doubt. Auto-updates doubt status to 'answered' if open. Rate limit: 30 posts/hr."""
    class_obj = get_class_for_faculty(db, class_id, current_user)
    enforce_rate_limit(
        f"comm:faculty:hr:{current_user.id}",
        limit=30,
        window_seconds=3600,
        detail="Hourly post limit exceeded (max 30 posts per hour). Please try again later."
    )

    doubt = db.query(ClassDoubt).filter(ClassDoubt.id == doubt_id, ClassDoubt.class_id == class_obj.id).first()
    if not doubt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doubt not found")

    clean_body = validate_plain_text(payload.body, max_length=2000, field_name="Reply", allow_newlines=True, required=True)

    reply = ClassDoubtReply(
        doubt_id=doubt.id,
        author_id=current_user.id,
        body=clean_body,
        created_at=datetime.utcnow(),
        is_deleted=False
    )
    db.add(reply)

    if doubt.status == "open":
        doubt.status = "answered"

    db.commit()
    db.refresh(reply)

    return ClassDoubtReplyOut(
        id=reply.id,
        doubt_id=reply.doubt_id,
        author_id=reply.author_id,
        author_name=current_user.full_name or "Instructor",
        author_role=current_user.role or "faculty",
        body=reply.body,
        created_at=reply.created_at.isoformat()
    )


@router.patch("/api/faculty/classes/{class_id}/doubts/{doubt_id}/close", response_model=ClassDoubtOut)
def close_doubt(
    class_id: int,
    doubt_id: int,
    current_user: User = Depends(require_faculty_or_admin),
    db: Session = Depends(get_db)
):
    """Faculty closes a doubt."""
    class_obj = get_class_for_faculty(db, class_id, current_user)
    doubt = db.query(ClassDoubt).filter(ClassDoubt.id == doubt_id, ClassDoubt.class_id == class_obj.id).first()
    if not doubt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doubt not found")

    doubt.status = "closed"
    db.commit()
    db.refresh(doubt)

    author_name = doubt.student.full_name if doubt.student and doubt.student.full_name else "Student"
    topic_title = doubt.topic.title if doubt.topic else None
    active_replies = [
        ClassDoubtReplyOut(
            id=rep.id,
            doubt_id=rep.doubt_id,
            author_id=rep.author_id,
            author_name=rep.author.full_name if rep.author and rep.author.full_name else "Instructor",
            author_role=rep.author.role if rep.author else "faculty",
            body=rep.body,
            created_at=rep.created_at.isoformat()
        )
        for rep in doubt.replies
        if not rep.is_deleted
    ]

    return ClassDoubtOut(
        id=doubt.id,
        class_id=doubt.class_id,
        student_id=doubt.student_id,
        title=doubt.title,
        body=doubt.body,
        visibility=doubt.visibility,
        status=doubt.status,
        topic_id=doubt.topic_id,
        topic_title=topic_title,
        created_at=doubt.created_at.isoformat(),
        author_name=author_name,
        is_my_doubt=False,
        replies=active_replies
    )


@router.delete("/api/faculty/classes/{class_id}/doubts/{doubt_id}/replies/{reply_id}")
def delete_doubt_reply(
    class_id: int,
    doubt_id: int,
    reply_id: int,
    current_user: User = Depends(require_faculty_or_admin),
    db: Session = Depends(get_db)
):
    """Faculty deletes an inappropriate reply. Soft-deleted and audited in AgentLog."""
    class_obj = get_class_for_faculty(db, class_id, current_user)
    reply = (
        db.query(ClassDoubtReply)
        .join(ClassDoubt, ClassDoubt.id == ClassDoubtReply.doubt_id)
        .filter(
            ClassDoubtReply.id == reply_id,
            ClassDoubtReply.doubt_id == doubt_id,
            ClassDoubt.class_id == class_obj.id,
            ClassDoubtReply.is_deleted == False
        )
        .first()
    )
    if not reply:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reply not found")

    reply.is_deleted = True
    db.add(AgentLog(
        user_id=current_user.id,
        agent_name="Faculty Portal",
        action="doubt_reply_deleted",
        message=f"Faculty {current_user.id} soft-deleted reply id {reply.id} on doubt {doubt_id} in class {class_obj.id}.",
        created_at=datetime.utcnow()
    ))
    db.commit()
    return {"message": "Reply deleted successfully"}


# ==============================================================================
# STUDENT CLASS RESOURCES & ANNOUNCEMENTS
# ==============================================================================

@router.get("/api/student/classes/{class_id}/resources", response_model=List[ClassResourceOut])
def get_student_class_resources(
    class_id: int,
    current_user: User = Depends(require_role("student")),
    db: Session = Depends(get_db)
):
    """Student lists active resources for an enrolled active class."""
    class_obj, _ = get_class_for_student(db, class_id, current_user)
    resources = (
        db.query(ClassResource)
        .filter(ClassResource.class_id == class_obj.id, ClassResource.is_deleted == False)
        .order_by(ClassResource.created_at.desc())
        .all()
    )

    result = []
    for r in resources:
        t_title = r.topic.title if r.topic else None
        result.append(ClassResourceOut(
            id=r.id,
            class_id=r.class_id,
            created_by=r.created_by,
            title=r.title,
            description=r.description,
            url=r.url,
            resource_type=r.resource_type,
            topic_id=r.topic_id,
            topic_title=t_title,
            created_at=r.created_at.isoformat(),
            is_deleted=r.is_deleted
        ))
    return result


@router.get("/api/student/classes/{class_id}/announcements", response_model=List[ClassAnnouncementOut])
def get_student_class_announcements(
    class_id: int,
    current_user: User = Depends(require_role("student")),
    db: Session = Depends(get_db)
):
    """Student lists announcements with read indicators for an enrolled active class."""
    class_obj, _ = get_class_for_student(db, class_id, current_user)
    announcements = (
        db.query(ClassAnnouncement)
        .filter(ClassAnnouncement.class_id == class_obj.id, ClassAnnouncement.is_deleted == False)
        .order_by(ClassAnnouncement.pinned.desc(), ClassAnnouncement.created_at.desc())
        .all()
    )

    read_ids = set(
        r[0] for r in
        db.query(AnnouncementRead.announcement_id)
        .filter(AnnouncementRead.student_id == current_user.id)
        .all()
    )

    return [
        ClassAnnouncementOut(
            id=a.id,
            class_id=a.class_id,
            created_by=a.created_by,
            title=a.title,
            body=a.body,
            pinned=a.pinned,
            created_at=a.created_at.isoformat(),
            is_read=(a.id in read_ids)
        )
        for a in announcements
    ]


@router.post("/api/student/classes/{class_id}/announcements/{announcement_id}/read")
def mark_announcement_read(
    class_id: int,
    announcement_id: int,
    current_user: User = Depends(require_role("student")),
    db: Session = Depends(get_db)
):
    """Student marks an announcement as read."""
    class_obj, _ = get_class_for_student(db, class_id, current_user)
    ann = (
        db.query(ClassAnnouncement)
        .filter(ClassAnnouncement.id == announcement_id, ClassAnnouncement.class_id == class_obj.id, ClassAnnouncement.is_deleted == False)
        .first()
    )
    if not ann:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found")

    existing = (
        db.query(AnnouncementRead)
        .filter(AnnouncementRead.announcement_id == announcement_id, AnnouncementRead.student_id == current_user.id)
        .first()
    )
    if not existing:
        db.add(AnnouncementRead(
            announcement_id=announcement_id,
            student_id=current_user.id,
            read_at=datetime.utcnow()
        ))
        db.commit()

    return {"message": "Announcement marked as read", "announcement_id": announcement_id}


@router.get("/api/student/classes/{class_id}/announcements/unread-count")
def get_unread_announcements_count(
    class_id: int,
    current_user: User = Depends(require_role("student")),
    db: Session = Depends(get_db)
):
    """Returns the number of unread announcements in this class for the student."""
    class_obj, _ = get_class_for_student(db, class_id, current_user)
    total_active = (
        db.query(ClassAnnouncement)
        .filter(ClassAnnouncement.class_id == class_obj.id, ClassAnnouncement.is_deleted == False)
        .count()
    )
    read_count = (
        db.query(AnnouncementRead)
        .join(ClassAnnouncement, ClassAnnouncement.id == AnnouncementRead.announcement_id)
        .filter(
            ClassAnnouncement.class_id == class_obj.id,
            ClassAnnouncement.is_deleted == False,
            AnnouncementRead.student_id == current_user.id
        )
        .count()
    )
    unread = max(0, total_active - read_count)
    return {"unread_count": unread}


# ==============================================================================
# STUDENT DOUBTS
# ==============================================================================

@router.post("/api/student/classes/{class_id}/doubts", response_model=ClassDoubtOut, status_code=status.HTTP_201_CREATED)
def ask_doubt(
    class_id: int,
    payload: ClassDoubtCreate,
    current_user: User = Depends(require_role("student")),
    db: Session = Depends(get_db)
):
    """Student asks a doubt. Rate limits: max 5/hr, max 20/day."""
    class_obj, _ = get_class_for_student(db, class_id, current_user)

    # Hourly rate limit (5/hr)
    enforce_rate_limit(
        f"doubt:student:hr:{current_user.id}",
        limit=5,
        window_seconds=3600,
        detail="Hourly doubt limit exceeded (max 5 doubts per hour). Please try again later."
    )
    # Daily rate limit (20/day)
    enforce_rate_limit(
        f"doubt:student:day:{current_user.id}",
        limit=20,
        window_seconds=86400,
        detail="Daily doubt limit exceeded (max 20 doubts per day). Please try again tomorrow."
    )

    clean_title = validate_plain_text(payload.title, max_length=150, field_name="Title", required=True)
    clean_body = validate_plain_text(payload.body, max_length=2000, field_name="Body", allow_newlines=True, required=True)
    clean_visibility = validate_doubt_visibility(payload.visibility)

    topic_title = None
    if payload.topic_id is not None:
        topic = db.query(Topic).filter(Topic.id == payload.topic_id, Topic.course_id == class_obj.course_id).first()
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected topic does not belong to the class course."
            )
        topic_title = topic.title

    doubt = ClassDoubt(
        class_id=class_obj.id,
        student_id=current_user.id,
        topic_id=payload.topic_id,
        title=clean_title,
        body=clean_body,
        visibility=clean_visibility,
        status="open",
        created_at=datetime.utcnow()
    )
    db.add(doubt)
    db.commit()
    db.refresh(doubt)

    return ClassDoubtOut(
        id=doubt.id,
        class_id=doubt.class_id,
        student_id=doubt.student_id,
        title=doubt.title,
        body=doubt.body,
        visibility=doubt.visibility,
        status=doubt.status,
        topic_id=doubt.topic_id,
        topic_title=topic_title,
        created_at=doubt.created_at.isoformat(),
        author_name="You",
        is_my_doubt=True,
        replies=[]
    )


@router.get("/api/student/classes/{class_id}/doubts", response_model=List[ClassDoubtOut])
def get_student_class_doubts(
    class_id: int,
    current_user: User = Depends(require_role("student")),
    db: Session = Depends(get_db)
):
    """
    Student views doubts for their class.
    Shows:
    - Doubts created by the calling student (both private and class-visible)
    - Doubts created by active classmates WHERE visibility == 'class' (author first name ONLY, never email)
    - Never shows classmates' private doubts
    """
    class_obj, _ = get_class_for_student(db, class_id, current_user)

    doubts = (
        db.query(ClassDoubt)
        .filter(
            ClassDoubt.class_id == class_obj.id,
            (ClassDoubt.student_id == current_user.id) | (ClassDoubt.visibility == "class")
        )
        .order_by(ClassDoubt.created_at.desc())
        .all()
    )

    result = []
    for d in doubts:
        is_my = (d.student_id == current_user.id)
        if is_my:
            author_display = "You"
            student_id_val = current_user.id
        else:
            # Mask author name: first name only! Never expose email, full surname, or password hash.
            first_name = d.student.full_name.split()[0] if d.student and d.student.full_name else "Classmate"
            author_display = first_name
            student_id_val = None

        topic_title = d.topic.title if d.topic else None

        active_replies = [
            ClassDoubtReplyOut(
                id=rep.id,
                doubt_id=rep.doubt_id,
                author_id=rep.author_id,
                author_name=rep.author.full_name if rep.author and rep.author.full_name else "Instructor",
                author_role=rep.author.role if rep.author else "faculty",
                body=rep.body,
                created_at=rep.created_at.isoformat()
            )
            for rep in d.replies
            if not rep.is_deleted
        ]

        result.append(ClassDoubtOut(
            id=d.id,
            class_id=d.class_id,
            student_id=student_id_val,
            title=d.title,
            body=d.body,
            visibility=d.visibility,
            status=d.status,
            topic_id=d.topic_id,
            topic_title=topic_title,
            created_at=d.created_at.isoformat(),
            author_name=author_display,
            is_my_doubt=is_my,
            replies=active_replies
        ))
    return result


@router.post("/api/student/classes/{class_id}/doubts/{doubt_id}/replies")
def student_reply_to_doubt_blocked(
    class_id: int,
    doubt_id: int,
    current_user: User = Depends(require_role("student"))
):
    """Students cannot reply to doubts in this version."""
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Students cannot reply to doubts in this version."
    )
