import { useState, useRef, useEffect } from "react";

import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { useNavigate } from "react-router-dom";

import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import Paper from '@mui/material/Paper';
import FormControlLabel from '@mui/material/FormControlLabel';
import Checkbox from '@mui/material/Checkbox';
import Grid from '@mui/material/Grid';
import Grid2 from '@mui/material/Unstable_Grid2';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Container from '@mui/material/Container';

function SessionForm() {
  const [sessionId, setSessionId] = useState('');

  const navigate = useNavigate();

  async function join_session(e) {
    e.preventDefault();
    await fetch(`/api/session/${sessionId}`,
      { method: 'GET'}
    ).then(res => {
      if(res.status === 200) {
        res.json().then(data => {
            //$('#session-details').html(JSON.stringify(data));
            //$('#question-id').attr('value', data.question);
            navigate('/session');
        });
      } else {
          res.text().then(data => {
              //$('#session-details').html(`ERROR (${res.status}): ${data}`);
          });
      }
    }).catch(res => {

    });
  }
  return (
    <form onSubmit={join_session}>
      <label>
        Session:
        <input name="session-id" type="text" value={sessionId} onChange={(e) => setSessionId(e.target.value)} required />
      </label>
      <input type="submit" value="Join session"></input>
    </form>
  )
}

function Login() {
  const handleSubmit = (event) => {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    console.log({
      email: data.get('email'),
      password: data.get('password'),
    });
  };

  return (
  <Container component="main" maxWidth="xs">
    <Box
      sx={{
        marginTop: 8,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
      }}
    >
      <Typography component="h1" variant="h4">
        Join session
      </Typography>
      <Box component="form" onSubmit={handleSubmit} noValidate sx={{ mt: 1 }}>
        <TextField
          margin="normal"
          required
          fullWidth
          id="username"
          label="User name"
          name="username"
          autoComplete="username"
          autoFocus
        />
        <TextField
          margin="normal"
          required
          fullWidth
          id="session-id"
          name="session-id"
          label="Session ID"
        />
        <Button
          type="submit"
          fullWidth
          variant="contained"
          sx={{ mt: 3, mb: 2 }}
        >
          Join
        </Button>
      </Box>
    </Box>
  </Container>
  );
}

function BoardView({ answers, userMagnetPosition, peerMagnetPositions, centralCuePosition, onUserMagnetMove }) {
  const svg = useRef();

  const magnetSize = 30;
  const halfMagnetSize = magnetSize / 2;
  const answersRadius = 450;
  let points = [];
  for(let angle = -Math.PI/2; angle < 2*Math.PI; angle += 2*Math.PI/answers.length) {
    points.push({
      x: ~~(answersRadius * Math.cos(angle)),
      y: ~~(answersRadius * Math.sin(angle))})
  }

  function startDrag(event) {
    event.preventDefault();
    
    function mousemove(event) {
      event.preventDefault();
      let cursorPoint = svg.current.createSVGPoint();
      cursorPoint.x = event.clientX;
      cursorPoint.y = event.clientY;
      cursorPoint = cursorPoint.matrixTransform(svg.current.getScreenCTM().inverse());
      let newPosition = {
        x: Math.min(Math.max(cursorPoint.x, -500), 500),
        y: Math.min(Math.max(cursorPoint.y, -500), 500)
      };
      onUserMagnetMove(newPosition);
    }
    function mouseup(event) {
      document.removeEventListener("mousemove", mousemove);
      document.removeEventListener("mouseup", mouseup);
    }
    
    document.addEventListener("mousemove", mousemove);
    document.addEventListener("mouseup", mouseup);
  }

  return (
    <svg ref={svg}
      viewBox="-500 -500 1000 1000"
    >
      <polygon
        points={points.map((p) => `${p.x},${p.y}`).join(' ')}
        stroke="blue"
        strokeWidth="5px"
        fill="none"
      />
      <circle
          cx={centralCuePosition.x}
          cy={centralCuePosition.y}
          r="80"
          fill="#DDDDDD"
          stroke="black"
          strokeWidth="2"
        />
      <g transform={`translate(-${halfMagnetSize}, -${halfMagnetSize})`}>
        {peerMagnetPositions.map((point, i) => (
          <rect
            x={point.x}
            y={point.y}
            key={i}
            width={magnetSize}
            height={magnetSize}
            fill="#000000AA"
          />
        ))}
        <rect
          x={userMagnetPosition.x}
          y={userMagnetPosition.y}
          width={magnetSize}
          height={magnetSize}
          fill="#FF0000"
          onMouseDown={startDrag}
        />
      </g>
    </svg>
  );
}

function QuestionDetails({ image }) {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <img
        src={image}
        alt="question 1"
        width="100%"
      />
      <Typography component="h4" variant="h6" textAlign='center'>
        <b>Question 1</b>
      </Typography>
      <Typography component="span" textAlign='center'>
        00:00:30
      </Typography>
    </Box>
  )
}

function Session() {
  const [questionPrompt, setQuestionPrompt] = useState("");
  const [questionImage, setQuestionImage] = useState(
    'https://www.researchgate.net/profile/Tadakazu-Shimoda/publication/44602457/figure/fig1/AS:272139123163203@1441894431683/Tumor-budding-an-isolated-single-cancer-cell-or-a-cluster-composed-of-fewer-than-five_Q320.jpg'
  );
  const [answers, setAnswers] = useState(['Adipose', 'Tumoral stroma', 'Tumoral cells', 'Stroma', 'Cells']);
  const [userMagnetPosition, setUserMagnetPosition] = useState({x: 0, y: 0});
  const [peerMagnetPositions, setPeerMagnetPositions] = useState([
    {x: Math.random() * 800 - 400, y: Math.random() * 800 - 400},
    {x: Math.random() * 800 - 400, y: Math.random() * 800 - 400},
    {x: Math.random() * 800 - 400, y: Math.random() * 800 - 400},
    {x: Math.random() * 800 - 400, y: Math.random() * 800 - 400},
    {x: Math.random() * 800 - 400, y: Math.random() * 800 - 400},
    {x: Math.random() * 800 - 400, y: Math.random() * 800 - 400},
    {x: Math.random() * 800 - 400, y: Math.random() * 800 - 400},
  ]);
  const [centralCuePosition, setCentralCuePosition] = useState({x: 0, y: 0});

  // DEBUG-ONLY
  useEffect(() => {
    setQuestionPrompt("Classify this tissue");
    // The component was drawn for the first time, configure a 1-second interval to simulate peer updates
    const interval = setInterval(() => {
      setPeerMagnetPositions(peerPositions => peerPositions.map((p) => ({
        x: Math.min(Math.max(p.x + Math.random() * 30 - 15, -500), 500),
        y: Math.min(Math.max(p.y + Math.random() * 30 - 15, -500), 500)
      })));
    }, 100);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    // Update central Cue based on magnet positions
    setCentralCuePosition({
      x: peerMagnetPositions.reduce((sum, pos) => sum + pos.x, userMagnetPosition.x) / (1 + peerMagnetPositions.length),
      y: peerMagnetPositions.reduce((sum, pos) => sum + pos.y, userMagnetPosition.y) / (1 + peerMagnetPositions.length)
    });
  }, [userMagnetPosition, peerMagnetPositions])

  return (
    <Box
      component="main"
      height='100vh'
      sx={{
        display:'flex', 
        flexDirection: 'column',
      }}
    >
      <Paper
        component="header"
        elevation={2}
        sx={{
          m: 1,
          p: 1,
          borderRadius: 2
        }}
      >
        <Typography component="h1" variant="h4" textAlign='center'>
          {questionPrompt}
        </Typography>
      </Paper>
      <Box
        sx={{
          flex: 1,
          minHeight: 0,
          gap: '10px',
          m: 1,
          display: 'flex',
          alignItems: 'stretch',
        }}
      >
        <Paper
          variant="outlined"
          sx={{
            flex: 1, /* grow: 1, shrink: 1, basis: 0*/
            alignSelf: 'flex-start',
            bgcolor: '#EEEEEE',
            p: 1,
          }}
        >
          <QuestionDetails
            image={questionImage}
          />
        </Paper>
        <Paper
          elevation={2}
          sx={{
            flex: 2, // grow: 2, shrink: 2, basis: 0
            height: '100%',
            p: 1,
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <BoardView
            answers={answers}
            centralCuePosition={centralCuePosition}
            peerMagnetPositions={peerMagnetPositions}
            userMagnetPosition={userMagnetPosition}
            onUserMagnetMove={setUserMagnetPosition}
          />
        </Paper>
      </Box>
    </Box>
  )
}

function App() {
  return (
    <Router basename={process.env.PUBLIC_URL}>
      <div>
        <Routes>
          <Route path="/" element={<Login/>} />
          <Route path="/session" element={<Session/>} />
        </Routes>
      </div>
    </Router>
  )
}

export default App;
