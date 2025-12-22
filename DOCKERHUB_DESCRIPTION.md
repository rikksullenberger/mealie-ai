# Docker Hub Description for mealie-ai

## Short Description (100 characters max)
AI-enabled Mealie recipe manager with OpenAI integration for recipe generation and image creation

## Full Description

# Mealie AI v3.5.15

A fork of [Mealie](https://github.com/mealie-recipes/mealie) with enhanced AI capabilities for automatic recipe generation and image creation using OpenAI.

## Features

### Latest Updates
- **v3.5.15**: Added **ARM64 Support** (e.g., Raspberry Pi), Security updates (CVE-2025-68146, CVE-2025-8869 analysis), Python 3.13 support, and dependency refreshes
- **v3.5.13**: Recipe Remix feature - Create variations of existing recipes with AI modifications, plus bug fixes for 404 redirects
- **v3.5.8**: Enhanced fusion capabilities for recipe remixing
- **v3.5.5**: Fixed "ChunkLoadError" issues by implementing auto-reload on frontend and improved cache control headers

### Core AI Features
- **Recipe Remix/Variants**: Transform existing recipes with AI - make them healthier, change cuisines, adjust servings, or create fusion variations
- **AI Recipe Generation**: Generate complete recipes from simple descriptions using GPT-4o or GPT-3.5-turbo
- **AI Image Generation**: Create professional food photography images using DALL-E 3
- **Batch Operations**: Generate missing images for multiple recipes in one click
- **Smart Auto-tagging**: Automatically tag recipes based on their content
- **Custom Image Prompts**: Provide specific instructions for AI-generated recipe images
- **Parse Ingredients**: Automatically parse and structure recipe ingredients
- **Enhanced Security**: Hardened image with patched system libraries and `urllib3` updates
- **One-Click Setup**: Simple Docker deployment with OpenAI API key

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Basic Usage

```bash
docker run -d \
  -p 9099:9000 \
  -v mealie-data:/app/data \
  -e OPENAI_API_KEY="your-openai-api-key-here" \
  -e OPENAI_MODEL="gpt-4o" \
  -e BASE_URL="https://your-domain.com" \
  --name mealie-ai \
  rikksullenber/mealie-ai:latest
```

### Using Docker Compose

```yaml
services:
  mealie-ai:
    image: rikksullenber/mealie-ai:latest
    container_name: mealie-ai
    restart: always
    ports:
      - "9099:9000"
    volumes:
      - mealie-data:/app/data
    environment:
      OPENAI_API_KEY: "your-openai-api-key-here"
      OPENAI_MODEL: "gpt-4o"
      BASE_URL: "https://your-domain.com"
      OPENAI_ENABLED: "true"
      ALLOW_SIGNUP: "false"

volumes:
  mealie-data:
```

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | Your OpenAI API key | - | Yes |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-4o` | No |
| `OPENAI_ENABLED` | Enable AI features | `true` | No |
| `OPENAI_ENABLE_IMAGE_SERVICES` | Enable image generation | `true` | No |
| `BASE_URL` | Public URL (required for sharing/auth) | - | Yes (if public) |

## Usage

After starting the container:

1. Access the application at `http://localhost:9099`
2. Create an account or log in
3. Navigate to **Create** → **Generate with AI**
4. Enter a recipe description
5. Optionally check "Generate Image" for AI-generated food photography
6. Click **Generate**

### Recipe Remix (New in v3.5.13!)

Transform existing recipes with AI:

1. Open any recipe
2. Click the **context menu** (three dots)
3. Select **Remix Recipe**
4. Choose a remix type (healthier, different cuisine, adjust servings, fusion, or custom)
5. Click **Remix** to generate the variation

## Documentation & Source

- **Full Documentation**: [https://github.com/rikksullenberger/mealie-ai](https://github.com/rikksullenberger/mealie-ai)
- **Deployment Guide**: [DEPLOYMENT.md](https://github.com/rikksullenberger/mealie-ai/blob/main/DEPLOYMENT.md)
- **Original Mealie Project**: [https://github.com/mealie-recipes/mealie](https://github.com/mealie-recipes/mealie)

## Cost Considerations

- Recipe Generation: ~$0.50-1.50 per million tokens
- Image Generation: ~$0.04-0.08 per image (DALL-E 3)
- Image generation is optional and disabled by default

## License

AGPL-3.0 (same as original Mealie project)

## Acknowledgments

Built on top of the excellent [Mealie](https://github.com/mealie-recipes/mealie) project by [hay-kot](https://github.com/hay-kot). Thanks to the original developers for creating such an outstanding recipe manager!
