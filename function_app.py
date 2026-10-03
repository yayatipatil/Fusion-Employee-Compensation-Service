import json
import logging
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

    except Exception:
        logging.exception("Error while processing request.")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error."}),
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

    except Exception:
        logging.exception("Error while processing request.")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error."}),
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

    except Exception:
        logging.exception("Error while processing request.")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error."}),
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

    except Exception:
        logging.exception("Error while processing request.")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error."}),
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

    except Exception:
        logging.exception("Error while processing request.")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error."}),
            status_code=500,
            mimetype="application/json"
        )

    
@app.route(route="reports/total-bonus", methods=["GET"])
def get_total_bonus(req: func.HttpRequest) -> func.HttpResponse:
    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT COALESCE(SUM(COALESCE(Bonus, 0)), 0) AS TotalBonus
            FROM Employee
            """
        )

        row = cursor.fetchone()

        cursor.close()
        connection.close()

        return func.HttpResponse(
            json.dumps({
                "totalBonus": float(row.TotalBonus)
            }),
            status_code=200,
            mimetype="application/json"
        )

    except Exception:
        logging.exception("Error while processing request.")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error."}),
            status_code=500,
            mimetype="application/json"
        )


@app.route(route="reports/no-bonus", methods=["GET"])
def get_employees_with_no_bonus(req: func.HttpRequest) -> func.HttpResponse:
    try:
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
            WHERE Bonus IS NULL
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

    except Exception:
        logging.exception("Error while processing request.")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error."}),
            status_code=500,
            mimetype="application/json"
        )


@app.route(route="reports/bonus-percentage", methods=["GET"])
def get_bonus_percentage(req: func.HttpRequest) -> func.HttpResponse:
    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                EmployeeID,
                FirstName,
                LastName,
                Salary,
                Bonus,
                ROUND((Bonus / Salary) * 100, 2) AS BonusPercentage
            FROM Employee
            WHERE Bonus IS NOT NULL
            ORDER BY EmployeeID
            """
        )

        rows = cursor.fetchall()

        result = [
            {
                "employeeId": row.EmployeeID,
                "firstName": row.FirstName,
                "lastName": row.LastName,
                "salary": float(row.Salary),
                "bonus": float(row.Bonus),
                "bonusPercentage": float(row.BonusPercentage)
            }
            for row in rows
        ]

        cursor.close()
        connection.close()

        return func.HttpResponse(
            json.dumps(result),
            status_code=200,
            mimetype="application/json"
        )

    except Exception:
        logging.exception("Error while processing request.")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error."}),
            status_code=500,
            mimetype="application/json"
        )


@app.route(route="reports/departments-bonus", methods=["GET"])
def get_departments_bonus_exceeds_average(req: func.HttpRequest) -> func.HttpResponse:
    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                d.DepartmentID,
                d.DepartmentName,
                SUM(COALESCE(e.Bonus, 0)) AS TotalBonus,
                AVG(e.Salary) AS AverageSalary
            FROM Department d
            INNER JOIN Employee e
                ON d.DepartmentID = e.DepartmentID
            GROUP BY
                d.DepartmentID,
                d.DepartmentName
            HAVING SUM(COALESCE(e.Bonus, 0)) > AVG(e.Salary)
            ORDER BY d.DepartmentID
            """
        )

        rows = cursor.fetchall()

        result = [
            {
                "departmentId": row.DepartmentID,
                "departmentName": row.DepartmentName,
                "totalBonus": float(row.TotalBonus),
                "averageSalary": round(float(row.AverageSalary), 2)
            }
            for row in rows
        ]

        cursor.close()
        connection.close()

        return func.HttpResponse(
            json.dumps(result),
            status_code=200,
            mimetype="application/json"
        )

    except Exception:
        logging.exception("Error while processing request.")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error."}),
            status_code=500,
            mimetype="application/json"
        )


@app.route(route="reports/bonus-ranking", methods=["GET"])
def get_bonus_ranking(req: func.HttpRequest) -> func.HttpResponse:
    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                EmployeeID,
                FirstName,
                LastName,
                Salary,
                Bonus,
                RANK() OVER (
                    ORDER BY
                        CASE WHEN Bonus IS NULL THEN 1 ELSE 0 END,
                        COALESCE(Bonus, 0) DESC
                ) AS BonusRank
            FROM Employee
            ORDER BY BonusRank, EmployeeID
            """
        )

        rows = cursor.fetchall()

        result = [
            {
                "employeeId": row.EmployeeID,
                "firstName": row.FirstName,
                "lastName": row.LastName,
                "salary": float(row.Salary),
                "bonus": float(row.Bonus) if row.Bonus is not None else None,
                "bonusRank": int(row.BonusRank)
            }
            for row in rows
        ]

        cursor.close()
        connection.close()

        return func.HttpResponse(
            json.dumps(result),
            status_code=200,
            mimetype="application/json"
        )

    except Exception:
        logging.exception("Error while processing request.")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error."}),
            status_code=500,
            mimetype="application/json"
        )


@app.route(route="reports/highest-compensation", methods=["GET"])
def get_highest_compensation(req: func.HttpRequest) -> func.HttpResponse:
    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT TOP 1
                EmployeeID,
                FirstName,
                LastName,
                Salary,
                Bonus
            FROM Employee
            ORDER BY Salary DESC, EmployeeID
            """
        )

        highest_salary_row = cursor.fetchone()

        cursor.execute(
            """
            SELECT TOP 1
                EmployeeID,
                FirstName,
                LastName,
                Salary,
                Bonus,
                (Salary + COALESCE(Bonus, 0)) AS TotalCompensation
            FROM Employee
            ORDER BY
                (Salary + COALESCE(Bonus, 0)) DESC,
                EmployeeID
            """
        )

        highest_total_row = cursor.fetchone()

        cursor.close()
        connection.close()

        highest_salary_employee = {
            "employeeId": highest_salary_row.EmployeeID,
            "firstName": highest_salary_row.FirstName,
            "lastName": highest_salary_row.LastName,
            "salary": float(highest_salary_row.Salary),
            "bonus": (
                float(highest_salary_row.Bonus)
                if highest_salary_row.Bonus is not None
                else None
            )
        }

        highest_total_employee = {
            "employeeId": highest_total_row.EmployeeID,
            "firstName": highest_total_row.FirstName,
            "lastName": highest_total_row.LastName,
            "salary": float(highest_total_row.Salary),
            "bonus": (
                float(highest_total_row.Bonus)
                if highest_total_row.Bonus is not None
                else None
            ),
            "totalCompensation": float(highest_total_row.TotalCompensation)
        }

        same_employee = (
            highest_salary_row.EmployeeID == highest_total_row.EmployeeID
        )

        result = {
            "highestBaseSalary": highest_salary_employee,
            "highestTotalCompensation": highest_total_employee,
            "sameEmployee": same_employee
        }

        return func.HttpResponse(
            json.dumps(result),
            status_code=200,
            mimetype="application/json"
        )

    except Exception:
        logging.exception("Error while processing request.")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error."}),
            status_code=500,
            mimetype="application/json"
        )