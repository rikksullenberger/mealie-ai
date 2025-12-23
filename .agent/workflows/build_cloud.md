---
description: Build and Deploy Mealie AI using Docker Cloud Build to avoid local resource exhaustion
---

# Build and Deploy with Docker Cloud Build

This workflow ensures that the resource-intensive build process is offloaded to Docker Build Cloud, preventing high load and crashes on the local machine.

1.  **Login to Docker** (if needed)
    Ensure you are logged in as `rikksullenber`.
    ```bash
    docker login
    ```

2.  **Select the Cloud Builder**
    Explicitly select the cloud builder to ensure `docker build` commands don't run locally.
    ```bash
    // turbo
    docker buildx use cloud-rikksullenber-mealie-ai
    ```

3.  **Build and Start Application**
    Run the compose stack. Docker Compose V2 with BuildKit will utilize the selected builder.
    ```bash
    cd docker
    docker compose -f docker-compose.yml up -d --build
    ```
