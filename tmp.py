from groq import Groq
import os
import dotenv
import streamlit as st
dotenv.load_dotenv()
def summarize_paragraph(paragraph):
    """Summarize the given paragraph into 1‑2 sentences.

    Parameters
    ----------
    paragraph : str
        The paragraph to be summarized. Must be a non‑empty string.

    Returns
    -------
    dict
        A dictionary with a single key ``summary`` containing the generated
        summary.

    Raises
    ------
    ValueError
        If ``paragraph`` is not a non‑empty string or if the ``GROQ_API_KEY``
        environment variable is missing.
    """
    # Step 1: Validate input
    if not isinstance(paragraph, str) or not paragraph.strip():
        raise ValueError("paragraph must be a non‑empty string")

    # Step 2: Retrieve API key from environment
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not set")

    # Step 3: Initialise Groq client (only api_key is passed)
    client = Groq(api_key=api_key)

    # Step 4: Build the user prompt
    user_message = (
        "Summarize the following paragraph in 1-2 sentences:\n\n"
        f"{paragraph}"
    )

    # Step 5: Call the LLM using the required model
    llm_response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": user_message}],
        temperature=0.5,
        max_tokens=150,
    )

    # Step 6: Extract the summary from the response
    summary_text = llm_response.choices[0].message.content.strip()

    # Step 7: Return the result with the exact required key
    return {"summary": summary_text}

# Streamlit UI for testing
st.title("Paragraph Summarizer")
st.write("Enter a paragraph below to get a 1 sentence summary.")
# Text area for user input
user_input = st.text_area(
    "Paragraph to summarize:",
    height=200,
    placeholder="Enter your paragraph here..."
)
# Button to trigger summarization
if st.button("Summarize"):
    if user_input:
        try:
            with st.spinner("Generating summary..."):
                result = summarize_paragraph(user_input)
            st.success("Summary generated!")
            st.write("**Summary:**")
            st.write(result["summary"])
        except ValueError as e:
            st.error(f"Error: {str(e)}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")
    else:
        st.warning("Please enter a paragraph to summarize.")
        
if __name__ == "__main__":
    # For direct script testing (optional)
    sample_paragraph = "Une corne de licorne est un objet légendaire, connu en Europe occidentale. Durant la majeure partie du Moyen Âge et des Temps modernes, il est décrit comme la corne unique qui orne le front de la licorne, dotée de nombreux pouvoirs de guérison et de vertus de contrepoison. Ces propriétés, supposées réelles dès le XIIIe siècle, en font l'un des remèdes les plus chers et les plus réputés de la Renaissance, utilisé jusque dans les cours royales. Les croyances liées à la « corne de licorne » influencent l'alchimie, à travers la médecine spagyrique. L'objet est à l'origine d'une série de tests sur ses propriétés de purification, relatés entre autres dans l'ouvrage d'Ambroise Paré Discours de la licorne, paru en 1582, qui annonce les prémices de la méthode expérimentale ; il suscite des écrits d'érudits visant à défendre la croyance en ces propriétés, ou au contraire à les tester et les mettre en doute."
    
    print("Sample Paragraph:")
    print(sample_paragraph)
    print("\nGenerated Summary:")
    print(summarize_paragraph(sample_paragraph)["summary"])