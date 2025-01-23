import aiosqlite as aq

# import logging

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

class ClientDatabaseHandler:
    def __init__(self, db_path="app/clients.db"):
        self.db_path = db_path

    async def add_order(self, client_id: int, product_id: int):
        """Создание нового заказа для клиента."""
        async with aq.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO orders (client_id, product_id, status, payment_status)
                VALUES (?, ?, 'pending', 'waiting_for_payment')
                """,
                (client_id, product_id)
            )
            await db.commit()

    async def get_client_orders(self, client_id: int):
        """Получение всех заказов клиента."""
        async with aq.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT o.id, o.product_id, p.name, p.price, o.status, o.payment_status, o.created_at
                FROM orders o
                JOIN products p ON o.product_id = p.id
                WHERE o.client_id = ?
                ORDER BY o.created_at DESC
                """,
                (client_id,)
            )
            orders = await cursor.fetchall()
            return [
                {
                    "order_id": row[0],
                    "product_id": row[1],
                    "product_name": row[2],
                    "price": row[3],
                    "status": row[4],
                    "payment_status": row[5],
                    "created_at": row[6],
                }
                for row in orders
            ]

    async def cancel_order(self, order_id: int, client_id: int):
        """Отмена заказа клиента."""
        async with aq.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE orders
                SET status = 'cancelled'
                WHERE id = ? AND client_id = ? AND status = 'pending'
                """,
                (order_id, client_id)
            )
            await db.commit()

    async def get_categories(self):
        """Получение всех доступных категорий."""
        async with aq.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT id, name
                FROM categories
                ORDER BY name ASC
                """
            )
            categories = await cursor.fetchall()
            return [{"category_id": row[0], "name": row[1]} for row in categories]
        
    async def get_products_by_category(self, category_id: int):
        """Получение списка товаров из указанной категории."""
        async with aq.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT id, name, description, price, available_until
                FROM products
                WHERE category_id = ? AND is_active = TRUE
                AND (available_until IS NULL OR available_until > CURRENT_TIMESTAMP)
                ORDER BY created_at DESC
                """,
                (category_id,)
            )
            products = await cursor.fetchall()
            return [
                {
                    "product_id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "price": row[3],
                    "available_until": row[4],
                }
                for row in products
            ]

    
    async def get_available_products(self):
        """Получение списка доступных товаров."""
        async with aq.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT id, name, description, price, available_until
                FROM products
                WHERE is_active = TRUE AND (available_until IS NULL OR available_until > CURRENT_TIMESTAMP)
                ORDER BY created_at DESC
                """
            )
            products = await cursor.fetchall()
            return [
                {
                    "product_id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "price": row[3],
                    "available_until": row[4],
                }
                for row in products
            ]

    async def get_order_details(self, order_id: int, client_id: int):
        """Получение деталей заказа клиента."""
        async with aq.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT o.id, p.name, p.description, p.price, o.status, o.payment_status, o.created_at
                FROM orders o
                JOIN products p ON o.product_id = p.id
                WHERE o.id = ? AND o.client_id = ?
                """,
                (order_id, client_id)
            )
            order = await cursor.fetchone()
            if order:
                return {
                    "order_id": order[0],
                    "product_name": order[1],
                    "product_description": order[2],
                    "price": order[3],
                    "status": order[4],
                    "payment_status": order[5],
                    "created_at": order[6],
                }
            return None

class ExecutorDatabaseHandler:
    def __init__(self, db_path="app/clients.db"):
        self.db_path = db_path

    async def get_available_orders(self):
        """Получение всех доступных заказов для исполнения."""
        async with aq.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT o.id, o.client_id, p.name, p.description, p.price, o.status, o.created_at
                FROM orders o
                JOIN products p ON o.product_id = p.id
                WHERE o.status = 'pending'
                ORDER BY o.created_at ASC
                """
            )
            orders = await cursor.fetchall()
            return [
                {
                    "order_id": row[0],
                    "client_id": row[1],
                    "product_name": row[2],
                    "product_description": row[3],
                    "price": row[4],
                    "status": row[5],
                    "created_at": row[6],
                }
                for row in orders
            ]

    async def assign_executor_to_order(self, order_id: int):
        """Автоматическое назначение свободного исполнителя на заказ."""
        async with aq.connect(self.db_path) as db:
            # Получение первого доступного исполнителя
            cursor = await db.execute(
                """
                SELECT id FROM users
                WHERE role_id = (SELECT id FROM roles WHERE name = 'executor')
                AND is_available = TRUE
                LIMIT 1
                """
            )
            executor = await cursor.fetchone()
            print(executor)
            if executor:
                executor_id = executor[0]

                # Назначение исполнителя на заказ
                await db.execute(
                    """
                    UPDATE orders
                    SET executor_id = ?, status = 'in_progress'
                    WHERE id = ?
                    """,
                    (executor_id, order_id)
                )

                # Обновление статуса исполнителя на "занят"
                await db.execute(
                    """
                    UPDATE users
                    SET is_available = FALSE
                    WHERE id = ?
                    """,
                    (executor_id,)
                )

                await db.commit()
                return executor_id
            else:
                return None

    async def mark_order_as_completed(self, order_id: int):
        """Завершение заказа и освобождение исполнителя."""
        async with aq.connect(self.db_path) as db:
            # Получение исполнителя, назначенного на заказ
            cursor = await db.execute(
                """
                SELECT executor_id FROM orders
                WHERE id = ?
                """,
                (order_id,)
            )
            executor = await cursor.fetchone()

            if executor:
                executor_id = executor[0]

                # Завершение заказа
                await db.execute(
                    """
                    UPDATE orders
                    SET status = 'completed', updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (order_id,)
                )

                # Освобождение исполнителя
                await db.execute(
                    """
                    UPDATE users
                    SET is_available = TRUE
                    WHERE id = ?
                    """,
                    (executor_id,)
                )

                await db.commit()
                return True

            return False

    async def report_issue(self, executor_id: int, order_id: int, description: str):
        """Сообщение о проблеме с заказом."""
        async with aq.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO order_issues (order_id, executor_id, description, status)
                VALUES (?, ?, ?, 'open')
                """,
                (order_id, executor_id, description)
            )
            await db.commit()

    async def get_assigned_orders(self, executor_id: int):
        """Получение всех заказов, назначенных исполнителю."""
        async with aq.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT o.id, p.name, p.description, p.price, o.status, o.payment_status, o.created_at
                FROM orders o
                JOIN products p ON o.product_id = p.id
                WHERE o.executor_id = ?
                ORDER BY o.created_at DESC
                """,
                (executor_id,)
            )
            orders = await cursor.fetchall()
            return [
                {
                    "order_id": row[0],
                    "product_name": row[1],
                    "product_description": row[2],
                    "price": row[3],
                    "status": row[4],
                    "payment_status": row[5],
                    "created_at": row[6],
                }
                for row in orders
            ]

    async def resolve_issue(self, issue_id: int):
        """Закрытие проблемы с заказом."""
        async with aq.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE order_issues
                SET status = 'resolved', resolved_at = CURRENT_TIMESTAMP
                WHERE id = ? AND status = 'open'
                """,
                (issue_id,)
            )
            await db.commit()

# ----Создание базы данных----
async def create_tables():
    async with aq.connect("app/clients.db") as db:
        
        # Таблица ролей
        await db.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(50) UNIQUE NOT NULL
            )
        """)
        
        # Таблица пользователей
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id BIGINT UNIQUE NOT NULL,
            role_id INTEGER REFERENCES roles(id),
            email VARCHAR(255),
            verification_code VARCHAR(10),
            is_available BOOLEAN DEFAULT TRUE, -- Исполнитель доступен или нет
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Таблица товаров
        await db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                price NUMERIC(10, 2) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                available_until TIMESTAMP -- Срок, до которого товар доступен
            )
        """)
        
        # Таблица заказов
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER REFERENCES users(id),
                product_id INTEGER REFERENCES products(id),
                status VARCHAR(50) DEFAULT 'pending',
                payment_status VARCHAR(50) DEFAULT 'waiting_for_payment',
                executor_id INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Таблица истории операций
        await db.execute("""
            CREATE TABLE IF NOT EXISTS operation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id),
                operation_type VARCHAR(50) NOT NULL,
                target_table VARCHAR(50),
                target_id INTEGER,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Таблица для хранения заказов с проблемой
        await db.execute("""
        CREATE TABLE IF NOT EXISTS order_issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER REFERENCES orders(id),
            executor_id INTEGER REFERENCES users(id),
            description TEXT NOT NULL, -- Описание проблемы
            status VARCHAR(50) DEFAULT 'open', -- Статус проблемы (open, resolved, unresolved)
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP -- Время решения проблемы
        )
        """)
        
        await db.commit()

async def add_categories_to_db():
    async with aq.connect("app/clients.db") as db:
        # Создание таблицы категорий
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(255) NOT NULL UNIQUE
            )
            """
        )

        # Добавление связи между товарами и категориями
        await db.execute(
            """
            ALTER TABLE products
            ADD COLUMN category_id INTEGER REFERENCES categories(id)
            """
        )

        await db.commit()


class AdminDatabaseHandler:
    def __init__(self, db_path="app/clients.db"):
        self.db_path = db_path

    async def create_product(self, name: str, description: str, price: float, available_until=None):
        """Создание нового товара."""
        async with aq.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO products (name, description, price, available_until)
                VALUES (?, ?, ?, ?)
                """,
                (name, description, price, available_until)
            )
            await db.commit()

    async def update_product(self, product_id: int, name: str = None, description: str = None, price: float = None, available_until=None):
        """Обновление существующего товара."""
        async with aq.connect(self.db_path) as db:
            query = "UPDATE products SET "
            params = []

            if name is not None:
                query += "name = ?, "
                params.append(name)

            if description is not None:
                query += "description = ?, "
                params.append(description)

            if price is not None:
                query += "price = ?, "
                params.append(price)

            if available_until is not None:
                query += "available_until = ?, "
                params.append(available_until)

            query = query.rstrip(", ") + " WHERE id = ?"
            params.append(product_id)

            await db.execute(query, params)
            await db.commit()

    async def delete_product(self, product_id: int):
        """Удаление товара."""
        async with aq.connect(self.db_path) as db:
            await db.execute(
                """
                DELETE FROM products
                WHERE id = ?
                """,
                (product_id,)
            )
            await db.commit()

    async def get_all_products(self):
        """Получение списка всех товаров."""
        async with aq.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT id, name, description, price, created_at, available_until, is_active
                FROM products
                ORDER BY created_at DESC
                """
            )
            products = await cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "price": row[3],
                    "created_at": row[4],
                    "available_until": row[5],
                    "is_active": row[6],
                }
                for row in products
            ]

# Пример использования логики клиента
# if __name__ == "__main__":
#     import asyncio

#     async def main():
#         client_db = ClientDatabaseHandler()

#         # Пример добавления заказа
#         await client_db.add_order(client_id=1, product_id=2)

#         # Пример получения всех заказов клиента
#         orders = await client_db.get_client_orders(client_id=1)
#         print("Заказы клиента:", orders)

#         # Пример отмены заказа
#         await client_db.cancel_order(order_id=1, client_id=1)

#         # Пример получения доступных товаров
#         products = await client_db.get_available_products()
#         print("Доступные товары:", products)

#         # Пример получения деталей заказа
#         order_details = await client_db.get_order_details(order_id=1, client_id=1)
#         print("Детали заказа:", order_details)

#     asyncio.run(main())

# Пример использования логики исполнителя
# if __name__ == "__main__":
#     import asyncio

#     async def main():
#         executor_db = ExecutorDatabaseHandler()

#         # Пример автоматического назначения исполнителя
#         assigned_executor = await executor_db.assign_executor_to_order(order_id=1)
#         if assigned_executor:
#             print(f"Исполнитель с ID {assigned_executor} назначен на заказ.")
#         else:
#             print("Нет доступных исполнителей.")

#         # Пример завершения заказа
#         completed = await executor_db.mark_order_as_completed(order_id=1)
#         if completed:
#             print("Заказ завершён, исполнитель освобождён.")
#         else:
#             print("Не удалось завершить заказ.")

#     asyncio.run(main())

# Пример использования логики администратора
# if __name__ == "__main__":
#     import asyncio

#     async def main():
#         admin_db = AdminDatabaseHandler()

#         # Создание товара
#         await admin_db.create_product(
#             name="Пример товара",
#             description="Описание примера товара",
#             price=99.99,
#             available_until="2025-12-31 23:59:59",
#         )
#         print("Товар создан.")

#         # Обновление товара
#         await admin_db.update_product(
#             product_id=1,
#             name="Обновлённый товар",
#             price=109.99,
#         )
#         print("Товар обновлён.")

#         # Получение списка товаров
#         products = await admin_db.get_all_products()
#         print("Список товаров:", products)

#         # Удаление товара
#         await admin_db.delete_product(product_id=1)
#         print("Товар удалён.")
#     asyncio.run(main())
