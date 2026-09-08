import os
import sys
from datetime import datetime

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import models
from database import engine, SessionLocal

def test_demo_student_progress():
    print("=" * 80)
    print("TEST: Verifying Demo Student LMS Data Retrieval (Sachi Prasad)")
    print("=" * 80)

    db = SessionLocal()
    try:
        # 1. Verify User
        student = db.query(models.User).filter(models.User.email == "sachi@test.com").first()
        assert student is not None, "Error: Demo student sachi@test.com not found!"
        print("\n[1/6] USER MODEL VERIFICATION:")
        print(f"  - ID: {student.id}")
        print(f"  - Name: {student.name}")
        print(f"  - Email: {student.email}")
        print(f"  - Role: {student.role}")
        assert student.name == "Sachi Prasad"
        assert student.email == "sachi@test.com"
        print("  -> User model verified successfully.")

        # 2. Verify Course
        course = db.query(models.Course).filter(models.Course.course_id == "course_network_sec").first()
        assert course is not None, "Error: Course course_network_sec not found!"
        print("\n[2/6] COURSE MODEL VERIFICATION:")
        print(f"  - ID: {course.id}")
        print(f"  - Course ID: {course.course_id}")
        print(f"  - Course Name: {course.course_name}")
        print(f"  - Description: {course.description}")
        print(f"  - Total Modules: {course.total_modules}")
        assert course.course_name == "Network Security Basics"
        print("  -> Course model verified successfully.")

        # 3. Verify Enrollment
        enrollment = db.query(models.Enrollment).filter(
            models.Enrollment.user_id == student.id,
            models.Enrollment.course_id == "course_network_sec"
        ).first()
        assert enrollment is not None, "Error: Enrollment not found for student!"
        print("\n[3/6] ENROLLMENT MODEL VERIFICATION:")
        print(f"  - User ID: {enrollment.user_id}")
        print(f"  - Course ID: {enrollment.course_id}")
        print(f"  - Status: {enrollment.enrollment_status}")
        print(f"  - Enrolled At: {enrollment.enrolled_at}")
        print(f"  - Completion %: {enrollment.completion_percentage}%")
        print(f"  - Overall Score: {enrollment.overall_score}%")
        assert enrollment.enrollment_status == "active"
        print("  -> Enrollment model verified successfully.")

        # 4. Verify Course Progress
        cp = db.query(models.CourseProgress).filter(
            models.CourseProgress.user_id == student.id,
            models.CourseProgress.course_id == "course_network_sec"
        ).first()
        assert cp is not None, "Error: CourseProgress record not found!"
        print("\n[4/6] COURSE PROGRESS MODEL VERIFICATION:")
        print(f"  - User ID: {cp.user_id}")
        print(f"  - Course ID: {cp.course_id}")
        print(f"  - Overall Completion: {cp.completion_percentage}%")
        print(f"  - Completed Modules: {cp.completed_modules} / {cp.total_modules}")
        print(f"  - Current Module: {cp.current_module}")
        print(f"  - Last Activity: {cp.last_activity}")
        assert cp.completion_percentage == 65.0
        assert cp.completed_modules == 4
        assert cp.total_modules == 6
        assert cp.current_module == "Firewall Configuration"
        print("  -> Course Progress model verified successfully.")

        # 5. Verify Module Progress
        modules = db.query(models.ModuleProgress).filter(
            models.ModuleProgress.user_id == student.id,
            models.ModuleProgress.course_id == "course_network_sec"
        ).order_by(models.ModuleProgress.id).all()
        assert len(modules) == 6, f"Error: Expected 6 modules, found {len(modules)}"
        print("\n[5/6] MODULE PROGRESS MODEL VERIFICATION (6 Modules):")
        completed_count = 0
        in_progress_count = 0
        not_started_count = 0
        for i, mod in enumerate(modules, 1):
            score_str = f"{mod.score}%" if mod.score is not None else "N/A"
            print(f"  Module {i}: {mod.module_name}")
            print(f"    - Status: {mod.module_status}")
            print(f"    - Completion: {mod.completion_percentage}%")
            print(f"    - Score: {score_str}")
            if mod.module_status == "Completed":
                completed_count += 1
            elif mod.module_status == "In Progress":
                in_progress_count += 1
            elif mod.module_status == "Not Started":
                not_started_count += 1

        assert completed_count == 4, f"Expected 4 completed modules, got {completed_count}"
        assert in_progress_count == 1, f"Expected 1 in-progress module, got {in_progress_count}"
        assert not_started_count == 1, f"Expected 1 not-started module, got {not_started_count}"
        print(f"  -> Breakdown: {completed_count} Completed, {in_progress_count} In Progress, {not_started_count} Not Started.")
        print("  -> Module Progress model verified successfully.")

        # 6. Verify Assessments
        student_assessments = db.query(models.StudentAssessment).filter(
            models.StudentAssessment.user_id == student.id,
            models.StudentAssessment.course_id == "course_network_sec"
        ).all()
        assert len(student_assessments) >= 5, f"Expected at least 5 assessments, found {len(student_assessments)}"
        print(f"\n[6/6] ASSESSMENT MODEL VERIFICATION ({len(student_assessments)} Assessments):")
        for sa in student_assessments:
            a_name = sa.assessment_name or (sa.assessment.assessment_name if sa.assessment else "Assessment")
            print(f"  - {a_name}: Score {sa.score}/{sa.maximum_score} (Status: {sa.status})")

        print("\n" + "=" * 80)
        print("ALL 6 LMS DATABASE MODELS & DEMO STUDENT DATA VERIFIED 100% SUCCESSFULLY!")
        print("=" * 80)
        return True

    finally:
        db.close()

if __name__ == "__main__":
    success = test_demo_student_progress()
    if not success:
        sys.exit(1)
