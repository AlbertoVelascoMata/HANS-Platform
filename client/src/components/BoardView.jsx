import { React, useRef } from "react";

export default function BoardView({ answers, userMagnetPosition, peerMagnetPositions, centralCuePosition, onUserMagnetMove }) {
  const svg = useRef();

  const magnetSize = 30;
  const halfMagnetSize = magnetSize / 2;
  const answersRadius = 430;
  const answersTextRadius = answersRadius + 25;
  let answerPoints = [];
  let answersText = [];
  for(let i=0, angle = -Math.PI/2; i < answers.length; i++, angle += 2*Math.PI/answers.length) {
    answerPoints.push({
      x: ~~(answersRadius * Math.cos(angle)),
      y: ~~(answersRadius * Math.sin(angle))
    });
    answersText.push({
      x: ~~(answersTextRadius * Math.cos(angle)),
      y: ~~(answersTextRadius * Math.sin(angle)),
      text: answers[i]
    });
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
        points={answerPoints.map((p) => `${p.x},${p.y}`).join(' ')}
        stroke="blue"
        strokeWidth="5px"
        fill="none"
      />
      {answerPoints.map((p, i) => (
        <circle
          key={i}
          cx={p.x}
          cy={p.y}
          r="20"
          fill="lightgreen"
          stroke="blue"
          strokeWidth="2"
        />
      ))}
      {answersText.map((anchor, i) => (
        <text
          key={anchor.text}
          x={anchor.x}
          y={anchor.y}
          fill="black"
          fontSize="30"
          textAnchor={anchor.x === 0 ? "middle" : (anchor.x < 0 ? "end" : "start")}
          dominantBaseline={anchor.y === 0 ? "middle" : (anchor.y < 0 ? "ideographic" : "hanging")}
        >
          {anchor.text}
        </text>
      ))}
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
