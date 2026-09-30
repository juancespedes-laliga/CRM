"""agregar tabla titular color

Revision ID: b7f3c1a9d420
Revises: 29f4e6d30d1f
Create Date: 2026-09-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7f3c1a9d420'
down_revision: Union[str, Sequence[str], None] = '29f4e6d30d1f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "mercadeo_crm_titular_color",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("titular_id", sa.Integer(), nullable=False),
        sa.Column("color", sa.String(length=7), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("fecha_actualizacion", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["titular_id"], ["intranet_planliga.id"]),
        sa.ForeignKeyConstraint(["usuario_id"], ["intranet_usuarios.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("titular_id"),
    )

    # Autonumeracion de "id" (secuencia + trigger BEFORE INSERT): mismo patron
    # que el resto de tablas mercadeo_crm_* creadas despues de
    # 4e379ceb9f70_agregar_identity_a_ids_crm_mercadeo.py (ver esa migracion
    # para el porque de secuencia+trigger en vez de IDENTITY nativo).
    conn = op.get_bind()
    conn.exec_driver_sql(
        "CREATE SEQUENCE seq_titular_color START WITH 1 INCREMENT BY 1 NOCACHE"
    )
    conn.exec_driver_sql(
        """
        CREATE OR REPLACE TRIGGER trg_titular_color_bi
        BEFORE INSERT ON mercadeo_crm_titular_color
        FOR EACH ROW
        WHEN (NEW.id IS NULL)
        BEGIN
            SELECT seq_titular_color.NEXTVAL INTO :NEW.id FROM dual;
        END;
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    conn.exec_driver_sql(
        """
        BEGIN
            EXECUTE IMMEDIATE 'DROP TRIGGER trg_titular_color_bi';
        EXCEPTION
            WHEN OTHERS THEN
                IF SQLCODE != -4080 THEN RAISE; END IF;
        END;
        """
    )
    conn.exec_driver_sql(
        """
        BEGIN
            EXECUTE IMMEDIATE 'DROP SEQUENCE seq_titular_color';
        EXCEPTION
            WHEN OTHERS THEN
                IF SQLCODE != -2289 THEN RAISE; END IF;
        END;
        """
    )
    op.drop_table("mercadeo_crm_titular_color")
