from langchain_core.chat_history import InMemoryChatMessageHistory


chat_map = {}

def get_chat_history(session_id): 
    if session_id not in chat_map: 
        chat_map[session_id] = InMemoryChatMessageHistory() # stores session IDs (keys) and values (messages) as a dict
    return chat_map[session_id] # returns a dict with session ID and messages


def last_n_messages(session_id, n):
    last_chats = chat_map[session_id].messages[-n:]
    return last_chats


