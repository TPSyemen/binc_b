# Project Recommendation System Overview

This document explains how the AI-based recommendation system works in this project, and what libraries and techniques are used.

---

## How Recommendations Work in This Project

1. **Data Source:**
   - The system uses data from user interactions (such as product views, purchases, ratings, or favorites) stored in the database models (e.g., `Product`, `User`, `Favorite`, etc.).

2. **Recommendation Logic:**
   - The recommendation logic is based on content-based filtering and simple collaborative filtering:
     - **Content-based:** Recommends products similar to those the user has interacted with (e.g., same category, similar attributes).
     - **Collaborative filtering (simple):** Recommends products that are popular among users with similar preferences.
   - The logic is implemented using custom Python code and Django ORM queries.

3. **Library Used:**
   - No external machine learning library (like TensorFlow, PyTorch, or scikit-learn) is used for recommendations.
   - All logic is implemented using Python and Django ORM.
   - Sometimes, simple statistical or rule-based methods are used (e.g., “most viewed”, “users who liked X also liked Y”).

4. **Serving Recommendations:**
   - The backend exposes API endpoints (e.g., `/api/recommendations/`) that the frontend calls to get recommended products for a user.
   - The logic is implemented in files like `recommendations/ai_services.py` and `recommendations/views.py`.

---

## Example Logic

- The system may recommend products in the same category as those the user liked.
- It may aggregate user actions (favorites, ratings) and recommend the most popular or similar items.
- No deep learning or external ML model is used—just Python, Django, and database queries.

---

## Summary

- The recommendation system is based on user behavior and product similarity.
- It is implemented with custom Python code and Django ORM.
- No external AI/ML libraries are used.
- Recommendations are served via REST API endpoints.

---

For more details or to improve the recommendation logic, see the code in `recommendations/ai_services.py` and `recommendations/views.py`.
