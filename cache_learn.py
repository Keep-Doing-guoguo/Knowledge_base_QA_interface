#!/usr/bin/env python
# coding=utf-8

"""
@author: zgw
@date: 2025/6/27 14:45
@source from: 
"""
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from typing import Optional, Union, Tuple, List, Any
from threading import RLock
from collections import OrderedDict
from contextlib import contextmanager
import threading

# ========== base.py ==========
Base = declarative_base()

# ========== models.py ==========
class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, autoincrement=True)  # ✅ 自动分配唯一ID

    #id = Column(Integer, primary_key=True)
    name = Column(String)
    age = Column(Integer)

# ========== session.py ==========
engine = create_engine("sqlite:///students.db", echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

# ========== cache.py ==========
class ThreadSafeObject:
    def __init__(self, key: Union[str, Tuple], obj: Any = None, pool: "CachePool" = None):
        self._obj = obj
        self._key = key
        self._pool = pool
        self._lock = RLock()
        self._loaded = threading.Event()
        self._loaded.set()

    @property
    def key(self):
        return self._key

    @contextmanager
    def acquire(self, owner: str = "", msg: str = ""):
        with self._lock:
            if self._pool:
                self._pool._cache.move_to_end(self.key)
            yield self._obj

    @property
    def obj(self):
        return self._obj

    @obj.setter
    def obj(self, val: Any):
        self._obj = val

class CachePool:
    def __init__(self, cache_num: int = -1):
        self._cache_num = cache_num
        self._cache = OrderedDict()
        self.atomic = RLock()

    def get(self, key: str) -> Optional[ThreadSafeObject]:
        return self._cache.get(key)

    def set(self, key: str, obj: ThreadSafeObject) -> ThreadSafeObject:
        self._cache[key] = obj
        self._check_count()
        return obj

    def _check_count(self):
        if self._cache_num > 0:
            while len(self._cache) > self._cache_num:
                self._cache.popitem(last=False)

# ========== repository.py ==========
class StudentRepository:
    def __init__(self, db: Session, cache_pool: Optional[CachePool] = None):
        self.db = db
        self.cache_pool = cache_pool

    def add_student(self, name: str, age: int):
        student = Student(name=name, age=age)
        self.db.add(student)
        self.db.commit()
        self.db.refresh(student)
        if self.cache_pool:
            self.cache_pool.set(student.id, ThreadSafeObject(student.id, student, self.cache_pool))
        return student

    def get_student(self, student_id: int) -> Optional[Student]:
        if self.cache_pool and (cache := self.cache_pool.get(student_id)):
            return cache.obj
        student = self.db.query(Student).filter(Student.id == student_id).first()
        if student and self.cache_pool:
            self.cache_pool.set(student.id, ThreadSafeObject(student.id, student, self.cache_pool))
        return student

    def update_student(self, student_id: int, name: Optional[str] = None, age: Optional[int] = None):
        student = self.get_student(student_id)
        if not student:
            return None
        if name:
            student.name = name
        if age:
            student.age = age
        self.db.commit()
        self.db.refresh(student)
        if self.cache_pool:
            self.cache_pool.set(student.id, ThreadSafeObject(student.id, student, self.cache_pool))
        return student

    def delete_student(self, student_id: int):
        student = self.get_student(student_id)
        if not student:
            return False
        self.db.delete(student)
        self.db.commit()
        if self.cache_pool:
            self.cache_pool._cache.pop(student_id, None)
        return True

# ========== main.py ==========
import threading

def run_operations(repo: StudentRepository, index: int):
    student = repo.add_student(name=f"User{index}", age=20 + index)
    print(f"[Thread-{index}] Added: {student.name}")
    updated = repo.update_student(student.id, age=30)
    print(f"[Thread-{index}] Updated Age: {updated.age}")
    found = repo.get_student(student.id)
    print(f"[Thread-{index}] Fetched: {found.name} ({found.age})")
    repo.delete_student(student.id)
    print(f"[Thread-{index}] Deleted student {student.id}")

if __name__ == "__main__":
    init_db()
    session = SessionLocal()
    cache_pool = CachePool(cache_num=100)
    repo = StudentRepository(session, cache_pool=cache_pool)

    threads = [threading.Thread(target=run_operations, args=(repo, i)) for i in range(5)]
    for t in threads: t.start()
    for t in threads: t.join()