# Hackathon Teammate Finder

### A web application designed to help students connect with and find teammates for hackathons.

## Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Contributing](#contributing)
- [License](#license)

## Introduction
Hackathons are a great way for students to collaborate, learn new skills, and build innovative projects. However, finding the right teammates can be challenging. **Hackathon Teammate Finder** is a platform where students can create profiles, browse other participants, and find team members based on their skills, goals, and experience levels.

## Features
- **User Profiles**: Users can create profiles, indicating their experience level, preferred roles, and programming languages.
- **Team Matching**: Browse potential teammates based on skills, roles, or goals.
- **Notifications**: Get notified when someone is interested in forming a team with you.

## Tech Stack
- **Frontend**: Next.js
- **Backend**: Python (FastAPI)
- **Database**: PostgreSQL
- **Authentication**: JWT (JSON Web Tokens)


## Installation

### Prerequisites
- Python 3.9+
- PostgreSQL


### Backend Setup
1. Clone the repository:
    ```bash
    git clone https://github.com/Vishak-V/HackNet.git
    ```

2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Set up the environment variables:
    - Create a `.env` file in the backend directory with the following:
      ```
      DATABASE_URL=postgresql://username:password@localhost:5432/your_db
      SECRET_KEY=your_secret_key
      ALGORITHM=HS256
      ACCESS_TOKEN_EXPIRE_MINUTES=30
      ```


5. Start the FastAPI server:
    ```bash
    uvicorn app.main:app --reload
    ```

### Frontend Setup
