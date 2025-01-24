import asyncio
import aiosqlite as aq

async def insert_test_data():
    async with aq.connect("app/clients.db") as db:
        # Очищаем таблицы перед вставкой тестовых данных
        await db.execute("DELETE FROM roles")
        await db.execute("DELETE FROM users")
        await db.execute("DELETE FROM categories")
        await db.execute("DELETE FROM products")
        await db.execute("DELETE FROM orders")
        await db.execute("DELETE FROM operation_history")
        await db.execute("DELETE FROM order_issues")

        # Вставляем роли
        await db.executemany(
            "INSERT INTO roles (name) VALUES (?)",
            [("client",), ("executor",), ("admin",)]
        )
        
        # Вставляем пользователей
        await db.executemany(
            """
            INSERT INTO users (telegram_id, role_id, email, verification_code, is_available)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (123456789, 1, "client1@example.com", "ABC123", None),
                (987654321, 2, "executor1@example.com", "XYZ456", True),
                (1122334455, 3, "admin@example.com", "ADM789", None),
            ]
        )
        
        # Вставляем категории
        await db.executemany(
            "INSERT INTO categories (name) VALUES (?)",
            [("Акции",), ("Гемы",), ("БП",)]
        )
        
        # Вставляем товары
        await db.executemany(
            """
            INSERT INTO products (name, description, price, is_active, category_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                # Товары в категории "Акции"
                ("Гемы по 100 (Акции)", "Гемы со скидкой", 100.00, True, 1),
                ("Гемы по 50 (Акции)", "Гемы со скидкой", 50.00, True, 1),
                
                # Товары в категории "Гемы"
                ("Гемы по 100 (Гемы)", "Гемы без скидки", 150.00, True, 2),
                ("Гемы по 50 (Гемы)", "Гемы без скидки", 75.00, True, 2),

                # Товары в категории "БП"
                ("Боевой Пропуск", "Полный доступ к боевому пропуску", 999.00, True, 3),
            ]
        )
        
        # Вставляем заказы
        await db.executemany(
            """
            INSERT INTO orders (client_id, product_ids, status, payment_status)
            VALUES (?, ?, ?, ?)
            """,
            [
                (1, "[1,2]", "pending", "waiting_for_payment"),
                (1, "[3,5]", "completed", "paid"),
            ]
        )
        
        # Вставляем историю операций
        await db.executemany(
            """
            INSERT INTO operation_history (user_id, operation_type, target_table, target_id, details)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (1, "create", "orders", 1, "Created order #1"),
                (2, "update", "products", 1, "Updated product details"),
            ]
        )
        
        # Вставляем проблемные заказы
        await db.executemany(
            """
            INSERT INTO order_issues (order_id, executor_id, description, status)
            VALUES (?, ?, ?, ?)
            """,
            [
                (1, 2, "Delayed delivery", "open"),
                (2, 2, "Incorrect item delivered", "resolved"),
            ]
        )
        
        await db.commit()

# Выполняем скрипт для вставки данных
if __name__ == "__main__":
    asyncio.run(insert_test_data())
