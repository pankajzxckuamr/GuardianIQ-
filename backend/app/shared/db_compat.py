import inspect
import asyncio

async def db_get(db, model, ident):
    res = db.get(model, ident)
    if inspect.isawaitable(res):
        return await res
    return res

async def execute_statement(db, stmt):
    res = db.execute(stmt)
    if inspect.isawaitable(res):
        return await res
    return res

async def db_flush(db):
    res = db.flush()
    if inspect.isawaitable(res):
        return await res
    return res

async def commit_session(db):
    res = db.commit()
    if inspect.isawaitable(res):
        return await res
    return res
