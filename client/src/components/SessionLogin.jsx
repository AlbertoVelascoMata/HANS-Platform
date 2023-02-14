import { React, useState } from "react";
import { useNavigate } from "react-router-dom";

import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
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

export default function Login() {
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
