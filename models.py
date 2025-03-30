from datetime import datetime
import json
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from app import db

class GiveawayModel(db.Model):
    """Database model for giveaways"""
    __tablename__ = 'giveaways'
    
    id = Column(Integer, primary_key=True)
    message_id = Column(String(20), unique=True, nullable=False)
    channel_id = Column(String(20), nullable=False)
    guild_id = Column(String(20), nullable=False)
    creator_id = Column(String(20), nullable=False)
    prize = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    end_time = Column(Float, nullable=False)
    winners_count = Column(Integer, default=1, nullable=False)
    ended = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    entries = relationship("GiveawayEntryModel", back_populates="giveaway", cascade="all, delete-orphan")
    winners = relationship("GiveawayWinnerModel", back_populates="giveaway", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Giveaway(id={self.id}, prize='{self.prize}', end_time={datetime.fromtimestamp(self.end_time)})>"
    
    def to_dict(self):
        """Convert the model to a dictionary"""
        return {
            'id': self.id,
            'message_id': self.message_id,
            'channel_id': self.channel_id,
            'guild_id': self.guild_id,
            'creator_id': self.creator_id,
            'prize': self.prize,
            'description': self.description,
            'end_time': self.end_time,
            'winners_count': self.winners_count,
            'ended': self.ended,
            'entries_count': len(self.entries)
        }
    
    @property
    def entries_set(self):
        """Return a set of user IDs who entered the giveaway"""
        return {entry.user_id for entry in self.entries}
    
    @property
    def entries_count(self):
        """Return the number of entries in the giveaway"""
        return len(self.entries)
    
    @property
    def time_remaining(self):
        """Return the time remaining in seconds"""
        now = datetime.now().timestamp()
        return max(0, self.end_time - now)
    
    @property
    def is_ended(self):
        """Return True if the giveaway has ended"""
        return self.ended or self.time_remaining <= 0


class GiveawayEntryModel(db.Model):
    """Database model for giveaway entries"""
    __tablename__ = 'giveaway_entries'
    
    id = Column(Integer, primary_key=True)
    giveaway_id = Column(Integer, ForeignKey('giveaways.id'), nullable=False)
    user_id = Column(String(20), nullable=False)
    entry_time = Column(Float, default=lambda: datetime.now().timestamp(), nullable=False)
    
    # Relationships
    giveaway = relationship("GiveawayModel", back_populates="entries")
    
    __table_args__ = (
        # Ensure a user can only enter a giveaway once
        db.UniqueConstraint('giveaway_id', 'user_id', name='unique_entry'),
    )
    
    def __repr__(self):
        return f"<GiveawayEntry(giveaway_id={self.giveaway_id}, user_id={self.user_id})>"


class GiveawayWinnerModel(db.Model):
    """Database model for giveaway winners"""
    __tablename__ = 'giveaway_winners'
    
    id = Column(Integer, primary_key=True)
    giveaway_id = Column(Integer, ForeignKey('giveaways.id'), nullable=False)
    user_id = Column(String(20), nullable=False)
    selected_time = Column(Float, default=lambda: datetime.now().timestamp(), nullable=False)
    
    # Relationships
    giveaway = relationship("GiveawayModel", back_populates="winners")
    
    def __repr__(self):
        return f"<GiveawayWinner(giveaway_id={self.giveaway_id}, user_id={self.user_id})>"