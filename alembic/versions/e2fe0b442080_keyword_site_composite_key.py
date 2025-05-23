"""KeywordSite 복합키로 변경

Revision ID: e2fe0b442080
Revises: 874f88d33a9f
Create Date: 2025-05-13 10:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# Enum을 사용하기 위해 모델 파일에서 가져올 수 있도록 경로를 맞춰주세요.
# 실제 프로젝트 구조에 따라 이 부분은 수정이 필요할 수 있습니다.
# from app.src.domain.hotdeal.enums import SiteName # 이 파일에서는 직접 사용하지 않으므로 주석처리 또는 삭제 가능


# revision identifiers, used by Alembic.
revision: str = "e2fe0b442080"
down_revision: str | None = "874f88d33a9f"  # 이전 리비전 ID로 수정
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    # 기존 id 컬럼 PK 제약조건 이름 확인 필요 (보통 hotdeal_keyword_sites_pkey)
    # 만약 테이블 생성 시 PK 이름을 명시적으로 지정했다면 그 이름을 사용해야 합니다.
    # 일반적으로 Alembic이 자동으로 생성한 PK 제약조건 이름은 <테이블명>_pkey 입니다.
    op.drop_constraint(
        "hotdeal_keyword_sites_pkey", "hotdeal_keyword_sites", type_="primary"
    )
    op.drop_column("hotdeal_keyword_sites", "id")

    # keyword_id 와 site_name 컬럼을 복합 PK로 설정
    op.create_primary_key(
        "pk_hotdeal_keyword_sites",  # 새로운 복합 PK 제약조건 이름
        "hotdeal_keyword_sites",
        ["keyword_id", "site_name"],
    )

    # 기존 UniqueConstraint('uq_keyword_site')가 존재하면 삭제
    bind = op.get_bind()
    result = bind.execute(
        sa.text(
            "SELECT 1 FROM pg_constraint "
            "WHERE conname = 'uq_keyword_site' "
            "AND conrelid = (SELECT oid FROM pg_class WHERE relname = 'hotdeal_keyword_sites' AND relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = current_schema()))"
        )
    ).scalar_one_or_none()

    if result == 1:
        op.drop_constraint("uq_keyword_site", "hotdeal_keyword_sites", type_="unique")
        print("INFO: Constraint 'uq_keyword_site' found and dropped.")
    else:
        print("INFO: Constraint 'uq_keyword_site' does not exist, skipping drop.")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    # 복합 PK 제약조건 제거
    op.drop_constraint(
        "pk_hotdeal_keyword_sites", "hotdeal_keyword_sites", type_="primary"
    )

    # id 컬럼 다시 추가 및 PK로 설정
    op.add_column(
        "hotdeal_keyword_sites",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
    )
    op.create_primary_key("hotdeal_keyword_sites_pkey", "hotdeal_keyword_sites", ["id"])

    # UniqueConstraint 다시 추가 (이 부분은 주석 해제)
    op.create_unique_constraint(
        "uq_keyword_site", "hotdeal_keyword_sites", ["keyword_id", "site_name"]
    )
    # ### end Alembic commands ###
