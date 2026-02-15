#!/bin/bash
docker system prune
docker compose build
docker compose up -d
docker ps
