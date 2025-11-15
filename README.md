# SarvSaathi - A Healthcare Platform

**Project Status (as of November 2025)**

This document provides a high-level overview of the SarvSaathi project, detailing its architecture, current progress, and next steps.

---

### 1. Backend (`django`)

The backend is built with Django and Django REST Framework (DRF) to create a powerful API. It's the most developed part of the project so far.

#### a. Main API Configuration (`sarvsaathi_api`)

*   **Technology**: Django, Django REST Framework, and Simple JWT for authentication.
*   **Authentication**: The system uses JSON Web Tokens (JWT). Users log in by sending their credentials to `/api/token/` and receive an access token that must be used for all other secure API calls.
*   **Apps**: The project is organized into three main Django apps: `accounts`, `appointments`, and `emergency`.
*   **CORS**: It's configured to allow requests from any origin (`CORS_ALLOW_ALL_ORIGINS = True`), which is suitable for development but should be restricted in production.

#### b. Accounts App (`apps/accounts`)

This is the core of the application and is substantially complete. It handles user identity, profiles, and roles.

*   **User Roles**: There are two types of users: `Patient` and `Doctor`. This is defined in the `CustomUser` model.
*   **Authentication ID**: Users register and log in with their `email`, not a username.
*   **Patient & Family Accounts**:
    *   A single user account (the `account_holder`) can manage multiple patient profiles (e.g., for themselves, a child, or a parent).
    *   The `Patient` model stores detailed information like name, date of birth, and contact info.
    *   It includes business logic to check if a profile is "complete" and calculates the patient's age.
    *   There is a validation rule ensuring that the main account holder (`relationship='self'`) must be 18 years or older.
*   **Doctor Profiles**:
    *   A user with the `Doctor` role has a linked `DoctorProfile`.
    *   This profile stores professional information like `specialty`, `license_number`, `consultation_fee`, and clinic address.
*   **API Endpoints**:
    *   `/api/accounts/register/`: Public endpoint to create a new `Patient` or `Doctor` user.
    *   `/api/accounts/patients/`: Secure endpoint for a logged-in user to list their associated patient profiles or add a new one (e.g., add a child).
    *   `/api/accounts/patients/<id>/`: Secure endpoint to view, update, or delete a specific patient profile.
    *   `/api/accounts/doctor-profile/`: Secure endpoint for a doctor to view or update their own professional profile.

#### c. Emergency App (`apps/emergency`)

*   **Current Status**: The app has been created within the Django project structure, but the `models.py` and `views.py` files are currently empty. No functionality has been implemented yet.

---

### 2. Frontend (`react`)

*   **Current Status**: The `frontend` directory is set up for a React application, but the `package.json` and `src/App.js` files are empty. **No frontend development has started.**

---

### 3. ML Service (`ml_service`)

*   **Current Status**: The `ml_service` directory exists, but its `app.py` file is empty. **No work has been done on the machine learning component.**

---

### Summary of Progress:

*   **What is Done**: The foundational backend for user management is complete. This includes user registration, login, and detailed profile management for both patients (with a family account system) and doctors. The API is well-structured and secure.
*   **What is Next**:
    1.  **Backend**: Implement the `emergency` and `appointments` apps. This will involve defining models for appointments and emergency requests, and creating the corresponding API views and serializers.
    2.  **Frontend**: Start building the React application. The first steps would be to create login, registration, and user dashboard pages that interact with the existing backend APIs.
    3.  **ML Service**: Define the scope of the ML service and begin implementation.

