
import streamlit as st
from datetime import datetime, date, timedelta
import json
import os
import time
import pandas as pd

# ==================================================
# AI STUDY PLANNER
# ==================================================

st.set_page_config(
    page_title="AI Study Planner",
    page_icon="📚",
    layout="wide"
)

HISTORY_FILE = "study_history.json"
TIMER_FILE = "timer_history.json"


# ==================================================
# FILE FUNCTIONS
# ==================================================

def load_json(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as file:
                data = json.load(file)

                if isinstance(data, list):
                    return data

                return []

        except (json.JSONDecodeError, OSError):
            return []

    return []


def save_json(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(
                data,
                file,
                indent=4,
                ensure_ascii=False
            )

    except OSError as error:
        st.error(f"Unable to save file: {error}")


def format_timer(seconds):
    seconds = max(0, int(seconds or 0))

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def calculate_study_streak(history):

    study_dates = set()

    for item in history:

        try:

            if int(item.get("seconds", 0)) > 0:

                study_dates.add(
                    datetime.strptime(
                        item["date"],
                        "%Y-%m-%d"
                    ).date()
                )

        except (ValueError, TypeError, KeyError):
            pass

    if not study_dates:
        return 0

    today = date.today()

    current_date = (
        today
        if today in study_dates
        else today - timedelta(days=1)
    )

    streak = 0

    while current_date in study_dates:

        streak += 1

        current_date -= timedelta(days=1)

    return streak


# ==================================================
# SESSION STATE
# ==================================================

if "study_history" not in st.session_state:
    st.session_state.study_history = load_json(HISTORY_FILE)

if "timer_history" not in st.session_state:
    st.session_state.timer_history = load_json(TIMER_FILE)

if "study_plan" not in st.session_state:
    st.session_state.study_plan = []

if "plan_created" not in st.session_state:
    st.session_state.plan_created = False

if "completed_tasks" not in st.session_state:
    st.session_state.completed_tasks = []

if "timer_running" not in st.session_state:
    st.session_state.timer_running = False

if "timer_paused" not in st.session_state:
    st.session_state.timer_paused = False

if "timer_start_timestamp" not in st.session_state:
    st.session_state.timer_start_timestamp = None

if "timer_elapsed_before_pause" not in st.session_state:
    st.session_state.timer_elapsed_before_pause = 0

if "timer_subject" not in st.session_state:
    st.session_state.timer_subject = ""

if "timer_session_date" not in st.session_state:
    st.session_state.timer_session_date = date.today().isoformat()


# ==================================================
# LIGHT BLUE BACKGROUND
# ==================================================

st.markdown(
    """
    <style>

    .stApp {
        background-color: #EAF4FF;
        color: #16324F;
    }

    [data-testid="stHeader"] {
        background-color: #EAF4FF;
    }

    .stTextInput input,
    .stNumberInput input,
    .stTextArea textarea {
        background-color: white !important;
        color: #16324F !important;
    }

    .stButton button,
    .stDownloadButton button {
        border-radius: 10px;
        font-weight: bold;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ==================================================
# HEADER
# ==================================================

st.title("📚 AI Study Planner")

st.write(
    "Plan your study sessions, track your actual study time, "
    "and download your study reports."
)

st.caption(
    "Your personal study companion 💙"
)


# ==================================================
# STUDENT DETAILS
# ==================================================

st.header("👩‍🎓 Student Details")

col1, col2, col3 = st.columns(3)

with col1:

    student_name = st.text_input(
        "Student Name",
        placeholder="Enter your name"
    )

with col2:

    department = st.text_input(
        "Department",
        value="AI & Data Science"
    )

with col3:

    year = st.selectbox(
        "Year of Study",
        [
            "1st Year",
            "2nd Year",
            "3rd Year",
            "4th Year"
        ],
        index=1
    )


# ==================================================
# CREATE STUDY PLAN
# ==================================================

st.header("📝 Create Your Study Plan")

with st.form("study_plan_form"):

    col1, col2 = st.columns(2)

    with col1:

        subject = st.text_input(
            "Subject",
            placeholder="Example: Mathematics"
        )

        sessions = st.number_input(
            "Number of Study Sessions",
            min_value=1,
            max_value=12,
            value=3,
            step=1
            session_duration = st.selectbox(
    "Study Session Duration (minutes)",
    [30, 45, 50, 60, 90],
    index=2)

        )

        study_date = st.date_input(
            "Study Date",
            value=date.today()
        )

    with col2:

        start_time = st.time_input(
            "Start Time",
            value=datetime.now().replace(
                second=0,
                microsecond=0
            ).time()
        )

        difficulty = st.selectbox(
            "Difficulty",
            ["Easy", "Medium", "Hard"]
        )

        daily_goal = st.number_input(
            "Daily Study Goal (hours)",
            min_value=0.5,
            max_value=24.0,
            value=3.0,
            step=0.5
        )

    topics = st.text_area(
        "Topics / Tasks (one topic per line)",
        placeholder="Topic 1\nTopic 2\nTopic 3"
    )

    create_button = st.form_submit_button(
        "✨ Create Study Plan",
        use_container_width=True
    )


# ==================================================
# GENERATE PLAN
# ==================================================

if create_button:

    if not subject.strip():

        st.error("Please enter a subject.")

    else:

        topic_list = [
            topic.strip()
            for topic in topics.splitlines()
            if topic.strip()
        ]

        if not topic_list:

            topic_list = [
                f"{subject} - Session {i + 1}"
                for i in range(int(sessions))
            ]

        while len(topic_list) < int(sessions):

            topic_list.append(
                f"{subject} - Session {len(topic_list) + 1}"
            )

        topic_list = topic_list[:int(sessions)]

        current_time = datetime.combine(
            study_date,
            start_time
        )

        plan = []

        for i, topic in enumerate(topic_list):

            session_start = current_time

            session_end = (
                session_start + timedelta(minutes=50)
            )

            plan.append(
                {
                    "date": study_date.isoformat(),
                    "subject": subject.strip(),
                    "topic": topic,
                    "session": i + 1,
                    "start": session_start.strftime("%I:%M %p"),
                    "end": session_end.strftime("%I:%M %p"),
                    "duration_minutes": 50,
                    "difficulty": difficulty
                }
            )

            current_time = (
                session_end + timedelta(minutes=10)
            )

        st.session_state.study_plan = plan

        st.session_state.completed_tasks = [
            False for _ in plan
        ]

        st.session_state.plan_created = True

        history_record = {
            "created_at": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "student": student_name or "Student",
            "department": department,
            "year": year,
            "date": study_date.isoformat(),
            "subject": subject.strip(),
            "difficulty": difficulty,
            "daily_goal_hours": float(daily_goal),
            "sessions": int(sessions),
            "topics": topic_list
        }

        st.session_state.study_history.append(
            history_record
        )

        save_json(
            HISTORY_FILE,
            st.session_state.study_history
        )

        st.success(
            "Your study plan has been created successfully! 🎉"
        )


# ==================================================
# DISPLAY STUDY PLAN
# ==================================================

if st.session_state.plan_created:

    st.divider()

    st.header("📅 Your Study Schedule")

    for i, item in enumerate(
        st.session_state.study_plan
    ):

        with st.container(border=True):

            st.subheader(
                f"Session {item['session']}"
            )

            st.write(
                f"📘 Topic: {item['topic']}"
            )

            st.write(
                f"🕒 {item['start']} - {item['end']}"
            )

            st.write(
                f"Duration: {item['duration_minutes']} minutes"
            )

            st.write(
                f"Difficulty: {item['difficulty']}"
            )

            st.session_state.completed_tasks[i] = st.checkbox(
                "Mark as completed",
                value=st.session_state.completed_tasks[i],
                key=f"completed_{i}"
            )

    completed = sum(
        st.session_state.completed_tasks
    )

    total = len(
        st.session_state.study_plan
    )

    progress = (
        completed / total
        if total > 0
        else 0
    )

    st.progress(progress)

    st.write(
        f"**Progress: {completed}/{total} sessions "
        f"({int(progress * 100)}%)**"
    )

    if completed == total and total > 0:

        st.balloons()

        st.success(
            "Amazing! You completed your study plan! 🥳"
        )

    if st.button("🔄 Reset Current Study Plan"):

        st.session_state.plan_created = False

        st.session_state.study_plan = []

        st.session_state.completed_tasks = []

        st.rerun()


# ==================================================
# STUDY PLAN HISTORY
# ==================================================

st.divider()

st.header("📚 Study Plan History")

if st.session_state.study_history:

    history_df = pd.DataFrame(
        st.session_state.study_history
    )

    st.dataframe(
        history_df,
        use_container_width=True
    )

    if "date" in history_df.columns:

        history_df["date"] = pd.to_datetime(
            history_df["date"],
            errors="coerce"
        )

        history_df = history_df.dropna(
            subset=["date"]
        )

        if not history_df.empty:

            if "sessions" in history_df.columns:

                history_df["planned_minutes"] = (
                    pd.to_numeric(
                        history_df["sessions"],
                        errors="coerce"
                    ).fillna(0) * 50
                )

                st.subheader(
                    "📊 Daily Planned Study Time"
                )

                daily_plan = history_df.groupby(
                    history_df["date"].dt.date
                )["planned_minutes"].sum()

                st.bar_chart(daily_plan)

            if (
                "subject" in history_df.columns
                and "planned_minutes" in history_df.columns
            ):

                st.subheader(
                    "📊 Subject-wise Planned Study Time"
                )

                subject_plan = history_df.groupby(
                    "subject"
                )["planned_minutes"].sum()

                st.bar_chart(subject_plan)

else:

    st.info(
        "Your study plan history will appear here."
    )


# ==================================================
# ACTUAL STUDY TIMER
# ==================================================

st.divider()

st.header("⏱️ Actual Study Timer")

st.write(
    "Start the timer when you begin studying. "
    "Stop & Save to record your actual study time."
)

timer_subject = st.text_input(
    "Subject for Timer",
    value=st.session_state.timer_subject,
    placeholder="Example: Mathematics"
)

timer_col1, timer_col2, timer_col3 = st.columns(3)


# ---------------- START TIMER ----------------

with timer_col1:

    if st.button(
        "▶️ Start Timer",
        disabled=(
            st.session_state.timer_running
            or st.session_state.timer_paused
        ),
        use_container_width=True
    ):

        if not timer_subject.strip():

            st.warning(
                "Please enter a subject first."
            )

        else:

            st.session_state.timer_subject = (
                timer_subject.strip()
            )

            st.session_state.timer_start_timestamp = (
                time.time()
            )

            st.session_state.timer_elapsed_before_pause = 0

            st.session_state.timer_running = True

            st.session_state.timer_paused = False

            st.session_state.timer_session_date = (
                date.today().isoformat()
            )

            st.rerun()


# ---------------- PAUSE / RESUME ----------------

with timer_col2:

    if st.button(
        "⏸️ Pause / Resume",
        disabled=not (
            st.session_state.timer_running
            or st.session_state.timer_paused
        ),
        use_container_width=True
    ):

        if st.session_state.timer_running:

            elapsed = (
                time.time()
                - st.session_state.timer_start_timestamp
            )

            st.session_state.timer_elapsed_before_pause += (
                elapsed
            )

            st.session_state.timer_start_timestamp = None

            st.session_state.timer_running = False

            st.session_state.timer_paused = True

        elif st.session_state.timer_paused:

            st.session_state.timer_start_timestamp = (
                time.time()
            )

            st.session_state.timer_running = True

            st.session_state.timer_paused = False

        st.rerun()


# ---------------- STOP AND SAVE ----------------

with timer_col3:

    if st.button(
        "⏹️ Stop & Save",
        disabled=not (
            st.session_state.timer_running
            or st.session_state.timer_paused
        ),
        use_container_width=True
    ):

        total_seconds = (
            st.session_state.timer_elapsed_before_pause
        )

        if st.session_state.timer_running:

            total_seconds += (
                time.time()
                - st.session_state.timer_start_timestamp
            )

        total_seconds = int(total_seconds)

        if total_seconds > 0:

            record = {
                "date": st.session_state.timer_session_date,
                "subject": st.session_state.timer_subject,
                "seconds": total_seconds,
                "minutes": round(
                    total_seconds / 60,
                    2
                ),
                "saved_at": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            }

            st.session_state.timer_history.append(
                record
            )

            save_json(
                TIMER_FILE,
                st.session_state.timer_history
            )

            st.success(
                f"Study session saved: "
                f"{format_timer(total_seconds)}"
            )

        else:

            st.warning(
                "Timer duration is zero. Nothing was saved."
            )

        st.session_state.timer_running = False

        st.session_state.timer_paused = False

        st.session_state.timer_start_timestamp = None

        st.session_state.timer_elapsed_before_pause = 0

        st.rerun()


# ==================================================
# TIMER DISPLAY
# ==================================================

if st.session_state.timer_running:

    elapsed = (
        st.session_state.timer_elapsed_before_pause
        + time.time()
        - st.session_state.timer_start_timestamp
    )

elif st.session_state.timer_paused:

    elapsed = (
        st.session_state.timer_elapsed_before_pause
    )

else:

    elapsed = 0


st.metric(
    "⏳ Timer",
    format_timer(elapsed)
)

if st.session_state.timer_running:

    st.caption(
        "Timer is running. It refreshes every second."
    )

    time.sleep(1)

    st.rerun()


# ==================================================
# ACTUAL STUDY SUMMARY
# ==================================================

st.divider()

st.header("📈 Actual Study Summary")

today = date.today().isoformat()

today_seconds = 0

for item in st.session_state.timer_history:

    try:

        if item.get("date") == today:

            today_seconds += int(
                item.get("seconds", 0)
            )

    except (ValueError, TypeError):

        pass


today_hours = today_seconds / 3600

goal_hours = 3.0

if st.session_state.study_history:

    try:

        goal_hours = float(
            st.session_state.study_history[-1].get(
                "daily_goal_hours",
                3.0
            )
        )

    except (ValueError, TypeError):

        goal_hours = 3.0


goal_seconds = goal_hours * 3600

goal_progress = (
    min(today_seconds / goal_seconds, 1.0)
    if goal_seconds > 0
    else 0
)


summary_col1, summary_col2, summary_col3 = st.columns(3)

with summary_col1:

    st.metric(
        "Study Time Today",
        format_timer(today_seconds)
    )

with summary_col2:

    st.metric(
        "Daily Study Goal",
        f"{goal_hours:g} hours"
    )

with summary_col3:

    st.metric(
        "Study Streak",
        f"{calculate_study_streak(st.session_state.timer_history)} days"
    )


st.progress(goal_progress)

st.write(
    f"**Goal Progress: {int(goal_progress * 100)}%**"
)

st.caption(
    f"Today's study time: {today_hours:.2f} hours"
)


# ==================================================
# ACTUAL STUDY CHARTS
# ==================================================

if st.session_state.timer_history:

    actual_df = pd.DataFrame(
        st.session_state.timer_history
    )

    if "date" not in actual_df.columns:
        actual_df["date"] = today

    if "subject" not in actual_df.columns:
        actual_df["subject"] = "Unknown"

    if "seconds" not in actual_df.columns:
        actual_df["seconds"] = 0

    actual_df["seconds"] = pd.to_numeric(
        actual_df["seconds"],
        errors="coerce"
    ).fillna(0)

    actual_df["minutes"] = (
        actual_df["seconds"] / 60
    )

    actual_df["date"] = pd.to_datetime(
        actual_df["date"],
        errors="coerce"
    )

    actual_df = actual_df.dropna(
        subset=["date"]
    )

    if not actual_df.empty:

        st.subheader(
            "📊 Actual Study Time — Daily"
        )

        daily_actual = actual_df.groupby(
            actual_df["date"].dt.date
        )["minutes"].sum()

        st.bar_chart(daily_actual)

        st.subheader(
            "📊 Actual Study Time — Subject-wise"
        )

        subject_actual = actual_df.groupby(
            "subject"
        )["minutes"].sum()

        st.bar_chart(subject_actual)

        st.subheader(
            "🗂️ Actual Study Sessions"
        )

        display_df = actual_df.copy()

        display_df["Study Duration"] = (
            display_df["seconds"].apply(
                format_timer
            )
        )

        display_df["Date"] = (
            display_df["date"].dt.strftime(
                "%Y-%m-%d"
            )
        )

        display_df.rename(
            columns={
                "subject": "Subject",
                "minutes": "Study Minutes"
            },
            inplace=True
        )

        st.dataframe(
            display_df[
                [
                    "Date",
                    "Subject",
                    "Study Duration",
                    "Study Minutes"
                ]
            ],
            use_container_width=True
        )

else:

    st.info(
        "Start the timer and save a session "
        "to see your actual study analytics."
    )


# ==================================================
# DOWNLOAD REPORTS
# ==================================================

st.divider()

st.header("📥 Download Study Reports")

download_col1, download_col2 = st.columns(2)


# ==================================================
# DOWNLOAD ACTUAL STUDY REPORT
# ==================================================

with download_col1:

    st.subheader(
        "⏱️ Actual Study Report"
    )

    if st.session_state.timer_history:

        actual_report = pd.DataFrame(
            st.session_state.timer_history
        )

        # Avoid missing column errors

        if "date" not in actual_report.columns:

            actual_report["date"] = ""

        if "subject" not in actual_report.columns:

            actual_report["subject"] = "Unknown"

        if "seconds" not in actual_report.columns:

            actual_report["seconds"] = 0

        actual_report["seconds"] = pd.to_numeric(
            actual_report["seconds"],
            errors="coerce"
        ).fillna(0)

        # Create duration column

        actual_report["Study Duration"] = (
            actual_report["seconds"].apply(
                format_timer
            )
        )

        actual_report["Study Minutes"] = (
            actual_report["seconds"] / 60
        ).round(2)

        actual_report.rename(
            columns={
                "date": "Date",
                "subject": "Subject",
                "seconds": "Study Seconds"
            },
            inplace=True
        )

        csv_actual = actual_report.to_csv(
            index=False
        ).encode("utf-8-sig")

        st.download_button(
            label="⬇️ Download Actual Study Report",
            data=csv_actual,
            file_name="actual_study_report.csv",
            mime="text/csv",
            use_container_width=True
        )

    else:

        st.info(
            "Save at least one timer session "
            "to download the actual study report."
        )


# ==================================================
# DOWNLOAD STUDY PLAN REPORT
# ==================================================

with download_col2:

    st.subheader(
        "📚 Study Plan Report"
    )

    if st.session_state.study_history:

        plan_report = pd.DataFrame(
            st.session_state.study_history
        )

        csv_plan = plan_report.to_csv(
            index=False
        ).encode("utf-8-sig")

        st.download_button(
            label="⬇️ Download Study Plan Report",
            data=csv_plan,
            file_name="study_plan_report.csv",
            mime="text/csv",
            use_container_width=True
        )

    else:

        st.info(
            "Create a study plan to download "
            "your plan report."
        )


# ==================================================
# FOOTER
# ==================================================

st.divider()

st.caption(
    "Made with 💙 for your study journey. "
    "Keep going — small progress every day adds up!"
)
