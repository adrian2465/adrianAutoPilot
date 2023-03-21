from flask import Flask 
from flask import render_template
from modules.brain import getInstance as get_brain
from modules.status import DISABLED as STATUS_DISABLED, ENABLED as STATUS_ENABLED
from modules.sensors import readGPSDirection

app = Flask(__name__)

brain = get_brain()

@app.route("/")
def index():
  global brain
  return render_template('mainNav.html', status=brain.get_status(), course=brain.get_course())

@app.route("/getstatus")
def get_status():
  global brain
  return brain.get_status()

@app.route("/status/<newStatus>")
def update_status(newStatus:str):
  global brain
  msg=""
  if newStatus == 'enable':
    brain.set_status(STATUS_ENABLED)
    brain.set_course(readGPSDirection())
  elif newStatus == 'disable':
    brain.set_status(STATUS_DISABLED)
  else:
    msg="ERROR: status command must be enable or disable"
  return render_template('mainNav.html', status=brain.get_status(), course=brain.get_course(), msg=msg)

@app.route("/course/<courseAdjustment>")
def adjust_course(courseAdjustment:str):
  global brain
  msg = ""
  print(type(int(courseAdjustment)))
  print(int(courseAdjustment))
  brain.adjust_course(int(courseAdjustment))
  return render_template('mainNav.html', status=brain.get_status(), course=brain.get_course(), msg=msg)

@app.route("/messages")
def get_messages():
  global brain
  return brain.get_messages()


if __name__ == "__main__":
  print("This is not meant to run as an application.")
  print("Use Flask: flask --app autopilotWebApp run")


