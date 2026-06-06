from dataclasses import dataclass
from typing import Any, Callable
import json
import os
from openai import OpenAI

from dotenv import load_dotenv


load_dotenv()


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_OPENROUTER_MODEL = "anthropic/claude-sonnet-4-6"
MIN_MEANINGFUL_WORD_COUNT = 5
QUESTION_KEYS_WITH_MINIMUM_DETAIL = {
    "topic",
    "target_audience",
    "knowledge_level",
    "primary_learning_objective",
}
KNOWLEDGE_LEVEL_VALUES = {"beginner", "intermediate", "advanced"}
DEFAULT_OUTPUT_PATH = "training_spec.json"


class LLMConfigurationError(RuntimeError):
    pass


class LLMRequestError(RuntimeError):
    pass


@dataclass
class Question:
    key: str
    canonical_question: str
    purpose: str
    expected_format: str


@dataclass
class IntakeReply:
    text: str
    is_complete: bool
    training_spec: dict[str, Any] | None = None


class LLMClient:
    def __init__(self) -> None:
        self.api_key = (os.getenv("OPENROUTER_API_KEY") or "").strip()
        self.model = os.getenv("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL).strip()

        if not self.api_key:
            raise LLMConfigurationError(
                "Missing OPENROUTER_API_KEY. Export it before running, for example:\n"
                'export OPENROUTER_API_KEY="your_openrouter_key"'
            )

        if self.api_key in {"your_openrouter_key", "YOUR_OPENROUTER_KEY"}:
            raise LLMConfigurationError(
                "OPENROUTER_API_KEY still contains the placeholder value. "
                "Replace it with your real OpenRouter key."
            )

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=OPENROUTER_BASE_URL,
        )

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 600,
    ) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
        except Exception as error:
            raise LLMRequestError(
                f"OpenRouter request failed while using model '{self.model}'.\n{error}"
            ) from error

        return response.choices[0].message.content


def extract_json(text: str) -> dict:
    """
    Robust enough for hackathon use.
    First try direct JSON.
    If the model adds extra text, extract the first JSON object.
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1:
            raise ValueError(f"No JSON object found in LLM response:\n{text}")

        return json.loads(text[start : end + 1])


class LLMSequentialIntakeAgent:
    def __init__(self, llm: LLMClient, questions: list[Question]) -> None:
        self.llm = llm
        self.questions = questions
        self.training_spec: dict[str, Any] = {}

    def run(
        self,
        on_complete: Callable[[dict[str, Any]], None] | None = None,
        output_path: str = DEFAULT_OUTPUT_PATH,
    ) -> dict:
        session = IntakeChatSession(
            agent=self,
            on_complete=on_complete,
            output_path=output_path,
            persist_on_complete=True,
        )
        reply = session.start()
        print(f"\n{reply.text}\n")

        while not reply.is_complete:
            user_answer = input("> ").strip()

            if user_answer.lower() in {"quit", "exit"}:
                raise SystemExit("Intake cancelled.")

            reply = session.handle_message(user_answer)
            print(f"{reply.text}\n")

        return reply.training_spec or self.training_spec

    def get_intro_message(self) -> str:
        return (
            "Hi, I am SlideKick.\n"
            "I am here to help you shape your ideas into a clear training PowerPoint.\n"
            "I will ask a few short questions so the slides match your topic, audience, timing, and learning goal."
        )

    def make_friendly_question(self, question: Question) -> str:
        system_prompt = """
You are a friendly but professional intake chatbot for a training PowerPoint generator.

Your job:
- Ask exactly one intake question.
- Keep the meaning of the canonical question.
- Do not ask multiple questions at once.
- Be concise.
- Sound natural and human.
- For duration questions, ask about session length or available time; do not ask about days.
"""

        user_prompt = f"""
Current collected training spec:
{json.dumps(self.training_spec, indent=2)}

Canonical question:
{question.canonical_question}

Why this question matters:
{question.purpose}

Rewrite the canonical question as one friendly question.
Return only the question text.
"""

        return self.llm.chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7,
            max_tokens=120,
        ).strip()

    def validate_answer(self, question: Question, user_answer: str, attempt_count: int) -> dict:
        cheap_validation = self.validate_with_cheap_checks(question, user_answer)
        if cheap_validation is not None:
            return cheap_validation

        system_prompt = """
You are a practical validation agent for a Maverx training deck intake flow.

Your job:
- Validate only the current question and answer.
- Do not validate future questions.
- Accept answers that are specific enough to generate a useful training deck, even if the wording is imperfect.
- Reject only answers that are clearly vague, unrelated, incomplete, or unusable.
- If rejected, ask a follow-up for the same question.
- If accepted, normalize the answer.
- Do not include examples in feedback unless the user has failed the same question 3 or more times.

Return only valid JSON with exactly this structure:

{
  "is_valid": true,
  "normalized_value": "string or number",
  "feedback_to_user": "short message",
  "follow_up_question": null
}

or:

{
  "is_valid": false,
  "normalized_value": null,
  "feedback_to_user": "short explanation and follow-up question",
  "follow_up_question": "the question to ask again"
}
"""

        user_prompt = f"""
We are collecting requirements for a Tier 1 training PowerPoint generator.

Already collected spec:
{json.dumps(self.training_spec, indent=2)}

Current field key:
{question.key}

Current question:
{question.canonical_question}

Purpose:
{question.purpose}

Expected format:
{question.expected_format}

User answer:
{user_answer}

Attempt number for this same question:
{attempt_count}

Validation standards:
- The answer must be specific enough to generate a professional training.
- Reject generic answers like "AI", "employees", "everyone", "business", "training", or "understand it".
- For knowledge level, normalize to exactly one of: beginner, intermediate, advanced.
- For duration, normalize to an integer number of minutes.
- For learning objective, accept practical phrasing if it names a concrete direction, skill, tool, or context.
- For learning objective, do not reject solely because the wording uses "understand" or is not perfectly measurable.
- For learning objective, normalize it into a concise outcome if the intent is clear.
- If rejecting and attempt number is 1 or 2, ask one short clarification question without giving examples.
- If rejecting and attempt number is 3 or more, you may give one short example.
- Keep feedback_to_user friendly and short.
"""

        raw_response = self.llm.chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.0,
            max_tokens=500,
        )

        validation = extract_json(raw_response)
        return self.hard_guard(question, validation)

    def validate_with_cheap_checks(self, question: Question, user_answer: str) -> dict | None:
        if question.key == "knowledge_level":
            normalized_level = self.normalize_knowledge_level(user_answer)
            if normalized_level:
                return {
                    "is_valid": True,
                    "normalized_value": normalized_level,
                    "feedback_to_user": "Accepted.",
                    "follow_up_question": None,
                }

        if not self.has_minimum_detail(question, user_answer):
            return self.reject_more_detail()

        if question.key != "primary_learning_objective":
            return None

        if self.is_good_enough_learning_objective(user_answer):
            return {
                "is_valid": True,
                "normalized_value": self.normalize_learning_objective(user_answer),
                "feedback_to_user": "Accepted.",
                "follow_up_question": None,
            }

        return None

    def has_minimum_detail(self, question: Question, answer: str) -> bool:
        if question.key not in QUESTION_KEYS_WITH_MINIMUM_DETAIL:
            return True

        if question.key == "knowledge_level" and answer.strip().lower() in KNOWLEDGE_LEVEL_VALUES:
            return True

        return len(answer.strip().split()) >= MIN_MEANINGFUL_WORD_COUNT

    def normalize_knowledge_level(self, answer: str) -> str | None:
        lowered = answer.strip().lower()

        beginner_terms = {"beginner", "beginners", "basic", "new", "none", "no experience"}
        intermediate_terms = {"intermediate", "some experience", "medium"}
        advanced_terms = {"advanced", "expert", "experienced"}

        if lowered in beginner_terms:
            return "beginner"

        if lowered in intermediate_terms:
            return "intermediate"

        if lowered in advanced_terms:
            return "advanced"

        return None

    def is_good_enough_learning_objective(self, answer: str) -> bool:
        lowered = answer.strip().lower()

        unrelated_terms = {"lunch", "weather", "holiday", "vacation"}
        if any(term in lowered for term in unrelated_terms):
            return False

        action_terms = {
            "apply",
            "use",
            "build",
            "create",
            "design",
            "evaluate",
            "explain",
            "identify",
            "integrate",
            "implement",
            "understand",
        }
        context_terms = {
            "agentic",
            "ai",
            "python",
            "project",
            "workflow",
            "tool",
            "ethical",
            "ethics",
            "real",
            "world",
        }

        return any(term in lowered for term in action_terms) and any(
            term in lowered for term in context_terms
        )

    def normalize_learning_objective(self, answer: str) -> str:
        cleaned = answer.strip().strip("\"'")
        if cleaned.lower().startswith("by the end"):
            return cleaned

        lowered = cleaned.lower()
        prefixes = [
            "i want them to ",
            "they should be able to ",
            "they should ",
            "participants should be able to ",
            "participants can ",
            "learners should be able to ",
            "learners can ",
        ]

        for prefix in prefixes:
            if lowered.startswith(prefix):
                cleaned = cleaned[len(prefix) :]
                break

        return f"By the end, participants can {cleaned[0].lower() + cleaned[1:]}"

    def hard_guard(self, question: Question, validation: dict) -> dict:
        """
        Python validation still protects us from bad LLM output.
        The LLM judges semantics; Python enforces structure.
        """
        required_keys = {
            "is_valid",
            "normalized_value",
            "feedback_to_user",
            "follow_up_question",
        }

        if set(validation.keys()) != required_keys:
            return self.reject("Internal validation error: response schema was incorrect.")

        if not isinstance(validation["is_valid"], bool):
            return self.reject("Internal validation error: is_valid was not a boolean.")

        if not isinstance(validation["feedback_to_user"], str):
            return self.reject("Internal validation error: feedback was not text.")

        if not validation["is_valid"]:
            if not validation["follow_up_question"]:
                validation["follow_up_question"] = "Could you make your answer more specific?"
            return validation

        value = validation["normalized_value"]

        if question.key == "knowledge_level":
            if value not in {"beginner", "intermediate", "advanced"}:
                return self.reject("Please choose beginner, intermediate, or advanced.")

        if question.key == "duration_minutes":
            try:
                value = int(value)
            except (TypeError, ValueError):
                return self.reject("Please give the duration clearly, for example: 3 hours or 180 minutes.")

            if value < 30:
                return self.reject("The duration seems too short for a complete training. Please give at least 30 minutes.")

            if value > 480:
                return self.reject("For Tier 1, keep it to one training session, ideally under 8 hours.")

            validation["normalized_value"] = value

        if question.key in {"topic", "target_audience", "primary_learning_objective"}:
            if not isinstance(value, str) or len(value.strip()) < 4:
                return self.reject("Please make your answer more specific.")

        if not self.has_minimum_detail(question, str(value)):
            return self.reject_more_detail()

        return validation

    def reject_more_detail(self) -> dict:
        return self.reject("Please add a bit more detail.")

    def reject(self, message: str) -> dict:
        return {
            "is_valid": False,
            "normalized_value": None,
            "feedback_to_user": message,
            "follow_up_question": message,
        }

    def add_fixed_challenge_requirements(self) -> None:
        self.training_spec["tier"] = "Tier 1"
        self.training_spec["didactic_model"] = [
            "kick_off",
            "theory",
            "example",
            "exercise",
            "wrap_up",
        ]
        self.training_spec["required_outputs"] = {
            "editable_pptx": True,
            "maverx_house_style": True,
            "speaker_notes_per_slide": True,
            "speaker_notes_fields": [
                "aim",
                "time_indication",
                "instruction_steps",
                "reflective_question",
                "debrief_summary",
            ],
            "pre_bite": True,
            "post_bite": True,
        }

    def save_json(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as file:
            json.dump(self.training_spec, file, indent=2, ensure_ascii=False)

        print(f"Saved JSON to {path}\n")


class IntakeChatSession:
    def __init__(
        self,
        agent: LLMSequentialIntakeAgent,
        on_complete: Callable[[dict[str, Any]], None] | None = None,
        output_path: str = DEFAULT_OUTPUT_PATH,
        persist_on_complete: bool = False,
    ) -> None:
        self.agent = agent
        self.on_complete = on_complete
        self.output_path = output_path
        self.persist_on_complete = persist_on_complete
        self.current_question_index = 0
        self.attempt_counts = {question.key: 0 for question in self.agent.questions}
        self.is_started = False
        self.is_complete = False
        self.completion_hook_error: str | None = None

    def chat(self, user_message: str | None = None) -> IntakeReply:
        if not self.is_started and user_message is None:
            return self.start()

        return self.handle_message(user_message or "")

    def start(self) -> IntakeReply:
        self.is_started = True
        if self.is_complete:
            return self.build_completion_reply()

        return IntakeReply(
            text=f"{self.agent.get_intro_message()}\n\n{self.current_question_prompt()}",
            is_complete=False,
            training_spec=None,
        )

    def handle_message(self, user_message: str) -> IntakeReply:
        if not self.is_started:
            self.is_started = True

        if self.is_complete:
            return self.build_completion_reply()

        user_answer = user_message.strip()
        if not user_answer:
            return IntakeReply(
                text=f"Please add a bit more detail.\n\n{self.current_question_prompt()}",
                is_complete=False,
                training_spec=None,
            )

        question = self.current_question()
        self.attempt_counts[question.key] += 1
        validation = self.agent.validate_answer(
            question,
            user_answer,
            self.attempt_counts[question.key],
        )

        if not validation["is_valid"]:
            follow_up = validation["follow_up_question"] or self.current_question_prompt()
            return IntakeReply(
                text=f"{validation['feedback_to_user']}\n\n{follow_up}",
                is_complete=False,
                training_spec=None,
            )

        self.agent.training_spec[question.key] = validation["normalized_value"]
        self.current_question_index += 1

        if self.current_question_index >= len(self.agent.questions):
            self.complete()
            return self.build_completion_reply()

        return IntakeReply(
            text=f"Accepted.\n\n{self.current_question_prompt()}",
            is_complete=False,
            training_spec=None,
        )

    def current_question(self) -> Question:
        return self.agent.questions[self.current_question_index]

    def current_question_prompt(self) -> str:
        return self.agent.make_friendly_question(self.current_question())

    def complete(self) -> None:
        if self.is_complete:
            return

        self.agent.add_fixed_challenge_requirements()

        if self.persist_on_complete:
            self.agent.save_json(self.output_path)

        if self.on_complete:
            try:
                self.on_complete(self.agent.training_spec)
            except Exception as error:
                self.completion_hook_error = str(error)

        self.is_complete = True

    def build_completion_reply(self) -> IntakeReply:
        hook_note = ""
        if self.completion_hook_error:
            hook_note = "\n\nThe questionnaire finished, but the next-step hook could not run yet."

        return IntakeReply(
            text=f"Accepted.\n\nThe questionnaire is complete. Your training PowerPoint spec is ready.{hook_note}",
            is_complete=True,
            training_spec=self.agent.training_spec,
        )


def create_intake_chat_session(
    llm: LLMClient | None = None,
    on_complete: Callable[[dict[str, Any]], None] | None = None,
    output_path: str = DEFAULT_OUTPUT_PATH,
    persist_on_complete: bool = False,
) -> IntakeChatSession:
    agent = LLMSequentialIntakeAgent(llm or LLMClient(), build_questions())
    return IntakeChatSession(
        agent=agent,
        on_complete=on_complete,
        output_path=output_path,
        persist_on_complete=persist_on_complete,
    )


def handle_completed_training_spec(training_spec: dict[str, Any]) -> None:
    """
    Hook for the next pipeline step. Keep this as a no-op so the intake module
    can still run independently while another module is not wired in yet.
    """
    return None


def build_questions() -> list[Question]:
    return [
        Question(
            key="topic",
            canonical_question="What is the topic or skill to be trained?",
            purpose="Sets the domain and skill focus of the training.",
            expected_format="A specific topic or skill, for example: prompt engineering for marketing, Power BI dashboard basics, or Excel automation with Power Query.",
        ),
        Question(
            key="target_audience",
            canonical_question="Who is the target audience?",
            purpose="Sets tone, examples, difficulty, and use cases.",
            expected_format="A specific role, team, or group, for example: marketing team, HR managers, sales employees, or finance analysts.",
        ),
        Question(
            key="knowledge_level",
            canonical_question="What is the knowledge level of participants?",
            purpose="Determines whether explanations should be beginner, intermediate, or advanced.",
            expected_format="One of: beginner, intermediate, advanced.",
        ),
        Question(
            key="duration_minutes",
            canonical_question="How much time should the training session take?",
            purpose="Determines module count, timing, and approximate slide count.",
            expected_format="A clear duration, for example: 90 minutes, 3 hours, half day, or full day.",
        ),
        Question(
            key="primary_learning_objective",
            canonical_question="What is the primary learning objective?",
            purpose="Anchors the whole training and keeps the content outcome-driven.",
            expected_format="A measurable objective, for example: By the end, participants can create and evaluate prompts for common marketing tasks.",
        ),
    ]


if __name__ == "__main__":
    try:
        llm = LLMClient()
        agent = LLMSequentialIntakeAgent(llm, build_questions())
        final_spec = agent.run(on_complete=handle_completed_training_spec)
    except (LLMConfigurationError, LLMRequestError) as error:
        raise SystemExit(f"\n{error}\n") from error

    print("Final TrainingSpec:")
    print(json.dumps(final_spec, indent=2, ensure_ascii=False))
