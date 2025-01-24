


def replace_umlaute(string_to_clean):
    replacements = {
            'ä': 'ae',
            'ö': 'oe',
            'ü': 'ue',
            'Ä': 'Ae',
            'Ö': 'Oo',
            'Ü': 'Ue',
            'ß': 'ss'
            }
    for umlaut, replacement in replacements.items():
        string_to_clean = string_to_clean.replace(umlaut, replacement)
    return string_to_clean

def process_list(query_list):
    query_list = [replace_umlaute(query) for query in query_list]
    return query_list

def process_chat(chat_logs):
    for snippet in chat_logs:
        for key in snippet:
            if isinstance(snippet[key], str):
                snippet[key] = replace_umlaute(snippet[key])
    return chat_logs

def check_matricle_number(matricle_number=""):
    return len(matricle_number) >= 6
