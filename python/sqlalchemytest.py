#!/usr/bin/env python3

from sqlalchemy import create_engine
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy_mixins import ReprMixin


DB_ENGINE_URL = 'sqlite:///{filename}'


class SessionManager(object):
    def __init__(self, session):
        self.session = session

    def __enter__(self):
        return self.session

    def __exit__(self, exc_type, exc_value, exc_traceback):
        try:
            self.session.commit()
        except:
            self.session.rollback()
            raise
        finally:
            self.session.close()


class SessionFactory(object):
    def __init__(self, db_engine):
        self.session_func = sessionmaker(bind=db_engine)

    def create_session(self):
        return SessionManager(self.session_func())


def create_db_engine(dbname):
    db_engine_url = DB_ENGINE_URL.format(filename='{}.db'.format(dbname))
    return create_engine(db_engine_url)


Base = declarative_base()
class BaseModel(Base, ReprMixin):
    __abstract__ = True
    __repr__ = ReprMixin.__repr__


class User(BaseModel):
    __tablename__ = 'users'
    __repr_attrs__ = ['name']
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)


class Address(BaseModel):
    __tablename__ = 'addresses'
    __repr_attrs__ = ['street_name', 'street_number', 'post_code', 'user']
    id = Column(Integer, primary_key=True)
    street_name = Column(String(250))
    street_number = Column(String(250))
    post_code = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship(User)


db_engine = create_db_engine('test.db')

# Create all tables in the engine
Base.metadata.create_all(db_engine)

session_factory = SessionFactory(db_engine)

#with session_factory.create_session() as session:
#    user = User(name="John Smith")
#    address = Address(post_code='00000', user=user)
#    session.add(user)
#    session.add(address)

with session_factory.create_session() as session:
    users = session.query(User).all()
    print('\n'.join([repr(u) for u in users]))
    address = session.query(Address).first()
    print(address)

