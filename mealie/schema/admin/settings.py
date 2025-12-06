from typing import Annotated

from pydantic import ConfigDict, Field, field_validator
from slugify import slugify

from mealie.schema._mealie import MealieModel

from ..recipe.recipe_category import RecipeCategoryResponse


class CustomPageBase(MealieModel):
    name: str
    slug: str | None = Field(default=None, validate_default=True)
    position: int
    categories: list[RecipeCategoryResponse] = []
    model_config = ConfigDict(from_attributes=True)

    @field_validator("slug", mode="before")
    def validate_slug(slug: str | None, info):
        name: str = info.data.get("name", "")
        calc_slug: str = slugify(name)

        if slug != calc_slug:
            slug = calc_slug

        return slug


class CustomPageOut(CustomPageBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
