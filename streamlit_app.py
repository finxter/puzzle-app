import streamlit as st
import openai
import os
import sys
from io import StringIO

# Initialize OpenAI API key
client = OpenAI(st.secrets.get("OPENAI_KEY", ""))

# Function to generate code puzzles using GPT-3.5
def generate_puzzle(difficulty):
    prompt = f"""
    Generate a Python code snippet that is suitable for a coding puzzle.
    The snippet should have no syntax errors and should not require any external packages.
    The difficulty level is {difficulty} on a scale from 1 (easy) to 5 (hard).
    Provide the code snippet only without any explanations or comments.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates Python code puzzles."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.5,
        )
        code = response.choices[0].message.content.strip()
        return code
    except openai.error.OpenAIError as e:
        st.error(f"OpenAI API Error: {e}")
        return None
    except Exception as e:
        st.error(f"Unexpected Error: {e}")
        return None

# Function to get the output of a code snippet
def get_code_output(code):
    try:
        # Capture the output of the code
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

st.title("🧩 Python Code Puzzle Challenge")
st.write("Test your understanding of Python by guessing the output of the following code snippets.")

# Function to load a new puzzle
def load_new_puzzle():
    code = generate_puzzle(st.session_state.difficulty)
    if code:
        st.session_state.current_puzzle = code
        st.session_state.current_output = get_code_output(code)

# If no puzzle is loaded yet, load one
if st.session_state.current_puzzle is None:
    with st.spinner("Generating a new puzzle..."):
        load_new_puzzle()

# Display the current puzzle
with st.expander("🔍 View the Puzzle Code"):
    st.code(st.session_state.current_puzzle, language='python')

# User input for guessing the output
user_guess = st.text_input("What is the output of the above code?")

# Submit button
if st.button("Submit Answer"):
    if user_guess:
        st.session_state.total += 1
        correct_output = st.session_state.current_output
        if user_guess.strip() == correct_output:
            st.session_state.score += 10
            st.session_state.correct += 1
            st.success("✅ Correct!")
            # Increase difficulty every 5 correct answers
            if st.session_state.correct % 5 == 0 and st.session_state.difficulty < 5:
                st.session_state.difficulty += 1
                st.info(f"Great job! Increasing difficulty to {st.session_state.difficulty}.")
        else:
            st.session_state.score -= 5
            st.error(f"❌ Incorrect. The correct output was:\n```\n{correct_output}\n```")
            # Decrease difficulty if there are more than 3 incorrect answers
            if st.session_state.difficulty > 1 and (st.session_state.total - st.session_state.correct) >= 3:
                st.session_state.difficulty -= 1
                st.warning(f"Let's take it down a notch. Decreasing difficulty to {st.session_state.difficulty}.")
        
        # Load a new puzzle after submission
        with st.spinner("Loading a new puzzle..."):
            load_new_puzzle()
    else:
        st.warning("Please enter your guess before submitting.")

# Display the user's performance
st.sidebar.header("🏆 Your Performance")
st.sidebar.write(f"**Score:** {st.session_state.score}")
st.sidebar.write(f"**Correct Answers:** {st.session_state.correct}")
st.sidebar.write(f"**Total Attempts:** {st.session_state.total}")
if st.session_state.total > 0:
    accuracy = (st.session_state.correct / st.session_state.total) * 100
    st.sidebar.write(f"**Accuracy:** {accuracy:.2f}%")
st.sidebar.write(f"**Current Difficulty Level:** {st.session_state.difficulty}/5")

# Option to reset the game
if st.sidebar.button("🔄 Reset Game"):
    st.session_state.score = 0
    st.session_state.total = 0
    st.session_state.correct = 0
    st.session_state.difficulty = 1
    with st.spinner("Resetting the game..."):
        load_new_puzzle()
    st.sidebar.success("Game has been reset!")
