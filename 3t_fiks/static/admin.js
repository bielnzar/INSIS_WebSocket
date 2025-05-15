const genBtn = document.getElementById('genBtn');
const info   = document.getElementById('codes');
const sendBtn= document.getElementById('sendMsg');

genBtn.addEventListener('click', async () => {
  const res = await fetch('/generate',{method:'POST'});
  const {room,codes}=await res.json();
  info.style.display='block';
  info.innerText=`Room: ${room}\nKode: ${codes.join(', ')}`;
});

sendBtn.addEventListener('click', async () => {
  const msg=document.getElementById('adminMsg').value.trim();
  if(!msg)return;
  await fetch('/admin/message',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({msg})
  });
  document.getElementById('adminMsg').value='';
});
