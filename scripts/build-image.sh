#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME=${1:-mindflow:latest}

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Building ${IMAGE_NAME}..."
docker build -t "${IMAGE_NAME}" "${DIR}"
echo "Image ${IMAGE_NAME} built successfully."
