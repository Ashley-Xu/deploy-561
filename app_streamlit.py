import os
import logging
import re
import streamlit as st
from dotenv import load_dotenv
import openai
from auth import login_user, register_user, get_user_by_id

# Basic Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# --- Configuration ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- Config Checks ---
openai_config_missing = False
if not OPENAI_API_KEY:
    logging.warning("OpenAI API key not set. AI features will fail.")
    openai_config_missing = True
else:
    # Configure OpenAI client
    openai.api_key = OPENAI_API_KEY

# --- AI Helper Function ---
def get_ai_decomposition(task_description):
    """Calls the OpenAI API with updated prompt for natural output."""
    if openai_config_missing: 
        logging.error("OpenAI Config Missing")
        return None
    
    if not OPENAI_API_KEY:
        logging.error("OpenAI API Key Missing")
        return None

    system_prompt = """You are Em, a supportive, non-judgmental AI assistant for users with ADHD. Your goal is to help users start tasks they feel overwhelmed by. Be gentle, understanding, sincere, and focus on breaking things down into 3-5 small, concrete, actionable first steps. Avoid demanding or overly cheerful language."""

    user_prompt = f"""I'm feeling overwhelmed by this task: '{task_description}'.

Can you help me figure out just the first few steps to get started? Keep it simple and clear. Please list the steps first (maybe numbered or bulleted). After the steps, please provide a separate, brief (1-2 sentences) encouraging thought focused specifically on tackling the very first step you listed. Sound sincere and understanding."""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=300,
            temperature=0.7,
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0
        )
        
        message_content = response.choices[0].message.content.strip()
        logging.info(f"Raw AI Response: {message_content}")

        # --- Parsing Logic ---
        steps = "Could not identify clear steps in the response."
        encouragement = "Remember, just starting is a win!"
        step_pattern = r"^(?:\s*(?:[1-9][.)]|[*\-+])\s+.*(?:\n|$))+"
        step_match = re.search(step_pattern, message_content, re.MULTILINE)
        paragraphs = re.split(r'\n\s*\n', message_content)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        if step_match and len(paragraphs) > 1:
            steps = step_match.group(0).strip()
            potential_encouragement = paragraphs[-1]
            if not re.match(r"^\s*(?:[1-9][.)]|[*\-+])\s+", potential_encouragement):
                encouragement = potential_encouragement
            else: 
                encouragement = "Focus on that first step, you can do it!"
        elif len(paragraphs) > 1:
            steps = "\n\n".join(paragraphs[:-1])
            encouragement = paragraphs[-1]
        elif len(paragraphs) == 1:
            if step_match: 
                steps = message_content
                encouragement = "Just taking the first step is progress!"
            else: 
                steps = "No specific steps identified."
                encouragement = message_content
        else: 
            logging.warning("Could not parse steps/encouragement.")
            steps = message_content
            encouragement = "Remember to take it one step at a time."

        logging.info(f"Parsed Steps:\n{steps}")
        logging.info(f"Parsed Encouragement:\n{encouragement}")
        return {"steps": steps, "encouragement": encouragement}
        
    except Exception as e:
        logging.error(f"Error during OpenAI call: {e}", exc_info=True)
        return None

def show_login_page():
    """Display the login page."""
    st.title("Welcome to ADHD Guardian AI")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.header("Login")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if not username or not password:
                    st.error("Please fill in all fields")
                else:
                    success, result = login_user(username, password)
                    if success:
                        st.session_state.user = result
                        st.session_state.authenticated = True
                        st.rerun()
                    else:
                        st.error(result)
    
    with tab2:
        st.header("Register")
        with st.form("register_form"):
            new_username = st.text_input("Choose a username")
            email = st.text_input("Email")
            new_password = st.text_input("Choose a password", type="password")
            confirm_password = st.text_input("Confirm password", type="password")
            submit = st.form_submit_button("Register")
            
            if submit:
                if not all([new_username, email, new_password, confirm_password]):
                    st.error("Please fill in all fields")
                elif new_password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    success, message = register_user(new_username, email, new_password)
                    if success:
                        st.success(message)
                        # Switch to login tab
                        st.session_state.active_tab = "Login"
                    else:
                        st.error(message)

def show_main_app():
    """Display the main application interface."""
    # Sidebar with user info and logout
    with st.sidebar:
        st.title("ADHD Guardian AI")
        if st.session_state.user:
            st.write(f"Welcome, {st.session_state.user['username']}!")
            if st.button("Logout"):
                st.session_state.clear()
                st.rerun()
    
    # Main content area
    st.title("ADHD Guardian AI")
    st.markdown("""
    ### Your AI Partner for Navigating Focus Flow
    
    > "For those of us with ADHD, starting tasks isn't just about discipline—it's about overcoming invisible executive function barriers that others don't see."
    
    This tool helps break down overwhelming tasks into manageable steps, with gentle encouragement to get started.
    """)
    
    # Task Decomposition
    st.header("Task Decomposition")
    
    task_description = st.text_area("What task are you feeling overwhelmed by?", height=100)
    
    if st.button("Break it down"):
        if not task_description:
            st.warning("Please enter a task description.")
        else:
            with st.spinner("Thinking..."):
                result = get_ai_decomposition(task_description)
                
            if result:
                st.subheader("Here's how we can break this down:")
                st.markdown(result["steps"])
                st.info(result["encouragement"])
            else:
                st.error("Sorry, I couldn't process your request. Please try again.")
    
    # About section
    with st.expander("About ADHD Guardian"):
        st.markdown("""
        ### What is ADHD Guardian?
        
        ADHD Guardian is an AI-powered tool designed to help people with ADHD overcome the "Wall of Awful" - that feeling of being overwhelmed by tasks, especially complex or open-ended ones.
        
        ### How it works
        
        1. **Input your task**: Tell us what you're feeling overwhelmed by
        2. **Get actionable steps**: We break it down into 3-5 small, concrete first steps
        3. **Receive encouragement**: Get gentle, understanding support focused on taking that first step
        
        ### Why it helps
        
        For people with ADHD, starting tasks can be the hardest part. This tool:
        - Reduces the perceived scope of overwhelming tasks
        - Provides concrete, actionable first steps
        - Offers non-judgmental support and encouragement
        - Focuses on the critical first step of task initiation
        
        Remember: This tool is not a replacement for professional help, but rather a supportive companion for daily task management.
        """)

# --- Streamlit UI ---
def main():
    st.set_page_config(
        page_title="ADHD Guardian AI",
        page_icon="🧠",
        layout="wide"
    )
    
    # Initialize session state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None
    
    # Show appropriate page based on authentication status
    if not st.session_state.authenticated:
        show_login_page()
    else:
        show_main_app()

if __name__ == "__main__":
    main() 