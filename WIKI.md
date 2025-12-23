# Mealie AI - Official Wiki

Welcome to the **Mealie AI** Wiki! This guide serves as the definitive reference for utilizing the enhanced AI capabilities of this Mealie fork.

---

## 📚 Table of Contents
1. [Core AI Features](#core-ai-features)
    - [Recipe Generation](#recipe-generation)
    - [Recipe Remix](#recipe-remix)
    - [Image Generation](#image-generation)
    - [Auto-Tagging](#auto-tagging)
2. [Configuration Guide](#configuration-guide)
    - [Environment Variables](#environment-variables)
    - [Cost Management](#cost-management)
3. [Deployment](#deployment)
    - [Docker Compose (Standard)](#docker-compose-standard)
    - [ARM64 / Raspberry Pi](#arm64--raspberry-pi)
4. [Troubleshooting](#troubleshooting)

---

## <a name="core-ai-features"></a> 🧠 Core AI Features

This fork integrates OpenAI's powerful models to automate and enhance your recipe management experience.

### <a name="recipe-generation"></a> Recipe Generation
Generate complete recipes from a simple phrase or list of ingredients.
- **How to use**: Go to **Create** -> **Generate with AI**.
- **Models**: Uses `gpt-3.5-turbo` by default for speed and cost-efficiency. Can be configured to `gpt-4o` for higher quality.
- **capabilities**:
    - Generates ingredients list, step-by-step instructions, prep time, cook time, and yield.
    - Understands dietary restrictions (add them to your prompt, e.g., "Vegan lasagna").

### <a name="recipe-remix"></a> Recipe Remix
Transform your existing recipes into something new.
- **How to use**: Open a recipe -> Click the **3-dots menu** -> **Remix Recipe**.
- **Modes**:
    - **Healthier**: Automatically reduces creates a variant with less fat/sugar/sodium.
    - **Fusion**: Combines the current recipe with a cuisine of your choice (e.g., "Mexican" style Pizza).
    - **Adjust Servings**: Smartly scales ingredients and adjusts cooking steps/times appropriately.
    - **Custom**: Free-form instruction (e.g., "Make this gluten-free using almond flour").

### <a name="image-generation"></a> Image Generation
Create stunning, professional-grade food photography for your recipes.
- **Engine**: OpenAI **DALL-E 3**.
- **How to use**:
    - **New Recipe**: Check "Generate Image" during creation.
    - **Existing Recipe**: Click **Regenerate Image** on the recipe edit page.
- **Prompts**: You can let the AI generate a prompt based on the recipe title, or provide your own custom artistic direction.

### <a name="auto-tagging"></a> Auto-Tagging
- **How to use**: Check "Auto-Tag" when generating a recipe.
- **Logic**: Analyzes the recipe title and ingredients to apply relevant categories (e.g., "Dinner", "Italian", "Vegetarian") and tags.

---

## <a name="configuration-guide"></a> ⚙️ Configuration Guide

Configure the AI behavior using environment variables in your `docker-compose.yml`.

### <a name="environment-variables"></a> Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | Your secret API Key from OpenAI. | - | **Yes** |
| `OPENAI_MODEL` | The LLM to use for text generation. Options: `gpt-3.5-turbo`, `gpt-4o`. | `gpt-3.5-turbo` | No |
| `OPENAI_ENABLE_IMAGE_SERVICES` | Set to `true` to allow DALL-E 3 image generation. | `true` | No |
| `OPENAI_ENABLED` | Global switch for all AI features. | `true` | No |

### <a name="cost-management"></a> Cost Management
AI services are paid. Here are estimates to help you budget:
- **Recipe Text**: cheap! ~$0.01 per 10-20 recipes using GPT-3.5.
- **Images**: ~$0.04 - $0.08 **per image** (DALL-E 3 standard).
    - *Tip*: Disable `OPENAI_ENABLE_IMAGE_SERVICES` if you want to prevent accidental image costs.

---

## <a name="deployment"></a> 🚀 Deployment

### <a name="docker-compose-standard"></a> Docker Compose (Standard)
For most users on x86_64 (Intel/AMD) systems.

```yaml
version: "3.7"
services:
  mealie:
    image: rikksullenberger/mealie-ai:latest
    container_name: mealie
    ports:
        - "9099:9000"
    environment:
      - OPENAI_API_KEY=sk-proj-....
      # ... other env vars
    volumes:
      - ./mealie/data:/app/data
    restart: always
```

### <a name="arm64--raspberry-pi"></a> ARM64 / Raspberry Pi
As of **v3.8.13**, native ARM64 support is included! No special tag is needed; Docker will automatically pull the correct architecture for your text.

**Requirements for Pi:**
- Raspberry Pi 4 (4GB RAM) or Pi 5 recommended.
- 64-bit OS (Raspberry Pi OS 64-bit or Ubuntu Server 64-bit).

---

## <a name="troubleshooting"></a> ❓ Troubleshooting

**Q: I don't see the "Generate with AI" button.**
A: Ensure `OPENAI_API_KEY` is correctly set in your environment variables and the container has been restarted.

**Q: Image generation fails.**
A:
1. Check your OpenAI credit balance.
2. Confirm `OPENAI_ENABLE_IMAGE_SERVICES` is not set to `false`.
3. Check the logs: `docker logs mealie-ai`.

**Q: Can I use a local LLM (Ollama/LocalAI)?**
A: Currently, the integration is hardcoded for OpenAI's API. Local LLM support is a planned future feature.
