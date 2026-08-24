"""
SIH26162 — Thermal Classification & Risk Repository.

Provides async storage and querying for ML classifications and risk assessments.
"""

from typing import Any, Dict, List, Optional, Sequence, Tuple
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.classification import ThermalClassification
from app.models.risk_assessment import RiskAssessment
from app.repositories.base_repository import BaseRepository


class ClassificationRepository(BaseRepository[ThermalClassification]):
    """Repository handling ML classifications and joined risk assessments."""

    def __init__(self, session: AsyncSession):
        super().__init__(ThermalClassification, session)

    async def create_classification_with_risk(
        self,
        classification_data: Dict[str, Any],
        risk_data: Optional[Dict[str, Any]] = None,
    ) -> ThermalClassification:
        """Create a classification and its associated risk assessment in a single transaction."""
        clf = ThermalClassification(**classification_data)
        self.session.add(clf)
        await self.session.flush()

        if risk_data:
            risk_data["classification_id"] = clf.id
            if "observation_id" not in risk_data and clf.observation_id:
                risk_data["observation_id"] = clf.observation_id
            risk = RiskAssessment(**risk_data)
            self.session.add(risk)
            await self.session.flush()
            clf.risk_assessment = risk

        return clf

    async def query_classifications(
        self,
        predicted_class: Optional[str] = None,
        min_confidence: Optional[float] = None,
        risk_level: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[Sequence[ThermalClassification], int]:
        """Query classifications with risk level filtering and eager loading."""
        conditions = []
        if predicted_class:
            conditions.append(ThermalClassification.predicted_class == predicted_class)
        if min_confidence is not None:
            conditions.append(ThermalClassification.confidence >= min_confidence)

        query = (
            select(ThermalClassification)
            .options(selectinload(ThermalClassification.risk_assessment))
        )

        if risk_level:
            query = query.join(ThermalClassification.risk_assessment).where(
                RiskAssessment.risk_level == risk_level.upper()
            )

        if conditions:
            query = query.where(and_(*conditions))

        # Count
        count_stmt = select(func.count(ThermalClassification.id))
        if risk_level:
            count_stmt = count_stmt.join(ThermalClassification.risk_assessment).where(
                RiskAssessment.risk_level == risk_level.upper()
            )
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))

        total_count = (await self.session.execute(count_stmt)).scalar() or 0

        query = query.order_by(ThermalClassification.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return result.scalars().all(), total_count
