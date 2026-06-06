from dataclasses import dataclass
import json
import re
from typing import Callable, Any


@dataclass
class ValidationResult:
    is_valid: bool
    feedback: str = ""
    normalized_value: Any = None


@dataclass
class Question:
    key: str
    prompt: str
    validator: Callable[[str], ValidationResult]


class SequentialIntakeAgent:
    def __init__(self, questions: list[Question]):
        self.questions = questions
        self.training_spec = {}

    def run(self) -> dict:
        print("\nMaverx Training Intake")
        print("Answer each question. If the answer is too vague, I will ask again.\n")

        for question in self.questions:
            while True:
                user_answer = input(question.prompt + "\n> ").strip()

                if user_answer.lower() in {"quit", "exit"}:
                    raise SystemExit("Intake cancelled.")

                result = question.validator(user_answer)

                if result.is_valid:
                    self.training_spec[question.key] = result.normalized_value
                    print("Accepted.\n")
                    break

                print(f"Not good enough yet: {result.feedback}\n")

        self.training_spec["tier"] = "Tier 1"
        self.training_spec["didactic_model"] = [
            "kick_off",
            "theory",
            "example",
            "exercise",
            "wrap_up"
        ]
        self.training_spec["required_outputs"] = {
            "editable_pptx": True,
            "speaker_notes": True,
            "pre_bite": True,
            "post_bite": True
        }

        return self.training_spec

    def save_json(self, path: str = "training_spec.json") -> None:
        with open(path, "w", encoding="utf-8") as file:
            json.dump(self.training_spec, file, indent=2, ensure_ascii=False)

        print(f"Saved intake JSON to {path}")


def validate_topic(answer: str) -> ValidationResult:
    vague_topics = {
        "ai", "training", "business", "communication", "leadership",
        "management", "technology", "software", "data"
    }

    cleaned = answer.strip()
    lowered = cleaned.lower()

    if len(cleaned) < 3:
        return ValidationResult(
            False,
            "The topic is too short. Give a specific skill or domain."
        )

    if lowered in vague_topics:
        return ValidationResult(
            False,
            "The topic is too broad. Specify the concrete skill, for example: "
            "'prompt engineering for marketing' or 'Power BI dashboard basics'."
        )

    return ValidationResult(True, normalized_value=cleaned)


def validate_audience(answer: str) -> ValidationResult:
    vague_audiences = {
        "everyone", "employees", "people", "staff", "team",
        "users", "workers", "students"
    }

    cleaned = answer.strip()
    lowered = cleaned.lower()

    if len(cleaned) < 4:
        return ValidationResult(
            False,
            "The audience is too short. Name a specific role, department, or group."
        )

    if lowered in vague_audiences:
        return ValidationResult(
            False,
            "The audience is too vague. Specify who they are, for example: "
            "'marketing team', 'HR managers', 'new sales employees', or 'finance analysts'."
        )

    return ValidationResult(True, normalized_value=cleaned)


def validate_knowledge_level(answer: str) -> ValidationResult:
    lowered = answer.strip().lower()

    beginner_terms = {"beginner", "beginners", "no experience", "no prior knowledge", "basic"}
    intermediate_terms = {"intermediate", "some experience", "medium"}
    advanced_terms = {"advanced", "expert", "experienced"}

    if lowered in beginner_terms:
        return ValidationResult(True, normalized_value="beginner")

    if lowered in intermediate_terms:
        return ValidationResult(True, normalized_value="intermediate")

    if lowered in advanced_terms:
        return ValidationResult(True, normalized_value="advanced")

    return ValidationResult(
        False,
        "Please choose one of: beginner, intermediate, or advanced."
    )


def validate_duration(answer: str) -> ValidationResult:
    lowered = answer.strip().lower()

    hour_match = re.search(r"(\d+(?:\.\d+)?)\s*(hour|hours|hr|hrs|h)", lowered)
    minute_match = re.search(r"(\d+)\s*(minute|minutes|min|mins|m)", lowered)

    if hour_match:
        hours = float(hour_match.group(1))
        minutes = int(hours * 60)

        if minutes < 30:
            return ValidationResult(False, "The training duration seems too short.")
        if minutes > 480:
            return ValidationResult(False, "For Tier 1, keep it to one training session, ideally under 8 hours.")

        return ValidationResult(True, normalized_value=minutes)

    if minute_match:
        minutes = int(minute_match.group(1))

        if minutes < 10:
            return ValidationResult(False, "The training duration seems too short.")
        if minutes > 480:
            return ValidationResult(False, "For Tier 1, keep it to one training session, ideally under 8 hours.")

        return ValidationResult(True, normalized_value=minutes)

    if lowered in {"half day", "half-day"}:
        return ValidationResult(True, normalized_value=240)

    if lowered in {"full day", "full-day"}:
        return ValidationResult(True, normalized_value=480)

    return ValidationResult(
        False,
        "Please give the duration clearly, for example: '3 hours', '180 minutes', or 'half day'."
    )


def validate_learning_objective(answer: str) -> ValidationResult:
    cleaned = answer.strip()
    lowered = cleaned.lower()

    weak_phrases = {
        "learn about",
        "understand",
        "know about",
        "get familiar with"
    }

    action_verbs = {
        "apply", "create", "build", "use", "evaluate", "improve",
        "write", "design", "explain", "analyze", "compare", "choose",
        "identify", "practice"
    }

    if len(cleaned.split()) < 6:
        return ValidationResult(
            False,
            "The learning objective is too short. Use the format: "
            "'By the end, participants can ...'"
        )

    if any(phrase in lowered for phrase in weak_phrases):
        return ValidationResult(
            False,
            "The objective is a bit vague. Make it measurable. For example: "
            "'By the end, participants can create and evaluate prompts for marketing tasks.'"
        )

    if not any(verb in lowered for verb in action_verbs):
        return ValidationResult(
            False,
            "The objective should include a concrete action verb, such as create, apply, use, evaluate, or improve."
        )

    return ValidationResult(True, normalized_value=cleaned)


def build_questions() -> list[Question]:
    return [
        Question(
            key="topic",
            prompt="1. What is the topic or skill to be trained?",
            validator=validate_topic
        ),
        Question(
            key="target_audience",
            prompt="2. Who is the target audience?",
            validator=validate_audience
        ),
        Question(
            key="knowledge_level",
            prompt="3. What is the knowledge level of participants? Beginner, intermediate, or advanced?",
            validator=validate_knowledge_level
        ),
        Question(
            key="duration_minutes",
            prompt="4. How long is the training?",
            validator=validate_duration
        ),
        Question(
            key="primary_learning_objective",
            prompt="5. What is the primary learning objective?",
            validator=validate_learning_objective
        ),
    ]


if __name__ == "__main__":
    agent = SequentialIntakeAgent(build_questions())
    spec = agent.run()
    agent.save_json()

    print("\nFinal TrainingSpec:")
    print(json.dumps(spec, indent=2, ensure_ascii=False))