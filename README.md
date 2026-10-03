# Employee Compensation Service

Backend service built with Python, Azure Functions, and Azure SQL Database for managing employee records and generating compensation reports.

## Architecture

```text
Client
   |
   v
Azure Functions (HTTP APIs)
   |
   v
Azure SQL Database
   |
   +-- Department
   +-- Employee
```

All employee and compensation data is accessed through the Azure Functions layer. Clients do not access the database directly.

## Tech Stack

- Python
- Azure Functions
- Azure SQL Database
- pyodbc


## Setup

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Configure the database connection:
   - Set the `SQL_CONNECTION_STRING` environment variable.
   - For local development, configure it in `local.settings.json`.
   - Do not commit database credentials or `local.settings.json` to source control.

3. Create and seed the database:
   Run the following SQL scripts against your database:

   ```sql
   sql/schema.sql
   sql/seed.sql
   ```

   `schema.sql` creates the `Department` and `Employee` tables. `seed.sql` inserts sample departments and employees used for testing the CRUD APIs and compensation reports.

4. Start the Azure Functions app locally:

   ```bash
   func start
   ```

Local API base URL:

```text
http://localhost:7071/api
```

## API Endpoints

### Employee CRUD

| Method | Endpoint | Description |
|---|---|---|
| POST | `/employees` | Create an employee |
| GET | `/employees` | Retrieve all employees |
| GET | `/employees/{id}` | Retrieve an employee by ID |
| GET | `/employees?departmentId={id}` | Retrieve employees by department |
| PUT | `/employees/{id}` | Update an employee |
| DELETE | `/employees/{id}` | Delete an employee |
| GET | `/employees-with-default-bonus` | Retrieve employees with a 5% default bonus when no bonus is stored |

### Compensation Reports

| Method | Endpoint | Description |
|---|---|---|
| GET | `/reports/total-bonus` | Total bonus paid across the company |
| GET | `/reports/no-bonus` | Employees who have never received a bonus |
| GET | `/reports/bonus-percentage` | Bonus as a percentage of salary |
| GET | `/reports/departments-bonus` | Departments where total bonus exceeds average salary |
| GET | `/reports/bonus-ranking` | Employees ranked by bonus amount |
| GET | `/reports/highest-compensation` | Highest base salary and highest total compensation |

## Default Bonus Handling

The optional default bonus requirement is implemented as a read-time calculation.

- Employees with an actual stored bonus return that bonus.
- Employees with `NULL` bonus receive a calculated default of 5% of salary through the `/employees-with-default-bonus` endpoint.
- The default bonus is not written back to the database.
- Standard employee endpoints continue to return the actual stored bonus value, including `NULL` when applicable.

This preserves the distinction between an employee having no stored bonus and having a calculated default bonus.

## Error Handling

The service returns appropriate HTTP status codes for common scenarios:

- `200 OK` — successful retrieval or update
- `201 Created` — employee successfully created
- `204 No Content` — employee successfully deleted
- `400 Bad Request` — invalid request data or parameters
- `404 Not Found` — employee does not exist
- `500 Internal Server Error` — unexpected server or database error

## Production Configuration

- Database credentials are stored as environment or application settings and are not hardcoded in the source code.
- The deployed Azure Function uses the `SQL_CONNECTION_STRING` application setting to connect to Azure SQL Database.

## Deployed Application

Azure Function App:

```text
https://fusion-employee-compensation-2026.azurewebsites.net
```

API base URL:

```text
https://fusion-employee-compensation-2026.azurewebsites.net/api
```

The deployed HTTP-triggered functions require a function key for authentication.

## Testing

The application was tested locally and after Azure deployment.

Testing covered:

- Employee CRUD operations
- Department filtering
- Invalid request validation
- Default bonus calculation
- All six compensation reports
- Azure Function to Azure SQL connectivity
