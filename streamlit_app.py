import streamlit as st
from openai import OpenAI
import os
import sys
from io import StringIO

# Initialize OpenAI API key
client = OpenAI(api_key=st.secrets.get("OPENAI_KEY", ""))

# Function to generate a code puzzle using GPT-3.5
def generate_puzzle(difficulty):
    prompt = f"""
    Generate a unique Python code snippet that is suitable for a coding puzzle.
    The snippet should have no syntax errors and should not require any external packages.
    The difficulty level is {difficulty} on a scale from 1 (easy) to 30 (hard).
    The code should not simply print a string like "Hello". It should involve basic Python operations, control structures, or data manipulations.
    Provide the code snippet only without any explanations or comments.
    The answer given must be executable right away and provide a simple output with at most 10 characters.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates Python code puzzles."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7,  # Increase temperature for more variation
        )
        code = response.choices[0].message.content.strip().replace("```python", "").replace("```", "")
        return code
    except Exception as e:
        st.error(f"Error generating puzzle: {e}")
        return None

# Function to get the output of a code snippet
def get_code_output(code):
    try:
        local_namespace = {}
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            exec(code, {}, local_namespace)
            output = sys.stdout.getvalue().strip()
        except Exception as e:
            output = f"Error: {e}"
        finally:
            sys.stdout = old_stdout

        return output
    except Exception as e:
        return f"Error executing code: {e}"

# Initialize session state
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'total' not in st.session_state:
    st.session_state.total = 0
if 'correct' not in st.session_state:
    st.session_state.correct = 0
if 'current_puzzle' not in st.session_state:
    st.session_state.current_puzzle = None
if 'current_output' not in st.session_state:
    st.session_state.current_output = ""
if 'difficulty' not in st.session_state:
    st.session_state.difficulty = 1  # Start with easy puzzles
if 'answer_submitted' not in st.session_state:
    st.session_state.answer_submitted = False  # Track if the answer has been submitted

# Function to load a new puzzle
def load_new_puzzle():
    code = generate_puzzle(st.session_state.difficulty)
    if code:
        st.session_state.current_puzzle = code
        st.session_state.current_output = get_code_output(code)
        st.session_state.answer_submitted = False  # Reset submission status

# Generate a new puzzle if there isn't a current puzzle
if st.session_state.current_puzzle is None:
    load_new_puzzle()

# Display the current puzzle
st.subheader("🔍 Puzzle Code")
st.code(st.session_state.current_puzzle, language='python')

# User input for guessing the output
user_guess = st.text_area("What is the output of the above code?", height=150, disabled=st.session_state.answer_submitted)

# Submit button to check the user's guess
if st.button("Submit Answer", disabled=st.session_state.answer_submitted):
    if user_guess:
        st.session_state.total += 1
        correct_output = st.session_state.current_output
        if user_guess.strip() == correct_output:
            st.session_state.score += 10
            st.session_state.correct += 1
            st.success("✅ Correct!")
            if st.session_state.correct % 5 == 0 and st.session_state.difficulty < 30:
                st.session_state.difficulty += 1
                st.info(f"Great job! Increasing difficulty to {st.session_state.difficulty}.")
        else:
            st.session_state.score -= 5
            st.error(f"❌ Incorrect. The correct output was:\n```\n{correct_output}\n```")
            if st.session_state.difficulty > 1 and (st.session_state.total - st.session_state.correct) >= 3:
                st.session_state.difficulty -= 1
                st.warning(f"Let's take it down a notch. Decreasing difficulty to {st.session_state.difficulty}.")
        st.session_state.answer_submitted = True
    else:
        st.warning("Please enter your guess before submitting.")

# Next Puzzle button
if st.button("Next Puzzle", disabled=not st.session_state.answer_submitted):
    load_new_puzzle()

# Display user's performance in the sidebar
st.sidebar.header("🏆 Your Performance")
st.sidebar.write(f"**Score:** {st.session_state.score}")
st.sidebar.write(f"**Correct Answers:** {st.session_state.correct}")
st.sidebar.write(f"**Total Attempts:** {st.session_state.total}")
if st.session_state.total > 0:
    accuracy = (st.session_state.correct / st.session_state.total) * 100
    st.sidebar.write(f"**Accuracy:** {accuracy:.2f}%")
st.sidebar.write(f"**Current Difficulty Level:** {st.session_state.difficulty}/30")

# Option to reset the game
if st.sidebar.button("🔄 Reset Game"):
    st.session_state.score = 0
    st.session_state.total = 0
    st.session_state.correct = 0
    st.session_state.difficulty = 1
    st.session_state.answer_submitted = False
    load_new_puzzle()
    st.sidebar.success("Game has been reset!")
