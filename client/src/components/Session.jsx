import { React, useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

import Backdrop from '@mui/material/Backdrop';
import CircularProgress from '@mui/material/CircularProgress';

import Paper from '@mui/material/Paper';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import QuestionDetails from './QuestionDetails';
import BoardView from './BoardView';

export default function Session() {
  const [loading, setLoading] = useState(true);
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
  const navigate = useNavigate();

  const sessionId = sessionStorage.getItem('session_id');
  const participantId = sessionStorage.getItem('participant_id');
  const username = sessionStorage.getItem('username');

  useEffect(() => {
    if(!sessionId || !participantId || !username) {
      navigate("/");
    }
  }, [navigate, sessionId, participantId, username]);

  const get_question_details = async (question_id) => {
    setQuestionImage(`/api/question/${question_id}/image`);
    await fetch(
      `/api/question/${question_id}`,
      {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
      }
    ).then(res => {
      if(res.status === 200) {
        res.json().then(data => {
          setQuestionPrompt(data.prompt);
          setAnswers(data.answers);
        });
      } else {
        res.text().then(msg => console.log(msg));
      }
    }).catch(error => {
      console.log(error);
    });
  };

  useEffect(() => {
    fetch(
      `/api/session/${sessionId}`,
      {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
      }
    ).then(res => {
      if(res.status === 200) {
        res.json().then(data => {
          setLoading(false);
          if(data.question_id) {
            get_question_details(data.question_id);
          }
        });
      } else {
        res.text().then(msg => console.log(msg));
      }
    }).catch(error => {
      console.log(error);
    });
  }, [sessionId]);

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

  return loading ? (
    <Backdrop
      sx={{ color: '#fff', zIndex: (theme) => theme.zIndex.drawer + 1 }}
      open={loading}
    >
      <Paper
        sx={{
          p: 2,
          display: 'flex',
          alignItems: 'center',
          gap: 3
        }}
      >
        <CircularProgress color="inherit" />
        <Typography component="span" textAlign='center'>
          Joining session {sessionId}
        </Typography>
      </Paper>
    </Backdrop>
  ) : (
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
