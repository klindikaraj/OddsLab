# python/db_connector.py
"""
Connettore Database Singleton per OddsLab.
Gestisce la connessione MySQL e fornisce metodi helper.

I metodi sono separati per tipo di ritorno:
- fetch_all() → list[dict]       (SELECT multiple righe)
- fetch_one() → Optional[dict]   (SELECT singola riga)
- execute()   → int              (INSERT/UPDATE/DELETE)
- count()     → int              (SELECT COUNT)
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
        """Restituisce la connessione attiva (o ne crea una nuova)."""
        try:
            if cls._instance is None or not cls._instance.is_connected():
                cls._instance = mysql.connector.connect(
                    host=DATABASE['host'],
                    user=DATABASE['user'],
                    password=DATABASE['password'],
                    database=DATABASE['database'],
                    charset='utf8mb4',
                    autocommit=False
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
        """
        Esegue una SELECT e ritorna TUTTE le righe.

        Returns:
            list[dict] — lista di dizionari (può essere vuota [])
        """
        conn = cls.get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(query, params or ())
            rows: Any = cursor.fetchall()
            cursor.close()
            result: list[dict[str, Any]] = list(rows) if rows else []
            return result

        except Error as e:
            print(f"[DB] Errore query: {e}")
            print(f"[DB] Query: {query}")
            print(f"[DB] Params: {params}")
            raise

    @classmethod
    def fetch_one(cls, query: str,
                  params: Optional[tuple[Any, ...]] = None
                  ) -> Optional[dict[str, Any]]:
        """
        Esegue una SELECT e ritorna UNA SOLA riga.

        Returns:
            dict se trovata, None se nessun risultato
        """
        conn = cls.get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(query, params or ())
            row: Any = cursor.fetchone()
            cursor.close()

            if row is None:
                return None

            result: dict[str, Any] = dict(row)
            return result

        except Error as e:
            print(f"[DB] Errore query: {e}")
            print(f"[DB] Query: {query}")
            print(f"[DB] Params: {params}")
            raise

    @classmethod
    def execute(cls, query: str,
                params: Optional[tuple[Any, ...]] = None
                ) -> int:
        """
        Esegue INSERT/UPDATE/DELETE e fa commit.

        Returns:
            int — lastrowid per INSERT, rowcount per UPDATE/DELETE
        """
        conn = cls.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(query, params or ())
            conn.commit()
            last_id: int = cursor.lastrowid or 0
            cursor.close()
            return last_id

        except Error as e:
            conn.rollback()
            print(f"[DB] Errore query: {e}")
            print(f"[DB] Query: {query}")
            print(f"[DB] Params: {params}")
            raise

    @classmethod
    def execute_many(cls, query: str,
                     data_list: list[tuple[Any, ...]]
                     ) -> int:
        """Esegue una query con molti set di parametri."""
        conn = cls.get_connection()
        cursor = conn.cursor()

        try:
            cursor.executemany(query, data_list)
            conn.commit()
            count: int = cursor.rowcount
            cursor.close()
            return count
        except Error as e:
            conn.rollback()
            print(f"[DB] Errore bulk: {e}")
            raise

    @classmethod
    def count(cls, query: str,
              params: Optional[tuple[Any, ...]] = None
              ) -> int:
        """
        Esegue una SELECT COUNT(*) AS n e ritorna il numero.

        Returns:
            int — il conteggio
        """
        row: Optional[dict[str, Any]] = cls.fetch_one(query, params)
        if row is not None and 'n' in row:
            return int(row['n'])
        return 0

    @classmethod
    def close(cls) -> None:
        """Chiude la connessione."""
        if cls._instance is not None:
            try:
                if cls._instance.is_connected():
                    cls._instance.close()
                    print("[DB] Connessione chiusa")
            except Exception:
                pass
            cls._instance = None


# --- Test standalone ---
if __name__ == '__main__':
    try:
        conn = DB.get_connection()
        info: str = conn.get_server_info()
        print(f"Server MySQL: {info}")

        tables: list[dict[str, Any]] = DB.fetch_all("SHOW TABLES")
        print(f"\nTabelle nel database '{DATABASE['database']}':")
        for t in tables:
            nome: str = str(list(t.values())[0])
            n: int = DB.count(
                f"SELECT COUNT(*) AS n FROM `{nome}`"
            )
            print(f"  📋 {nome}: {n} righe")

        DB.close()
    except Exception as e:
        print(f"❌ Errore: {e}")