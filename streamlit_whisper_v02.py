from openai import OpenAI
import os
import streamlit as st
import tempfile

st.title("Memos to Text")

# Request OpenAI API Key from the user
api_key = st.text_input("Enter your OpenAI API Key", type="password")

if api_key:
    client = OpenAI(api_key=api_key)

    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-4o-mini"

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "transcribed_text" not in st.session_state:
        st.session_state.transcribed_text = None

    # Audio file uploader
    audio_file = st.file_uploader("Upload an audio file", type=['mp3', 'wav', 'm4a'])

    # Create two columns for text and audio input
    col1, col2 = st.columns(2)

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Handle audio input
    if audio_file is not None and st.session_state.transcribed_text is None:
        with st.spinner("Transcribing audio..."):
            # Create a temporary file to store the uploaded audio
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio_file.name)[1]) as tmp_file:
                tmp_file.write(audio_file.getvalue())
                tmp_file_path = tmp_file.name

            try:
                # Transcribe the audio file
                with open(tmp_file_path, "rb") as audio:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio
                    )
                
                # Add transcription to messages
                st.session_state.transcribed_text = transcript.text
                st.session_state.messages.append({"role": "user", "content": st.session_state.transcribed_text})
                with st.chat_message("user"):
                    st.markdown(st.session_state.transcribed_text)

                # Generate response
                assistant_response = "This is your input from the audio file. What would you like me to do with it?"
                st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                with st.chat_message("assistant"):
                    st.markdown(assistant_response)

            finally:
                # Clean up the temporary file
                os.unlink(tmp_file_path)

    # Handle text input
    if prompt := st.chat_input("What is up?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
                model=st.session_state["openai_model"],
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                stream=True,
            )
            response = st.write_stream(stream)
        st.session_state.messages.append({"role": "assistant", "content": response})