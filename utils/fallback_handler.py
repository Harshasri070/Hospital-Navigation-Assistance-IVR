def fallback_response(session):

    session["fail_count"] += 1

    if session["fail_count"] >= 3:
        return "I am transferring your call to a human operator."

    return "Sorry, I did not understand that. Could you please repeat?"