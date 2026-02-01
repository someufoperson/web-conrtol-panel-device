from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from config import db_config

engine = create_async_engine(url=db_config.URL, echo=db_config.ECHO)
async_session = async_sessionmaker(engine, 
                                   expire_on_commit=False, 
                                   autoflush=False)