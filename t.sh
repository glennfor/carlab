#!/usr/bin/env bash

case "$1" in
    init)
        source venv/bin/activate
        ;;
    serve)
        python -m project.api.server
        ;;
    clean)
        python scripts/cleanup.py
        ;;
    *)
        echo "Usage: ./run.sh {train|serve|clean}"
        ;;
esac
