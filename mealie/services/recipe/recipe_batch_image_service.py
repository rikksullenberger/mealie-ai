"""
Batch AI Image Generation Service

Service for scanning recipes and generating AI images for those missing images.
Uses OpenAI's DALL-E 3 to create professional food photography images.
"""
import asyncio
from uuid import UUID

from pydantic import UUID4

from mealie.lang.providers import Translator
from mealie.repos.repository_factory import AllRepositories
from mealie.schema.recipe.recipe import Recipe
from mealie.schema.reports.reports import (
    ReportCategory,
    ReportCreate,
    ReportEntryCreate,
    ReportEntryOut,
    ReportSummaryStatus,
)
from mealie.schema.household.household import HouseholdInDB
from mealie.schema.user.user import GroupInDB
from mealie.services._base_service import BaseService
from mealie.services.recipe.recipe_data_service import RecipeDataService
from mealie.services.recipe.recipe_service import RecipeService
from mealie.services.openai import OpenAIService


class RecipeBatchImageService(BaseService):
    """Service for batch generating AI images for recipes without images."""

    report_entries: list[ReportEntryCreate]

    def __init__(
        self,
        recipe_service: RecipeService,
        repos: AllRepositories,
        group: GroupInDB,
        household: HouseholdInDB,
        translator: Translator,
    ) -> None:
        self.recipe_service = recipe_service
        self.repos = repos
        self.group = group
        self.household = household
        self.report_entries = []
        self.translator = translator
        self.report = None

        super().__init__()

    def get_report_id(self) -> UUID4:
        """Create a new report for tracking batch image generation progress."""
        report = ReportCreate(
            name="Batch AI Image Generation",
            category=ReportCategory.ai_image_generation,
            status=ReportSummaryStatus.in_progress,
            group_id=self.group.id,
        )

        self.report = self.repos.group_reports.create(report)
        return self.report.id

    def _add_error_entry(self, message: str, exception: str = "") -> None:
        """Add an error entry to the report."""
        if self.report is None:
            return

        self.report_entries.append(
            ReportEntryCreate(
                report_id=self.report.id,
                success=False,
                message=message,
                exception=exception,
            )
        )

    def _add_success_entry(self, message: str) -> None:
        """Add a success entry to the report."""
        if self.report is None:
            return

        self.report_entries.append(
            ReportEntryCreate(
                report_id=self.report.id,
                success=True,
                message=message,
                exception="",
            )
        )

    def _save_all_entries(self) -> None:
        """Save all report entries and update final status."""
        if self.report is None:
            return

        is_success = True
        is_failure = True

        new_entries: list[ReportEntryOut] = []
        for entry in self.report_entries:
            if is_failure and entry.success:
                is_failure = False

            if is_success and not entry.success:
                is_success = False

            new_entries.append(self.repos.group_report_entries.create(entry))

        if is_success:
            self.report.status = ReportSummaryStatus.success

        if is_failure:
            self.report.status = ReportSummaryStatus.failure

        if not is_success and not is_failure:
            self.report.status = ReportSummaryStatus.partial

        self.report.entries = new_entries
        self.repos.group_reports.update(self.report.id, self.report)

    async def generate_missing_images(self) -> None:
        """
        Scan all recipes in the household and generate AI images for those without images.
        
        This method:
        1. Queries all recipes in the household
        2. Filters for recipes without images that user can edit
        3. Generates AI images concurrently (max 3 at a time)
        4. Tracks progress and errors in a report
        """
        # Create semaphore to limit concurrent API calls
        sem = asyncio.Semaphore(3)

        async def _generate_for_recipe(recipe: Recipe) -> None:
            """Generate AI image for a single recipe."""
            async with sem:
                try:
                    # Fetch full recipe to get settings and ingredients
                    full_recipe = self.repos.recipes.get_by_slug(self.group.id, recipe.slug)
                    if not full_recipe:
                        return
                    


                    # Verify if a valid image exists on disk
                    # We check disk regardless of DB state to avoid overwrites and handle sync issues
                    data_service = RecipeDataService(full_recipe.id)
                    
                    # Check for valid image files: exists, correct extension, size > 0 bytes
                    valid_extensions = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
                    has_valid_image = False
                    
                    if data_service.dir_image.exists():
                        all_files = list(data_service.dir_image.iterdir())
                        for f in all_files:
                            is_file = f.is_file()
                            suffix = f.suffix.lower()
                            size = f.stat().st_size if is_file else 0
                            is_valid = is_file and suffix in valid_extensions and size > 0
                            
                            if is_valid:
                                has_valid_image = True
                                self.logger.debug(f"Found valid image for {full_recipe.slug}: {f.name}")
                                break
                    if has_valid_image:
                        self.logger.debug(f"Skipping recipe {full_recipe.slug} - valid image exists on disk")
                        return

                    if full_recipe.image and not has_valid_image:
                         self.logger.info(f"Recipe {full_recipe.slug} has DB image but no valid files on disk. Generating new image.")

                    # Build prompt from recipe data
                    prompt_parts = [f"A hyper-realistic, professional food photography shot of {full_recipe.name}. The image must be photorealistic and not cartoony or illustrated."]

                    if full_recipe.description:
                        prompt_parts.append(full_recipe.description)

                    # Add key ingredients for context
                    if full_recipe.recipe_ingredient and len(full_recipe.recipe_ingredient) > 0:
                        ingredients = [ing.note for ing in full_recipe.recipe_ingredient[:5] if ing.note]
                        if ingredients:
                            prompt_parts.append(f"Key ingredients: {', '.join(ingredients)}.")

                    prompt = " ".join(prompt_parts)

                    # Generate the image
                    openai_service = OpenAIService()
                    image_data = await openai_service.generate_image(prompt)

                    if not image_data:
                        raise ValueError("Failed to generate image from OpenAI")

                    # Save the image
                    data_service = RecipeDataService(full_recipe.id)
                    data_service.write_image(image_data, "webp")

                    # Update the recipe image reference
                    self.recipe_service.group_recipes.update_image(full_recipe.slug, "webp")

                    self._add_success_entry(f"Successfully generated AI image for recipe: {full_recipe.name}")
                    self.logger.info(f"Generated AI image for recipe {full_recipe.slug}")

                except Exception as e:
                    self.logger.error(f"Failed to generate AI image for recipe {recipe.slug}: {e}")
                    self.logger.exception(e)
                    self._add_error_entry(
                        f"Failed to generate image for recipe '{recipe.name}' ({recipe.slug})", str(e)
                    )

        # Initialize report
        if self.report is None:
            self.get_report_id()

        # Get all recipes in the household
        try:
            # Query recipes without pagination to get all
            all_recipes = self.repos.recipes.get_all()

            if not all_recipes:
                self._add_success_entry("No recipes found to process")
                self._save_all_entries()
                return

            # Process all recipes to check for missing files even if DB says image exists
            recipes_to_process = all_recipes

            if not recipes_to_process:
                self._add_success_entry("No recipes found to process")
                self._save_all_entries()
                return

            self.logger.info(
                f"Scanning {len(recipes_to_process)} recipes for missing images..."
            )

            # Generate images concurrently
            tasks = [_generate_for_recipe(recipe) for recipe in recipes_to_process]
            await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            self.logger.error(f"Failed during batch image generation: {e}")
            self.logger.exception(e)
            self._add_error_entry("Batch image generation failed", str(e))

        # Save all entries and update report status
        self._save_all_entries()
