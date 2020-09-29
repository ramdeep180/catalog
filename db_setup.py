import sys
import os
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import create_engine
Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    email = Column(String(150), nullable=False)
    picture = Column(String(250))


class TextBook(Base):
    __tablename__ = 'textbook'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User, backref="textbook")

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id
        }


class TBEdition(Base):
    __tablename__ = 'tb_edition'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    author = Column(String(250))
    edition = Column(String(250))
    publisher = Column(String(250))
    price = Column(String(8))
    tbtype = Column(String(250))
    date = Column(DateTime, nullable=False)
    textbookid = Column(Integer, ForeignKey('textbook.id'))
    textbook = relationship(
        TextBook, backref=backref('tb_edition', cascade='all, delete'))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User, backref="tb_edition")

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self. name,
            'author': self. author,
            'edition': self. edition,
            'publisher': self. publisher,
            'price': self. price,
            'tbtype': self. tbtype,
            'date': self. date,
            'id': self. id
        }

engin = create_engine('sqlite:///textbookeditions.db')
Base.metadata.create_all(engin)
