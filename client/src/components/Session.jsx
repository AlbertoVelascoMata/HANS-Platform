import { React, useRef, useState, useEffect } from "react";
import { Navigate, useNavigate } from "react-router-dom";

import Backdrop from '@mui/material/Backdrop';
import CircularProgress from '@mui/material/CircularProgress';
import CheckCircleOutlineRoundedIcon from '@mui/icons-material/CheckCircleOutlineRounded';
import Button from '@mui/material/Button';
import LogoutIcon from '@mui/icons-material/Logout';

import Paper from '@mui/material/Paper';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import QuestionDetails from './QuestionDetails';
import BoardView from './BoardView';

import mqtt from 'precompiled-mqtt';

class Session {
  constructor(sessionId, participantId, controlCallback, updateCallback) {
    console.log("SESSION CONSTRUCTOR CALLED");
    this.sessionId = sessionId;
    this.participantId = participantId;

    this.client = mqtt.connect(
      `ws://${window.location.hostname}:9001/`,
      {
        clean: true,
        connectTimeout: 4000,
      }
    );
    this.client.on('connect', () => {
      console.log('[MQTT] Client connected to broker');
      this.client.subscribe([
        `swarm/session/${sessionId}/control`,
        `swarm/session/${sessionId}/updates/+`,
      ], (err) => {
          if(!err) console.log("[MQTT] Subscribed to /swarm/session/#");
      });
    });
    this.client.on('message', (topic, message) => {
      const topic_data = topic.split('/', 5);
      if(
        (topic_data.length < 4)
        || (topic_data[0] !== 'swarm')
        || (topic_data[1] !== 'session')
        || !topic_data[2].length || isNaN(topic_data[2])
      ) {
        console.log(`[MQTT] Invalid topic '${topic}'`);
        return;
      }

      const sessionId = topic_data[2];
      if(sessionId !== this.sessionId) {
        console.log(`[MQTT] Unknown session ID '${sessionId}'`);
        return;
      }

      if(topic_data[3] === 'control') {
        controlCallback(JSON.parse(message));
      }
      else if(topic_data[3] === 'updates') {
        if(topic_data.length !== 5) {
          console.log('[MQTT] An update was received in a non-participant-specific topic');
          return;
        }
        const participantId = topic_data[4];
        if(participantId !== this.participantId) {  // Discard self updates
          updateCallback(participantId, JSON.parse(message));
        }
      }
    });
  }
  publishControl(controlMessage) {
    this.client.publish(
      `swarm/session/${this.sessionId}/control/${this.participantId}`,
      JSON.stringify(controlMessage)
    );
  }
  publishUpdate(updateMessage) {
    this.client.publish(
      `swarm/session/${this.sessionId}/updates/${this.participantId}`,
      JSON.stringify(updateMessage)
    );
  }
  close() {
    this.client.end();
  }
}

const SessionStatus = Object.freeze({
  Joining: Symbol("joining"), // Getting session info and subscribing to MQTT topics
  Waiting: Symbol("waiting"), // Waiting for the question to be defined and loaded
  Active: Symbol("active"),   // Answering the question, all users are interacting
});

const QuestionStatus = Object.freeze({
  Undefined: Symbol("undefined"), // No question defined
  Loading: Symbol("loading"),     // Question ID defined, but details were not retrieved yet
  Loaded: Symbol("loaded"),       // Question fully loaded, all details are available
});

export default function SessionView() {
  const navigate = useNavigate();
  const sessionRef = useRef(null);
  const [sessionStatus, setSessionStatus] = useState(SessionStatus.Joining);
  const [question, setQuestion] = useState({status: QuestionStatus.Undefined});
  const [userMagnetPosition, setUserMagnetPosition] = useState({x: 0, y: 0, norm: []});
  const [peerMagnetPositions, setPeerMagnetPositions] = useState({});
  const [centralCuePosition, setCentralCuePosition] = useState([]);

  const sessionId = sessionStorage.getItem('session_id');
  const participantId = sessionStorage.getItem('participant_id');
  const username = sessionStorage.getItem('username');

  useEffect(() => {
    if(!sessionId || !participantId || !username) return;

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
          setSessionStatus(SessionStatus.Waiting);
          if(data.question_id) {
            setQuestion({status: QuestionStatus.Loading, id: data.question_id});
          }
        });
      } else {
        res.text().then(msg => console.log(msg));
      }
    }).catch(error => {
      console.log(error);
    });

    sessionRef.current = new Session(sessionId, participantId,
      (controlMessage) => {
        switch(controlMessage.type) {
          case 'setup': {
            if(controlMessage.question_id === null) {
              setQuestion({status: QuestionStatus.Undefined});
            } else {
              setQuestion({
                status: QuestionStatus.Loading,
                id: controlMessage.question_id
              });
            }
            break;
          }
          case 'start': {
            setSessionStatus(SessionStatus.Active);
            break;
          }
          case 'stop': {
            setSessionStatus(SessionStatus.Waiting);
            break;
          }
          default: break;
        }
      },
      (participantId, updateMessage) => {
        setPeerMagnetPositions((peerPositions) => {
          return {
            ...peerPositions,
            [participantId]: updateMessage.data.position
          }
        });
      });
  }, [sessionId, participantId, username]);

  useEffect(() => {
    let ignore = false;
    if(question.status === QuestionStatus.Loading) {
      fetch(
        `/api/question/${question.id}`,
        {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
          },
        }
      ).then(res => {
        if(res.status === 200) {
          res.json().then(data => {
            if(!ignore) {
              setQuestion({
                status: QuestionStatus.Loaded,
                id: data.id,
                prompt: data.prompt,
                answers: data.answers,
                image: `/api/question/${data.id}/image`
              });
              sessionRef.current.publishControl({type: 'ready'});
            }
          });
        } else {
          res.text().then(msg => console.log(msg));
        }
      }).catch(error => {
        console.log(error);
      });
    }
    return () => { ignore = true };
  }, [question]);

  useEffect(() => {
    // Update central Cue based on magnet positions
    const usablePeerPositions = Object.keys(peerMagnetPositions).map(
      k => peerMagnetPositions[k]
    ).filter(peerPosition => peerPosition.length === userMagnetPosition.norm.length);
    setCentralCuePosition(
      usablePeerPositions.reduce(
        (cuePosition, peerPosition) => cuePosition.map(
          (value, i) => value + peerPosition[i]
        ),
        userMagnetPosition.norm
      ).map(value => value / (1 + usablePeerPositions.length))
    );
  }, [userMagnetPosition, peerMagnetPositions])

  // DEBUG-ONLY
  /*useEffect(() => {
    // The component was drawn for the first time, configure a 1-second interval to simulate peer updates
    const interval = setInterval(() => {
      setPeerMagnetPositions(peerPositions => peerPositions.map(
        peerPosition => 
          ((question.status === QuestionStatus.Loaded) && (peerPosition.length !== question.answers.length))
          ? new Array(question.answers.length).fill(0).map(_ => Math.random())
          : peerPosition.map(
            value => Math.min(1.1, Math.max(0, value + (Math.random() - 0.5) * 0.1))
          )
      ));
    }, 100);
    return () => clearInterval(interval);
  }, [question]);*/

  const onUserMagnetMove = (position) => {
    if(sessionStatus !== SessionStatus.Active) return;

    setUserMagnetPosition(position);
    sessionRef.current.publishUpdate({data: {position: position.norm}});
  };

  const handleLogout = () => {
    // TODO: User should double-check the intention to logout (showing a modal when the leave/logout button is pressed)

    // TODO: The server should be notified about the user leaving the session:
    //sessionRef.current.leave()

    sessionStorage.removeItem('session_id');
    sessionStorage.removeItem('participant_id');
    sessionStorage.removeItem('username');
    navigate('/');
  }

  return (!sessionId || !participantId || !username) ? (
    // User not logged in
    <Navigate to='/' />
  ) : (
    <>
      <Backdrop
        sx={{ color: '#fff', zIndex: (theme) => theme.zIndex.drawer + 1 }}
        open={sessionStatus !== SessionStatus.Active}
      >
        <Paper
          sx={{
            p: 4,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 3,
          }}
        >
          <Typography variant="h5" textAlign='center'>
            <b>Session {sessionId}</b>
          </Typography>
          {sessionStatus === SessionStatus.Joining ? (
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: 3,
              }}
            >
              <CircularProgress color="inherit" />
              <Typography component="span" textAlign='center'>
                Joining
              </Typography>
            </Box>
          ) : (
            <>
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: 1,
                }}
              >
                <CheckCircleOutlineRoundedIcon fontSize="large" color="success"/>
                <Typography component="span" textAlign='center'>
                  Joined!
                </Typography>
              </Box>
              <Typography component="span" textAlign='center' >
                {question.status === QuestionStatus.Loaded ? (
                  "Question ready! Session will start soon"
                ) : (
                  question.status === QuestionStatus.Loading ? (
                    "Retrieving question details"
                  ) : (
                    "Waiting for a question..."
                  )
                )}
              </Typography>
            </>
          )}
          <Button
            color="error"
            variant="outlined"
            startIcon={<LogoutIcon/>}
            onClick={handleLogout}
          >
            Leave session
          </Button>
        </Paper>
      </Backdrop>
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
            {question.status === QuestionStatus.Loaded ? question.prompt : "Question not defined yet"}
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
            image={question.status === QuestionStatus.Loaded ? question.image : ""}
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
            answers={question.status === QuestionStatus.Loaded ? question.answers : []}
            centralCuePosition={centralCuePosition}
            peerMagnetPositions={Object.keys(peerMagnetPositions).map(
              k => peerMagnetPositions[k]
            )}
            userMagnetPosition={userMagnetPosition}
            onUserMagnetMove={onUserMagnetMove}
          />
          </Paper>
        </Box>
      </Box>
    </>
  );
}
