# Mealie AI

A fork of [Mealie](https://github.com/mealie-recipes/mealie) with enhanced AI capabilities for automatic recipe generation and image generation.

## About This Fork

This is a modified version of the excellent **Mealie** recipe management application, created by the talented team at [mealie-recipes](https://github.com/mealie-recipes). 

### Acknowledgments

**Huge thanks to the original Mealie developers** for creating such an outstanding open-source recipe manager! Their clean architecture, beautiful UI, and thoughtful design made it possible to add these AI features seamlessly. This fork builds upon their incredible work and wouldn't exist without their dedication to the project.

---

## What's Different?

This fork adds **comprehensive AI-powered recipe management** features with enterprise-grade security:

### Latest Updates (v3.6.0)

#### Security Enhancements
- **Rate Limiting**: Token bucket rate limiting on all AI endpoints (5 req/min per IP for AI, 30 req/min for standard)
- **Input Validation**: Prompt injection protection with keyword filtering and length limits (10-2000 chars)
- **Security Audit Logging**: Structured JSON logging of all AI usage to `/app/data/security_audit.log`
- **Error Sanitization**: Generic error messages that don't leak internal exception details
- **CVE Fixes**: Addresses CVE-2025-68146 and CVE-2025-8869

#### Core AI Features
- **Recipe Remix/Variants**: Transform existing recipes with AI - make them healthier, change cuisines, adjust servings, or create fusion variations
- **AI Recipe Generation**: Generate complete recipes from simple descriptions using GPT-4o-mini or GPT-3.5-turbo
- **AI Image Generation**: Create professional food photography images using DALL-E 3
- **Batch Operations**: Generate missing images for multiple recipes in one click
- **Smart Auto-tagging**: Automatically tag recipes based on their content
- **Custom Image Prompts**: Provide specific instructions for AI-generated recipe images
- **High-Quality Images**: Images are generated at 1024x1024 resolution with professional food photography style
- **Optional Features**: Image generation is disabled by default to avoid unexpected API costs

---

## Prerequisites

- Docker and Docker Compose
- **OpenAI API Key** (required for AI features)
  - Without an API key, the AI recipe generation and image features will not be visible in the UI
  - Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)

---

## Installation

### Using Docker Compose (Recommended)

1. **Clone this repository:**
   ```bash
   git clone https://github.com/rikksullenberger/mealie-ai.git
   cd mealie-ai
   ```

2. **Configure environment variables:**

   Create a `.env` file in the `docker/` directory:
   ```bash
   cd docker
   cat > .env << 'EOF'
   OPENAI_API_KEY=your-openai-api-key-here
   OPENAI_MODEL=gpt-4o-mini
   OPENAI_ENABLE_IMAGE_SERVICES=true
   ALLOW_SIGNUP=true
   EOF
   ```

   > **Security Note:** Never commit your `.env` file or API keys to version control. The `.env` file is already in `.gitignore`.

3. **Build and run:**
   ```bash
   docker compose up -d --build
   ```

4. **Access the application:**

   Open your browser to `http://localhost:9091`

5. **Create your admin account** (only available when `ALLOW_SIGNUP=true`)

6. **Disable signups** after account creation (recommended):
   ```bash
   # Edit docker-compose.yml or .env
   ALLOW_SIGNUP=false
   docker compose up -d
   ```

### Environment Variables

Required environment variables for AI features:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | Your OpenAI API key | - | Yes (for AI features) |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-4o-mini` | No |
| `OPENAI_ENABLE_IMAGE_SERVICES` | Enable image generation | `true` | No |
| `ALLOW_SIGNUP` | Allow new user registration | `false` | No |

**Important:** 
- If `OPENAI_API_KEY` is not set, the AI recipe generation menu option will be hidden from the UI.
- `gpt-4o-mini` is used by default for cost efficiency while maintaining quality.
- Set `ALLOW_SIGNUP=true` temporarily to create your account, then disable it.

---

## Security Features

### Rate Limiting
- **AI Endpoints**: 5 requests per minute per IP (token bucket algorithm)
- **Standard Endpoints**: 30 requests per minute per IP
- Applied to: `/create/ai`, `/images/generate-missing`, `/{slug}/image/ai-generate`
- Returns `429 Too Many Requests` when limit exceeded

### Input Validation
- Prompts are validated for length (10-2000 characters)
- Prompt injection protection blocks keywords: `ignore previous instructions`, `system:`, `<script`, `javascript:`, `eval(`, `exec(`
- Returns `400 Bad Request` with clear error message for invalid input

### Security Audit Logging
- All AI usage is logged to `/app/data/security_audit.log` in structured JSON format
- Captures: user ID, IP address, endpoint, prompt length, image generation status
- Use for compliance monitoring and anomaly detection

### Error Handling
- Generic error messages to clients: "An unexpected error occurred. Please try again later."
- Internal exception details are logged but never exposed to API consumers

---

## Docker Compose Example

```yaml
services:
  mealie:
    container_name: mealie-ai
    image: rikksullenberger/mealie-ai:latest
    restart: unless-stopped
    volumes:
      - mealie-data:/app/data/
    ports:
      - 9091:9000
    environment:
      # Core
      ALLOW_SIGNUP: "false"
      LOG_LEVEL: "INFO"
      DB_ENGINE: sqlite
      
      # AI Configuration
      OPENAI_ENABLED: "true"
      OPENAI_API_KEY: ${OPENAI_API_KEY}  # From .env file
      OPENAI_MODEL: "gpt-4o-mini"
      OPENAI_ENABLE_IMAGE_SERVICES: "true"
      
      # Timezone
      TZ: America/New_York
      
volumes:
  mealie-data:
    driver: local
```

---

## Building from Source

If you want to build the Docker image yourself:

```bash
git clone https://github.com/rikksullenberger/mealie-ai.git
cd mealie-ai
docker build -f docker/Dockerfile -t mealie-ai:local .
```

The Dockerfile includes multi-stage builds for development and production targets.

---

## Troubleshooting

### AI Features Not Visible
- Verify `OPENAI_API_KEY` is set correctly
- Check container logs: `docker logs mealie-ai`
- Ensure `OPENAI_ENABLED` is not set to `false`

### Rate Limiting
- If you see `429 Too Many Requests`, wait 1 minute before retrying
- AI endpoints are limited to 5 requests per minute per IP

### Security Audit Logs
- Check `/app/data/security_audit.log` inside the container
- Logs all AI usage in JSON format for monitoring

### Container Won't Start
- Check port availability: `docker ps` to see if port 9091 is in use
- Verify volume permissions for `mealie-data`
- Check `docker logs mealie-ai` for startup errors

---

## Contributing

This is a personal fork with security enhancements. For the upstream project, see [mealie-recipes/mealie](https://github.com/mealie-recipes/mealie).

---

## License

Same as the original Mealie project. See [LICENSE](LICENSE) for details.

---

## Changelog

### v3.6.0 (2026-04-25)
- **Security**: Added rate limiting, input validation, security audit logging, and error sanitization
- **Security**: Fixed CVE-2025-68146 and CVE-2025-8869
- **AI**: Default model changed to `gpt-4o-mini` for cost efficiency
- **Docs**: Updated installation instructions with security best practices

### v3.5.15
- Added ARM64 Support (e.g., Raspberry Pi)
- Security updates
- Python 3.13 support
- Dependency refreshes

### v3.5.13
- Recipe Remix feature
- Bug fixes for 404 redirects

### v3.5.8
- Enhanced fusion capabilities for recipe remixing

### v3.5.5
- Fixed "ChunkLoadError" issues
- Auto-reload on frontend
- Improved cache control headers
