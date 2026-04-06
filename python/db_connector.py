# python/db_connector.py
"""
Connettore Database Singleton per OddsLab.
"""

from __future__ import annotations

from typing import Optional, Any

import mysql.connector
from mysql.connector import Error
from config import DATABASE


class DB:
    """Singleton per la connessione al database MySQL."""

    _instance: Any = None

    @classmethod
    def get_connection(cls) -> Any:
        try:
            if cls._instance is None or not cls._instance.is_connected():
                cls._instance = mysql.connector.connect(
                    host=DATABASE['host'],
                    user=DATABASE['user'],
                    password=DATABASE['password'],
                    database=DATABASE['database'],
                    charset='utf8mb4',
                    autocommit=False,
                    consume_results=True,   # svuota automaticamente risultati non letti
                )
                print(f"[DB] Connesso a {DATABASE['database']}")
            return cls._instance
        except Error as e:
            print(f"[DB] Errore di connessione: {e}")
            raise

    @classmethod
    def fetch_all(cls, query: str,
                  params: Optional[tuple[Any, ...]] = None
                  ) -> list[dict[str, Any]]:
        conn = cls.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(query, params or ())
            rows: Any = cursor.fetchall()
            return list(rows) if rows else []
        except Error as e:
            print(f"[DB] Errore query: {e}\n[DB] Query: {query}\n[DB] Params: {params}")
            raise
        finally:
            cursor.close()

    @classmethod
    def fetch_one(cls, query: str,
                  params: Optional[tuple[Any, ...]] = None
                  ) -> Optional[dict[str, Any]]:
        conn = cls.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(query, params or ())
            row: Any = cursor.fetchone()
            # Svuota eventuali righe rimanenti per evitare "Unread result found"
            cursor.fetchall()
            if row is None:
                return None
            return dict(row)
        except Error as e:
            print(f"[DB] Errore query: {e}\n[DB] Query: {query}\n[DB] Params: {params}")
            raise
        finally:
            cursor.close()

    @classmethod
    def execute(cls, query: str,
                params: Optional[tuple[Any, ...]] = None
                ) -> int:
        conn = cls.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params or ())
            conn.commit()
            return cursor.lastrowid or 0
        except Error as e:
            conn.rollback()
            print(f"[DB] Errore query: {e}\n[DB] Query: {query}\n[DB] Params: {params}")
            raise
        finally:
            cursor.close()

    @classmethod
    def execute_many(cls, query: str,
                     data_list: list[tuple[Any, ...]]
                     ) -> int:
        conn = cls.get_connection()
        cursor = conn.cursor()
        try:
            cursor.executemany(query, data_list)
            conn.commit()
            return cursor.rowcount
        except Error as e:
            conn.rollback()
            print(f"[DB] Errore bulk: {e}")
            raise
        finally:
            cursor.close()

    @classmethod
    def count(cls, query: str,
              params: Optional[tuple[Any, ...]] = None
              ) -> int:
        row = cls.fetch_one(query, params)
        if row is not None and 'n' in row:
            return int(row['n'])
        return 0

    @classmethod
    def close(cls) -> None:
        if cls._instance is not None:
            try:
                if cls._instance.is_connected():
                    cls._instance.close()
                    print("[DB] Connessione chiusa")
            except Exception:
                pass
            cls._instance = None
