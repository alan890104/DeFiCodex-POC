# DeFiCodex

## Setup

1. Edit `.env` file

    ```bash
    cp .env.example .env
    ```

    Add your own configuration to `.env` file

2. create a virtual environment and install requirements

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3. Export environment variables

    ```bash
    export $(grep -v '^#' .env | xargs -d '\n')
    ```

4. Run the script

    ```bash
    python3 main.py
    ```
