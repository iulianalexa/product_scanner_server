# API Reference

## Admin Authentication
#### POST /admin/login
Logs in an admin and returns an authentication token.

Request (JSON):

```json
{
  "username": "admin_username",
  "password": "admin_password"
}
```

Response (JSON):

```json
{
  "token": "your_auth_token"
}
```

Include this token in the Authorization header for all admin endpoints:
`Authorization: your_auth_token`

## Public endpoints
### Sponsor
#### GET /sponsor
Fetches a list of sponsor products (publicly accessible).

Query Parameters:
- count (optional, default: 10): number of items to return
- after (optional, default: 0): offset from the beginning

Response:

```json
[
  {
    "sponsor_name": "Cool Corp",
    "product_name": "Smart Widget",
    "product_description": "A cool device.",
    "product_picture": "https://example.com/pic.jpg"
  }
]
```

## Admin endpoints
### Sponsor
#### POST /admin/sponsor

Create a new sponsor product.
Requires Auth
Request (JSON):

```json
{
  "sponsor_name": "Cool Corp",
  "product_name": "Smart Widget",
  "product_description": "A cool device.",
  "product_picture": "https://example.com/pic.jpg"
}
```

Response:

```json
{ "status": "sponsor product created" }
```

#### PUT /admin/sponsor/<id>

Edit an existing sponsor product by ID.

Requires Auth
Request (JSON):

```json
{
  "sponsor_name": "Cool Corp",
  "product_name": "Smarter Widget",
  "product_description": "An improved device.",
  "product_picture": "https://example.com/pic2.jpg"
}
```

Response:

```json
{ "status": "sponsor product updated" }
```

#### DELETE /admin/sponsor/<id>

Delete a sponsor product by ID.

Requires Auth
Response:

```json
{ "status": "sponsor product deleted" }
```

### Ingredients
#### GET /admin/ingredients

List all ingredients (paginated).

Requires Auth
Query Parameters:

- count (optional, default: 10)
- after (optional, default: 0)

Response:

```json
[
  {
    "id": 1,
    "name": "Tomato",
    "description": "Fresh and red",
    "ingredient_score" 10.0
  }
]
```

#### POST /admin/ingredient

Create a new ingredient.

Requires Auth
Request (JSON):

```json
{
  "name": "Lettuce",
  "description": "Crisp and green",
  "ingredient_score" 10.0
}
```

Response:

```json
{ "status": "ingredient created" }
```

#### PUT /admin/ingredient/<id>

Edit an ingredient by ID.

Requires Auth
Request (JSON):

```json
{
  "name": "Spinach",
  "description": "Leafy and nutritious",
  "ingredient_score": 10.0
}
```

Response:

```json
{ "status": "ingredient updated" }
```

#### DELETE /admin/ingredient/<id>

Delete an ingredient by ID.

Requires Auth
Response:

```json
{ "status": "ingredient deleted" }
```

## Notes

- All admin routes require a valid token in the Authorization header.
- Tokens are temporary and will expire after some time (e.g., 1 hour) or after a server reset. If token fails on the frontend, prompt the user to log in again to get a new one.
- Use the `add_user.py` script to insert new users into the database (no registration endpoint).
