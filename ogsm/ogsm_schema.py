"""
Domain models for OGSM schema.
"""

from pydantic import BaseModel, Field


class MeasureItem(BaseModel):
    id: str = Field(..., description="Unique code for the Measure e.g. M1.1")
    strategy_id: str = Field(..., description="Parent Strategy ID e.g. S1")
    description: str = Field(..., description="Actionable measure details")
    unit: str = Field(default="Percent", description="Unit of metric")
    target: float = Field(..., description="Target quantitative milestone")
    actual: float = Field(default=0.0, description="Actual achieved value")
    owner: str = Field(..., description="Responsible department/person")
    status: str = Field(default="In Progress", description="Status")


class StrategyItem(BaseModel):
    id: str = Field(...)
    goal_id: str = Field(...)
    description: str = Field(...)


class GoalItem(BaseModel):
    id: str = Field(...)
    objective_id: str = Field(...)
    description: str = Field(...)


class ObjectiveItem(BaseModel):
    id: str = Field(...)
    title: str = Field(...)
    description: str = Field(...)
