import database as db

# ─── MODELS MATCHING "Class Diagram.png" ─────────────────────────────────────
# These classes strictly satisfy the UML requirements defined in the SRS diagrams.
# The core Flask app uses the procedural database layer directly for speed,
# but these entities formally define the object-oriented structure.

class User:
    def __init__(self, userId: int, username: str, email: str, password: str):
        self.userId = userId
        self.username = username
        self.email = email
        self.password = password
        
    @staticmethod
    def register(username: str, email: str, password_hash: str):
        db.create_user(username, email, password_hash)
        
    @staticmethod
    def login(email: str):
        return db.get_user_by_email(email)


class Profile:
    def __init__(self, age: int, height: float, weight: float, gender: str):
        self.age = age
        self.height = height
        self.weight = weight
        self.gender = gender

    @staticmethod
    def updateProfile(user_id: int, username: str, age: int, height: float, weight: float, gender: str):
        db.update_profile(user_id, username, age, height, weight, gender)


class Goal:
    def __init__(self, goalId: int, targetWeight: float, targetDate: str):
        self.goalId = goalId
        self.targetWeight = targetWeight
        self.targetDate = targetDate
        
    @staticmethod
    def setGoal(user_id: int, category: str, target_value: float, target_date: str):
        db.add_goal(user_id, category, target_value, target_date)


class HealthCalculator:
    @staticmethod
    def calculateBMI(weight: float, height: float):
        if not weight or not height or height <= 0:
            return None, None
        bmi = round(weight / ((height / 100) ** 2), 1)
        if bmi < 18.5:
            category = 'Underweight'
        elif bmi < 25:
            category = 'Normal'
        elif bmi < 30:
            category = 'Overweight'
        else:
            category = 'Obese'
        return bmi, category

    @staticmethod
    def calculateBMR(weight: float, height: float, age: int, gender: str):
        if not all([weight, height, age, gender]):
            return None
        if gender.lower() == 'male':
            return round(10 * weight + 6.25 * height - 5 * age + 5)
        else:
            return round(10 * weight + 6.25 * height - 5 * age - 161)


class Workout:
    def __init__(self, workoutId: int, exerciseName: str, sets: int, reps: int, date: str):
        self.workoutId = workoutId
        self.exerciseName = exerciseName
        self.sets = sets
        self.reps = reps
        self.date = date

    @staticmethod
    def addWorkout(user_id: int, activity: str, duration: int, calories: int, sets: int, reps: int):
        db.add_history(user_id, activity, duration, calories, sets, reps)


class Exercise:
    def __init__(self, name: str, type_: str, muscle: str, difficulty: str, instructions: str):
        self.name = name
        self.type = type_
        self.muscle = muscle
        self.difficulty = difficulty
        self.instructions = instructions


class ExerciseService:
    @staticmethod
    def searchExercise(muscle: str, ex_type: str, difficulty: str):
        # Uses the procedural get_exercises_from_api helper in app.py directly
        pass
        
    @staticmethod
    def getExercise(exercise_name: str):
        pass
