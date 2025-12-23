# AI Context & Project Status

## Critical Build Instructions
- **NEVER** build the image locally ("context: ."). It causes high load and crashes the user's machine due to resource exhaustion (frontend + backend compilation).
- **ALWAYS** use Docker Cloud Build.
- **Builder Name**: `cloud-rikksullenber-mealie-ai`
- **Setup**: `docker buildx use cloud-rikksullenber-mealie-ai` <there is a dev area with the 3.8.x files in it
- **Workflow**: Refer to `.agent/workflows/build_cloud.md` for the exact procedure.

## Recent Changes (v3.8.7)
### Fixes
1.  **Frontend**: Fixed `Module not found: use-notifier` in `frontend/pages/admin/maintenance/index.vue`.
    -   *Solution*: Replaced missing `useNotifier` with `alert` from `~/composables/use-toast`.
2.  **Backend**: Fixed `AttributeError: type object 'ReportCategory' has no attribute 'ai_image_generation'`.
    -   *Solution*: Added `ai_image_generation` to the `ReportCategory` enum in `mealie/schema/reports/reports.py`.

3.  **Backend**: Fixed `AttributeError: 'OpenAIRecipeService' object has no attribute 'get_one'`.
    -   *Solution*: Changed `OpenAIRecipeService` inheritance from `RecipeServiceBase` to `RecipeService`.

4.  **Frontend**: Fixed Image Regeneration Dialog ignoring user prompts.
    -   *Solution*: Updated `RecipeGenerateImageDialog.vue` to use `regenerateAiImage` API method.

5.  **Frontend**: Fixed missing translation keys for Image Generation dialog.
    -   *Solution*: Added `describe-recipe-hint` and `generate` keys to `en-US.json` and added a tooltip to the magic wand button.

6.  **Frontend**: Corrected UI labels to explicitly refer to "Image Generation".
    -   *Solution*: Created properties `recipe.generate-image*` and updated dialog to use them, avoiding confusion with recipe generation.

7.  **Frontend**: Refined UI text per user request.
    -   *Solution*: Updated dialog to say "Generate AI image" and "Describe the image to generate".

### Versioning
- Current Version: **3.8.17**
- Tags: `v3.8.17`, `latest`
- Platforms: `linux/amd64`, `linux/arm64`

## Current Status (2025-12-23)
- **Auto Image Generation**: Validated as **working**.
- **Auto Tagging**: Validated as **working** in **v3.8.8**.
- **Image Regeneration**: Fixed custom prompt support in **v3.8.9**.
- **UI Labels**: Refined text in **v3.8.13**.

## Next Steps
- **Security**: Fix vulnerabilities in the codebase.
