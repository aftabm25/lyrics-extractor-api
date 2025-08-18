#!/bin/bash

# Set the Gemini API key
export GEMINI_API_KEY='AIzaSyC9haPHXl1I8nwSo8Hx4TaZJDgOk5ihBtM'

# Activate virtual environment if it exists
if [ -d "../venv" ]; then
    source ../venv/bin/activate
fi

# Run the Flask server
python api.py
