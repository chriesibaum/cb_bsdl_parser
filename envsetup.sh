#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 Thomas@chriesibaum.dev

VENV_DIR=".venv"
ANTLR_VERSION="4.13.2"

export ANTLR4_TOOLS_ANTLR_VERSION="$ANTLR_VERSION"


if ! command -v uv >/dev/null 2>&1; then
    echo "uv is required but not installed. Install it from https://docs.astral.sh/uv/ and re-run this script."
    exit 1
fi


if [ -d "$VENV_DIR" ]; then
    echo "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
else
    echo "Virtual environment not found. Let's create it first."
    uv venv "$VENV_DIR"

    source "$VENV_DIR/bin/activate"

    echo "Installing project from pyproject.toml..."
    uv pip install -e .

    # ask the user if they want to install dev dependencies
    read -p "Do you want to install development dependencies? (y/n) " -n 1 -r
    echo
    if [[ "$REPLY" =~ ^[Yy]$ ]]; then
        echo "Installing development dependencies..."
        uv pip install -e ".[dev]"

        echo "Bootstrapping ANTLR tool (version $ANTLR_VERSION)..."
        uv pip install "antlr4-python3-runtime==$ANTLR_VERSION" "antlr4-tools==0.2.2"
        antlr4 >/dev/null
    fi

    echo "Virtual environment setup complete and ready to use."
fi
