# Employee Compensation Service

Backend service built with Python, Azure Functions, and Azure SQL Database for managing employee records and generating compensation reports.

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

2. Configure the `SQL_CONNECTION_STRING` environment variable.
3. Run the SQL scripts:

   ```bash
   sql/schema.sql
   sql/seed.sql
   ```

4. Start the Azure Functions app:

   ```bash
   func start
   ```

The API runs at:

```text
http://localhost:7071/api
```

## API Endpoints

### Employee CRUD

- `POST /employees` - Create employee
- `GET /employees` - Get all employees
- `GET /employees/{id}` - Get employee by ID
- `GET /employees?departmentId={id}` - Filter by department
- `PUT /employees/{id}` - Update employee
- `DELETE /employees/{id}` - Delete employee
- `GET /employees-with-default-bonus` - Get employees with a 5% default bonus where no bonus is stored

### Compensation Reports

- `GET /reports/total-bonus`
- `GET /reports/no-bonus`
- `GET /reports/bonus-percentage`
- `GET /reports/departments-bonus`
- `GET /reports/bonus-ranking`
- `GET /reports/highest-compensation`

## Notes

- `NULL` bonus represents no bonus and is treated as `0` for calculations where required.
- The optional 5% default bonus is implemented as a separate read-time endpoint: `/employees-with-default-bonus`.
- The standard employee endpoints return the actual stored bonus values, including `null` when no bonus exists.
- The default-bonus endpoint calculates 5% of salary for employees whose stored bonus is `NULL`, without modifying the database.
- Database credentials are stored in environment settings and are not committed to source control.