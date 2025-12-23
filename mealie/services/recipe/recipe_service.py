import json
import os
import shutil
from datetime import UTC, datetime
from pathlib import Path
from shutil import copytree, rmtree
from typing import Any
from uuid import UUID, uuid4
from zipfile import ZipFile

from fastapi import UploadFile

from mealie.core import exceptions
from mealie.core.config import get_app_settings
from mealie.core.dependencies.dependencies import get_temporary_path
from mealie.lang.providers import Translator
from mealie.pkgs import cache
from mealie.repos.all_repositories import get_repositories
from mealie.repos.repository_factory import AllRepositories
from mealie.repos.repository_generic import RepositoryGeneric
from mealie.schema.household.household import HouseholdInDB, HouseholdRecipeUpdate
from mealie.schema.openai.recipe import OpenAIRecipe
from mealie.schema.recipe.recipe import CreateRecipe, Recipe, create_recipe_slug
from mealie.schema.recipe.recipe_ingredient import RecipeIngredient
from mealie.schema.recipe.recipe_notes import RecipeNote
from mealie.schema.recipe.recipe_settings import RecipeSettings
from mealie.schema.recipe.recipe_step import RecipeStep
from mealie.schema.recipe.recipe_timeline_events import RecipeTimelineEventCreate, TimelineEventType
from mealie.schema.recipe.request_helpers import RecipeDuplicate
from mealie.schema.user.user import PrivateUser, UserRatingCreate
from mealie.services._base_service import BaseService
from mealie.services.household_services.household_service import HouseholdService
from mealie.services.openai import OpenAIDataInjection, OpenAILocalImage, OpenAIService
from mealie.schema.openai.auto_tag import OpenAIRecipeTags
from mealie.services.recipe.recipe_data_service import RecipeDataService
from mealie.services.scraper import cleaner

from .template_service import TemplateService


class RecipeServiceBase(BaseService):
    def __init__(self, repos: AllRepositories, user: PrivateUser, household: HouseholdInDB, translator: Translator):
        self.repos = repos
        self.user = user
        self.household = household

        if repos.group_id != user.group_id != household.group_id:
            raise Exception("group ids do not match")
        if repos.household_id != user.household_id != household.id:
            raise Exception("household ids do not match")

        self.group_recipes = get_repositories(repos.session, group_id=repos.group_id, household_id=None).recipes
        """Recipes repo without a Household filter"""

        self.translator = translator
        self.t = translator.t

        super().__init__()

    def _transform_category_or_tag(self, data: dict, repo: RepositoryGeneric) -> dict:
        slug = data.get("slug")
        if not slug:
            return data

        # if the item exists, return the actual data
        query = repo.get_one(slug, "slug")
        if query:
            return query.model_dump()

        # otherwise, create the item
        new_item = repo.create(data)
        return new_item.model_dump()


class RecipeService(RecipeServiceBase):
    def _get_recipe(self, data: str | UUID, key: str | None = None) -> Recipe:
        recipe = self.group_recipes.get_one(data, key)
        if recipe is None:
            raise exceptions.NoEntryFound("Recipe not found.")
        return recipe

    def can_delete(self, recipe: Recipe) -> bool:
        if self.user.admin:
            return True
        else:
            return self.can_update(recipe)

    def can_update(self, recipe: Recipe) -> bool:
        if recipe.settings is None:
            raise exceptions.UnexpectedNone("Recipe Settings is None")

        # Check if this user owns the recipe
        if self.user.id == recipe.user_id:
            return True

        # Check if this user has permission to edit this recipe
        if self.household.id != recipe.household_id:
            other_household = self.repos.households.get_one(recipe.household_id)
            if not (other_household and other_household.preferences):
                return False
            if other_household.preferences.lock_recipe_edits_from_other_households:
                return False
        if recipe.settings.locked:
            return False

        return True

    def can_lock_unlock(self, recipe: Recipe) -> bool:
        return recipe.user_id == self.user.id

    def check_assets(self, recipe: Recipe, original_slug: str) -> None:
        """Checks if the recipe slug has changed, and if so moves the assets to a new file with the new slug."""
        if original_slug != recipe.slug:
            current_dir = self.directories.RECIPE_DATA_DIR.joinpath(original_slug)

            try:
                copytree(current_dir, recipe.directory, dirs_exist_ok=True)
                self.logger.debug(f"Renaming Recipe Directory: {original_slug} -> {recipe.slug}")
            except FileNotFoundError:
                self.logger.error(f"Recipe Directory not Found: {original_slug}")

        if recipe.assets is None:
            recipe.assets = []

        all_asset_files = [x.file_name for x in recipe.assets]

        for file in recipe.asset_dir.iterdir():
            if file.is_dir():
                continue
            if file.name not in all_asset_files:
                file.unlink()

    def delete_assets(self, recipe: Recipe) -> None:
        recipe_dir = recipe.directory
        rmtree(recipe_dir, ignore_errors=True)
        self.logger.info(f"Recipe Directory Removed: {recipe.slug}")

    def _recipe_creation_factory(self, name: str, additional_attrs: dict | None = None) -> Recipe:
        """
        The main creation point for recipes. The factor method returns an instance of the
        Recipe Schema class with the appropriate defaults set. Recipes should not be created
        elsewhere to avoid conflicts.
        """
        additional_attrs = additional_attrs or {}
        additional_attrs["name"] = name
        additional_attrs["user_id"] = self.user.id
        additional_attrs["household_id"] = self.household.id
        additional_attrs["group_id"] = self.household.group_id

        if additional_attrs.get("tags"):
            for i in range(len(additional_attrs.get("tags", []))):
                additional_attrs["tags"][i]["group_id"] = self.user.group_id

        if not additional_attrs.get("recipe_ingredient"):
            additional_attrs["recipe_ingredient"] = [
                RecipeIngredient(note=self.t("recipe.recipe-defaults.ingredient-note"))
            ]

        if not additional_attrs.get("recipe_instructions"):
            additional_attrs["recipe_instructions"] = [RecipeStep(text=self.t("recipe.recipe-defaults.step-text"))]

        return Recipe(**additional_attrs)

    def get_one(self, slug_or_id: str | UUID) -> Recipe:
        if isinstance(slug_or_id, str):
            try:
                slug_or_id = UUID(slug_or_id)
            except ValueError:
                pass

        if isinstance(slug_or_id, UUID):
            return self._get_recipe(slug_or_id, "id")

        else:
            return self._get_recipe(slug_or_id, "slug")

    def create_one(self, create_data: Recipe | CreateRecipe) -> Recipe:
        if create_data.name is None:
            create_data.name = "New Recipe"

        data: Recipe = self._recipe_creation_factory(name=create_data.name, additional_attrs=create_data.model_dump())

        if isinstance(create_data, CreateRecipe) or create_data.settings is None:
            if self.household.preferences is not None:
                data.settings = RecipeSettings(
                    public=self.household.preferences.recipe_public,
                    show_nutrition=self.household.preferences.recipe_show_nutrition,
                    show_assets=self.household.preferences.recipe_show_assets,
                    landscape_view=self.household.preferences.recipe_landscape_view,
                    disable_comments=self.household.preferences.recipe_disable_comments,
                )
            else:
                data.settings = RecipeSettings()

        rating_input = data.rating
        data.last_made = None
        new_recipe = self.repos.recipes.create(data)

        # convert rating into user rating
        if rating_input:
            self.repos.user_ratings.create(
                UserRatingCreate(
                    user_id=self.user.id,
                    recipe_id=new_recipe.id,
                    rating=rating_input,
                    is_favorite=False,
                )
            )

        # create first timeline entry
        timeline_event_data = RecipeTimelineEventCreate(
            user_id=new_recipe.user_id,
            recipe_id=new_recipe.id,
            subject=self.t("recipe.recipe-created"),
            event_type=TimelineEventType.system,
            timestamp=new_recipe.created_at or datetime.now(UTC),
        )

        self.repos.recipe_timeline_events.create(timeline_event_data)
        return new_recipe

    def _transform_user_id(self, user_id: str) -> str:
        query = self.repos.users.get_one(user_id)
        if query:
            return user_id
        else:
            # default to the current user
            return str(self.user.id)

    def _process_recipe_data(self, key: str, data: list | dict | Any):
        if isinstance(data, list):
            return [self._process_recipe_data(key, item) for item in data]

        elif isinstance(data, str):
            # make sure the user is valid
            if key == "user_id":
                return self._transform_user_id(str(data))

            return data

        elif not isinstance(data, dict):
            return data

        # force group_id and household_id to match the group id of the current user
        data["group_id"] = str(self.user.group_id)
        data["household_id"] = str(self.user.household_id)

        # make sure categories and tags are valid
        if key == "recipe_category":
            return self._transform_category_or_tag(data, self.repos.categories)
        elif key == "tags":
            return self._transform_category_or_tag(data, self.repos.tags)

        # recursively process other objects
        for k, v in data.items():
            data[k] = self._process_recipe_data(k, v)

        return data

    def clean_recipe_dict(self, recipe: dict[str, Any]) -> dict[str, Any]:
        return self._process_recipe_data("recipe", recipe)

    def create_from_zip(self, archive: UploadFile, temp_path: Path) -> Recipe:
        """
        `create_from_zip` creates a recipe in the database from a zip file exported from Mealie. This is NOT
        a generic import from a zip file.
        """
        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(archive.file, buffer)

        recipe_dict: dict | None = None
        recipe_image: bytes | None = None

        with ZipFile(temp_path) as myzip:
            for file in myzip.namelist():
                if file.endswith(".json"):
                    with myzip.open(file) as myfile:
                        recipe_dict = json.loads(myfile.read())
                elif file.endswith(".webp"):
                    with myzip.open(file) as myfile:
                        recipe_image = myfile.read()

        if recipe_dict is None:
            raise exceptions.UnexpectedNone("No json data found in Zip")

        recipe = self.create_one(Recipe(**self.clean_recipe_dict(recipe_dict)))

        if recipe and recipe.id:
            data_service = RecipeDataService(recipe.id)

        if recipe_image:
            data_service.write_image(recipe_image, "webp")

        return recipe

    async def create_from_images(self, images: list[UploadFile], translate_language: str | None = None) -> Recipe:
        openai_recipe_service = OpenAIRecipeService(self.repos, self.user, self.household, self.translator)
        with get_temporary_path() as temp_path:
            local_images: list[Path] = []
            for image in images:
                with temp_path.joinpath(image.filename).open("wb") as buffer:
                    shutil.copyfileobj(image.file, buffer)
                local_images.append(temp_path.joinpath(image.filename))

            recipe_data = await openai_recipe_service.build_recipe_from_images(
                local_images, translate_language=translate_language
            )
            recipe_data = cleaner.clean(recipe_data, self.translator)

            recipe = self.create_one(recipe_data)
            data_service = RecipeDataService(recipe.id)

            with open(local_images[0], "rb") as f:
                data_service.write_image(f.read(), "webp")
            return recipe

    def duplicate_one(self, old_slug_or_id: str | UUID, dup_data: RecipeDuplicate) -> Recipe:
        """Duplicates a recipe and returns the new recipe."""

        old_recipe = self.get_one(old_slug_or_id)
        new_recipe_data = old_recipe.model_dump(exclude={"id", "name", "slug", "image", "comments"}, round_trip=True)
        new_recipe = Recipe.model_validate(new_recipe_data)

        # Asset images in steps directly link to the original recipe, so we
        # need to update them to references to the assets we copy below
        def replace_recipe_step(step: RecipeStep) -> RecipeStep:
            new_id = uuid4()
            new_text = step.text.replace(str(old_recipe.id), str(new_recipe.id))
            new_step = step.model_copy(update={"id": new_id, "text": new_text})
            return new_step

        # Copy ingredients to make them independent of the original
        def copy_recipe_ingredient(ingredient: RecipeIngredient):
            new_reference_id = uuid4()
            new_ingredient = ingredient.model_copy(update={"reference_id": new_reference_id})
            return new_ingredient

        new_name = dup_data.name if dup_data.name else old_recipe.name or ""
        new_recipe.id = uuid4()
        new_recipe.slug = create_recipe_slug(new_name)
        new_recipe.image = cache.cache_key.new_key() if old_recipe.image else None
        new_recipe.recipe_instructions = (
            None
            if old_recipe.recipe_instructions is None
            else list(map(replace_recipe_step, old_recipe.recipe_instructions))
        )
        new_recipe.recipe_ingredient = (
            None
            if old_recipe.recipe_ingredient is None
            else list(map(copy_recipe_ingredient, old_recipe.recipe_ingredient))
        )
        new_recipe.last_made = None

        new_recipe = self._recipe_creation_factory(new_name, additional_attrs=new_recipe.model_dump())

        new_recipe = self.repos.recipes.create(new_recipe)

        # Copy all assets (including images) to the new recipe directory
        # This assures that replaced links in recipe steps continue to work when the old recipe is deleted
        try:
            new_service = RecipeDataService(new_recipe.id)
            old_service = RecipeDataService(old_recipe.id)
            copytree(
                old_service.dir_data,
                new_service.dir_data,
                dirs_exist_ok=True,
            )
        except Exception as e:
            self.logger.error(f"Failed to copy assets from {old_recipe.slug} to {new_recipe.slug}: {e}")

        return new_recipe

    def has_recursive_recipe_link(self, recipe: Recipe, path: set[str] | None = None):
        """Recursively checks if a recipe links to itself through its ingredients."""
        if path is None:
            path = set()

        recipe_id = str(getattr(recipe, "id", None))

        # Check if this recipe is already in the current path (cycle detected)
        if recipe_id in path:
            return True

        # Add to the current path
        path.add(recipe_id)

        try:
            ingredients = getattr(recipe, "recipe_ingredient", [])
            for ing in ingredients:
                try:
                    sub_recipe = self.get_one(ing.referenced_recipe.id)
                except (AttributeError, exceptions.NoEntryFound):
                    continue

                # Recursively check - path is modified in place and cleaned up via backtracking
                if self.has_recursive_recipe_link(sub_recipe, path):
                    return True
        finally:
            # Backtrack: remove this recipe from the path when done exploring this branch
            path.discard(recipe_id)

        return False

    def _pre_update_check(self, slug_or_id: str | UUID, new_data: Recipe) -> Recipe:
        """
        gets the recipe from the database and performs a check to see if the user can update the recipe.
        If the user can't update the recipe, an exception is raised.

        Checks:
            - That the recipe exists
            - That the user can update the recipe (recipe is not locked or the user is the owner)
            - _if_ the user is locking the recipe, that they can lock the recipe (user is the owner)

        Args:
            slug_or_id (str | UUID): recipe slug or id
            new_data (Recipe): the new recipe data

        Raises:
            exceptions.PermissionDenied (403)
        """

        recipe = self.get_one(slug_or_id)

        if recipe is None or recipe.settings is None:
            raise exceptions.NoEntryFound("Recipe not found.")

        if not self.can_update(recipe):
            raise exceptions.PermissionDenied("You do not have permission to edit this recipe.")

        setting_lock = new_data.settings is not None and recipe.settings.locked != new_data.settings.locked
        if setting_lock and not self.can_lock_unlock(recipe):
            raise exceptions.PermissionDenied("You do not have permission to lock/unlock this recipe.")

        if self.has_recursive_recipe_link(new_data):
            raise exceptions.RecursiveRecipe("Recursive recipe link detected. Update aborted.")

        return recipe

    def update_one(self, slug_or_id: str | UUID, update_data: Recipe) -> Recipe:
        recipe = self._pre_update_check(slug_or_id, update_data)

        new_data = self.group_recipes.update(recipe.slug, update_data)
        self.check_assets(new_data, recipe.slug)
        return new_data

    def update_recipe_image(self, slug: str, image: bytes, extension: str):
        recipe = self.get_one(slug)
        if not self.can_update(recipe):
            raise exceptions.PermissionDenied("You do not have permission to edit this recipe.")

        data_service = RecipeDataService(recipe.id)
        data_service.write_image(image, extension)

        return self.group_recipes.update_image(slug, extension)

    def delete_recipe_image(self, slug: str) -> None:
        recipe = self.get_one(slug)
        if not self.can_update(recipe):
            raise exceptions.PermissionDenied("You do not have permission to edit this recipe.")

        data_service = RecipeDataService(recipe.id)
        data_service.delete_image()

        self.group_recipes.delete_image(slug)
        return None

    def patch_one(self, slug_or_id: str | UUID, patch_data: Recipe) -> Recipe:
        recipe: Recipe = self._pre_update_check(slug_or_id, patch_data)

        new_data = self.group_recipes.patch(recipe.slug, patch_data.model_dump(exclude_unset=True))

        self.check_assets(new_data, recipe.slug)
        return new_data

    async def generate_ai_recipe_image(self, slug_or_id: str | UUID, regenerate: bool = False, custom_text: str | None = None) -> Recipe:
        """
        Generate or regenerate an AI image for a recipe using OpenAI.
        
        Args:
            slug_or_id: Recipe slug or ID
            regenerate: If True, regenerates even if image exists. If False, only generates if no image exists.
            custom_text: Optional custom text to append to the image prompt (e.g., "Boneless ribs")
        
        Returns:
            Updated recipe with new AI-generated image
        
        Raises:
            exceptions.PermissionDenied: If user doesn't have permission to update the recipe
            ValueError: If OpenAI is not enabled or image services are disabled
        """
        settings = get_app_settings()
        
        if not settings.OPENAI_ENABLED:
            raise ValueError("OpenAI is not enabled")
        
        if not settings.OPENAI_ENABLE_IMAGE_SERVICES:
            raise ValueError("OpenAI image services are not enabled")
        
        recipe = self.get_one(slug_or_id)
        
        if not self.can_update(recipe):
            raise exceptions.PermissionDenied("You do not have permission to edit this recipe.")
        
        # Check if image exists and regenerate flag
        if recipe.image and not regenerate:
            self.logger.info(f"Recipe {recipe.slug} already has an image, skipping generation")
            return recipe
        
        # Build a detailed prompt from recipe data
        prompt_parts = [f"A high quality, professional food photography shot of {recipe.name}."]
        
        if recipe.description:
            prompt_parts.append(recipe.description)
        
        # Add some key ingredients to the prompt for better context
        if recipe.recipe_ingredient and len(recipe.recipe_ingredient) > 0:
            ingredients = [ing.note for ing in recipe.recipe_ingredient[:5] if ing.note]
            if ingredients:
                prompt_parts.append(f"Key ingredients: {', '.join(ingredients)}.")

        if custom_text:
            prompt_parts.append(f"Additional details: {custom_text}")
        
        prompt = " ".join(prompt_parts)
        
        # Generate the image
        openai_service = OpenAIService()
        try:
            image_data = await openai_service.generate_image(prompt)
            
            if not image_data:
                raise ValueError("Failed to generate image from OpenAI")
            
            # Save the image
            data_service = RecipeDataService(recipe.id)
            data_service.write_image(image_data, "webp")
            
            # Update the recipe image reference
            image_key = self.group_recipes.update_image(recipe.slug, "webp")
            recipe.image = str(image_key)
            
            self.logger.info(f"Successfully generated AI image for recipe {recipe.slug}")
            return recipe
            
        except Exception as e:
            self.logger.error(f"Failed to generate AI image for recipe {recipe.slug}: {e}")
            raise

    def update_last_made(self, slug_or_id: str | UUID, timestamp: datetime) -> Recipe:
        # we bypass the pre update check since any user can update a recipe's last made date, even if it's locked,
        # or if the user belongs to a different household

        household_service = HouseholdService(self.user.group_id, self.user.household_id, self.repos)
        household_service.set_household_recipe(slug_or_id, HouseholdRecipeUpdate(last_made=timestamp))

        return self.get_one(slug_or_id)

    def delete_one(self, slug_or_id: str | UUID) -> Recipe:
        recipe = self.get_one(slug_or_id)

        if not self.can_delete(recipe):
            raise exceptions.PermissionDenied("You do not have permission to delete this recipe.")

        data = self.group_recipes.delete(recipe.id, "id")
        self.delete_assets(data)
        return data

    # =================================================================
    # Recipe Template Methods

    def render_template(self, recipe: Recipe, temp_dir: Path, template: str) -> Path:
        t_service = TemplateService(temp_dir)
        return t_service.render(recipe, template)


class OpenAIRecipeService(RecipeService):
    def _convert_recipe(self, openai_recipe: OpenAIRecipe) -> Recipe:
        return Recipe(
            user_id=self.user.id,
            group_id=self.user.group_id,
            household_id=self.household.id,
            name=openai_recipe.name,
            slug=create_recipe_slug(openai_recipe.name),
            description=openai_recipe.description,
            recipe_yield=openai_recipe.recipe_yield,
            total_time=openai_recipe.total_time,
            prep_time=openai_recipe.prep_time,
            perform_time=openai_recipe.perform_time,
            recipe_ingredient=[
                RecipeIngredient(title=ingredient.title, note=ingredient.text)
                for ingredient in openai_recipe.ingredients
                if ingredient.text
            ],
            recipe_instructions=[
                RecipeStep(title=instruction.title, text=instruction.text)
                for instruction in openai_recipe.instructions
                if instruction.text
            ],
            notes=[RecipeNote(title=note.title or "", text=note.text) for note in openai_recipe.notes if note.text],
        )

    async def build_recipe_from_images(self, images: list[Path], translate_language: str | None) -> Recipe:
        settings = get_app_settings()
        if not (settings.OPENAI_ENABLED and settings.OPENAI_ENABLE_IMAGE_SERVICES):
            raise ValueError("OpenAI image services are not available")

        openai_service = OpenAIService()
        prompt = openai_service.get_prompt(
            "recipes.parse-recipe-image",
            data_injections=[
                OpenAIDataInjection(
                    description=(
                        "This is the JSON response schema. You must respond in valid JSON that follows this schema. "
                        "Your payload should be as compact as possible, eliminating unncessesary whitespace. "
                        "Any fields with default values which you do not populate should not be in the payload."
                    ),
                    value=OpenAIRecipe,
                )
            ],
        )

        openai_images = [OpenAILocalImage(filename=os.path.basename(image), path=image) for image in images]
        message = (
            f"Please extract the recipe from the {'images' if len(openai_images) > 1 else 'image'} provided."
            "There should be exactly one recipe."
        )

        if translate_language:
            message += f" Please translate the recipe to {translate_language}."

        try:
            response = await openai_service.get_response(
                prompt, message, images=openai_images, force_json_response=True
            )
        except Exception as e:
            raise Exception("Failed to call OpenAI services") from e

        try:
            openai_recipe = OpenAIRecipe.parse_openai_response(response)
            recipe = self._convert_recipe(openai_recipe)
        except Exception as e:
            raise ValueError("Unable to parse recipe from image") from e

        return recipe

    async def generate_recipe_from_prompt(self, user_prompt: str, include_image: bool = False) -> Recipe:
        openai_service = OpenAIService()
        prompt = openai_service.get_prompt(
            "recipes.generate-recipe",
            data_injections=[
                OpenAIDataInjection(
                    description=(
                        "This is the JSON response schema. You must respond in valid JSON that follows this schema. "
                    ),
                    value=OpenAIRecipe,
                )
            ],
        )

        response_json = await openai_service.get_response(prompt, user_prompt, force_json_response=True)
        if not response_json:
            raise Exception("No response from OpenAI")

        openai_recipe = OpenAIRecipe.parse_openai_response(response_json)
        recipe = self._convert_recipe(openai_recipe)

        if include_image:
            image_prompt = f"A high quality, professional food photography shot of {recipe.name}. {recipe.description or ''}"
            image_data = await openai_service.generate_image(image_prompt)
            if image_data:
                # We need to save the image after the recipe is created in the database
                # so we attach it to the recipe object temporarily or handle it in the caller
                # For now, let's return the recipe and handle image saving in the caller or here if we had the ID.
                # Since this method returns a Recipe object (not yet in DB), we can't save the image to disk yet
                # using RecipeDataService easily without an ID.
                # However, the caller `create_recipe_from_ai` creates the recipe immediately.
                # Let's modify this method to return the image data as well, or handle it differently.
                # Actually, `Recipe` schema has an `image` field but it's usually a filename/key.
                # A better approach is to return the image data alongside the recipe.
                # But to minimize changes, let's attach it to the extras for now or just return a tuple.
                # Wait, `create_recipe_from_ai` in routes calls `create_one`.
                # Let's modify `generate_recipe_from_prompt` to return `(Recipe, bytes | None)`.
                pass

        return recipe

    async def generate_recipe_with_image(self, user_prompt: str, include_image: bool = False) -> tuple[Recipe, bytes | None]:
        recipe = await self.generate_recipe_from_prompt(user_prompt)
        image_data = None
        if include_image:
            openai_service = OpenAIService()
            image_prompt = f"A high quality, professional food photography shot of {recipe.name}. {recipe.description or ''}"
            image_data = await openai_service.generate_image(image_prompt)
        
        return recipe, image_data

    async def auto_tag_recipe(self, slug: str) -> Recipe:
        self.logger.info(f"Auto-tagging processing: {slug}")
        recipe = self.get_one(slug)
        
        # Prepare recipe data for AI
        recipe_data = {
            "name": recipe.name,
            "description": recipe.description,
            "ingredients": [ing.note for ing in recipe.recipe_ingredient if ing.note],
            "instructions": [step.text for step in recipe.recipe_instructions if step.text],
        }
        
        openai_service = OpenAIService()
        prompt = openai_service.get_prompt(
            "recipes.auto-tag",
            data_injections=[
                OpenAIDataInjection(
                    description="Response data.",
                    value=OpenAIRecipeTags,
                )
            ],
        )
        
        try:
            response_json = await openai_service.get_response(
                prompt, 
                json.dumps(recipe_data), 
                force_json_response=True
            )
            
            self.logger.info(f"OpenAI response for {slug}: {response_json}")
            
            if not response_json:
                raise ValueError("No response from OpenAI")

            try:    
                tags_data = OpenAIRecipeTags.parse_openai_response(response_json)
                self.logger.info(f"Parsed tags data for {slug}: categories={tags_data.categories}, tags={tags_data.tags}")
            except Exception as e:
                self.logger.error(f"JSON Validation failed for {slug}. Response: {response_json}")
                raise e
            
            current_tags = [t.slug for t in recipe.tags] if recipe.tags else []
            current_categories = [c.slug for c in recipe.recipe_category] if recipe.recipe_category else []
            
            self.logger.info(f"Current tags for {slug}: {current_tags}")
            self.logger.info(f"Current categories for {slug}: {current_categories}")
            
            new_tags = []
            for tag_name in tags_data.tags:
                tag_slug = create_recipe_slug(tag_name)
                if tag_slug not in current_tags:
                    tag_data = {"name": tag_name, "slug": tag_slug, "group_id": recipe.group_id}
                    processed_tag = self._transform_category_or_tag(tag_data, self.repos.tags)
                    new_tags.append(processed_tag)
                    self.logger.info(f"Adding new tag for {slug}: {tag_name} (slug: {tag_slug})")
            
            new_categories = []
            for cat_name in tags_data.categories:
                cat_slug = create_recipe_slug(cat_name)
                if cat_slug not in current_categories:
                    cat_data = {"name": cat_name, "slug": cat_slug, "group_id": recipe.group_id}
                    processed_cat = self._transform_category_or_tag(cat_data, self.repos.categories)
                    new_categories.append(processed_cat)
                    self.logger.info(f"Adding new category for {slug}: {cat_name} (slug: {cat_slug})")

            if not new_tags and not new_categories:
                self.logger.info(f"No new tags or categories found for {slug}")
                return recipe

            # Update recipe - keep existing tags as objects, convert new tag dicts to objects
            update_data = recipe.model_copy()
            
            # Convert new tag/category dicts to proper Pydantic objects
            from mealie.schema.recipe.recipe import RecipeTag, RecipeCategory
            
            new_tag_objects = [RecipeTag(**tag) for tag in new_tags]
            new_category_objects = [RecipeCategory(**cat) for cat in new_categories]
            
            # Combine existing objects with new objects
            all_tags = list(recipe.tags) + new_tag_objects if recipe.tags else new_tag_objects
            all_categories = list(recipe.recipe_category) + new_category_objects if recipe.recipe_category else new_category_objects
            
            self.logger.info(f"Final tags for {slug}: {[t.name for t in all_tags]}")
            self.logger.info(f"Final categories for {slug}: {[c.name for c in all_categories]}")
            
            update_data.tags = all_tags
            update_data.recipe_category = all_categories
            
            updated_recipe = self.update_one(recipe.slug, update_data)
            self.logger.info(f"Successfully updated recipe {slug} with auto-tags")
            return updated_recipe

        except Exception as e:
            self.logger.error(f"Failed to auto-tag recipe {slug}: {e}")
            raise

    async def remix_recipe(self, original_recipe: Recipe, user_prompt: str) -> Recipe:
        self.logger.info(f"Remixing recipe {original_recipe.slug} with prompt: {user_prompt}")
        
        # Prepare recipe data for AI
        recipe_data = {
            "name": original_recipe.name,
            "description": original_recipe.description,
            "yield": original_recipe.recipe_yield,
            "ingredients": [ing.note for ing in original_recipe.recipe_ingredient if ing.note],
            "instructions": [step.text for step in original_recipe.recipe_instructions if step.text],
        }

        openai_service = OpenAIService()
        prompt = openai_service.get_prompt(
            "recipes.remix-recipe",
            data_injections=[
                 OpenAIDataInjection(
                    description=(
                        "This is the JSON response schema. You must respond in valid JSON that follows this schema. "
                    ),
                    value=OpenAIRecipe,
                )
            ]
        )
        
        full_msg = f"Original Recipe JSON: {json.dumps(recipe_data)}\n\nInstruction: {user_prompt}\n\nPlease output the modified recipe."

        response_json = await openai_service.get_response(prompt, full_msg, force_json_response=True)
        if not response_json:
            raise Exception("No response from OpenAI")

        try:
            openai_recipe = OpenAIRecipe.parse_openai_response(response_json)
            new_recipe = self._convert_recipe(openai_recipe)
            return new_recipe
        except Exception as e:
             self.logger.error(f"Failed to parse OpenAI response: {response_json}")
             raise ValueError("Unable to parse remix recipe") from e
