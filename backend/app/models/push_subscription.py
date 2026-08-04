import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base


class PushSubscription(Base):
    """Stores a browser Web Push subscription endpoint + ECDH keys for a user."""
    __tablename__ = "push_subscriptions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # The push service endpoint URL (unique per browser+user)
    endpoint = Column(Text, nullable=False, unique=True)
    # ECDH public key (base64url encoded)
    p256dh = Column(Text, nullable=False)
    # Auth secret (base64url encoded)
    auth = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User")
