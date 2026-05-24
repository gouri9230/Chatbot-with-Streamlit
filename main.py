import os
from dotenv import load_dotenv
from openai import OpenAI
import tiktoken # counts ticks for the tokens
import streamlit as st

load_dotenv()
# load openai api
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set.")

client = OpenAI(api_key=api_key)
MODEL = "gpt-4.1-nano-2025-04-14"
TEMPERATURE = 0.5
MAX_TOKENS = 100
TOKEN_BUDGET = 100
SYSTEM_PROMPT = "You are a helpful assistant. Answer promptly to the questions asked."
messages= [{"role":"system", "content": SYSTEM_PROMPT}]

# encoding the model (encoding method)
def encoding(model):
    try:
        return tiktoken.encoding_for_model(model)
    except KeyError:
        print(f"Warning: Tokenizer for model '{model}' not found. Going ahead with default encoder 'cl100k_base'.")
        return tiktoken.get_encoding("cl100k_base")

ENCODING = encoding(MODEL)

def count_tokens(text):
    return len(ENCODING.encode(text))

def total_tokens_used(messages):
    try:
        return sum(count_tokens(msg["content"]) for msg in messages)
    except Exception as e:
        print(f"[token count error]: {e}")
        return 0

def enforce_token_budget(messages, budget= TOKEN_BUDGET):
    try:
        while total_tokens_used(messages) > budget:
            # if the total tokens exceed the budget limit, pop the oldest message, except for the system message
            if len(messages) <= 2:
                break
            messages.pop(1)
    except Exception as e:
        print(f"[token count error]: {e}")
        return 0

def chat(user_input, temperature= TEMPERATURE, max_tokens=MAX_TOKENS):
    messages = st.session_state.messages
    messages.append({"role": "user", "content": user_input})
    enforce_token_budget(messages)
    response = client.chat.completions.create(
        model= MODEL,
        messages= messages,
        temperature= temperature,
        max_tokens=max_tokens
    )
    chat_reply = response.choices[0].message.content
    messages.append({"role": "assistant", "content": chat_reply})
    
    return chat_reply


#while True:
#    user_input = input("You: ")
#    if user_input.strip().lower() in {'exit', "quit"}:
#        break
#    answer = chat(user_input)
#    print("Chatbot: ", answer)
#    print("Current tokens used: ", total_tokens_used(messages))

##### Streamlit #######

st.title("Personal Chatbot")
st.sidebar.header("Recent Chats")
st.sidebar.write("How to build a chatbot using streamlit?")

st.sidebar.header("Options")
max_tokens = st.sidebar.slider("Max Tokens", 1, 250, 50)
temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.5)
system_message_type = st.sidebar.selectbox("System Behaviour", ("Funny Assistant", "Angry Assistant", "Custom"))

if system_message_type == "Sassy Assistant":
    SYSTEM_PROMPT = "You are a sassy, bold assistant who answer questions with a bit of attitude."
elif system_message_type == "Angry Assistant":
    SYSTEM_PROMPT = "You are an angry assistant who is fed of all questions and likes to yell."
elif system_message_type == "Custom":
    SYSTEM_PROMPT = st.sidebar.text_area("Create your own assistant behaviour", "Enter your custom message here.")
else:
    SYSTEM_PROMPT = "You are a helpful assistant."

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

if st.sidebar.button("Apply New System Message"):
    st.session_state.messages[0] = {"role": "system", "content": SYSTEM_PROMPT}
    st.success("System message updated successfully.")

if st.sidebar.button("Reset Conversation"):
    st.session_state.messages = {"role": "system", "content": SYSTEM_PROMPT}
    st.success("Conversation reset.")

if prompt := st.chat_input("How may I help you today?"):
    reply = chat(prompt, temperature=temperature, max_tokens=max_tokens)

for message in st.session_state.messages[1:]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
