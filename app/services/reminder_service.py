from datetime import date, timedelta
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.reminder import Reminder, ReminderType, ReminderStatus
from app.models.trademark import Trademark
from app.models.correction import Correction
from app.models.customer import Customer
from app.schemas.reminder import ReminderCreate, ReminderUpdate


def get_reminder(db: Session, reminder_id: int) -> Reminder:
    reminder = db.query(Reminder).filter(
        Reminder.id == reminder_id,
        Reminder.is_deleted == False
    ).first()
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"提醒 ID {reminder_id} 不存在"
        )
    return reminder


def list_reminders(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    trademark_id: Optional[int] = None,
    reminder_type: Optional[ReminderType] = None,
    status: Optional[ReminderStatus] = None,
    priority: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    keyword: Optional[str] = None
) -> Tuple[List[Reminder], int]:
    query = db.query(Reminder).filter(Reminder.is_deleted == False)

    if trademark_id is not None:
        query = query.filter(Reminder.trademark_id == trademark_id)
    if reminder_type is not None:
        query = query.filter(Reminder.reminder_type == reminder_type.value)
    if status is not None:
        query = query.filter(Reminder.status == status.value)
    if priority is not None:
        query = query.filter(Reminder.priority == priority)
    if start_date is not None:
        query = query.filter(Reminder.reminder_date >= start_date)
    if end_date is not None:
        query = query.filter(Reminder.reminder_date <= end_date)
    if keyword:
        search_pattern = f"%{keyword}%"
        query = query.filter(
            (Reminder.title.ilike(search_pattern)) |
            (Reminder.content.ilike(search_pattern)) |
            (Reminder.recipient.ilike(search_pattern))
        )

    total = query.count()
    items = query.order_by(
        Reminder.priority.desc(),
        Reminder.reminder_date.asc(),
        Reminder.updated_at.desc()
    ).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return items, total


def create_reminder(db: Session, reminder_in: ReminderCreate) -> Reminder:
    trademark = db.query(Trademark).filter(
        Trademark.id == reminder_in.trademark_id,
        Trademark.is_deleted == False
    ).first()
    if not trademark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"商标 ID {reminder_in.trademark_id} 不存在"
        )

    reminder_data = reminder_in.model_dump()

    if reminder_data.get("reminder_type"):
        try:
            reminder_type_enum = ReminderType(reminder_data["reminder_type"])
            reminder_data["reminder_type"] = reminder_type_enum.value
        except (ValueError, KeyError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的提醒类型: {reminder_data['reminder_type']}"
            )

    if reminder_data.get("status"):
        try:
            status_enum = ReminderStatus(reminder_data["status"])
            reminder_data["status"] = status_enum.value
        except (ValueError, KeyError):
            reminder_data["status"] = ReminderStatus.PENDING.value

    reminder = Reminder(**reminder_data)
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder


def update_reminder(
    db: Session,
    reminder_id: int,
    reminder_in: ReminderUpdate
) -> Reminder:
    reminder = get_reminder(db, reminder_id)
    update_data = reminder_in.model_dump(exclude_unset=True)

    if update_data.get("trademark_id"):
        trademark = db.query(Trademark).filter(
            Trademark.id == update_data["trademark_id"],
            Trademark.is_deleted == False
        ).first()
        if not trademark:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"商标 ID {update_data['trademark_id']} 不存在"
            )

    if update_data.get("reminder_type"):
        try:
            reminder_type_enum = ReminderType(update_data["reminder_type"])
            update_data["reminder_type"] = reminder_type_enum.value
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的提醒类型: {update_data['reminder_type']}"
            )

    if update_data.get("status"):
        try:
            status_enum = ReminderStatus(update_data["status"])
            update_data["status"] = status_enum.value
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的状态值: {update_data['status']}"
            )

    for field, value in update_data.items():
        setattr(reminder, field, value)

    db.commit()
    db.refresh(reminder)
    return reminder


def delete_reminder(db: Session, reminder_id: int) -> None:
    reminder = get_reminder(db, reminder_id)
    reminder.is_deleted = True
    db.commit()


def generate_expiry_reminders(
    db: Session,
    days_threshold: int = 180,
    only_pending: bool = True
) -> Tuple[int, List[Reminder]]:
    today = date.today()
    threshold_date = today + timedelta(days=days_threshold)

    expiring_trademarks = db.query(Trademark).filter(
        Trademark.is_deleted == False,
        Trademark.expiry_date <= threshold_date,
        Trademark.expiry_date >= today
    ).all()

    existing_reminder_keys = set()
    if only_pending:
        existing = db.query(Reminder).filter(
            Reminder.is_deleted == False,
            Reminder.reminder_type == ReminderType.EXPIRY.value,
            Reminder.status != ReminderStatus.RESOLVED.value
        ).all()
        existing_reminder_keys = {(r.trademark_id, r.deadline_date) for r in existing if r.deadline_date}

    created_reminders = []

    for trademark in expiring_trademarks:
        days_until_expiry = (trademark.expiry_date - today).days

        if only_pending and (trademark.id, trademark.expiry_date) in existing_reminder_keys:
            continue

        if days_until_expiry <= 30:
            priority = 3
            escalation_level = 3
        elif days_until_expiry <= 90:
            priority = 2
            escalation_level = 2
        else:
            priority = 1
            escalation_level = 1

        customer = db.query(Customer).filter(
            Customer.id == trademark.customer_id,
            Customer.is_deleted == False
        ).first()

        reminder_data = {
            "reminder_type": ReminderType.EXPIRY.value,
            "reminder_date": today,
            "deadline_date": trademark.expiry_date,
            "days_remaining": days_until_expiry,
            "title": f"商标临期提醒 - {trademark.trademark_name}",
            "content": (
                f"商标「{trademark.trademark_name}」（注册号: {trademark.registration_number}）"
                f"将于 {trademark.expiry_date} 到期，还剩 {days_until_expiry} 天。"
                f"请及时办理续展手续。"
            ),
            "recipient": customer.name if customer else None,
            "recipient_email": customer.email if customer else None,
            "recipient_phone": customer.phone if customer else None,
            "status": ReminderStatus.PENDING.value,
            "priority": priority,
            "escalation_level": escalation_level,
            "trademark_id": trademark.id
        }

        reminder = Reminder(**reminder_data)
        db.add(reminder)
        created_reminders.append(reminder)

    db.commit()
    for reminder in created_reminders:
        db.refresh(reminder)

    return len(created_reminders), created_reminders


def generate_correction_reminders(
    db: Session,
    days_threshold: int = 15,
    only_pending: bool = True
) -> Tuple[int, List[Reminder]]:
    today = date.today()
    threshold_date = today + timedelta(days=days_threshold)

    pending_corrections = db.query(Correction).filter(
        Correction.is_deleted == False,
        Correction.correction_status != "completed",
        Correction.deadline <= threshold_date,
        Correction.deadline >= today
    ).all()

    existing_reminder_keys = set()
    if only_pending:
        existing = db.query(Reminder).filter(
            Reminder.is_deleted == False,
            Reminder.reminder_type == ReminderType.CORRECTION_DEADLINE.value,
            Reminder.status != ReminderStatus.RESOLVED.value
        ).all()
        existing_reminder_keys = {(r.trademark_id, r.deadline_date) for r in existing if r.deadline_date}

    created_reminders = []

    for correction in pending_corrections:
        days_until_deadline = (correction.deadline - today).days

        if only_pending and (correction.trademark_id, correction.deadline) in existing_reminder_keys:
            continue

        if days_until_deadline <= 3:
            priority = 3
            escalation_level = 3
        elif days_until_deadline <= 7:
            priority = 2
            escalation_level = 2
        else:
            priority = 1
            escalation_level = 1

        trademark = db.query(Trademark).filter(
            Trademark.id == correction.trademark_id,
            Trademark.is_deleted == False
        ).first()

        if not trademark:
            continue

        customer = db.query(Customer).filter(
            Customer.id == trademark.customer_id,
            Customer.is_deleted == False
        ).first()

        reminder_data = {
            "reminder_type": ReminderType.CORRECTION_DEADLINE.value,
            "reminder_date": today,
            "deadline_date": correction.deadline,
            "days_remaining": days_until_deadline,
            "title": f"补正期限提醒 - {trademark.trademark_name}",
            "content": (
                f"商标「{trademark.trademark_name}」（注册号: {trademark.registration_number}）"
                f"的补正期限为 {correction.deadline}，还剩 {days_until_deadline} 天。"
                f"补正原因: {correction.correction_reason}"
            ),
            "recipient": customer.name if customer else None,
            "recipient_email": customer.email if customer else None,
            "recipient_phone": customer.phone if customer else None,
            "status": ReminderStatus.PENDING.value,
            "priority": priority,
            "escalation_level": escalation_level,
            "trademark_id": trademark.id,
            "notes": f"补正记录ID: {correction.id}"
        }

        reminder = Reminder(**reminder_data)
        db.add(reminder)
        created_reminders.append(reminder)

    db.commit()
    for reminder in created_reminders:
        db.refresh(reminder)

    return len(created_reminders), created_reminders


def send_reminder(
    db: Session,
    reminder_id: int,
    sent_by: Optional[str] = None
) -> Reminder:
    reminder = get_reminder(db, reminder_id)

    if reminder.status == ReminderStatus.SENT.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"提醒 ID {reminder_id} 已发送"
        )

    reminder.status = ReminderStatus.SENT.value
    reminder.sent_at = date.today().isoformat()
    if sent_by:
        reminder.notes = (reminder.notes or "") + f"\n由 {sent_by} 于 {date.today()} 发送"

    db.commit()
    db.refresh(reminder)
    return reminder


def acknowledge_reminder(
    db: Session,
    reminder_id: int,
    acknowledged_by: str
) -> Reminder:
    reminder = get_reminder(db, reminder_id)

    if reminder.status == ReminderStatus.ACKNOWLEDGED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"提醒 ID {reminder_id} 已确认"
        )

    if reminder.status not in [ReminderStatus.SENT.value, ReminderStatus.PENDING.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"提醒 ID {reminder_id} 状态不支持确认操作"
        )

    reminder.status = ReminderStatus.ACKNOWLEDGED.value
    reminder.acknowledged_at = date.today().isoformat()
    reminder.acknowledged_by = acknowledged_by

    db.commit()
    db.refresh(reminder)
    return reminder
