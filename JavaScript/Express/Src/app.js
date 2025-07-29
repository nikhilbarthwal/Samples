import express from 'express';
import { Devices } from './devices.js';
import session from 'express-session';

const app = express();
const port = 3000;


app.use(express.urlencoded({ extended: true }));
app.use(express.static('public'));
app.use(express.json());

app.use(session({
  secret: 'secret', // NOTE: In real life, this would be read from secret store
  resave: false,
  saveUninitialized: true,
  cookie: { secure: false } // set to true if using HTTPS
}));

const devices = new Devices('devices.json');

function action(msg, req, res, handler) {

  function response(msg) {
    if ('error' in msg)
      console.error(msg);
    else
      console.log(msg);
    res.send(JSON.stringify(msg));
  }

  console.log(msg, req.body);
  const param  = new Map(Object.entries(req.body));

  if (req.sessionID) {
    if (param.has('devId'))
      handler(param.get('devId'), req.sessionID, response);
    else
      response({ "error": "No Id found in body!" });
  } else response({ "error": "No session found!" });
}

app.get('/', (req, res) => {
  if (req.sessionID)
    res.send(`Hello from Netflix (Session ID: ${req.sessionID})!`);
  else
    res.send('Hello from Netflix!');
});

app.post('/search', (req, res) => {
  console.log('Received Search request:', req.body);
  const result = devices.search(new Map(Object.entries(req.body)))
  console.log('Search result:', result);
  res.send(result);
});

app.post('/start', (req, res) => {
  action('Received Start request:', req, res, devices.start);
});

app.post('/stop', (req, res) => {
  action('Received Stop request:', req, res, devices.stop);
});

app.post('/log', (req, res) => {
  action('Received Logs download request:', req, res, devices.log);
});

app.listen(port, () => {
  console.log(`Netflix device lab app running at http://localhost:${port}`);
});
