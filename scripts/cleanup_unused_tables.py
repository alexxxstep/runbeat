#!/usr/bin/env python3
"""
Скрипт для очищення невикористаних таблиць з бази даних.

Аналізує структуру проекту, знаходить всі таблиці, які використовуються в коді,
і видаляє ті таблиці з БД, які не використовуються.

Використання:
    python scripts/cleanup_unused_tables.py [--yes] [--dry-run]

Аргументи:
    --yes      Автоматично підтвердити видалення (без інтерактивного запиту)
    --dry-run  Тільки показати, які таблиці будуть видалені, без видалення
"""
import os
import sys
import re
import argparse
from pathlib import Path
from typing import Set, List
from supabase import create_client
from loguru import logger

# Додаємо шлях до backend для імпорту налаштувань
backend_path = Path(__file__).parent.parent / "apps" / "backend"
sys.path.insert(0, str(backend_path))

try:
    from app.core.config import settings
except ImportError:
    logger.error("Не вдалося імпортувати налаштування. Переконайтеся, що ви в корені проекту.")
    sys.exit(1)


# Системні таблиці Supabase, які не потрібно видаляти
SYSTEM_TABLES = {
    'schema_migrations',
    'supabase_migrations',
    'storage.objects',
    'storage.buckets',
    'auth.users',
    'auth.sessions',
    'auth.refresh_tokens',
    'auth.audit_log_entries',
    'realtime.schema_migrations',
    'pg_stat_statements',
    'pg_stat_statements_info',
}


def get_all_tables_from_db_via_psycopg2() -> Set[str]:
    """
    Отримує список всіх таблиць з бази даних через psycopg2.
    Потрібен DATABASE_URL з environment variables або Supabase connection string.
    """
    try:
        import psycopg2
        from urllib.parse import urlparse

        # Спробуємо отримати connection string з environment
        database_url = os.getenv('DATABASE_URL') or os.getenv('SUPABASE_DB_URL')

        if not database_url:
            logger.warning("DATABASE_URL не знайдено в environment variables.")
            logger.info("Додайте DATABASE_URL до .env файлу або використайте інший метод.")
            return set()

        logger.info("Підключаюся до бази даних через psycopg2...")

        conn = psycopg2.connect(database_url)
        cur = conn.cursor()

        # Отримуємо список таблиць з public схеми
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)

        tables = {row[0] for row in cur.fetchall()}

        cur.close()
        conn.close()

        logger.info(f"Отримано {len(tables)} таблиць з бази даних")
        return tables

    except ImportError:
        logger.warning("psycopg2 не встановлено. Встановіть: pip install psycopg2-binary")
        return set()
    except Exception as e:
        logger.error(f"Помилка при підключенні до БД через psycopg2: {e}")
        return set()


def get_tables_from_sql_query(supabase_client) -> Set[str]:
    """
    Отримує список таблиць через SQL запит.
    Потрібно виконати SQL запит вручну або через Supabase Dashboard.
    """
    sql_query = """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_type = 'BASE TABLE'
    ORDER BY table_name;
    """

    logger.info("SQL запит для отримання списку таблиць:")
    logger.info(sql_query)
    logger.info("\nВиконайте цей запит в Supabase SQL Editor і введіть результати.")

    return set()


def find_used_tables_in_code(project_root: Path) -> Set[str]:
    """Знаходить всі таблиці, які використовуються в коді проекту."""
    used_tables = set()

    # Патерни для пошуку використання таблиць
    patterns = [
        r'\.table\(["\']([^"\']+)["\']\)',  # .table("table_name")
        r'FROM\s+([a-z_]+)\s+',  # FROM table_name
        r'JOIN\s+([a-z_]+)\s+',  # JOIN table_name
        r'INTO\s+([a-z_]+)\s+',  # INTO table_name
        r'UPDATE\s+([a-z_]+)\s+',  # UPDATE table_name
        r'DELETE\s+FROM\s+([a-z_]+)\s+',  # DELETE FROM table_name
    ]

    # Директорії для пошуку
    search_dirs = [
        project_root / "apps" / "backend",
    ]

    # Розширення файлів для пошуку
    extensions = ['.py', '.ts', '.tsx', '.js', '.jsx', '.sql']

    logger.info("Сканую код проекту на використання таблиць...")

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue

        for ext in extensions:
            for file_path in search_dir.rglob(f"*{ext}"):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                        for pattern in patterns:
                            matches = re.finditer(pattern, content, re.IGNORECASE)
                            for match in matches:
                                table_name = match.group(1).lower().strip()
                                # Фільтруємо системні таблиці та невалідні назви
                                if table_name and table_name not in SYSTEM_TABLES:
                                    if re.match(r'^[a-z_][a-z0-9_]*$', table_name):
                                        used_tables.add(table_name)

                except Exception as e:
                    logger.debug(f"Помилка при читанні {file_path}: {e}")
                    continue

    logger.info(f"Знайдено використаних таблиць в коді: {len(used_tables)}")
    return used_tables


def get_tables_from_db_via_supabase(supabase_client) -> Set[str]:
    """
    Спроба отримати таблиці через Supabase client.
    Використовує обхідний шлях через тестування таблиць.
    """
    # Список можливих таблиць з міграції
    known_tables = {
        'users', 'workouts', 'playlists', 'conversations', 'error_logs'
    }

    existing_tables = set()

    logger.info("Перевіряю наявність таблиць в БД...")

    for table in known_tables:
        try:
            # Спробуємо зробити простий запит до таблиці
            result = supabase_client.table(table).select("id").limit(1).execute()
            existing_tables.add(table)
            logger.info(f"  ✓ Таблиця '{table}' існує")
        except Exception as e:
            # Якщо таблиця не існує, помилка буде містити інформацію про це
            error_msg = str(e).lower()
            if 'does not exist' in error_msg or 'relation' in error_msg:
                logger.debug(f"  ✗ Таблиця '{table}' не існує")
            else:
                # Якщо помилка інша, можливо таблиця існує, але є проблема з доступом
                existing_tables.add(table)
                logger.warning(f"  ? Таблиця '{table}' - невідомий статус: {e}")

    return existing_tables


def delete_table_via_psycopg2(table_name: str) -> bool:
    """Видаляє таблицю з бази даних через psycopg2."""
    try:
        import psycopg2

        database_url = os.getenv('DATABASE_URL') or os.getenv('SUPABASE_DB_URL')

        if not database_url:
            logger.error("DATABASE_URL не знайдено. Неможливо видалити таблицю.")
            return False

        conn = psycopg2.connect(database_url)
        conn.autocommit = True  # Для DDL операцій
        cur = conn.cursor()

        logger.warning(f"⚠️  Видалення таблиці '{table_name}'...")
        cur.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")

        cur.close()
        conn.close()

        logger.info(f"✅ Таблиця '{table_name}' видалена успішно")
        return True

    except ImportError:
        logger.error("psycopg2 не встановлено. Неможливо видалити таблицю.")
        return False
    except Exception as e:
        logger.error(f"Помилка при видаленні таблиці '{table_name}': {e}")
        return False


def main():
    """Головна функція скрипта."""
    parser = argparse.ArgumentParser(
        description="Очищення невикористаних таблиць з бази даних"
    )
    parser.add_argument(
        '--yes',
        action='store_true',
        help='Автоматично підтвердити видалення (без інтерактивного запиту)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Тільки показати, які таблиці будуть видалені, без видалення'
    )
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Скрипт очищення невикористаних таблиць")
    if args.dry_run:
        logger.info("🔍 DRY-RUN режим (таблиці не будуть видалені)")
    logger.info("=" * 60)

    # Отримуємо корінь проекту
    project_root = Path(__file__).parent.parent

    # Ініціалізуємо Supabase client
    try:
        supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_KEY
        )
        logger.info("✓ Підключення до Supabase успішне")
    except Exception as e:
        logger.error(f"Помилка підключення до Supabase: {e}")
        sys.exit(1)

    # Знаходимо використані таблиці в коді
    used_tables = find_used_tables_in_code(project_root)
    logger.info(f"\n📋 Використані таблиці в коді ({len(used_tables)}):")
    for table in sorted(used_tables):
        logger.info(f"  - {table}")

    # Отримуємо таблиці з БД
    # Спробуємо через psycopg2 (якщо DATABASE_URL доступний)
    db_tables = get_all_tables_from_db_via_psycopg2()

    # Якщо не вдалося через psycopg2, спробуємо через Supabase client
    if not db_tables:
        logger.info("Спробую отримати таблиці через Supabase client...")
        db_tables = get_tables_from_db_via_supabase(supabase_client)

    if not db_tables:
        logger.warning("\n⚠️  Не вдалося автоматично отримати список таблиць з БД.")
        logger.info("Можливі рішення:")
        logger.info("1. Додайте DATABASE_URL до .env файлу (Supabase connection string)")
        logger.info("2. Використайте SQL запит в Supabase SQL Editor:")
        logger.info("""
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_type = 'BASE TABLE'
ORDER BY table_name;
        """)
        logger.info("\nАбо вкажіть таблиці вручну в коді скрипта.")
        return

    logger.info(f"\n📊 Таблиці в базі даних ({len(db_tables)}):")
    for table in sorted(db_tables):
        logger.info(f"  - {table}")

    # Знаходимо невикористані таблиці
    unused_tables = db_tables - used_tables - SYSTEM_TABLES

    # Фільтруємо системні таблиці
    unused_tables = {t for t in unused_tables if not t.startswith('_') and t not in SYSTEM_TABLES}

    logger.info(f"\n🔍 Аналіз:")
    logger.info(f"  Використані в коді: {len(used_tables)}")
    logger.info(f"  В базі даних: {len(db_tables)}")
    logger.info(f"  Невикористані: {len(unused_tables)}")

    if not unused_tables:
        logger.info("\n✅ Всі таблиці використовуються в проекті. Нічого видаляти.")
        return

    logger.warning(f"\n⚠️  Знайдено невикористаних таблиць ({len(unused_tables)}):")
    for table in sorted(unused_tables):
        logger.warning(f"  - {table}")

    # Підтвердження видалення
    if args.dry_run:
        logger.info("\n" + "=" * 60)
        logger.info("🔍 DRY-RUN: Таблиці НЕ будуть видалені")
        logger.info("=" * 60)
        # Показуємо SQL скрипт для dry-run
        logger.info("\n📝 SQL скрипт для видалення невикористаних таблиць:")
        logger.info("=" * 60)
        logger.info("-- Виконайте цей SQL в Supabase SQL Editor:")
        logger.info("")
        for table in sorted(unused_tables):
            logger.info(f"DROP TABLE IF EXISTS {table} CASCADE;")
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ Dry-run завершено. Таблиці не були видалені.")
        return

    if not args.yes:
        logger.info("\n" + "=" * 60)
        response = input("Видалити невикористані таблиці? (yes/no): ").strip().lower()

        if response != 'yes':
            logger.info("Операцію скасовано.")
            return

    # Спробуємо видалити через psycopg2
    database_url = os.getenv('DATABASE_URL') or os.getenv('SUPABASE_DB_URL')

    if database_url:
        logger.info("\n🗑️  Видаляю таблиці через psycopg2...")
        deleted_count = 0
        for table in sorted(unused_tables):
            if delete_table_via_psycopg2(table):
                deleted_count += 1

        logger.info(f"\n✅ Видалено {deleted_count} з {len(unused_tables)} таблиць")
    else:
        # Генеруємо SQL скрипт для видалення
        logger.info("\n📝 SQL скрипт для видалення невикористаних таблиць:")
        logger.info("=" * 60)
        logger.info("-- Виконайте цей SQL в Supabase SQL Editor:")
        logger.info("")

        for table in sorted(unused_tables):
            logger.info(f"DROP TABLE IF EXISTS {table} CASCADE;")

        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ Скрипт завершено. Виконайте SQL запити вручну в Supabase SQL Editor.")
        logger.info("💡 Або додайте DATABASE_URL до .env для автоматичного видалення.")


if __name__ == "__main__":
    main()

