# User Interaction System Overview

This document explains how the user interaction system works in this project, including what types of interactions are tracked and how they are used.

---

## How User Interaction Works in This Project

1. **Types of User Interactions:**
   - The system tracks various user actions, such as:
     - Product views (when a user visits a product page)
     - Adding products to favorites or wishlist
     - Product ratings and reviews
     - Adding products to cart or making purchases
     - Likes/dislikes or other reactions to products

2. **Data Storage:**
   - Each interaction is stored in the database, often in dedicated models such as `Favorite`, `UserProductReaction`, `Review`, or logs tables.
   - These models typically link the user to the product and record the type of action and timestamp.

3. **Usage of Interaction Data:**
   - Interaction data is used to:
     - Personalize recommendations (e.g., recommend products similar to those the user liked or viewed)
     - Display user-specific lists (e.g., favorites, recently viewed)
     - Generate analytics and statistics (e.g., most popular products, user engagement)
     - Enable social features (e.g., showing what friends liked)

4. **APIs and Endpoints:**
   - The backend provides API endpoints to:
     - Add or remove favorites
     - Submit ratings or reviews
     - Record product views or other actions
     - Retrieve lists of user interactions (e.g., GET /api/user/favorites/)

5. **No External Libraries:**
   - All logic for tracking and using user interactions is implemented using Django models and views.
   - No external analytics or tracking libraries are used; everything is handled in Python and the database.

---

## Example Logic

- When a user clicks on a product, a `ProductView` record is created linking the user and the product.
- When a user adds a product to favorites, a `Favorite` record is created or updated.
- When a user rates a product, a `Review` record is created with the rating and comment.
- These records are then used to personalize the user experience and generate statistics.

---

## Summary

- The user interaction system tracks actions like views, favorites, ratings, and more.
- All data is stored in Django models and used for personalization and analytics.
- No external tracking libraries are used; everything is custom and integrated with the backend.

---

For more details, see the models and views in the `core` and `products` apps, such as `models_favorites.py`, `models.py`, and related API views.
