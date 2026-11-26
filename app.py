from flask import Flask, render_template, request,redirect,url_for,session
from weather import agent
import uuid
app= Flask(__name__)
# set a secret key for session management
app.secret_key = 'your_secret_key'  # Replace

@app.route("/")
def home():
    session['thread_id'] = str(uuid.uuid4())  # Generate a unique thread ID for each session
    if 'messages' not in session:
        session['messages'] = []
    return render_template("chat.html", messages=session['messages'])

@app.route("/send", methods=["POST"])
def weather():
    user_input = request.form["user_input"]
    user_lat=request.form.get('latitude')
    user_lon=request.form.get('longitude')
    session.setdefault('messages', []) #
    if user_lat and user_lon:
        session['user_location'] = {'lat': user_lat, 'lon': user_lon}
    response = agent.invoke({"messages":[{"role": "user","content": user_input}]},{"configurable":{"thread_id": session['thread_id']}})
    #print(response)
    session['messages'].append({'type': 'human', 'content': user_input})
    session['messages'].append({'type': 'ai', 'content': response['messages'][-1].content })
    session.modified = True  # Mark the session as modified to ensure it gets saved
    return redirect(url_for("home"))

app.run(debug=True)