

from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter 
from langchain_core.documents import Document
from youtube_transcript_api import YouTubeTranscriptApi
ytt_api = YouTubeTranscriptApi()

import fitz #pymuPDF


from utils import read_json, write_json


# write a function that takes a video_id and returns the transcript text
def get_transcript(video_id):
    """Fetch and join the transcript for a YouTube video.

    Args:
        video_id: YouTube video identifier (the part after `v=` in the URL).

    Returns:
        A single string containing the full transcript text in timeline order.
    """
    ytt_api = YouTubeTranscriptApi()
    transcript = ytt_api.fetch(video_id) 
    extracted = [script.text for script in transcript]
    joined = " ".join(extracted)
    return joined

def get_PDF_text(filepath_in):
    """Extract all text from a PDF file.

    Args:
        filepath_in: Path to the PDF file on disk.

    Returns:
        Concatenated text from every page in the document.
    """
    doc = fitz.open(filepath_in)

    pdf_text = ""
    for page in doc:
        pdf_text += page.get_text()

    doc.close()
    return pdf_text

def write_documnent_metadata(title, author, exercise_type, difficulty, text):
    """Build a metadata dictionary for a transcript document.

    Args:
        title: Title of the content.
        author: Creator or channel name.
        exercise_type: Activity category (e.g., yoga, HIIT).
        difficulty: Difficulty label.
        text: Raw transcript text to attach.

    Returns:
        Dictionary containing the provided metadata fields.
    """
    doc_metadata = {"title": title, "author": author, "exercise_type": exercise_type,  "difficulty": difficulty, "transcript": text}
    return doc_metadata

def write_metadata(video_id, difficulty, title, author, exercise_type, transcript):
    """Create metadata for a YouTube transcript with a constructed URL.

    Args:
        video_id: YouTube video identifier.
        difficulty: Difficulty label for the workout.
        title: Video title.
        author: Channel or creator name.
        exercise_type: Activity category.
        transcript: Raw transcript text.

    Returns:
        Dictionary containing metadata and the full YouTube URL.
    """
    full_url = f"https://www.youtube.com/watch?v={video_id}"
    metadata = {"video_id": video_id, "title": title, "author": author, "difficulty": difficulty, "exercise_type": exercise_type, "transcript": transcript, "full_url": full_url}
    return metadata


# Read that dictionary (data) back from the JSON
def clean_and_save_transcript(filepath_in, filepath_out):
    """Clean a transcript with an LLM and save updated metadata.

    Args:
        filepath_in: Path to the JSON file containing a `transcript` field.
        filepath_out: Destination path for the cleaned JSON metadata.

    Returns:
        None. Writes the cleaned metadata file to `filepath_out`.
    """
    # pull the raw transcript from the raw JSON dictionary
    # Step 1: Read the dictionary
    data = read_json(filepath_in)
    # Step 2: Get the raw transcript from it
    raw_transcript = data["transcript"]
    # Step 3: Clean it with GPT
    llm = ChatOpenAI(model='gpt-5')
    # invoke LLM to clean the and edit the raw_transcript, producing cleaned_text
    response = llm.invoke(f"Edit this document {raw_transcript}. Make the transcript clean and readable by a human." 
                        "Remove all line break characters '/n'. Clean all typos. Return ONLY the transcript." 
                        "NO comment from you.")
    # Step 4: Add cleaned text to dictionary
    cleaned_text = response.content # .content turns the response into a string
    data["clean_transcript"] = cleaned_text
    # remove raw transcript from metadata
    data.pop('transcript')
    # save and export
    cleaned_json_file = write_json(filepath_out, data)
    return cleaned_json_file



import re
def clean_classification_text(r):
    """Strip non-letter characters from an LLM response.

    Args:
        r: LLM response object with a `.content` string attribute.

    Returns:
        String containing only alphabetical characters and spaces.
    """
    create_string = r.content
    response_cleaned = re.sub(r'[^a-zA-Z]', ' ', create_string)
    return response_cleaned

def split_text_add_video_metadata(cleaned_json_dict):
    """Chunk cleaned transcript text and attach source metadata.

    Args:
        cleaned_json_dict: Path to a JSON file containing `clean_transcript`
            plus source metadata fields.

    Returns:
        List of LangChain `Document` objects with chunked text and metadata.
    """
    json_doc = read_json(cleaned_json_dict)
    cleaned_transcript = json_doc["clean_transcript"]

    metadata = {
    "video_id": json_doc["video_id"],
    "title": json_doc["title"],
    "author": json_doc["author"],
    "difficulty": json_doc["difficulty"],
    "exercise_type": json_doc["exercise_type"],
}
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_text(cleaned_transcript)

    chunked_documents = [Document(page_content=chunk, metadata=metadata) for chunk in chunks]

    return chunked_documents


def split_text_add_TEXT_metadata(cleaned_json_dict):
    """Chunk cleaned transcript text and attach minimal metadata.

    Args:
        cleaned_json_dict: Path to a JSON file containing `clean_transcript`
            plus text-level metadata fields.

    Returns:
        List of LangChain `Document` objects with chunked text and metadata.
    """
    json_doc = read_json(cleaned_json_dict)
    cleaned_transcript = json_doc["clean_transcript"]

    metadata = {
    "title": json_doc["title"],
    "author": json_doc["author"],
    "difficulty": json_doc["difficulty"],
    "exercise_type": json_doc["exercise_type"],
}
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_text(cleaned_transcript)

    chunked_documents = [Document(page_content=chunk, metadata=metadata) for chunk in chunks]

    return chunked_documents
