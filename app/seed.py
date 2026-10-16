"""Початкове наповнення БД: ролі, дозволи, група, дисципліна, користувачі."""
from app.database import SessionLocal
from app.models import Grade, Group, Permission, Role, Subject, User
from app.security import hash_password

PERMISSIONS = {
    "read_grades": "Перегляд оцінок",
    "edit_grades": "Редагування оцінок",
    "read_schedule": "Перегляд розкладу",
    "manage_users": "Управління користувачами",
    "manage_groups": "Управління групами",
    "manage_subjects": "Управління дисциплінами",
    "view_reports": "Перегляд звітів",
}

# Матриця RBAC (принцип мінімальних привілеїв)
ROLE_MATRIX = {
    "admin": list(PERMISSIONS),
    "teacher": ["read_grades", "edit_grades", "read_schedule", "view_reports"],
    "student": ["read_grades", "read_schedule"],
}


def seed():
    db = SessionLocal()
    try:
        if db.query(Role).first():
            print("Database already seeded.")
            return

        perms = {name: Permission(name=name, description=desc)
                 for name, desc in PERMISSIONS.items()}
        db.add_all(perms.values())

        roles = {}
        for role_name, perm_names in ROLE_MATRIX.items():
            role = Role(name=role_name)
            role.permissions = [perms[p] for p in perm_names]
            roles[role_name] = role
        db.add_all(roles.values())

        group = Group(name="КН-31", department="Комп'ютерні науки", year=3)
        subject = Subject(name="Безпека інформаційних систем",
                          credits=4.0, semester=5)
        db.add_all([group, subject])
        db.flush()  # отримуємо id групи та дисципліни до commit

        admin = User(username="admin", email="admin@university.edu",
                     full_name="Адміністратор Системи",
                     password_hash=hash_password("Admin123!@#"))
        admin.roles.append(roles["admin"])

        teacher = User(username="teacher01", email="teacher@university.edu",
                       full_name="Іваненко Петро Миколайович",
                       password_hash=hash_password("Teacher123!"))
        teacher.roles.append(roles["teacher"])

        student = User(username="student01", email="student@university.edu",
                       full_name="Петренко Марія Олексіївна",
                       password_hash=hash_password("Student123!"),
                       group_id=group.id)
        student.roles.append(roles["student"])

        db.add_all([admin, teacher, student])
        db.flush()

        db.add(Grade(student_id=student.id, subject_id=subject.id,
                     grade=92, assigned_by=teacher.id))
        db.commit()

        print("Seed completed successfully!")
        print(f"  Roles: {db.query(Role).count()}, "
              f"Permissions: {db.query(Permission).count()}, "
              f"Users: {db.query(User).count()}")
    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
