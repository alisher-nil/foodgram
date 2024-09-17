# Foodgram
## Description
A social service to store and share recipes.
## Build Status
[![Foodgram Deploy Workflow](https://github.com/alisher-nil/foodgram-project-react/actions/workflows/main.yml/badge.svg)](https://github.com/alisher-nil/foodgram-project-react/actions/workflows/main.yml)
## Table of Contents
- [Installation](#installation)
- [API](#api)
- [Working project](#Working_project)
- [Contact](#contact)
## Prerequisites
[Docker](https://www.docker.com/)
## Installation
To install and set up the project, follow these steps:
1. Clone the repository:
    ```bash
    git clone https://github.com/alisher-nil/foodgram-project-react.git
    ```
2. Navigate to the infra directory:
    ```bash
    cd infra
    ```
3. Create .env file, example provided in `/infra` directory
4. Build and run from local files:
    ```bash
    docker compose up --build -d
    ```
5. Apply database migrations:
    ```
    docker compose exec backend python manage.py migrate
    ```
6. Load premade data
    ```
    docker compose exec backend python manage.py load_ingredients ingredients.json
    docker compose exec backend python manage.py load_tags tags.json
    ```
8. Open your web browser and visit `http://localhost/` to access the application.
## API
api schema is available at `/api/docs/` once the project is runnning
## Working_project
[foodgram](https://anfoodgram.ddns.net/recipes)
## Contact
Please feel free to contact me with any questions or feedback:
- Email: alisher.nil@gmail.com
- GitHub: [alisher-nil](https://github.com/alisher-nil/)
