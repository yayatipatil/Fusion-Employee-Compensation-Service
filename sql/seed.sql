--Employee Compensation Service
--Seed Data

INSERT INTO Department 
(DepartmentID, DepartmentName, Location)
VALUES
(1, 'HR', 'Bangalore'),
(2, 'Engineering', 'Pune'),
(3, 'Finance', 'Mumbai'),
(4, 'Sales', 'Delhi'),
(5, 'Marketing', 'Hyderabad');

INSERT INTO Employee
(FirstName, LastName, DepartmentID, Salary, Bonus, HireDate)
VALUES
('Tanvi', 'Patil', 2, 1200000.00, 120000.00, '2022-06-10'),
('Anusha', 'Karoshi', 2, 950000.00, 95000.00, '2021-04-15'),
('Kedar', 'Kusane', 2, 850000.00, NULL, '2023-01-20'),
('Sumedh', 'Betgeri', 1, 600000.00, 30000.00, '2022-08-12'),
('Sudeep', 'Hegde', 1, 550000.00, NULL, '2023-05-18'),
('Srushti', 'Bali', 3, 700000.00, 400000.00, '2020-07-01'),
('Khushi', 'Shirodkar', 3, 650000.00, 350000.00, '2021-09-25'),
('Shubham', 'Desai', 4, 1500000.00, NULL, '2019-03-15'),
('Rutuja', 'Jadhav', 4, 1100000.00, 500000.00, '2020-11-10'),
('Uma', 'Gowda', 5, 800000.00, 80000.00, '2022-12-05');
