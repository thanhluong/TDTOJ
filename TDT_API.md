# TDTOJ API Integration Plan

## Overview

This document outlines the detailed plan for building API endpoints to enable integration between TDTOJ (side B) and the student management system (side A). The implementation focuses on creating necessary endpoints that allow side A to manage organizations, contests, and users within the TDTOJ system.

## Required API Endpoints

### 1. Create Organization (POST /api/tdtu/organizations)

**Purpose:**
- Allow side A to create a new organization with users in TDTOJ

**Implementation Steps:**
1. Create a new view function that accepts POST requests
2. Extract organization data and user list from request
3. Validate the incoming data
4. Create a new Organization object in the database
5. Add the requesting user as an organization admin
6. Add all provided users to the organization
7. Return a redirect link to the contest creation page


### 2. Get Organization Edit Link (GET /api/tdtu/organizations/:id/edit-link)

**Purpose:**
- Provide side A with a link to edit an organization in TDTOJ

**Implementation Steps:**
1. Create a view function that accepts GET requests
2. Validate the organization ID and verify access rights
3. Generate an edit link for the organization
4. Return the link in the response



### 3. Delete Organization (DELETE /api/tdtu/organizations/:id)

**Purpose:**
- Allow side A to delete an organization in TDTOJ

**Implementation Steps:**
1. Create a view function that accepts DELETE requests
2. Validate the organization ID and verify access rights
3. Delete the organization and related data
4. Return success status




### 4. Get Organization Contests (GET /api/tdtu/organizations/:id/contests)

**Purpose:**
- Allow side A to retrieve all contests associated with an organization

**Implementation Steps:**
1. Create a view function that accepts GET requests
2. Validate the organization ID and verify access rights
3. Fetch all contests associated with the organization
4. Return contest data in the response



## Token Verification

### Implementation Plan

1. **Token Verification Function (utils.py)**
   ```python
   def verify_token(token):
       """
       Placeholder for token verification.
       In the future, this will call side A's API to verify the token.
       """
       # Mock implementation - always return success with dummy user data
       user_data = {
           'id': '12345',
           'username': 'testuser',
           'email': 'test@example.com',
           'name': 'Test User',
       }
       return True, user_data
   ```




- The first version will not include actual token verification - this will be implemented later
- All APIs will return JSON responses
- Error handling should be comprehensive with appropriate HTTP status codes
- Transaction management should be used where appropriate to ensure data consistency 