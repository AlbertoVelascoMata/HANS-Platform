import { React, useRef, useState, useEffect } from "react";

import Backdrop from '@mui/material/Backdrop';

import Paper from '@mui/material/Paper';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import SessionStatusView from './StatusView';
import QuestionDetails from './QuestionDetails';
import BoardView from '../BoardView';

import { Session, SessionStatus } from '../../context/Session';
import { QuestionStatus } from '../../context/Question';


export default function SessionView({ sessionId, participantId, onLeave=()=>{} }) {
  const sessionRef = useRef(null);
  const [sessionStatus, setSessionStatus] = useState(SessionStatus.Joining);
  const [question, setQuestion] = useState({status: QuestionStatus.Undefined});
  const [userMagnetPosition, setUserMagnetPosition] = useState({x: 0, y: 0, norm: []});
  const [peerMagnetPositions, setPeerMagnetPositions] = useState({});
  const [centralCuePosition, setCentralCuePosition] = useState([]);

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
  }, [sessionId, participantId]);

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

  const onLeaveSessionClick = () => {
    // TODO: User should double-check the intention to logout (showing a modal when the leave/logout button is pressed)

    // TODO: The server should be notified about the user leaving the session:
    //sessionRef.current.leave()

    onLeave();
  }

  return (
    <>
      <Backdrop
        sx={{ color: '#fff', zIndex: (theme) => theme.zIndex.drawer + 1 }}
        open={sessionStatus !== SessionStatus.Active}
      >
        <SessionStatusView
          sessionId={sessionId}
          sessionStatus={sessionStatus}
          questionStatus={question.status}
          onLeaveClick={onLeaveSessionClick}
        />
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
