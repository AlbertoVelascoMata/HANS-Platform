
import mqtt from 'precompiled-mqtt';

const SessionStatus = Object.freeze({
    Joining: Symbol("joining"), // Getting session info and subscribing to MQTT topics
    Waiting: Symbol("waiting"), // Waiting for the question to be defined and loaded
    Active: Symbol("active"),   // Answering the question, all users are interacting
});

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

export {SessionStatus, Session};
