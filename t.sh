#!/usr/bin/env bash

case "$1" in
    train)
        python -m project.training.train_model
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
