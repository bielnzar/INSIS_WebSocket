let socket;

function renderBoard(board) {
  const container = document.getElementById('board');
  container.innerHTML = '';
  board.forEach((cell, idx) => {
    const div = document.createElement('div');
    div.className = 'col-2 p-1';
    const btn = document.createElement('button');
    btn.className = 'btn btn-outline-dark btn-cell';
    btn.textContent = cell;
    btn.disabled = cell !== '';
    btn.onclick = () => socket.send(JSON.stringify({ type: 'move', index: idx }));
    div.appendChild(btn);
    container.appendChild(div);
  });
}

document.getElementById('joinBtn').onclick = () => {
  const code = document.getElementById('codeInput').value.trim();
  if (!code) return;
  const wsUrl = `ws://${location.host}/ws/${code}`;
  console.log('Connecting to', wsUrl);
  socket = new WebSocket(wsUrl);

  socket.onopen = () => {
    console.log('WebSocket opened');
    document.getElementById('status').classList.remove('d-none');
    document.getElementById('status').textContent = 'Connected. Waiting for opponent...';
  };

  socket.onmessage = ({ data }) => {
    const msg = JSON.parse(data);
    console.log('Message received', msg);
    if (msg.type === 'error') {
      alert(msg.message);
      socket.close();
      return;
    }
    if (msg.type === 'status') {
      document.getElementById('status').textContent = `Players: ${msg.players}/2`;
      if (msg.players === 2) {
        document.getElementById('board').classList.remove('d-none');
        renderBoard(['', '', '', '', '', '', '', '', '']);
      }
    }
    if (msg.type === 'update') {
      renderBoard(msg.board);
      document.getElementById('status').textContent = `Turn: ${msg.turn}`;
    }
  };

  socket.onclose = (event) => {
    console.log('WebSocket closed', event);
    alert('Connection closed or room full');
  };
};