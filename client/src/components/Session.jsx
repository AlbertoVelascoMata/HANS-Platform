import { React, useState, useEffect } from "react";

import Paper from '@mui/material/Paper';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import QuestionDetails from './QuestionDetails';
import BoardView from './BoardView';

export default function Session() {
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
