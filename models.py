from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Document(Base):
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    author = Column(String)
    status = Column(String, default='new')
    created_at = Column(DateTime, default=datetime.utcnow)
    qr_codes = relationship("QRCode", back_populates="document")
    history = relationship("DocumentHistory", back_populates="document")

class QRCode(Base):
    __tablename__ = 'qr_codes'
    
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('documents.id'))
    x_position = Column(Float)
    y_position = Column(Float)
    content = Column(String)
    document = relationship("Document", back_populates="qr_codes")

class DocumentHistory(Base):
    __tablename__ = 'document_history'
    
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('documents.id'))
    version = Column(String)
    changes = Column(Text)
    changed_by = Column(String)
    changed_at = Column(DateTime, default=datetime.utcnow)
    document = relationship("Document", back_populates="history")

# Создание базы данных
def init_db():
    engine = create_engine('sqlite:///documents.db')
    Base.metadata.create_all(engine)
    return engine 