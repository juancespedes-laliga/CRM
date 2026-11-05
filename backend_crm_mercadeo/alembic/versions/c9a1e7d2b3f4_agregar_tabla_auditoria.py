"""agregar tabla auditoria

Revision ID: c9a1e7d2b3f4
Revises: b7f3c1a9d420
Create Date: 2026-11-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9a1e7d2b3f4'
down_revision: Union[str, Sequence[str], None] = 'b7f3c1a9d420'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "mercadeo_crm_auditoria",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("fecha", sa.DateTime(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("ip", sa.String(length=45), nullable=True),
        sa.Column("modulo", sa.String(length=30), nullable=False),
        sa.Column("accion", sa.String(length=30), nullable=False),
        sa.Column("origen", sa.String(length=20), nullable=False),
        sa.Column("proceso_id", sa.BigInteger(), nullable=True),
        sa.Column("registro_id", sa.Integer(), nullable=False),
        sa.Column("registro_nombre", sa.String(length=150), nullable=True),
        sa.Column("documento", sa.String(length=20), nullable=True),
        sa.Column("titular_id", sa.Integer(), nullable=True),
        sa.Column("estado_antes", sa.String(length=20), nullable=True),
        sa.Column("estado_despues", sa.String(length=20), nullable=True),
        sa.Column("fecha_ingreso", sa.Date(), nullable=True),
        sa.Column("renovado", sa.String(length=1), nullable=True),
        sa.Column("fecha_renovado", sa.Date(), nullable=True),
        sa.Column("motivo", sa.String(length=500), nullable=True),
        sa.Column("cambios", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["usuario_id"], ["intranet_usuarios.id"]),
        sa.ForeignKeyConstraint(["proceso_id"], ["mercadeo_crm_historial_procesos.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    # Consultas tipicas: log de un modulo por rango de fechas, e historial de un registro.
    op.create_index("ix_auditoria_modulo_fecha", "mercadeo_crm_auditoria", ["modulo", "fecha"])
    op.create_index("ix_auditoria_modulo_registro", "mercadeo_crm_auditoria", ["modulo", "registro_id"])

    # Autonumeracion de "id" (secuencia + trigger BEFORE INSERT): mismo patron
    # que mercadeo_crm_titular_color y el resto de tablas mercadeo_crm_*.
    conn = op.get_bind()
    conn.exec_driver_sql(
        "CREATE SEQUENCE seq_auditoria START WITH 1 INCREMENT BY 1 NOCACHE"
    )
    conn.exec_driver_sql(
        """
        CREATE OR REPLACE TRIGGER trg_auditoria_bi
        BEFORE INSERT ON mercadeo_crm_auditoria
        FOR EACH ROW
        WHEN (NEW.id IS NULL)
        BEGIN
            SELECT seq_auditoria.NEXTVAL INTO :NEW.id FROM dual;
        END;
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    conn.exec_driver_sql(
        """
        BEGIN
            EXECUTE IMMEDIATE 'DROP TRIGGER trg_auditoria_bi';
        EXCEPTION
            WHEN OTHERS THEN
                IF SQLCODE != -4080 THEN RAISE; END IF;
        END;
        """
    )
    conn.exec_driver_sql(
        """
        BEGIN
            EXECUTE IMMEDIATE 'DROP SEQUENCE seq_auditoria';
        EXCEPTION
            WHEN OTHERS THEN
                IF SQLCODE != -2289 THEN RAISE; END IF;
        END;
        """
    )
    op.drop_index("ix_auditoria_modulo_registro", table_name="mercadeo_crm_auditoria")
    op.drop_index("ix_auditoria_modulo_fecha", table_name="mercadeo_crm_auditoria")
    op.drop_table("mercadeo_crm_auditoria")
