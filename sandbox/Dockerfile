# ==============================================================================
# OBEPath AI - Secure Student Code Execution Sandbox Image
# ==============================================================================
# Base: Minimal official Python 3.11 slim image
FROM python:3.11-slim

# Prevent python from buffering stdout/stderr and writing .pyc bytecode
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create unprivileged sandbox user (UID 1000)
RUN useradd -m -u 1000 -s /bin/bash sandboxuser

# Set working directory to sandboxuser home
WORKDIR /home/sandboxuser

# Switch to non-root user
USER sandboxuser

# Default entrypoint reads Python code & test harness from stdin
ENTRYPOINT ["python3", "-u", "-"]
