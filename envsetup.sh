#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 Thomas@chriesibaum.dev

VENV_DIR="/tmp/venv_cb_bsdl_parser"
ANTLR_VERSION="4.13.2"


if [ -d "$VENV_DIR" ]; then
    echo "Activating virtual environment..."
    source $VENV_DIR/bin/activate
else
    echo "Virtual environment not found. Let's create it first."
    python -m venv $VENV_DIR

    source $VENV_DIR/bin/activate

    pip install --upgrade pip
    pip install -r requirements.txt
    pip install -r requirements_dev.txt
    pip install "antlr4-python3-runtime==$ANTLR_VERSION" "antlr4-tools==0.2.2"

    echo "Bootstrapping ANTLR tool (version $ANTLR_VERSION)..."
    export ANTLR4_TOOLS_ANTLR_VERSION="$ANTLR_VERSION"
    antlr4 >/dev/null

    echo "Virtual environment setup complete and ready to use."
fi
