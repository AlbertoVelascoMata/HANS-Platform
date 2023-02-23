import { React } from "react";

import CircularProgress from '@mui/material/CircularProgress';
import CheckCircleOutlineRoundedIcon from '@mui/icons-material/CheckCircleOutlineRounded';
import Button from '@mui/material/Button';
import LogoutIcon from '@mui/icons-material/Logout';

import Paper from '@mui/material/Paper';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import { SessionStatus } from '../../context/Session';
import { QuestionStatus } from '../../context/Question';

export default function SessionStatusView({ sessionId, sessionStatus, questionStatus, onLeaveClick=()=>{} }) {
  return (
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
            {questionStatus === QuestionStatus.Loaded ? (
              "Question ready! Session will start soon"
            ) : (
              questionStatus === QuestionStatus.Loading ? (
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
        onClick={onLeaveClick}
      >
        Leave session
      </Button>
    </Paper>
  );
}
