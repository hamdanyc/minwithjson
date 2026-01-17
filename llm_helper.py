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

def summarize_financial_report(pdf_file):
    """
    Summarizes a financial report PDF using an LLM.
    """
    import pypdf
    
    try:
        # Extract text from PDF
        reader = pypdf.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
            
        if not text.strip():
            return "Error: Could not extract text from the PDF. It might be an image-based PDF."
            
        # Limit text length to avoid token limits (rough truncation)
        text = text[:15000] 

        # Retrieve API key
        import os
        api_key = None
        try:
            api_key = st.secrets.get("GROQ_API_KEY")
        except FileNotFoundError:
            pass
        
        if not api_key:
            api_key = os.environ.get("GROQ_API_KEY")
            
        if not api_key:
            return "Error: GROQ_API_KEY not found."

        client = Groq(api_key=api_key)
        
        prompt = f"""
You are an expert secretary drafting minutes of a meeting.
Please analyze the following text extracted from a quarterly financial statement PDF.
Summarize the key financial highlights into a single, professional paragraph in Malay (Bahasa Melayu).
Focus on:
1. Total Income (Pendapatan)
2. Total Expenditure (Perbelanjaan)
3. Current Balance (Baki Semasa)
4. Any significant anomalies or big items mentioned.

Do not use bullet points. Write it as a narrative paragraph suitable for "Agenda 4: Laporan Kewangan".

Extracted Text:
{text}
"""

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a professional secretary crafting meeting minutes."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=400
        )

        return completion.choices[0].message.content.strip()

    except Exception as e:
        return f"Error during summarization: {str(e)}"

def generate_new_matter(points):
    """
    Generates a professional paragraph for a new agenda item from a list of points.
    """
    if not points or all(not p.strip() for p in points):
        return ""

    try:
        # Retrieve API key
        import os
        api_key = None
        try:
            api_key = st.secrets.get("GROQ_API_KEY")
        except FileNotFoundError:
            pass
        
        if not api_key:
            api_key = os.environ.get("GROQ_API_KEY")
            
        if not api_key:
            return "Error: GROQ_API_KEY not found."

        client = Groq(api_key=api_key)
        
        # Filter out empty points
        valid_points = [p.strip() for p in points if p.strip()]
        points_str = "\n".join([f"- {p}" for p in valid_points])

        prompt = f"""
You are an expert secretary drafting minutes of a meeting. 
Based on the following points, generate a professional, detailed, and concise paragraph for a new agenda item in Malay (Bahasa Melayu), as per the standard format for formal minutes of meeting in Malaysia.

Points:
{points_str}

The output should be a single paragraph describing the discussion or decision. Do not include any other text or formatting.
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
