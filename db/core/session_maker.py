from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import db_config

engine = create_async_engine(url=db_config.URL, echo=db_config.ECHO)
async_session = async_sessionmaker(engine, 
                                   expire_on_commit=False, 
                                   autoflush=False)
sync_engine = create_engine(url=db_config.URL, echo=db_config.ECHO)
sync_session = sessionmaker(sync_engine)