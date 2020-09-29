from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import datetime
from db_setup import *

engine = create_engine('sqlite:///textbookeditions.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

# Delete Textbooks if exisitng.
session.query(TextBook).delete()
# Delete TBEdition if exisitng.
session.query(TBEdition).delete()
# Delete Users if exisitng.
session.query(User).delete()

# Create sample users
FirstUser = User(name="Shaik Badulla",
                 email="badullashaik507@gmail.com",
                 picture='http://www.enchanting-costarica.com/wp-content/'
                 'uploads/2018/02/jcarvaja17-min.jpg')
session.add(FirstUser)
session.commit()
print "Done to add FU"
# Create sample books
TextBook1 = TextBook(name="Digital Communication Systems",
                     user_id=1)
session.add(TextBook1)
session.commit()

TextBook2 = TextBook(name="Digital System Design",
                     user_id=1)
session.add(TextBook2)
session.commit

TextBook3 = TextBook(name="Computer Organisation",
                     user_id=1)
session.add(TextBook3)
session.commit()

# Populate a textbooks with editions for testing
# Using different users for text book edition also
TBEdition1 = TBEdition(name="Communication Systems",
                       author="Simon Hakin",
                       edition="4th Edition,2011",
                       publisher="Wiley India Edition",
                       price="550",
                       tbtype="TextBook",
                       date=datetime.datetime.now(),
                       textbookid=1,
                       user_id=1)
session.add(TBEdition1)
session.commit()

TBEdition2 = TBEdition(name="Digital Design Principles and Practices",
                       author="John F.Wakerly",
                       edition="4 th Edition,2009",
                       publisher="Pearson Education",
                       price="540",
                       tbtype="TextBook",
                       date=datetime.datetime.now(),
                       textbookid=2,
                       user_id=1)
session.add(TBEdition2)
session.commit()

TBEdition3 = TBEdition(name="5.Computer Organisation",
                       author="CarlHamacher",
                       edition="5 th Edition",
                       publisher="McGraw Hill,2002",
                       price="650",
                       tbtype="Reference",
                       date=datetime.datetime.now(),
                       textbookid=3,
                       user_id=1)
session.add(TBEdition3)
session.commit()

print("Your database has been inserted!")
