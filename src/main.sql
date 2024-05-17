SELECT 
    s1.student as one_student,
    s2.student as other_student,
    ABS(s1.score - s2.score) as score_diff
FROM scores s1 JOIN scores s2 ON 
ORDER BY score_diff, s1.student, s2.student
LIMIT 1

-- 1. Fetch all the duplicate records in a table
WITH duplicate as (
    select user_id, user_name, rank() over (partition by user_name order by user_id) as row_number, email
    from USERS
) SELECT user_id, user_name, email
FROM duplicate where row_number > 1;


-- 2. fetch the second last record from employee table
select emp_id, emp_name, dept_name, salary
from (
select *,
row_number() over (order by emp_id desc) as rn
from employee e) x
where x.rn = 2;


-- 3. Display details of employees who either earn the highest or the lowest salary in each department

WITH dep_salary as (
    SELECT dept_name,
    max(salary) over (partition by dept_name) as max_salary,
    min(salary) over (partition by dept_name) as min_salary
    FROM employee
) SELECT emp_id, emp_name, dept_name, salary, ds.min_salary, ds.max_salary
FROM dep_salary ds left join employee e on ds.dept_name = e.dept_name
WHERE salary = ds.min_salary or salary = ds.max_salary


-- 4. Details of doctors who work in the same hospital but different specialty

SELECT name, specialty, hospital
FROM doctors d1
    join doctors d2 on d1.id <> d2.id and d1.hospital = d2.hospital and d1.specialty <> d2.specialty


SELECT name, specialty, hospital
FROM doctors d1
    join doctors d2 on d1.id <> d2.id and d1.hospital = d2.hospital

-- 5. Fetch users who logged in consecutively 3 or more times
WITH repeated_users as (
    SELECT
		user_name, case
			when user_name = lead(user_name) over (order by login_date) and
				user_name = lead(user_name, 2) over (order by login_date)
			then TRUE
			end as repeated
    FROM login_details
) SELECT distinct user_name as repeated_names
from repeated_users where repeated is true

-- 6. write a SQL query to interchange the adjacent student names
SELECT
	student_name, case
		when lead(id) over () %2<>0 then lead(student_name, -1) over ()
		when lead(id) over () %2=0 then lead(student_name) over ()
		else student_name
	end as new_student_name
FROM students


-- 7. fetch all the records when London had extremely cold temperature for 3 consecutive days or more.


-- 8. query to get the histogram of specialties of the unique physicians who have done the procedures but never did prescribe anything.
with phy_procedure as (
	select physician_id
	from patient_treatment pt
	left join event_category ec on ec.event_name = pt.event_name
	where ec.category = 'Prescription'
) select speciality, count(ps.physician_id)
from patient_treatment pt
left join physician_speciality ps on pt.physician_id = ps.physician_id
where ps.physician_id not in (select * from phy_procedure) and event_name not in (select event_name from event_category where category<>'Procedure')
group by 1


-- 9. Find the top 2 accounts with the maximum number of unique patients on a monthly basis.
with leaderboard as (select 
	to_char(date, 'Month') as month, account_id, count(distinct patient_id) as no_unique_patients,
	rank() over (partition by to_char(date, 'Month') order by count(distinct patient_id) desc) as rank,
	row_number() over (partition by to_char(date, 'Month')) rn
from patient_logs
group by 1, 2) select month, account_id, no_unique_patients from leaderboard where rn <= 2