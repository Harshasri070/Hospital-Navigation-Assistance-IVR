from ivr_config import IVR_CONFIG

def generate_response(intent, entities=None):

    if intent in IVR_CONFIG:
        response = IVR_CONFIG[intent]["prompt"]

        if entities:
            for entity in entities:
                if entity["label"] == "LOC":
                    response += f" It is located near {entity['text']}."

        return response

    return "Sorry, I did not understand your request. Please ask about hospital departments."