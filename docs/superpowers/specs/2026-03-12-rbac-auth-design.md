# RBAC Auth System Design Specification

## 1. Overview
The goal is to replace the static `.auth` file-based authentication with a dynamic, database-backed Role-Based Access Control (RBAC) system. This will allow administrators to manage user permissions through bot commands and provide granular control over which commands are accessible to different user levels.

## 2. Goals & Success Criteria
- **Command-Driven Management:** Admins can grant/revoke access without editing files.
- **Role Hierarchy:** Support for `OWNER`, `ADMIN`, and `USER` roles.
- **Dynamic Access Control:** Ability to set minimum required roles for any bot command.
- **Seamless Migration:** Automatically migrate existing authorized users from `.auth`.
- **Auto-Registration:** New users are automatically added to the database as unauthorized.

## 3. Database Schema Evolution

### 3.1. `users` Table Updates
The existing `users` table will be updated to include authorization status and roles.
- `role` (TEXT): One of `OWNER`, `ADMIN`, `USER`.
- `is_authorized` (BOOLEAN): `1` for authorized, `0` for unauthorized.

### 3.2. `command_permissions` Table (New)
Stores the minimum role required to execute a specific command.
- `command` (TEXT PRIMARY KEY): The command name (e.g., `camera`, `weather`).
- `min_role` (TEXT): One of `PUBLIC`, `USER`, `ADMIN`, `OWNER`.

## 4. Middleware & Enforcement Logic

### 4.1. `AuthMiddleware`
- **User Discovery:** For every incoming message, fetch the user from the `users` table.
- **Auto-Registration:** If the user doesn't exist, create a new entry with `is_authorized=0` and `role='USER'`.
- **Access Check:**
    1. Identify the command being called (if any).
    2. Check `command_permissions` for the required `min_role`.
    3. **Default Behavior:**
        - If the command is currently protected by `AdminMiddleware` ( `log`, `photo`, `top`, `mygroups`), default `min_role` is `ADMIN`.
        - All other commands default to `PUBLIC`.
    4. Compare user's role and `is_authorized` status against the `min_role`.
- **Denial Behavior:** Unauthorized attempts to protected commands receive a notification message.

## 5. Management Commands

### 5.1. Authorization Management
- `/grant @username [USER|ADMIN|OWNER]`: Authorizes a user and assigns a role.
- `/revoke @username`: Deauthorizes a user.
- `/list_authorized`: Displays a list of all currently authorized users and their roles.

### 5.2. Access Configuration
- `/set_access [command] [PUBLIC|USER|ADMIN|OWNER]`: Sets the required role for a specific command.

## 6. Migration & Bootstrap Strategy
- **One-Time Migration:** On bot startup, if `.auth` exists:
    1. Read all user IDs.
    2. The first ID becomes the `OWNER`.
    3. Remaining IDs become `ADMIN`.
    4. Records are inserted into the `users` table with `is_authorized=1`.
    5. The `.auth` file is renamed to `.auth.bak` to prevent re-migration.

## 7. Security Rules
- Only `OWNER` can promote someone to `OWNER`.
- Only `ADMIN` or `OWNER` can `/grant` or `/revoke` permissions for `USER` and `ADMIN` roles.
- The `OWNER` cannot be `/revoke`d by an `ADMIN`.

## 8. Testing Strategy
- **Unit Tests:**
    - Test `AuthMiddleware` logic with various user roles and command levels.
    - Test migration script with a sample `.auth` file.
    - Test database helper functions for RBAC management.
- **Integration Tests:**
    - Verify that unauthorized users can access `PUBLIC` commands but are blocked from `ADMIN` commands (by default).
    - Verify that `/grant` and `/revoke` correctly update database state and bot behavior.
