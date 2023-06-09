import typing
from hashlib import sha256

from sqlalchemy import select

from apps.admin.models import AdminModel
from apps.base.accessor.base_accessor import BaseAccessor
from db.database import Database


class AdminAccessor(BaseAccessor):
    def __init__(self, db: "Database"):
        self.database = db

    async def get_by_email(self, email: str) -> AdminModel | None:
        async with self.database.session.begin() as session:
            result = await session.execute(
                select(AdminModel).filter(AdminModel.email == email)
            )
        admin = result.scalar()
        return admin

    async def create_admin(self, email: str, password: str) -> AdminModel:
        encrypted_pass = sha256(password.encode()).hexdigest()
        async with self.database.session.begin() as session:
            admin = AdminModel(email=email, password=encrypted_pass)
            session.add(admin)
        return admin
