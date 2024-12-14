#!/usr/bin/env bash

for file in src/*; do
    if [ -f "$file" ]; then
        echo "Filename: $(basename "$file")"
        echo "Content:"
        cat "$file"
        echo
        echo "---------------------------------"
    fi
done
