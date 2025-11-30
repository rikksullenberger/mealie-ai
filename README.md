# Mealie with AI Image Generation

A fork of [Mealie](https://github.com/mealie-recipes/mealie) with enhanced AI capabilities for automatic recipe image generation.

## About This Fork

This is a modified version of the excellent **Mealie** recipe management application, created by the talented team at [mealie-recipes](https://github.com/mealie-recipes). 

### Acknowledgments

**Huge thanks to the original Mealie developers** for creating such an outstanding open-source recipe manager! Their clean architecture, beautiful UI, and thoughtful design made it possible to add this AI image generation feature seamlessly. This fork builds upon their incredible work and wouldn't exist without their dedication to the project.

### What's Different?

This fork adds **AI-powered image generation** for recipes:

- **Automatic Image Creation**: When creating a recipe using AI, you can now optionally generate a professional food photography image using OpenAI's DALL-E 3
- **One-Click Generation**: Simply check the "Generate Image" box when creating a recipe from an AI prompt
- **High-Quality Images**: Images are generated at 1024x1024 resolution with professional food photography style
- **Optional Feature**: Image generation is disabled by default to avoid unexpected API costs

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

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | Your OpenAI API key | Yes (for AI features) |
| `OPENAI_MODEL` | OpenAI model to use | No (defaults to `gpt-4o`) |
| `OPENAI_ENABLE_IMAGE_SERVICES` | Enable image generation | No (defaults to `true`) |

**Important:** If `OPENAI_API_KEY` is not set, the AI recipe generation menu option will be hidden from the UI.

## Usage

### Creating a Recipe with AI Image Generation

1. Navigate to **Create** → **Generate with AI**
2. Enter your recipe description (e.g., "Creamy Italian Carbonara")
3. **Check the "Generate Image" checkbox** to create an AI-generated image
4. Click **Generate**
5. The recipe will be created with an AI-generated food photography image

### Cost Considerations

- **Recipe Generation**: Uses GPT-4o (standard OpenAI pricing)
- **Image Generation**: Uses DALL-E 3 (~$0.04-0.08 per image depending on quality settings)
- Image generation is **optional** and disabled by default to prevent unexpected charges

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

This is an unofficial fork and is not affiliated with or endorsed by the official Mealie project. Use at your own risk, especially regarding OpenAI API costs.
