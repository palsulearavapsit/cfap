from typing import List, Optional

from backend.models import CarbonEntry, db


class CarbonRepository:
    """Repository class for CarbonEntry database operations."""

    @staticmethod
    def get_by_id(entry_id: int) -> Optional[CarbonEntry]:
        return db.session.get(CarbonEntry, entry_id)

    @staticmethod
    def get_latest_for_user(user_id: int) -> Optional[CarbonEntry]:
        return (
            CarbonEntry.query.filter_by(user_id=user_id)
            .order_by(CarbonEntry.created_at.desc())
            .first()
        )

    @staticmethod
    def get_all_for_user(user_id: int) -> List[CarbonEntry]:
        return (
            CarbonEntry.query.filter_by(user_id=user_id)
            .order_by(CarbonEntry.created_at.asc())
            .all()
        )

    @staticmethod
    def create(entry: CarbonEntry, commit: bool = True) -> CarbonEntry:
        db.session.add(entry)
        if commit:
            db.session.commit()
        return entry

    @staticmethod
    def delete_all_for_user(user_id: int) -> None:
        CarbonEntry.query.filter_by(user_id=user_id).delete()
        db.session.commit()
