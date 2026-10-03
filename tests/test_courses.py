from app.services.courses import course_service


def test_courses_returned_for_missing_skills():
    missing = ["aws", "docker", "kubernetes"]
    courses = course_service.get_courses_for_skills(missing, max_courses=3)
    assert len(courses) == 3
    for c in courses:
        assert "http" in c["url"]
        assert len(c["title"]) > 3
        assert len(c["provider"]) > 2


def test_courses_max_limit():
    missing = ["aws", "docker", "kubernetes", "react", "python", "sql"]
    courses = course_service.get_courses_for_skills(missing, max_courses=3)
    assert len(courses) == 3


def test_courses_fallback():
    missing = ["some_extremely_rare_custom_tool_xyz"]
    courses = course_service.get_courses_for_skills(missing, max_courses=3)
    assert len(courses) == 3
    assert all("http" in c["url"] for c in courses)
