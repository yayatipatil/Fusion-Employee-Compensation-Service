import json
from datetime import datetime

import azure.functions as func

from db import get_connection


app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


def employee_to_dict(row):
    return {
        "employeeId": row.EmployeeID,
        "firstName": row.FirstName,
        "lastName": row.LastName,
        "departmentId": row.DepartmentID,
        "salary": float(row.Salary),
        "bonus": float(row.Bonus) if row.Bonus is not None else None,
        "hireDate": row.HireDate.isoformat() if row.HireDate else None
    }


def validate_employee_data(data):
    if not isinstance(data, dict):
        return "Request body must be a JSON object."

    required_fields = ["firstName", "lastName", "departmentId", "salary"]

    for field in required_fields:
        if field not in data:
            return f"Missing required field: {field}"

    if not isinstance(data["firstName"], str) or not data["firstName"].strip():
        return "firstName must be a non-empty string."

    if not isinstance(data["lastName"], str) or not data["lastName"].strip():
        return "lastName must be a non-empty string."

    if not isinstance(data["departmentId"], int):
        return "departmentId must be an integer."

    if not isinstance(data["salary"], (int, float)) or data["salary"] < 0:
        return "salary must be a non-negative number."

    if "bonus" in data and data["bonus"] is not None:
        if not isinstance(data["bonus"], (int, float)) or data["bonus"] < 0:
            return "bonus must be a non-negative number."

    if "hireDate" in data and data["hireDate"] is not None:
        try:
            datetime.strptime(data["hireDate"], "%Y-%m-%d")
        except (ValueError, TypeError):
            return "hireDate must use YYYY-MM-DD format."

    return None


@app.route(route="employees", methods=["POST"])
def create_employee(req: func.HttpRequest) -> func.HttpResponse:
    try:
        data = req.get_json()

        validation_error = validate_employee_data(data)

        if validation_error:
            return func.HttpResponse(
                json.dumps({"error": validation_error}),
                status_code=400,
                mimetype="application/json"
            )

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO Employee
                (FirstName, LastName, DepartmentID, Salary, Bonus, HireDate)
            OUTPUT
                INSERTED.EmployeeID,
                INSERTED.FirstName,
                INSERTED.LastName,
                INSERTED.DepartmentID,
                INSERTED.Salary,
                INSERTED.Bonus,
                INSERTED.HireDate
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            data["firstName"].strip(),
            data["lastName"].strip(),
            data["departmentId"],
            data["salary"],
            data.get("bonus"),
            data.get("hireDate")
        )

        row = cursor.fetchone()

        connection.commit()
        cursor.close()
        connection.close()

        return func.HttpResponse(
            json.dumps(employee_to_dict(row)),
            status_code=201,
            mimetype="application/json"
        )

    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON request body."}),
            status_code=400,
            mimetype="application/json"
        )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )


@app.route(route="employees", methods=["GET"])
def get_employees(req: func.HttpRequest) -> func.HttpResponse:
    try:
        department_id = req.params.get("departmentId")

        connection = get_connection()
        cursor = connection.cursor()

        if department_id:
            try:
                department_id = int(department_id)
            except ValueError:
                return func.HttpResponse(
                    json.dumps({"error": "departmentId must be an integer."}),
                    status_code=400,
                    mimetype="application/json"
                )

            cursor.execute(
                """
                SELECT
                    EmployeeID,
                    FirstName,
                    LastName,
                    DepartmentID,
                    Salary,
                    Bonus,
                    HireDate
                FROM Employee
                WHERE DepartmentID = ?
                ORDER BY EmployeeID
                """,
                department_id
            )
        else:
            cursor.execute(
                """
                SELECT
                    EmployeeID,
                    FirstName,
                    LastName,
                    DepartmentID,
                    Salary,
                    Bonus,
                    HireDate
                FROM Employee
                ORDER BY EmployeeID
                """
            )

        rows = cursor.fetchall()

        employees = [employee_to_dict(row) for row in rows]

        cursor.close()
        connection.close()

        return func.HttpResponse(
            json.dumps(employees),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )


@app.route(route="employees/{employee_id}", methods=["GET"])
def get_employee(req: func.HttpRequest) -> func.HttpResponse:
    try:
        employee_id = req.route_params.get("employee_id")

        try:
            employee_id = int(employee_id)
        except (ValueError, TypeError):
            return func.HttpResponse(
                json.dumps({"error": "Employee ID must be an integer."}),
                status_code=400,
                mimetype="application/json"
            )

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                EmployeeID,
                FirstName,
                LastName,
                DepartmentID,
                Salary,
                Bonus,
                HireDate
            FROM Employee
            WHERE EmployeeID = ?
            """,
            employee_id
        )

        row = cursor.fetchone()

        cursor.close()
        connection.close()

        if row is None:
            return func.HttpResponse(
                json.dumps({"error": "Employee not found."}),
                status_code=404,
                mimetype="application/json"
            )

        return func.HttpResponse(
            json.dumps(employee_to_dict(row)),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )


@app.route(route="employees/{employee_id}", methods=["PUT"])
def update_employee(req: func.HttpRequest) -> func.HttpResponse:
    try:
        employee_id = req.route_params.get("employee_id")

        try:
            employee_id = int(employee_id)
        except (ValueError, TypeError):
            return func.HttpResponse(
                json.dumps({"error": "Employee ID must be an integer."}),
                status_code=400,
                mimetype="application/json"
            )

        data = req.get_json()

        validation_error = validate_employee_data(data)

        if validation_error:
            return func.HttpResponse(
                json.dumps({"error": validation_error}),
                status_code=400,
                mimetype="application/json"
            )

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE Employee
            SET
                FirstName = ?,
                LastName = ?,
                DepartmentID = ?,
                Salary = ?,
                Bonus = ?,
                HireDate = ?
            WHERE EmployeeID = ?
            """,
            data["firstName"].strip(),
            data["lastName"].strip(),
            data["departmentId"],
            data["salary"],
            data.get("bonus"),
            data.get("hireDate"),
            employee_id
        )

        if cursor.rowcount == 0:
            cursor.close()
            connection.close()

            return func.HttpResponse(
                json.dumps({"error": "Employee not found."}),
                status_code=404,
                mimetype="application/json"
            )

        connection.commit()

        cursor.execute(
            """
            SELECT
                EmployeeID,
                FirstName,
                LastName,
                DepartmentID,
                Salary,
                Bonus,
                HireDate
            FROM Employee
            WHERE EmployeeID = ?
            """,
            employee_id
        )

        row = cursor.fetchone()

        cursor.close()
        connection.close()

        return func.HttpResponse(
            json.dumps(employee_to_dict(row)),
            status_code=200,
            mimetype="application/json"
        )

    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON request body."}),
            status_code=400,
            mimetype="application/json"
        )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )


@app.route(route="employees/{employee_id}", methods=["DELETE"])
def delete_employee(req: func.HttpRequest) -> func.HttpResponse:
    try:
        employee_id = req.route_params.get("employee_id")

        try:
            employee_id = int(employee_id)
        except (ValueError, TypeError):
            return func.HttpResponse(
                json.dumps({"error": "Employee ID must be an integer."}),
                status_code=400,
                mimetype="application/json"
            )

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM Employee
            WHERE EmployeeID = ?
            """,
            employee_id
        )

        if cursor.rowcount == 0:
            cursor.close()
            connection.close()

            return func.HttpResponse(
                json.dumps({"error": "Employee not found."}),
                status_code=404,
                mimetype="application/json"
            )

        connection.commit()

        cursor.close()
        connection.close()

        return func.HttpResponse(
            status_code=204
        )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )