from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session as DBSession
import uuid

from app.models import Session, TelemetryEvent, SessionStatus, Client

class SessionRepository:
    @staticmethod
    def create(db: DBSession, client_id: uuid.UUID, session_topic: str) -> Session:
        session = Session(
            client_id=client_id,
            session_topic=session_topic
        )
        db.add(session)
        db.flush()
        return session
    
    @staticmethod
    def get_current_active(db: DBSession) -> Optional[Session]:
        return db.query(Session).filter(
            Session.status == SessionStatus.ACTIVE
        ).order_by(Session.created_at.desc()).first()
    
    @staticmethod
    def get_by_id(db: DBSession, session_id: uuid.UUID) -> Optional[Session]:
        return db.query(Session).filter(
            Session.session_id == session_id
        ).first()

class TelemetryRepository:
    @staticmethod
    def create(db: DBSession, session_id: uuid.UUID) -> TelemetryEvent:
        telemetry = TelemetryEvent(
            session_id=session_id,
            created_at=datetime.utcnow()
        )
        db.add(telemetry)
        db.flush()
        return telemetry

class ClientRepository:
    @staticmethod
    def get_or_create(db: DBSession, client_id: uuid.UUID, client_name: str = None) -> Client:
        client = db.query(Client).filter(Client.client_id == client_id).first()
        if not client:
            client = Client(client_id=client_id, client_name=client_name)
            db.add(client)
            db.flush()
        return client