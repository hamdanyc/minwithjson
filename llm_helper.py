import streamlit as st
from groq import Groq

def generate_chairman_note(points):
    """
    Generates a professional chairman's welcome note paragraph from a list of points.
    """
    if not points or all(not p.strip() for p in points):
        return ""

    try:
        # Retrieve API key from Streamlit secrets or environment variables
        import os
        api_key = None
        try:
            api_key = st.secrets.get("GROQ_API_KEY")
        except FileNotFoundError:
            pass
        
        if not api_key:
            api_key = os.environ.get("GROQ_API_KEY")
            
        if not api_key:
            return "Error: GROQ_API_KEY not found. Please set it in .streamlit/secrets.toml or as an environment variable."

        client = Groq(api_key=api_key)
        
        # Filter out empty points
        valid_points = [p.strip() for p in points if p.strip()]
        points_str = "\n".join([f"- {p}" for p in valid_points])

        prompt = f"""
You are an expert secretary drafting minutes of a meeting. 
Based on the following points, generate a professional, welcoming, and concise "Chairman's Welcome Note" paragraph in Malay (Bahasa Melayu), as per the standard format for formal minutes of meeting in Malaysia.

Points:
{points_str}

The output should be a single paragraph. Do not include any other text or formatting.
"""

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a professional secretary crafting meeting minutes."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )

        return completion.choices[0].message.content.strip()

    except Exception as e:
        return f"Error during generation: {str(e)}"

def generate_closing_remark(points):
    """
    Generates a professional closing remark paragraph from a list of points.
    """
    if not points or all(not p.strip() for p in points):
        return ""

    try:
        # Retrieve API key from Streamlit secrets or environment variables
        import os
        api_key = None
        try:
            api_key = st.secrets.get("GROQ_API_KEY")
        except FileNotFoundError:
            pass
        
        if not api_key:
            api_key = os.environ.get("GROQ_API_KEY")
            
        if not api_key:
            return "Error: GROQ_API_KEY not found. Please set it in .streamlit/secrets.toml or as an environment variable."

        client = Groq(api_key=api_key)
        
        # Filter out empty points
        valid_points = [p.strip() for p in points if p.strip()]
        points_str = "\n".join([f"- {p}" for p in valid_points])

        prompt = f"""
You are an expert secretary drafting minutes of a meeting. 
Based on the following points, generate a professional, polite, and concise "Closing Remark" paragraph in Malay (Bahasa Melayu), as per the standard format for formal minutes of meeting in Malaysia.

Points:
{points_str}

The output should be a single paragraph. Do not include any other text or formatting.
"""

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a professional secretary crafting meeting minutes."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )

        return completion.choices[0].message.content.strip()

    except Exception as e:
        return f"Error during generation: {str(e)}"
