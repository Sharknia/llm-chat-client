"""user_keywords 테이블 keyword_id 외래 키에 ON DELETE CASCADE 추가

Revision ID: 332742179f0c
Revises: 8a91ecfb95a9
Create Date: 2025-05-07 23:41:35.977670

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "332742179f0c"
down_revision: str | None = "8a91ecfb95a9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(
        "user_keywords_keyword_id_fkey", "user_keywords", type_="foreignkey"
    )
    op.create_foreign_key(
        "user_keywords_keyword_id_fkey",  # 제약 조건 이름
        "user_keywords",  # 소스 테이블 (외래 키가 있는 테이블)
        "hotdeal_keywords",  # 참조 대상 테이블
        ["keyword_id"],  # 소스 테이블의 외래 키 컬럼
        ["id"],  # 참조 대상 테이블의 컬럼
        ondelete="CASCADE",
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(
        "user_keywords_keyword_id_fkey", "user_keywords", type_="foreignkey"
    )
    op.create_foreign_key(
        "user_keywords_keyword_id_fkey",
        "user_keywords",
        "hotdeal_keywords",
        ["keyword_id"],
        ["id"],
    )
    # ### end Alembic commands ###
