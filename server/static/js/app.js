const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const labels = {normal:'正常', mild:'轻度疲劳', moderate:'中度疲劳', severe:'重度疲劳'};
function toast(message){const node=$('#toast');if(!node)return;node.textContent=message;node.classList.add('show');setTimeout(()=>node.classList.remove('show'),2400)}
async function jsonRequest(url, options){const response=await fetch(url,options);const body=await response.json();if(!response.ok)throw new Error(body.error||'请求失败');return body}

$$('.segmented button').forEach(button=>button.addEventListener('click',()=>{$$('.segmented button').forEach(x=>x.classList.remove('active'));$$('.detect-panel').forEach(x=>x.classList.remove('active'));button.classList.add('active');$('#'+button.dataset.panel).classList.add('active')}));
if(location.hash && $(`[data-panel="${location.hash.slice(1)}"]`)) $(`[data-panel="${location.hash.slice(1)}"]`).click();

const images=$('#image-files');
images?.addEventListener('change',()=>{const label=document.querySelector('label[for="image-files"] span');label.textContent=images.files.length?`已选择 ${images.files.length} 张图片`:'支持多选，单次总大小不超过 100 MB'});
$('#image-submit')?.addEventListener('click',async()=>{if(!images.files.length)return toast('请先选择图片');const button=$('#image-submit');button.disabled=true;button.textContent='检测中…';const data=new FormData();[...images.files].forEach(file=>data.append('files',file));try{const body=await jsonRequest('/api/detect/images',{method:'POST',body:data});$('#image-empty').hidden=true;$('#image-results').innerHTML=body.results.map((item,index)=>`<article class="result-card"><img src="${URL.createObjectURL(images.files[index])}" alt="${item.filename} 检测预览"><div><span class="level ${item.level}">${labels[item.level]}</span><h3>${item.filename}</h3><p><span>疲劳分值</span><strong>${item.score}</strong></p><p><span>EAR / MAR</span><strong>${item.metrics.ear.toFixed(2)} / ${item.metrics.mar.toFixed(2)}</strong></p></div></article>`).join('');if(body.alert)showAlert()}catch(error){toast(error.message)}finally{button.disabled=false;button.textContent='开始检测'}});

const video=$('#video-file');
video?.addEventListener('change',()=>{if(!video.files.length)return;$('#video-name').textContent=video.files[0].name;$('#video-preview').src=URL.createObjectURL(video.files[0])});
$('#video-submit')?.addEventListener('click',async()=>{if(!video.files.length)return toast('请先选择视频');const data=new FormData();data.append('file',video.files[0]);try{const body=await jsonRequest('/api/detect/video',{method:'POST',body:data});$('#video-status').innerHTML=`<strong>任务已接收</strong><span>记录编号 #${body.record.id}</span>`}catch(error){toast(error.message)}});

let stream=null,timer=null;
$('#camera-start')?.addEventListener('click',async()=>{try{stream=await navigator.mediaDevices.getUserMedia({video:{width:{ideal:960},height:{ideal:540}},audio:false});$('#camera-preview').srcObject=stream;$('#camera-start').disabled=true;$('#camera-stop').disabled=false;timer=setInterval(processCameraFrame,500)}catch(error){toast('无法打开摄像头，请检查系统权限')}});
$('#camera-stop')?.addEventListener('click',stopCamera);
async function processCameraFrame(){const video=$('#camera-preview'),canvas=$('#camera-canvas');if(!video.videoWidth)return;canvas.width=video.videoWidth;canvas.height=video.videoHeight;canvas.getContext('2d').drawImage(video,0,0);try{const body=await jsonRequest('/api/detect/frame',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({frame:canvas.toDataURL('image/jpeg',.72)})});const r=body.result;const values=$$('#camera-metrics strong');values[0].textContent=r.metrics.ear.toFixed(2);values[1].textContent=r.metrics.mar.toFixed(2);values[2].textContent=r.metrics.pitch.toFixed(1);const level=$('#camera-level');level.className=`level ${r.level}`;level.textContent=labels[r.level];if(body.alert)showAlert()}catch(error){toast(error.message)}}
function stopCamera(){clearInterval(timer);stream?.getTracks().forEach(track=>track.stop());stream=null;$('#camera-start')&&( $('#camera-start').disabled=false);$('#camera-stop')&&( $('#camera-stop').disabled=true)}
function showAlert(){$('#severe-alert').hidden=false;$('#alert-close').focus()}
$('#alert-close')?.addEventListener('click',()=>$('#severe-alert').hidden=true);
window.addEventListener('beforeunload',stopCamera);

async function loadHistory(){const body=$('#history-body');if(!body)return;try{const payload=await jsonRequest('/api/records');body.innerHTML=payload.records.length?payload.records.map(record=>`<tr><td>${new Date(record.created_at).toLocaleString()}</td><td>${record.source_type==='image'?'图片':'视频'}</td><td>${record.source_name}</td><td><span class="level ${record.level}">${labels[record.level]}</span></td><td>${record.score}</td></tr>`).join(''):'<tr class="empty-row"><td colspan="5">暂无检测记录</td></tr>'}catch(error){toast(error.message)}}
$('#history-refresh')?.addEventListener('click',loadHistory);loadHistory();
