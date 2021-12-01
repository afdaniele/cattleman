import os

DEBUG = False

USER_DATA_DIR = os.environ.get("CATTLEMAN_USER_DATA_DIR", os.path.expanduser("~/.cattleman"))
DATABASES_DIR = os.path.join(USER_DATA_DIR, "databases")

DATABASE_SCHEMA_VERSION = "1.0"

UNDEFINED = object()
REQUIRED = object()

NoneType: type = type(None)


CANONICAL_ARCH = {
    "arm": "arm32v7",
    "arm32v7": "arm32v7",
    "armv7l": "arm32v7",
    "armhf": "arm32v7",
    "x64": "amd64",
    "x86_64": "amd64",
    "amd64": "amd64",
    "Intel 64": "amd64",
    "arm64": "arm64v8",
    "arm64v8": "arm64v8",
    "armv8": "arm64v8",
    "aarch64": "arm64v8",
}

ARCH_TO_DOCKER_PLATFORM = {
    "amd64": "linux/amd64",
    "arm32v7": "linux/arm/v7",
    "arm64v8": "linux/arm64/v8",
}

BUILD_COMPATIBILITY_MAP = {
    "arm32v7": ["arm32v7"],
    "arm64v8": ["arm32v7", "arm64v8"],
    "amd64": ["amd64"]
}

DOCKERHUB_API_URL = {
    "token": "https://auth.docker.io/token?scope=repository:{image}:pull&"
             "service=registry.docker.io",
    "digest": "https://registry-1.docker.io/v2/{image}/manifests/{tag}",
    "inspect": "https://registry-1.docker.io/v2/{image}/blobs/{digest}",
}
