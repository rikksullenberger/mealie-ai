# Mealie AI

A fork of [Mealie](https://github.com/mealie-recipes/mealie) with enhanced AI capabilities for automatic recipe image generation.

## About This Fork

This is a modified version of the excellent **Mealie** recipe management application, created by the talented team at [mealie-recipes](https://github.com/mealie-recipes). 

### Acknowledgments

**Huge thanks to the original Mealie developers** for creating such an outstanding open-source recipe manager! Their clean architecture, beautiful UI, and thoughtful design made it possible to add this AI image generation feature seamlessly. This fork builds upon their incredible work and wouldn't exist without their dedication to the project.

### What's Different?

This fork adds **comprehensive AI-powered recipe management** features:

#### Latest Updates
- **v3.5.15**: Added **ARM64 Support** (e.g., Raspberry Pi), Security updates (CVE-2025-68146, CVE-2025-8869 analysis), Python 3.13 support, and dependency refreshes
- **v3.5.13**: Recipe Remix feature - Create variations of existing recipes with AI modifications, plus bug fixes for 404 redirects
- **v3.5.8**: Enhanced fusion capabilities for recipe remixing
- **v3.5.5**: Fixed "ChunkLoadError" issues by implementing auto-reload on frontend and improved cache control headers

#### Core AI Features
- **Recipe Remix/Variants**: Transform existing recipes with AI - make them healthier, change cuisines, adjust servings, or create fusion variations
- **AI Recipe Generation**: Generate complete recipes from simple descriptions using GPT-4o or GPT-3.5-turbo
- **AI Image Generation**: Create professional food photography images using DALL-E 3
- **Batch Operations**: Generate missing images for multiple recipes in one click
- **Smart Auto-tagging**: Automatically tag recipes based on their content
- **Custom Image Prompts**: Provide specific instructions for AI-generated recipe images
- **High-Quality Images**: Images are generated at 1024x1024 resolution with professional food photography style
- **Optional Features**: Image generation is disabled by default to avoid unexpected API costs

## Prerequisites

- Docker and Docker Compose
- **OpenAI API Key** (required for AI features)
  - Without an API key, the AI recipe generation and image features will not be visible in the UI
  - Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)

## Installation

### Using Docker Compose (Recommended)

1. **Clone this repository:**
   ```bash
   git clone https://github.com/rikksullenber/mealie-ai.git
   cd mealie-ai
   ```

2. **Configure OpenAI API Key:**
   
   Edit `docker/docker-compose.yml` and add your OpenAI API key:
   ```yaml
   environment:
     OPENAI_API_KEY: "your-openai-api-key-here"
   ```

3. **Build and run:**
   ```bash
   cd docker
   docker compose up -d --build
   ```

4. **Access the application:**
   
   Open your browser to `http://localhost:9091`

### Environment Variables

Required environment variables for AI features:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | Your OpenAI API key | - | Yes (for AI features) |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-3.5-turbo` | No |
| `OPENAI_ENABLE_IMAGE_SERVICES` | Enable image generation | `true` | No |

**Important:** 
- If `OPENAI_API_KEY` is not set, the AI recipe generation menu option will be hidden from the UI.
- `gpt-3.5-turbo` is used by default for maximum compatibility with JSON mode features.
- You can also use `gpt-4o` or `gpt-4` (note: `gpt-4` does not support JSON mode).

## Usage

### Creating a Recipe with AI

1. Navigate to **Create** → **Generate with AI**
2. Enter your recipe description (e.g., "Creamy Italian Carbonara")
3. **Optional**: Check the "Generate Image" checkbox to create an AI-generated image
4. **Optional**: Check the "Auto-Tag" checkbox to automatically tag the recipe
5. Click **Generate**
6. The recipe will be created with all requested AI enhancements

### Recipe Remix (Create Variations)

**New in v3.5.13!** Transform existing recipes with AI:

1. Open any recipe
2. Click the **context menu** (three dots) in the toolbar
3. Select **Remix Recipe**
4. Choose a remix type:
   - **Healthier Version**: Reduce calories, fat, or sodium
   - **Different Cuisine**: Transform to another cuisine style
   - **Adjust Servings**: Scale ingredients up or down
   - **Fusion Recipe**: Combine with another cuisine
   - **Custom Instructions**: Provide specific modification instructions
5. Click **Remix** to generate the new recipe variant
6. The new recipe will be created with modifications and saved separately

### Regenerating Recipe Images

You can regenerate AI images for any recipe:

1. Open a recipe in edit mode
2. Click the **Regenerate Image** button near the image upload area
3. **Optional**: Provide a custom image prompt for specific styling
4. A new AI-generated image will be created and saved

### Cost Considerations

- **Recipe Generation**: Uses GPT-3.5-turbo (standard OpenAI pricing, ~$0.50-1.50 per million tokens)
- **Image Generation**: Uses DALL-E 3 (~$0.04-0.08 per image depending on quality settings)
- Image generation is **optional** and disabled by default to prevent unexpected charges

## Deployment to Remote Server

This repository includes scripts to deploy the AI-enabled Mealie to a remote server using Docker Hub.

### Prerequisites

- Docker Hub account
- Remote server with Docker and Docker Compose installed
- OpenAI API key

### Quick Deployment

1. **Configure deployment:**
   
   Edit `docker-compose.deploy.yml`:
   ```yaml
   OPENAI_API_KEY: "your-openai-api-key-here"
   ```

2. **Update deployment script:**
   
   Edit `deploy-to-remote.py` with your server credentials:
   ```python
   hostname = "your-server-ip"
   username = "your-username"
   password = "your-password"
   ```

3. **Run deployment:**
   ```bash
   python3 deploy-to-remote.py
   ```

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

### Remote Server Access

After deployment, access your instance at:
```
http://your-server-ip:9099
```

## Development

### Building from Source

```bash
# Install dependencies
task setup

# Run backend
task py

# Run frontend (in separate terminal)
task ui

# Build Docker image
task docker:build-from-package
```

### Running Tests

```bash
# Backend tests
task py:test

# Frontend tests
task ui:test
```

## Changes from Original Mealie

### Backend
- **`mealie/schema/recipe/recipe.py`**: Added `include_image` field to `CreateRecipeAI`
- **`mealie/services/openai/openai.py`**: Added `generate_image()` method using DALL-E 3
- **`mealie/services/recipe/recipe_service.py`**: Added `generate_recipe_with_image()` method
- **`mealie/routes/recipe/recipe_crud_routes.py`**: Updated AI recipe creation endpoint to handle image generation

### Frontend
- **`frontend/lib/api/user/recipes/recipe.ts`**: Updated API client to support `includeImage` parameter
- **`frontend/pages/g/[groupSlug]/r/create/ai.vue`**: Added "Generate Image" checkbox to UI

## Original Mealie Documentation

For complete documentation about Mealie's features, configuration, and usage, please refer to:
- [Official Mealie Documentation](https://docs.mealie.io/)
- [Original Repository](https://github.com/mealie-recipes/mealie)

## License

This project maintains the same license as the original Mealie project (AGPL-3.0).

## Support the Original Project

If you find this fork useful, please consider:
- ⭐ Starring the [original Mealie repository](https://github.com/mealie-recipes/mealie)
- 💰 [Sponsoring the Mealie developers](https://github.com/sponsors/hay-kot)
- 🐛 Contributing bug reports and features to the original project

## Disclaimer

This is an unofficial fork and is not affiliated with or endorsed by the official Mealie project.

### ⚠️ DISCLAIMER OF WARRANTY

**THIS SOFTWARE IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NONINFRINGEMENT. THE SOLE WARRANTY PROVIDED IS THAT THIS SOFTWARE MAY TAKE UP DRIVE SPACE ON YOUR SYSTEM.**

**IN NO EVENT SHALL THE AUTHORS, COPYRIGHT HOLDERS, OR CONTRIBUTORS BE LIABLE FOR ANY CLAIM, DAMAGES, OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT, OR OTHERWISE, ARISING FROM, OUT OF, OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.**

**YOU USE THIS SOFTWARE ENTIRELY AT YOUR OWN RISK.**

### 💰 AI USAGE AND COST INDEMNITY

**IMPORTANT**: This fork integrates with OpenAI's paid API services. By using the AI features in this software, you acknowledge and agree that:

1. **YOU ARE SOLELY RESPONSIBLE** for all costs incurred through your use of OpenAI's API, including but not limited to:
   - GPT model usage (recipe generation, remixing, auto-tagging)
   - DALL-E image generation and regeneration
   - Any other API calls made by this software

2. **YOU INDEMNIFY AND HOLD HARMLESS** Rikk Sullenberger, contributors to this fork, and the original Mealie project from any and all costs, expenses, damages, or liabilities arising from your use of AI features, including but not limited to unexpected API charges, rate limit violations, or service interruptions.

3. **NO COST GUARANTEES**: While this software attempts to provide cost estimates and warnings, these are informational only. Actual costs may vary and the maintainer makes no guarantees regarding API usage or costs.

4. **YOUR RESPONSIBILITY**: You are responsible for:
   - Managing your own OpenAI API key and account
   - Monitoring your API usage and costs in the OpenAI dashboard
   - Setting appropriate spending limits in your OpenAI account
   - Understanding OpenAI's current pricing before using AI features

5. **CONFIGURATION ERRORS**: The maintainer is not responsible for any costs incurred due to misconfiguration, software bugs, or unexpected behavior of the AI features.

**BY USING THE AI FEATURES OF THIS SOFTWARE, YOU ACCEPT FULL FINANCIAL RESPONSIBILITY FOR ALL API COSTS INCURRED.**

### 📋 General Use

Use this software at your own risk. The maintainer provides this fork as-is for personal use and makes no guarantees about functionality, reliability, data integrity, or fitness for any particular purpose.

