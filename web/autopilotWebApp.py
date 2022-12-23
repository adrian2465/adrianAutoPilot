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
  return render_template('mainNav.html', status=brain.getStatus(), course=brain.getCourse()) 
  
@app.route("/status/<newStatus>")
def update_status(newStatus:str):
  global brain
  msg=""
  if newStatus == 'enable':
    brain.setStatus(STATUS_ENABLED)
    brain.setCourse(readGPSDirection())
  elif newStatus == 'disable':
    brain.setStatus(STATUS_DISABLED)
  else:
    msg="ERROR: status command must be enable or disable"
  return render_template('mainNav.html', status=brain.getStatus(), course=brain.getCourse(), msg=msg) 

@app.route("/course/<courseAdjustment>")
def adjust_course(courseAdjustment:str):
  global brain
  msg = ""
  print(type(int(courseAdjustment)))
  print(int(courseAdjustment))
  brain.adjustCourse(int(courseAdjustment))
  return render_template('mainNav.html', status=brain.getStatus(), course=brain.getCourse(), msg=msg) 

@app.route("/messages")
def get_messages():
  global brain
  return brain.getMessages()


if __name__ == "__main__":
  print("This is not meant to run as an application.")
  print("Use Flask: flask --app autopilotWebApp run")


