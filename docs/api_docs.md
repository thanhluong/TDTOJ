# API Documentation

This document describes the custom API endpoints available in the system.

## Base URL

All API URLs referenced below are relative to the base URL of your installation.

## Endpoints

### 1. Organization API

#### List Organizations

```
GET /api/orgs/
```

Query Parameters:
- `name` (optional): Filter organizations by name (case-insensitive)
- `page` (optional, default=1): Page number for pagination
- `page_size` (optional, default=50): Number of results per page

Response:
```json
{
  "count": 100,
  "page": 1,
  "page_size": 50,
  "results": [
    {
      "id": 1,
      "name": "Sample Organization",
      "slug": "sample-org",
      "short_name": "SO",
      "about": "This is a sample organization",
      "is_open": true,
      "member_count": 15
    },
    ...
  ]
}
```

#### Create Organization

```
POST /api/orgs/
```

Request Body:
```json
{
  "name": "New Organization",
  "slug": "new-org",
  "short_name": "NO",
  "about": "This is a new organization",
  "is_open": true
}
```

Response (201 Created):
```json
{
  "id": 2,
  "name": "New Organization",
  "slug": "new-org",
  "short_name": "NO",
  "about": "This is a new organization",
  "is_open": true
}
```

Authentication: Required (user must be logged in)

### 2. Organization Contests API

```
GET /api/orgs/:org_id/contests/
```

Path Parameters:
- `org_id`: Organization ID

Query Parameters:
- `page` (optional, default=1): Page number for pagination
- `page_size` (optional, default=50): Number of results per page

Response:
```json
{
  "count": 25,
  "page": 1,
  "page_size": 50,
  "organization": {
    "id": 1,
    "name": "Sample Organization",
    "slug": "sample-org"
  },
  "results": [
    {
      "id": 1,
      "key": "contest1",
      "name": "Sample Contest",
      "start_time": "2023-01-01T12:00:00Z",
      "end_time": "2023-01-01T15:00:00Z",
      "time_limit": 10800,
      "is_rated": true,
      "is_private": false
    },
    ...
  ]
}
```

### 3. Contest Scoreboard API

```
GET /api/contests/:contest_id/scoreboard/
```

Path Parameters:
- `contest_id`: Contest ID

Query Parameters:
- `page` (optional, default=1): Page number for pagination
- `page_size` (optional, default=100): Number of results per page

Response:
```json
{
  "count": 150,
  "page": 1,
  "page_size": 100,
  "contest": {
    "id": 1,
    "key": "contest1",
    "name": "Sample Contest"
  },
  "problems": [
    {
      "id": 1,
      "name": "Problem A",
      "code": "A",
      "points": 100
    },
    ...
  ],
  "results": [
    {
      "user": {
        "id": 1,
        "username": "user1",
        "points": 1500,
        "rating": 1800
      },
      "score": 300,
      "problem_scores": {
        "1": 100,
        "2": 100,
        "3": 100
      },
      "cumulative_time": 300
    },
    ...
  ]
}
```

Authentication: Required if the contest is private or organization-private

### 4. Organization Users API

```
GET /api/orgs/:org_id/users/
```

Path Parameters:
- `org_id`: Organization ID

Query Parameters:
- `sort` (optional, default="-rating"): Field to sort by, prefix with `-` for descending
- `page` (optional, default=1): Page number for pagination
- `page_size` (optional, default=50): Number of results per page

Response:
```json
{
  "count": 75,
  "page": 1,
  "page_size": 50,
  "organization": {
    "id": 1,
    "name": "Sample Organization",
    "slug": "sample-org"
  },
  "results": [
    {
      "id": 1,
      "username": "user1",
      "points": 1500,
      "performance_points": 1200,
      "problem_count": 120,
      "display_rank": "user",
      "rating": 1800
    },
    ...
  ]
}
```

## Error Handling

All API endpoints return appropriate HTTP status codes:

- 200: Success
- 201: Created (for POST requests)
- 400: Bad Request (invalid parameters or request body)
- 403: Forbidden (authentication or permission issues)
- 404: Not Found (resource doesn't exist)
- 500: Internal Server Error

Error responses include a JSON object with an error message:

```json
{
  "error": "Error message description"
}
``` 