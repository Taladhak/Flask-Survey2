from flask import Flask, request, render_template, redirect, flash, session
from flask_debugtoolbar import DebugToolbarExtension
from surveys import satisfaction_survey as survey


app=Flask(__name__)
app.config['SECRET_KEY'] = "oh-so-secret"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

debug = DebugToolbarExtension(app)  

RESPONSES_KEY = "responses"
CURRENT_SURVEY_KEY = 'current_survey'

@app.route("/")
def show_survey_start():

    return render_template("survey_start.html", survey=survey)

@app.route("/", methods=["POST"])
def pick_survey():
    survey_id = request.form['survey_code']
    if request.cookies.get(f"completed_{survey_id}"):
        return render_template("already-done.html")
    survey = surveys[survey_id]
    session[CURRENT_SURVEY_KEY] = survey_id

    return render_template("survey_start.html",
                           survey=survey)


@app.route("/begin", methods=["POST"])
def start_survey():
    session[RESPONSES_KEY] = []

    return redirect("/questions/0")


@app.route("/answer", methods=["POST"])
def handle_question():
    choice = request.form['answer']
    text = request.form.get("text", "")
#add response to the session
    responses = session[RESPONSES_KEY]
    responses.append({"choice": choice, "text": text})

    session[RESPONSES_KEY] = responses
    survey_code = session[CURRENT_SURVEY_KEY]
    survey = surveys[survey_code]

    if (len(responses) == len(survey.questions)):
  
        return redirect("/complete")

    else:
        return redirect(f"/questions/{len(responses)}")


@app.route("/questions/<int:qid>")
def show_question(qid):
    responses = session.get(RESPONSES_KEY)
    survey_code = session[CURRENT_SURVEY_KEY]
    survey = surveys[survey_code]

    if (responses is None):
  
        return redirect("/")

    if (len(responses) == len(survey.questions)):
   
        return redirect("/complete")

    if (len(responses) != qid):
        # Trying to access questions out of order.
        flash(f"Invalid question id: {qid}.")
        return redirect(f"/questions/{len(responses)}")

    question = survey.questions[qid]

    return render_template(
        "question.html", question_num=qid, question=question)


@app.route("/complete")
def say_thanks():
    survey_id = session[CURRENT_SURVEY_KEY]
    survey = surveys[survey_id]
    responses = session[RESPONSES_KEY]

    html = render_template("completion.html",
                           survey=survey,
                           responses=responses)

    # Set cookie noting this survey is done so they can't re-do it
    response = make_response(html)
    response.set_cookie(f"completed_{survey_id}", "yes", max_age=60)
    return response
