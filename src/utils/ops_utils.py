import re


def postprocess(content: str):
    content = content.strip()
    content = re.sub(r'^(V/v |Số)', '', content)
    content = re.sub(r'^[":.\s]+', '', content)
    content = ' '.join(content.split())
    if content and content[0].isalpha():
        content = content.capitalize()
        
    if content == "" or content == None:
        return " "
    return content