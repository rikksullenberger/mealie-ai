from pydantic import Field

from ._base import OpenAIBase


class OpenAIRecipeTags(OpenAIBase):
    categories: list[str] = Field(
        [],
        description="A list of categories that the recipe belongs to (e.g. 'Breakfast', 'Italian', 'Soup').",
    )
    tags: list[str] = Field(
        [],
        description="A list of tags that apply to the recipe (e.g. 'Gluten-Free', 'Spicy', 'Kid-Friendly').",
    )
