from __future__ import with_statement
from alembic import context
from sqlalchemy import engine_from_config, pool
from logging.config import fileConfig
import os

# Importa la aplicación y el metadata de los modelos
from app import create_app, db

# Configuración de logging
fileConfig(context.config.config_file_name)

# Crear la aplicación Flask y cargar su configuración
app = create_app()

# Usar el contexto de la aplicación para obtener la metadata de los modelos
with app.app_context():
    context.config.set_main_option('sqlalchemy.url', app.config['SQLALCHEMY_DATABASE_URI'])
    target_metadata = db.metadata

def run_migrations_offline():
    """Ejecución en modo offline."""
    url = context.config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Ejecución en modo online."""
    connectable = engine_from_config(
        context.config.get_section(context.config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
