# Mealie AI - Docker Hub Deployment Guide

> **Source Code**: This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0).
> The complete source code is available at: [https://github.com/rikksullenberger/mealie-ai](https://github.com/rikksullenberger/mealie-ai)
>
> **IMPORTANT**: If you modify this software and provide it as a network service (e.g., hosting for others to use),
> you must make your modified source code available under the same AGPL-3.0 license.

This guide walks you through deploying your AI-enabled Mealie application to a remote server using Docker Hub.

## Prerequisites

- Docker and Docker Compose installed on both local and remote machines
- Docker Hub account
- OpenAI API key (for AI features)

## Part 1: Build and Push to Docker Hub (Local Machine)

### Step 1: Login to Docker Hub

```bash
docker login
```

Enter your Docker Hub username and password when prompted.

### Step 2: Build the Docker Image

From the mealie project root directory:

```bash
docker-compose -f docker/docker-compose-with-ai.yml build
```

This will build the image with all your AI modifications. The build process includes:
- Frontend build with AI recipe generation UI
- Backend with OpenAI integration
- All dependencies and configurations

### Step 3: Tag the Image for Docker Hub

Replace `<YOUR_DOCKERHUB_USERNAME>` with your actual Docker Hub username:

```bash
docker tag mealie:dev <YOUR_DOCKERHUB_USERNAME>/mealie-ai:latest
```

Optional: Also tag with a version number for tracking:

```bash
docker tag mealie:dev <YOUR_DOCKERHUB_USERNAME>/mealie-ai:v1.0.0
```

### Step 4: Push to Docker Hub

```bash
docker push <YOUR_DOCKERHUB_USERNAME>/mealie-ai:latest
```

If you created a version tag:

```bash
docker push <YOUR_DOCKERHUB_USERNAME>/mealie-ai:v1.0.0
```

**Note**: The push may take several minutes depending on your internet connection speed. The image is approximately 500MB-1GB.

### Step 5: Verify Upload

Visit `https://hub.docker.com/r/<YOUR_DOCKERHUB_USERNAME>/mealie-ai` to confirm the image was uploaded successfully.

## Part 2: Deploy on Remote Server

### Step 1: Transfer Configuration File

Copy the `docker-compose.deploy.yml` file to your remote server. You can use `scp`:

```bash
scp docker-compose.deploy.yml user@your-remote-server:/path/to/deployment/
```

Or copy the contents manually and create the file on the remote server.

### Step 2: Update Configuration

On the remote server, edit `docker-compose.deploy.yml`:

1. **Replace Docker Hub username**:
   ```yaml
   image: <YOUR_DOCKERHUB_USERNAME>/mealie-ai:latest
   ```
   Change `<YOUR_DOCKERHUB_USERNAME>` to your actual username.

2. **Add your OpenAI API key**:
   ```yaml
   OPENAI_API_KEY: "your-openai-api-key-here"
   ```
   Replace with your actual OpenAI API key.

3. **Optional**: Adjust other environment variables as needed.

### Step 3: Pull the Image

On the remote server:

```bash
docker-compose -f docker-compose.deploy.yml pull
```

### Step 4: Start the Container

```bash
docker-compose -f docker-compose.deploy.yml up -d
```

The `-d` flag runs it in detached mode (background).

### Step 5: Verify Deployment

Check that the container is running:

```bash
docker ps | grep mealie-ai
```

View logs to ensure no errors:

```bash
docker logs mealie-ai
```

Access the application in your browser:

```
http://<your-remote-server-ip>:9099
```

## Part 3: Data Migration (Restore Backup)

Since you're starting with a fresh instance and plan to restore from backup:

### Step 1: Create Admin Account

1. Visit `http://<your-remote-server-ip>:9099`
2. Create an admin account (since `ALLOW_SIGNUP` is set to `false`, you'll need to temporarily enable it or use the initial setup)

### Step 2: Restore Backup

1. In Mealie, go to Settings → Backups
2. Upload your backup file from the existing Mealie instance
3. Click "Restore" to import your recipes and data

## Management Commands

### View Logs

```bash
docker logs mealie-ai
# Follow logs in real-time
docker logs -f mealie-ai
```

### Restart Container

```bash
docker-compose -f docker-compose.deploy.yml restart
```

### Stop Container

```bash
docker-compose -f docker-compose.deploy.yml down
```

### Update to New Version

When you push a new version to Docker Hub:

```bash
docker-compose -f docker-compose.deploy.yml pull
docker-compose -f docker-compose.deploy.yml up -d
```

### Access Container Shell (for debugging)

```bash
docker exec -it mealie-ai bash
```

## Troubleshooting

### Container Won't Start

Check logs:
```bash
docker logs mealie-ai
```

Common issues:
- Port 9099 already in use
- Invalid OpenAI API key
- Incorrect environment variables

### Can't Access Web Interface

1. Check firewall rules allow port 9099
2. Verify container is running: `docker ps`
3. Check port binding: `docker port mealie-ai`

### AI Features Not Working

1. Verify `OPENAI_ENABLED: "true"` is set
2. Confirm `OPENAI_API_KEY` is valid
3. Check logs for OpenAI-related errors

### Data Not Persisting

Ensure the volume is properly mounted:
```bash
docker volume ls | grep mealie-ai-data
```

## Configuration Reference

### Key Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_ENABLED` | `false` | Enable/disable AI features |
| `OPENAI_API_KEY` | - | Your OpenAI API key (required for AI) |
| `OPENAI_MODEL` | `gpt-4` | Model to use for generation |
| `ALLOW_SIGNUP` | `true` | Allow new user registration |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `DB_ENGINE` | `sqlite` | Database engine (sqlite or postgres) |

## Notes

- The container runs on port 9000 internally, mapped to 9099 externally
- Data is persisted in the `mealie-ai-data` Docker volume
- The container will automatically restart on failure or server reboot
- Both instances (original and AI-enabled) can run simultaneously on different ports
