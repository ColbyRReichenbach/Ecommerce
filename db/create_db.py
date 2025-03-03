from sqlalchemy import text
from ecommerce_data_project.config.db_config import engine


def create_database():
    """Creates the database schema from the schema.sql file."""
    with engine.connect() as connection:
        with open("db/schema.sql", "r") as f:
            schema_sql = f.read()
        statements = schema_sql.split(";")

        for statement in statements:
            if statement.strip():
                connection.execute(text(statement))

        print("Database schema created successfully!")


if __name__ == "__main__":
    create_database()
