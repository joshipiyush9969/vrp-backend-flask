# vrp-backend-flask
Algorithm runs here :)

## Initialize ##
git clone https://github.com/joshipiyush9969/vrp-backend-flask.git <br/>
cd vrp-backend-flask

## Run ##
virtualenv venv <br/>
venv\Scripts\activate <br/>
pip install requirements.txt <br/>
run app.py
<ul>
<li><b>Using Docker</b></li>
docker build -t vrp_python:1.0 .<br/>
docker run -d --rm -p 5000:5000 --name pythonapp_vrp vrp_python:1.0
</ul>
