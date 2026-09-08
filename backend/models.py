from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    email = Column(String, unique=True, index=True)
    role = Column(String, default="student")
    hashed_password = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    enrollments = relationship("Enrollment", back_populates="user", cascade="all, delete-orphan")
    course_progress = relationship("CourseProgress", back_populates="user", cascade="all, delete-orphan")
    module_progress = relationship("ModuleProgress", back_populates="user", cascade="all, delete-orphan")
    progress_records = relationship("UserProgress", back_populates="user", cascade="all, delete-orphan")
    segment_performances = relationship("StudentSegmentPerformance", back_populates="user", cascade="all, delete-orphan")
    assessment_results = relationship("StudentAssessment", back_populates="user", cascade="all, delete-orphan")
    lab_performances = relationship("StudentLabPerformance", back_populates="user", cascade="all, delete-orphan")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(String, unique=True, index=True)  # e.g., 'course_network_sec'
    title = Column(String, nullable=False)
    category = Column(String, nullable=False, default="Cybersecurity")
    description = Column(Text, nullable=True)
    difficulty = Column(String, default="Beginner")
    total_segments = Column(Integer, default=10)
    total_modules = Column(Integer, default=6)
    total_labs = Column(Integer, default=3)
    created_at = Column(DateTime, default=datetime.utcnow)

    @property
    def course_name(self) -> str:
        return self.title

    @course_name.setter
    def course_name(self, val: str):
        self.title = val

    # Relationships
    segments = relationship("CourseSegment", back_populates="course", cascade="all, delete-orphan", order_by="CourseSegment.segment_number")
    enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")
    course_progress = relationship("CourseProgress", back_populates="course", cascade="all, delete-orphan")
    module_progress = relationship("ModuleProgress", back_populates="course", cascade="all, delete-orphan")
    progress_records = relationship("UserProgress", back_populates="course", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="course", cascade="all, delete-orphan")


class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    course_id = Column(String, ForeignKey("courses.course_id"), nullable=False, index=True)
    status = Column(String, default="active")  # 'active', 'completed', 'dropped'
    enrolled_at = Column(DateTime, default=datetime.utcnow)
    completion_percentage = Column(Float, default=0.0)
    overall_score = Column(Float, nullable=True)
    last_accessed = Column(DateTime, default=datetime.utcnow)

    @property
    def student_id(self) -> int:
        return self.user_id

    @property
    def enrollment_status(self) -> str:
        return self.status

    @enrollment_status.setter
    def enrollment_status(self, val: str):
        self.status = val

    # Relationships
    user = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")


class CourseProgress(Base):
    __tablename__ = "course_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    course_id = Column(String, ForeignKey("courses.course_id"), nullable=False, index=True)
    completion_percentage = Column(Float, default=0.0)
    completed_modules = Column(Integer, default=0)
    total_modules = Column(Integer, default=6)
    current_module = Column(String, nullable=True)
    last_activity = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="course_progress")
    course = relationship("Course", back_populates="course_progress")


class ModuleProgress(Base):
    __tablename__ = "module_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    course_id = Column(String, ForeignKey("courses.course_id"), nullable=False, index=True)
    module_name = Column(String, nullable=False)
    module_status = Column(String, default="Not Started")  # 'Not Started', 'In Progress', 'Completed'
    completion_percentage = Column(Float, default=0.0)
    score = Column(Float, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    last_activity = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="module_progress")
    course = relationship("Course", back_populates="module_progress")


class CourseSegment(Base):
    __tablename__ = "course_segments"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(String, ForeignKey("courses.course_id"), nullable=False, index=True)
    segment_number = Column(Integer, nullable=False)
    segment_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Relationships
    course = relationship("Course", back_populates="segments")
    segment_performances = relationship("StudentSegmentPerformance", back_populates="segment", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="segment", cascade="all, delete-orphan")
    labs = relationship("StudentLabPerformance", back_populates="segment", cascade="all, delete-orphan")


class StudentSegmentPerformance(Base):
    __tablename__ = "student_segment_performances"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    course_id = Column(String, ForeignKey("courses.course_id"), nullable=False, index=True)
    segment_id = Column(Integer, ForeignKey("course_segments.id"), nullable=False, index=True)
    status = Column(String, default="Not Started")  # 'Completed', 'In Progress', 'Not Started'
    score = Column(Float, nullable=True)
    max_score = Column(Float, default=100.0)
    completion_percentage = Column(Float, default=0.0)
    attempts = Column(Integer, default=0)
    completed_at = Column(DateTime, nullable=True)
    last_accessed = Column(DateTime, default=datetime.utcnow)

    @property
    def student_id(self) -> int:
        return self.user_id

    @property
    def maximum_score(self) -> float:
        return self.max_score

    # Relationships
    user = relationship("User", back_populates="segment_performances")
    segment = relationship("CourseSegment", back_populates="segment_performances")


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(String, ForeignKey("courses.course_id"), nullable=False, index=True)
    segment_id = Column(Integer, ForeignKey("course_segments.id"), nullable=True, index=True)
    assessment_name = Column(String, nullable=False)
    assessment_type = Column(String, default="quiz")  # 'quiz', 'exam', 'assignment'
    max_score = Column(Float, default=100.0)

    @property
    def maximum_score(self) -> float:
        return self.max_score

    # Relationships
    course = relationship("Course", back_populates="assessments")
    segment = relationship("CourseSegment", back_populates="assessments")
    student_results = relationship("StudentAssessment", back_populates="assessment", cascade="all, delete-orphan")


class StudentAssessment(Base):
    __tablename__ = "student_assessments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    course_id = Column(String, ForeignKey("courses.course_id"), nullable=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=True, index=True)
    assessment_name = Column(String, nullable=True)
    score = Column(Float, nullable=False)
    attempts = Column(Integer, default=1)
    status = Column(String, default="Completed")  # 'Passed', 'Failed', 'Completed', 'In Progress', 'Not Started'
    submitted_at = Column(DateTime, default=datetime.utcnow)

    @property
    def student_id(self) -> int:
        return self.user_id

    @property
    def maximum_score(self) -> float:
        if self.assessment and self.assessment.max_score is not None:
            return self.assessment.max_score
        return 100.0

    @property
    def max_score(self) -> float:
        return self.maximum_score

    # Relationships
    user = relationship("User", back_populates="assessment_results")
    assessment = relationship("Assessment", back_populates="student_results")


class StudentLabPerformance(Base):
    __tablename__ = "student_lab_performances"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    course_id = Column(String, ForeignKey("courses.course_id"), nullable=False, index=True)
    segment_id = Column(Integer, ForeignKey("course_segments.id"), nullable=True, index=True)
    lab_name = Column(String, nullable=False)
    status = Column(String, default="Not Started")  # 'Completed', 'In Progress', 'Not Started'
    score = Column(Float, nullable=True)
    attempts = Column(Integer, default=0)
    completed_at = Column(DateTime, nullable=True)

    @property
    def student_id(self) -> int:
        return self.user_id

    # Relationships
    user = relationship("User", back_populates="lab_performances")
    segment = relationship("CourseSegment", back_populates="labs")


class UserProgress(Base):
    __tablename__ = "user_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    course_id = Column(String, ForeignKey("courses.course_id"), nullable=False, index=True)
    completed_modules = Column(Integer, default=0)
    total_modules = Column(Integer, default=6)
    current_module = Column(String, nullable=True)
    completed_labs = Column(Integer, default=0)
    assessment_score = Column(Float, nullable=True)
    completion_percentage = Column(Float, default=0.0)
    last_activity = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="progress_records")
    course = relationship("Course", back_populates="progress_records")
