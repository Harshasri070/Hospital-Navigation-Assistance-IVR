def check_ambiguity(text):

    if "doctor" in text.lower():
        return ["cardiology", "neurology"]

    return None