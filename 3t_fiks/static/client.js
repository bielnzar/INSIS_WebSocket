const socket = io({
    reconnection: false,
    timeout: 60000
  });
  
  let mySymbol;
  let hasSurrendered = false;
  
  //    HEARTBEAT 30 DETIK
  let inactivityTimer;
  function resetInactivity() {
    clearTimeout(inactivityTimer);
    inactivityTimer = setTimeout(() => {
      console.log('[Heartbeat] 30s tanpa aktivitas — memaksa reconnect');
      socket.disconnect();
      socket.connect();
    }, 30000);
  }
  
  // Reset timer pada event-event penting
  [
    'connect','joined','start','update','end',
    'pong_server','chat','admin_message'
  ].forEach(evt => {
    socket.on(evt, resetInactivity);
  });
  
  // Log di console agar jelas di browser saat connect/disconnect
  socket.on('connect', () => {
    console.log('[Socket] connected:', socket.id);
    resetInactivity();
  });
  socket.on('disconnect', () => {
    console.log('[Socket] disconnected');
  });
  
  //      JOIN ROOM
  document.getElementById('joinBtn').onclick = () => {
    const room = document.getElementById('room').value.trim();
    const code = document.getElementById('code').value.trim();
    if (!room || !code) return alert('Isi Room & Kode Anda');
    socket.emit('join', { room, code });
  };
  
  //     SOCKET EVENTS
  socket.on('joined', data => {
    mySymbol = data.symbol;
    document.getElementById('joinDiv').style.display = 'none';
    document.getElementById('game').style.display = 'block';
  });
  socket.on('start', d => updateStatus(d.turn));
  socket.on('update', d => { renderBoard(d.board); updateStatus(d.turn); });
  socket.on('end', handleEnd);
  socket.on('error', e => alert(e.msg));
  
  // Pesan dari server/admin
  socket.on('admin_message', d => {
    const el = document.getElementById('adminBroadcast');
    el.innerText = `Pesan Server: ${d.msg}`;
    el.style.display = 'block';
    resetInactivity();
  });
  
  // Pong dari server
  socket.on('pong_server', d => {
    measureLatency(d.ts);
    showPong();
  });
  
  // Chat antar client
  socket.on('chat', d => showChat(d.sender, d.msg));
  
  //    INTERAKSI BOARD
  document.querySelectorAll('.cell').forEach(btn =>
    btn.onclick = () => {
      socket.emit('move', {
        room: document.getElementById('room').value,
        index: parseInt(btn.dataset.index, 10)
      });
    }
  );
  
  //     SURRENDER
  document.getElementById('surrenderBtn').onclick = () => {
    hasSurrendered = true;
    socket.emit('surrender', { room: document.getElementById('room').value });
    // langsung kembali ke form login
    document.getElementById('game').style.display = 'none';
    document.getElementById('joinDiv').style.display = 'block';
  };
  
  //        PING
  document.getElementById('pingBtn').onclick = () => {
    socket.emit('ping_client', { ts: Date.now() });
  };
  
  //      CHAT SEND
  document.getElementById('chatSendBtn').onclick = () => {
    const msg = document.getElementById('chatInput').value.trim();
    if (!msg) return;
    socket.emit('chat', {
      room: document.getElementById('room').value,
      msg
    });
    document.getElementById('chatInput').value = '';
  };
  
  //       HELPERS
  const cells = document.querySelectorAll('.cell');
  
  function renderBoard(board) {
    board.forEach((v, i) => cells[i].innerText = v);
  }
  
  function updateStatus(turn) {
    const s = turn === mySymbol ? 'Giliran Anda' : 'Giliran Lawan';
    document.getElementById('status').innerText = `${s} (${turn})`;
  }
  
  function handleEnd({ result, board }) {
    // jika client ini yang surrender, abaikan event end
    if (hasSurrendered) return;
  
    renderBoard(board);
    // tampilkan modal hasil
    const modal = new bootstrap.Modal(document.getElementById('winnerModal'));
    document.getElementById('winnerText').innerText = result;
    modal.show();
  
    // setelah 10 detik, kembali ke login
    setTimeout(() => {
      modal.hide();
      socket.disconnect();
      window.location.reload();
    }, 10000);
  }
  
  function measureLatency(sentTs) {
    document.getElementById('latency').innerText = Date.now() - sentTs;
  }
  
  function showPong() {
    document.getElementById('lastPong').innerText = new Date().toLocaleTimeString();
  }
  
  function showChat(sender, msg) {
    const cb = document.getElementById('chatBox');
    const div = document.createElement('div');
    div.innerText = `${sender}: ${msg}`;
    cb.appendChild(div);
    cb.scrollTop = cb.scrollHeight;
  }
  
  // mulai heartbeat pertama
  resetInactivity();
  