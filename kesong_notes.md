# Notes by Kesong

## Server + Client data handling

I'm trying to use Flask (python) for the backend and axios (javascript/typescript) for the frontend.

Flask is installed in a virtual environment. To config/init:

```
# cd into the project folder
conda deactivate # if you use conda, deactivate it (repeat this line until you dont see "(base)" in your shell)
python3 -m venv venv
. ./venv/bin/activate
pip install flask
pip install flask-cors
```

To run Flask:

```
python app.py
```

To start Flask and React at the same time:

```
npm run start_both
```

Caveat: this will make Flask run in the background. To kill it:
```
lsof -i :8123 # check process on port
kill PID_FOUND # kill the python process behind flask
```

**USE THIS URL WHEN TESTING:** http://localhost:3000/?workerId=kesong

(You can change the name but the field `workerId` must be included.)

### Tutorials I used

https://towardsdatascience.com/build-deploy-a-react-flask-app-47a89a5d17d9

https://www.bezkoder.com/react-typescript-axios/

### current progress
- In FE `src/App.tsx`, there's a function `testDataFunc()` that sends a POST request.
- In BE `app.py`, the function `api_call()` handles the POST request.
- The POST request will append one line to a file on server, with name being the passed workerId.

### TODO
- actually write data passing based on experiment logic
- integrate with jsPysch (for instructions/consent etc.)