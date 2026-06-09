# Student Attendance System - Specifications Report

## CHAPTER I: FUNCTIONAL REQUIREMENTS

### I. System Overview
The university needs to build an online student attendance system to automate attendance tracking, minimize errors, and provide real-time reports for both students and lecturers.

### II. System Features

#### User Account Management
1. Users (Students, Lecturers, and Administrators) log in to the system with their personal accounts to use features based on their roles.
2. Users can change their personal information and account passwords.
3. When a user forgets their password, the system supports creating a new temporary password and sending it to that user's university email.

#### Attendance Operations
*Each class session on the system includes the following information: course name, class section ID (unique), lecturer name, room, start time, end time, and attendance session status (not opened, open, or closed).*

4. When a lecturer opens an attendance session, students belonging to that class section can proceed to check in using their personal devices in class.
5. During the attendance time, students can view their recorded status, while lecturers can monitor the class list in real time and manually edit the status for each student (Present, Late, Excused Absence, Unexcused Absence).

**Attendance Processing Workflow:**
6. The system requires the lecturer to log in if there is no active session, then the lecturer selects the class section to officially open the attendance session.
7. The system displays the student list of the class and prepares the interface to be ready to receive check-in data.
8. Students perform attendance by scanning the lecturer's dynamic QR code or via the facial recognition camera located in the classroom.
9. Based on the time the student checks in, the system automatically classifies the status: checking in within the first 15 minutes of class is counted as **Present**; from minute 16 to minute 30 is counted as **Late**; after 30 minutes or when the lecturer closes the session, all students without data are automatically counted as **Absent**.
10. The system saves the information: actual timestamp, student ID, class ID, attendance method, and attendance status.
11. The system automatically sends a notification or confirmation email of the successful attendance result with time details to the student.

#### History and Attendance Statistics
12. Students can review their attendance history and attendance status for all courses taken during the semester.
13. Lecturers can view the summary statistics table of the total sessions attended and the absence percentage of each student in the class section.
14. Lecturers can export all attendance data and the class attendance report to an Excel file.

#### System Administration (For Academic Staff)
15. Academic staff can manage student records and update face data templates.
16. Academic staff can manage the course catalog, class sections, and timetables for the entire university.
17. Academic staff can manage and monitor attendance data across the entire system.

---

## CHAPTER II: SUPPLEMENTARY SPECIFICATION

### 1. Usability
18. The web interface for lecturers and academic staff must display clearly and intuitively on computer screens with a resolution of 1280 x 720 pixels or higher.
19. The interface for students must be highly responsive on the screens of mobile devices running iOS and Android.
20. Core actions such as scanning a QR code for attendance must be minimized, being completed within a maximum of 2 taps on the screen.

### 2. Reliability
21. The system must run stably and continuously with an availability rate of at least 99.5%, especially during the school hours from 06:30 AM to 09:30 PM daily.
22. The system must automatically perform a full data backup at 23:00 PM every night to prevent data loss due to hardware failures.
23. The system must support temporarily saving attendance data on the device when the local internet connection is lost and automatically synchronizing it to the server when the connection returns.

### 4. Supportability
27. The system source code must be divided into independent modules (accounts, attendance, reports) to facilitate convenient bug fixing or feature upgrades in the future.

### 5. Security
28. The system uses a Role-Based Access Control (RBAC) mechanism: students can only view their own data, and lecturers can only manage their assigned classes.
29. All data transmitted between user devices and the server must be securely encrypted via the HTTPS protocol.
30. The system must validate and sanitize input data to protect against common hacking threats such as SQL Injection or XSS.
31. The system applies a rate-limiting mechanism and Captcha codes to block automated software from checking in on behalf of others.

### 6. Business Rules
32. The attendance status of students is calculated automatically: checking in within the first 15 minutes of class is **Present**; from minute 16 to 30 is **Late**; after 30 minutes or when the session is closed is **Absent**.
33. The system automatically calculates the absence percentage over the total number of periods to provide visual attendance warnings.
