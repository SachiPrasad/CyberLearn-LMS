import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import models
from database import SessionLocal
from knowledge.ingestion import kb_pipeline
from knowledge import course_catalog
from rag.retrieval import hybrid_retriever
from rag.reranker import reranker
from rag.context_builder import context_builder

logger = logging.getLogger(__name__)

class LMSAgentTools:
    """Controlled production database and RAG tools for CyberLearn LMS DAX Assistant."""

    # =========================================================================
    # RAG General Knowledge Tools
    # =========================================================================
    @staticmethod
    def search_course_content(query: str, course_filter: Optional[str] = None) -> Dict[str, Any]:
        """Tool: Searches verified CyberLearn curriculum chunks using hybrid retrieval."""
        filter_meta = {"course_id": course_filter} if course_filter else None
        candidates = hybrid_retriever.retrieve(query, filter_metadata=filter_meta, top_k=10)
        selected, confidence, has_ctx = reranker.rerank_and_threshold(candidates)
        context_str, sources, doc_ids = context_builder.build_context(selected)
        
        return {
            "has_context": has_ctx,
            "confidence": confidence,
            "sources": sources,
            "context": context_str,
            "doc_ids": doc_ids
        }

    @staticmethod
    def search_courses(query: str) -> Dict[str, Any]:
        """Tool: Searches structured course catalog for matching courses."""
        return course_catalog.search_courses(query)

    @staticmethod
    def get_course_information(course_id: str) -> Optional[Dict[str, Any]]:
        """Tool: Retrieves full structured course metadata and syllabus."""
        return course_catalog.get_course_information(course_id)

    @staticmethod
    def recommend_courses(criteria: Optional[str] = None, difficulty: Optional[str] = None) -> Dict[str, Any]:
        """Tool: Recommends courses based on target career path or difficulty."""
        return course_catalog.recommend_courses(criteria=criteria, difficulty=difficulty)

    @staticmethod
    def compare_courses(course_id_1: str, course_id_2: str) -> Optional[Dict[str, Any]]:
        """Tool: Compares two courses side-by-side."""
        return course_catalog.compare_courses(course_id_1, course_id_2)

    @staticmethod
    def get_course_modules(course_id: str) -> Optional[Dict[str, Any]]:
        """Tool: Retrieves verified ordered syllabus and module list for a course."""
        return course_catalog.get_course_modules(course_id)

    @staticmethod
    def get_course_prerequisites(course_id: str) -> Optional[Dict[str, Any]]:
        """Tool: Retrieves verified prerequisites for a course."""
        return course_catalog.get_course_prerequisites(course_id)

    @staticmethod
    def get_course_duration(course_id: str) -> Optional[Dict[str, Any]]:
        """Tool: Retrieves verified duration for a course."""
        return course_catalog.get_course_duration(course_id)

    @staticmethod
    def get_course_labs(course_id: str) -> Optional[Dict[str, Any]]:
        """Tool: Retrieves verified hands-on virtual labs for a course."""
        return course_catalog.get_course_labs(course_id)

    @staticmethod
    def get_course_certification(course_id: str) -> Optional[Dict[str, Any]]:
        """Tool: Retrieves verified certification requirements for a course."""
        return course_catalog.get_course_certification(course_id)

    @staticmethod
    def get_course_skills(course_id: str) -> Optional[Dict[str, Any]]:
        """Tool: Retrieves verified skills and learning outcomes for a course."""
        return course_catalog.get_course_skills(course_id)

    @staticmethod
    def get_platform_info() -> Dict[str, Any]:
        """Tool: Retrieves platform and CyberDaksh overview facts."""
        return course_catalog.PLATFORM_INFO

    @staticmethod
    def get_course_details(course_id: str, db: Optional[Session] = None) -> Optional[Dict[str, Any]]:
        """Tool: Retrieves course details from DB or knowledge base."""
        # Prefer structured catalog first
        info = course_catalog.get_course_information(course_id)
        if info:
            return {
                "course_id": info["course_id"],
                "title": info["course_name"],
                "category": info["category"],
                "difficulty": info["difficulty"],
                "description": info["description"],
                "total_segments": info["total_segments"],
                "total_labs": info["labs"]
            }

        if db:
            course = db.query(models.Course).filter(
                (models.Course.course_id == course_id) | (models.Course.title.ilike(f"%{course_id}%"))
            ).first()
            if course:
                return {
                    "course_id": course.course_id,
                    "title": course.title,
                    "category": course.category,
                    "difficulty": course.difficulty,
                    "description": course.description,
                    "total_segments": course.total_segments,
                    "total_labs": course.total_labs
                }
        
        for doc in kb_pipeline.get_all_documents():
            if (doc.get("course_id") == course_id or course_id.lower() in doc.get("course_name", "").lower()) and doc.get("document_type") == "course_description":
                return {
                    "course_id": doc["course_id"],
                    "title": doc["course_name"],
                    "category": "Cybersecurity",
                    "difficulty": "Beginner",
                    "description": doc["content"],
                    "total_segments": 10,
                    "total_labs": 3
                }
        return None

    @staticmethod
    def get_certification_requirements() -> Dict[str, Any]:
        """Tool: Retrieves official CyberLearn certification criteria."""
        return {
            "required_module_completion": "100% of all lectures & text materials",
            "required_lab_completion": "All hands-on virtual lab exercises",
            "minimum_final_assessment_score": "75%",
            "issuer": "CyberDaksh Verified Certificate Authority"
        }

    @staticmethod
    def search_faq(topic: str) -> Dict[str, Any]:
        """Tool: Searches platform and advising FAQs."""
        return LMSAgentTools.search_course_content(query=topic)

    # =========================================================================
    # Personal LMS Student Database Tools (Isolated from RAG Knowledge Base)
    # =========================================================================

    @staticmethod
    def get_user_enrollments(user_id: int, db: Session) -> Dict[str, Any]:
        """
        Tool: Retrieves all enrolled courses for the authenticated student.
        Prevents IDOR by strictly enforcing user_id from the authenticated JWT session.
        """
        enrollments = db.query(models.Enrollment).filter(models.Enrollment.user_id == user_id).all()
        if not enrollments:
            return {
                "type": "enrollments",
                "count": 0,
                "enrollments": []
            }

        enr_list = []
        for e in enrollments:
            course = e.course or db.query(models.Course).filter(models.Course.course_id == e.course_id).first()
            c_name = course.title if course else e.course_id
            enr_list.append({
                "course_id": e.course_id,
                "course_name": c_name,
                "status": e.status,
                "completion_percentage": round(e.completion_percentage, 1),
                "overall_score": round(e.overall_score, 1) if e.overall_score is not None else None,
                "enrolled_at": e.enrolled_at.strftime("%B %d, %Y") if e.enrolled_at else None,
                "last_accessed": e.last_accessed.strftime("%B %d, %Y") if e.last_accessed else None
            })

        return {
            "type": "enrollments",
            "count": len(enr_list),
            "enrollments": enr_list
        }

    # Backward compatibility alias
    @staticmethod
    def get_enrollments(user_id: int, db: Session) -> List[Dict[str, Any]]:
        res = LMSAgentTools.get_user_enrollments(user_id, db)
        return [
            {
                "course_id": e["course_id"],
                "course_title": e["course_name"],
                "status": e["status"],
                "enrolled_at": e["enrolled_at"]
            }
            for e in res.get("enrollments", [])
        ]

    @staticmethod
    def get_course_progress(user_id: int, course_id: str, db: Session) -> Optional[Dict[str, Any]]:
        """
        Tool: Retrieves structured course progress, completion, score, and segment breakdown.
        """
        # Resolve course
        course = db.query(models.Course).filter(
            (models.Course.course_id == course_id) | 
            (models.Course.title.ilike(f"%{course_id}%"))
        ).first()

        if not course:
            return None

        # Check enrollment
        enr = db.query(models.Enrollment).filter(
            models.Enrollment.user_id == user_id,
            models.Enrollment.course_id == course.course_id
        ).first()

        # Retrieve segment performances
        segments = db.query(models.CourseSegment).filter(
            models.CourseSegment.course_id == course.course_id
        ).order_by(models.CourseSegment.segment_number).all()

        perfs = db.query(models.StudentSegmentPerformance).filter(
            models.StudentSegmentPerformance.user_id == user_id,
            models.StudentSegmentPerformance.course_id == course.course_id
        ).all()
        perf_map = {p.segment_id: p for p in perfs}

        seg_results = []
        completed_count = 0
        in_progress_count = 0
        not_started_count = 0
        total_comp_sum = 0.0
        scores_list = []

        for seg in segments:
            perf = perf_map.get(seg.id)
            status = perf.status if perf else "Not Started"
            score = perf.score if perf else None
            comp_pct = perf.completion_percentage if perf else 0.0
            attempts = perf.attempts if perf else 0
            last_act = perf.last_accessed.strftime("%B %d, %Y") if perf and perf.last_accessed else None

            if status == "Completed":
                completed_count += 1
            elif status == "In Progress":
                in_progress_count += 1
            else:
                not_started_count += 1

            total_comp_sum += comp_pct
            if score is not None:
                scores_list.append(score)

            seg_results.append({
                "segment_number": seg.segment_number,
                "segment_name": seg.segment_name,
                "description": seg.description,
                "status": status,
                "score": round(score, 1) if score is not None else None,
                "max_score": 100.0,
                "completion_percentage": round(comp_pct, 1),
                "attempts": attempts,
                "last_activity": last_act
            })

        total_segs = len(segments) or 10
        calc_overall_comp = round(total_comp_sum / total_segs, 1) if total_segs else 0.0
        calc_overall_score = round(sum(scores_list) / len(scores_list), 1) if scores_list else None

        last_acc_str = enr.last_accessed.strftime("%B %d, %Y") if enr and enr.last_accessed else (
            seg_results[0]["last_activity"] if seg_results else datetime.utcnow().strftime("%B %d, %Y")
        )

        return {
            "type": "course_progress",
            "course_id": course.course_id,
            "course_name": course.title,
            "difficulty": course.difficulty,
            "completion_percentage": enr.completion_percentage if enr else calc_overall_comp,
            "overall_score": enr.overall_score if enr and enr.overall_score is not None else calc_overall_score,
            "completed_segments": completed_count,
            "in_progress_segments": in_progress_count,
            "not_started_segments": not_started_count,
            "total_segments": total_segs,
            "status": enr.status if enr else ("In Progress" if completed_count < total_segs else "Completed"),
            "last_accessed": last_acc_str,
            "segments": seg_results
        }

    @staticmethod
    def get_user_progress(user_id: int, course_id: Optional[str] = None, db: Optional[Session] = None) -> Dict[str, Any]:
        """
        Tool: Retrieves the currently authenticated student's LMS course progress,
        including enrolled course, enrollment status, CourseProgress record, and
        all ModuleProgress records.
        """
        manage_db = False
        if db is None:
            db = SessionLocal()
            manage_db = True

        try:
            # 1. Verify user exists
            user = db.query(models.User).filter(models.User.id == user_id).first()
            if not user:
                return {
                    "type": "user_progress",
                    "found": False,
                    "reason": "user_not_found"
                }

            # 2. Resolve course & enrollment
            course = None
            enrollment = None

            if course_id:
                # Resolve requested course
                course = db.query(models.Course).filter(
                    (models.Course.course_id == course_id) |
                    (models.Course.title.ilike(f"%{course_id}%"))
                ).first()
                if not course:
                    return {
                        "type": "user_progress",
                        "found": False,
                        "reason": "course_not_found"
                    }

                # Verify student is enrolled in this specific course
                enrollment = db.query(models.Enrollment).filter(
                    models.Enrollment.user_id == user_id,
                    models.Enrollment.course_id == course.course_id
                ).first()
                if not enrollment:
                    return {
                        "type": "user_progress",
                        "found": False,
                        "reason": "not_enrolled"
                    }
            else:
                # Find student's active enrollment
                enrollment = db.query(models.Enrollment).filter(
                    models.Enrollment.user_id == user_id,
                    models.Enrollment.status == "active"
                ).first()

                if not enrollment:
                    # Fallback to any enrollment if no active one found
                    enrollment = db.query(models.Enrollment).filter(
                        models.Enrollment.user_id == user_id
                    ).first()

                if not enrollment:
                    return {
                        "type": "user_progress",
                        "found": False,
                        "reason": "no_enrollment"
                    }

                course = enrollment.course or db.query(models.Course).filter(
                    models.Course.course_id == enrollment.course_id
                ).first()

                if not course:
                    return {
                        "type": "user_progress",
                        "found": False,
                        "reason": "course_not_found"
                    }

            # 3. Retrieve CourseProgress record
            cp = db.query(models.CourseProgress).filter(
                models.CourseProgress.user_id == user_id,
                models.CourseProgress.course_id == course.course_id
            ).first()

            if cp:
                completion_pct = round(cp.completion_percentage, 1)
                completed_modules = cp.completed_modules
                total_modules = cp.total_modules
                current_module = cp.current_module
                last_activity = cp.last_activity.isoformat() if cp.last_activity else (
                    enrollment.last_accessed.isoformat() if enrollment.last_accessed else datetime.utcnow().isoformat()
                )
            else:
                # Fallback if CourseProgress record hasn't been created yet
                completion_pct = round(enrollment.completion_percentage, 1) if enrollment.completion_percentage is not None else 0.0
                completed_modules = 0
                total_modules = course.total_modules or 6
                current_module = None
                last_activity = enrollment.last_accessed.isoformat() if enrollment.last_accessed else datetime.utcnow().isoformat()

            # 4. Retrieve all ModuleProgress records for student & course
            mod_records = db.query(models.ModuleProgress).filter(
                models.ModuleProgress.user_id == user_id,
                models.ModuleProgress.course_id == course.course_id
            ).order_by(models.ModuleProgress.id).all()

            modules_list = [
                {
                    "name": m.module_name,
                    "completion_percentage": round(m.completion_percentage, 1) if m.completion_percentage is not None else 0.0,
                    "score": round(m.score, 1) if m.score is not None else None,
                    "status": m.module_status
                }
                for m in mod_records
            ]

            # 5. Build structured return object
            enrolled_at_str = enrollment.enrolled_at.isoformat() if enrollment.enrolled_at else None

            result = {
                "type": "user_progress",
                "user_id": user.id,
                "course": {
                    "id": course.id,
                    "course_id": course.course_id,
                    "name": course.course_name or course.title
                },
                "enrollment": {
                    "status": enrollment.status or enrollment.enrollment_status or "active",
                    "enrolled_at": enrolled_at_str
                },
                "progress": {
                    "completion_percentage": completion_pct,
                    "completed_modules": completed_modules,
                    "total_modules": total_modules,
                    "current_module": current_module,
                    "last_activity": last_activity
                },
                "performance": {
                    "overall_score": round(enrollment.overall_score, 1) if enrollment.overall_score is not None else None
                },
                "modules": modules_list
            }

            return result

        finally:
            if manage_db:
                db.close()

    @staticmethod
    def get_segment_performance(
        user_id: int,
        course_id: Optional[str] = None,
        segment_name: Optional[str] = None,
        segment_id: Optional[int] = None,
        status_filter: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Tool: Retrieves segment performance filtered by segment name, ID, or completion status.
        """
        if not db:
            return {"type": "segment_performance", "count": 0, "segments": []}

        query = db.query(
            models.StudentSegmentPerformance,
            models.CourseSegment,
            models.Course
        ).join(
            models.CourseSegment, models.StudentSegmentPerformance.segment_id == models.CourseSegment.id
        ).join(
            models.Course, models.StudentSegmentPerformance.course_id == models.Course.course_id
        ).filter(
            models.StudentSegmentPerformance.user_id == user_id
        )

        if course_id:
            query = query.filter(
                (models.StudentSegmentPerformance.course_id == course_id) |
                (models.Course.title.ilike(f"%{course_id}%"))
            )

        if segment_name:
            query = query.filter(models.CourseSegment.segment_name.ilike(f"%{segment_name}%"))

        if segment_id:
            query = query.filter(models.CourseSegment.id == segment_id)

        if status_filter:
            if status_filter.lower() in ("completed", "done", "finished"):
                query = query.filter(models.StudentSegmentPerformance.status == "Completed")
            elif status_filter.lower() in ("in progress", "pending", "active", "incomplete"):
                query = query.filter(models.StudentSegmentPerformance.status != "Completed")
            elif status_filter.lower() in ("not started", "unstarted"):
                query = query.filter(models.StudentSegmentPerformance.status == "Not Started")

        results = query.order_by(models.CourseSegment.segment_number).all()

        seg_items = []
        for perf, seg, course in results:
            seg_items.append({
                "course_name": course.title,
                "course_id": course.course_id,
                "segment_number": seg.segment_number,
                "segment_name": seg.segment_name,
                "status": perf.status,
                "score": round(perf.score, 1) if perf.score is not None else None,
                "max_score": perf.max_score,
                "completion_percentage": round(perf.completion_percentage, 1),
                "attempts": perf.attempts,
                "completed_at": perf.completed_at.strftime("%B %d, %Y") if perf.completed_at else None
            })

        return {
            "type": "segment_performance",
            "filter": status_filter or segment_name or "all",
            "count": len(seg_items),
            "segments": seg_items
        }

    @staticmethod
    def get_assessment_performance(
        user_id: int,
        course_id: Optional[str] = None,
        assessment_name: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Tool: Retrieves quiz/exam assessment performance for the authenticated student.
        """
        if not db:
            return {"type": "assessment_performance", "count": 0, "assessments": []}

        query = db.query(
            models.StudentAssessment,
            models.Assessment,
            models.Course
        ).join(
            models.Assessment, models.StudentAssessment.assessment_id == models.Assessment.id
        ).join(
            models.Course, models.Assessment.course_id == models.Course.course_id
        ).filter(
            models.StudentAssessment.user_id == user_id
        )

        if course_id:
            query = query.filter(
                (models.Assessment.course_id == course_id) |
                (models.Course.title.ilike(f"%{course_id}%"))
            )

        if assessment_name:
            query = query.filter(models.Assessment.assessment_name.ilike(f"%{assessment_name}%"))

        records = query.all()
        results = []
        for sa, a, course in records:
            results.append({
                "assessment_name": a.assessment_name,
                "assessment_type": a.assessment_type,
                "course_name": course.title,
                "score": round(sa.score, 1),
                "max_score": a.max_score,
                "attempts": sa.attempts,
                "status": sa.status,
                "submitted_at": sa.submitted_at.strftime("%B %d, %Y") if sa.submitted_at else None
            })

        return {
            "type": "assessment_performance",
            "count": len(results),
            "assessments": results
        }

    @staticmethod
    def get_lab_performance(
        user_id: int,
        course_id: Optional[str] = None,
        lab_name: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Tool: Retrieves hands-on virtual lab performance records.
        """
        if not db:
            return {"type": "lab_performance", "count": 0, "labs": []}

        query = db.query(
            models.StudentLabPerformance,
            models.Course
        ).join(
            models.Course, models.StudentLabPerformance.course_id == models.Course.course_id
        ).filter(
            models.StudentLabPerformance.user_id == user_id
        )

        if course_id:
            query = query.filter(
                (models.StudentLabPerformance.course_id == course_id) |
                (models.Course.title.ilike(f"%{course_id}%"))
            )

        if lab_name:
            query = query.filter(models.StudentLabPerformance.lab_name.ilike(f"%{lab_name}%"))

        records = query.all()
        results = []
        for lp, course in records:
            results.append({
                "lab_name": lp.lab_name,
                "course_name": course.title,
                "status": lp.status,
                "score": round(lp.score, 1) if lp.score is not None else None,
                "attempts": lp.attempts,
                "completed_at": lp.completed_at.strftime("%B %d, %Y") if lp.completed_at else None
            })

        return {
            "type": "lab_performance",
            "count": len(results),
            "labs": results
        }

    @staticmethod
    def get_overall_performance(user_id: int, course_id: Optional[str] = None, db: Optional[Session] = None) -> Dict[str, Any]:
        """
        Tool: Calculates cumulative learning performance across all courses.
        """
        if not db:
            return {"type": "overall_performance", "status": "No database session"}

        enrollments = db.query(models.Enrollment).filter(models.Enrollment.user_id == user_id).all()
        perfs = db.query(models.StudentSegmentPerformance).filter(models.StudentSegmentPerformance.user_id == user_id).all()
        assessments = db.query(models.StudentAssessment).filter(models.StudentAssessment.user_id == user_id).all()
        labs = db.query(models.StudentLabPerformance).filter(models.StudentLabPerformance.user_id == user_id).all()

        completed_segments = sum(1 for p in perfs if p.status == "Completed")
        in_progress_segments = sum(1 for p in perfs if p.status == "In Progress")
        total_segments = len(perfs)

        scores = [p.score for p in perfs if p.score is not None]
        avg_score = round(sum(scores) / len(scores), 1) if scores else None

        passed_quizzes = sum(1 for a in assessments if a.status in ("Passed", "Completed") and a.score >= 75)
        completed_labs = sum(1 for l in labs if l.status == "Completed")

        return {
            "type": "overall_performance",
            "enrolled_courses_count": len(enrollments),
            "average_score": avg_score,
            "completed_segments": completed_segments,
            "in_progress_segments": in_progress_segments,
            "total_tracked_segments": total_segments,
            "quizzes_passed": passed_quizzes,
            "labs_completed": completed_labs,
            "status": "Active Learner"
        }

lms_tools = LMSAgentTools()

def get_user_progress(user_id: int, course_id: Optional[str] = None, db: Optional[Session] = None) -> Dict[str, Any]:
    """
    Top-level helper function to retrieve a student's course progress.
    """
    return LMSAgentTools.get_user_progress(user_id, course_id, db)

def search_courses(query: str) -> Dict[str, Any]:
    """Top-level helper to search courses."""
    return LMSAgentTools.search_courses(query)

def get_course_information(course_id: str) -> Optional[Dict[str, Any]]:
    """Top-level helper to get full course information."""
    return LMSAgentTools.get_course_information(course_id)

def recommend_courses(criteria: Optional[str] = None, difficulty: Optional[str] = None) -> Dict[str, Any]:
    """Top-level helper to recommend courses."""
    return LMSAgentTools.recommend_courses(criteria=criteria, difficulty=difficulty)

def compare_courses(course_id_1: str, course_id_2: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Top-level helper to compare two courses."""
    return LMSAgentTools.compare_courses(course_id_1, course_id_2)

def get_course_modules(course_id: str) -> Optional[Dict[str, Any]]:
    """Top-level helper to get course modules."""
    return LMSAgentTools.get_course_modules(course_id)

def get_course_prerequisites(course_id: str) -> Optional[Dict[str, Any]]:
    """Top-level helper to get course prerequisites."""
    return LMSAgentTools.get_course_prerequisites(course_id)

def get_course_duration(course_id: str) -> Optional[Dict[str, Any]]:
    """Top-level helper to get course duration."""
    return LMSAgentTools.get_course_duration(course_id)

def get_course_labs(course_id: str) -> Optional[Dict[str, Any]]:
    """Top-level helper to get course labs."""
    return LMSAgentTools.get_course_labs(course_id)

def get_course_certification(course_id: str) -> Optional[Dict[str, Any]]:
    """Top-level helper to get course certification."""
    return LMSAgentTools.get_course_certification(course_id)

def get_course_skills(course_id: str) -> Optional[Dict[str, Any]]:
    """Top-level helper to get course skills."""
    return LMSAgentTools.get_course_skills(course_id)

def get_platform_info() -> Dict[str, Any]:
    """Top-level helper to get platform information."""
    return LMSAgentTools.get_platform_info()



