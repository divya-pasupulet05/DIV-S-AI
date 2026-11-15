import {useRef,useState} from "react";
import axios from "axios";
import {Bot,FileText,Send,UploadCloud,User,Sparkles,BookOpen,LoaderCircle} from "lucide-react";
const API=import.meta.env.VITE_API_BASE_URL||"";
export default function App(){
 const [file,setFile]=useState(null),[uploading,setUploading]=useState(false),[asking,setAsking]=useState(false);
 const [question,setQuestion]=useState(""),[notice,setNotice]=useState("");
 const [messages,setMessages]=useState([{role:"assistant",content:"Hi! I'm DIV'S AI, your document-aware AI assistant. Upload a PDF, TXT or Markdown file, then ask questions about its content."}]);
 const fileRef=useRef(null);
 async function upload(e){e.preventDefault();if(!file)return;setUploading(true);setNotice("");
  const body=new FormData();body.append("file",file);
  try{const r=await axios.post(`${API}/api/documents/upload`,body);setNotice(`Indexed ${r.data.original_filename}: ${r.data.chunks} chunks created.`);
   setMessages(p=>[...p,{role:"assistant",content:`I've indexed ${r.data.original_filename}. It produced ${r.data.chunks} searchable chunks. Ask me about it.`}]);setFile(null);if(fileRef.current)fileRef.current.value="";
  }catch(err){setNotice(err.response?.data?.detail||"Upload failed. Check the backend.")}finally{setUploading(false)}}
 async function send(e){e.preventDefault();const q=question.trim();if(!q||asking)return;setMessages(p=>[...p,{role:"user",content:q}]);setQuestion("");setAsking(true);
  try{const r=await axios.post(`${API}/api/chat`,{question:q});setMessages(p=>[...p,{role:"assistant",content:r.data.answer,sources:r.data.sources||[]}])}
  catch(err){setMessages(p=>[...p,{role:"assistant",content:`Request failed: ${err.response?.data?.detail||"Check backend and API configuration."}` }])}finally{setAsking(false)}}
 return <div className="layout"><aside><div className="brand"><div className="logo"><Sparkles/></div><div><b>DIV'S AI</b><small>RAG KNOWLEDGE ASSISTANT</small></div></div><label>WORKSPACE</label><div className="nav active"><BookOpen size={17}/> Document chat</div><div className="sidebox"><FileText/><h3>Ask your documents</h3><p>Upload knowledge and get answers grounded in your own content.</p></div><footer><i/> Gemini · LangChain · LangGraph</footer></aside>
 <main><header><div><small>YOUR AI WORKSPACE</small><h1>Document assistant</h1></div><span className="pill">● RAG pipeline active</span></header><section>
 <div className="upload"><div className="uploadtitle"><UploadCloud/><div><b>Knowledge base</b><p>Upload a PDF, TXT or Markdown file to give DIV'S AI context.</p></div></div>
 <form onSubmit={upload}><input ref={fileRef} type="file" accept=".pdf,.txt,.md" onChange={e=>setFile(e.target.files?.[0]||null)}/><button disabled={!file||uploading}>{uploading?<LoaderCircle className="spin"/>:<UploadCloud/>}{uploading?"Indexing...":"Upload & index"}</button></form>{notice&&<div className="notice">{notice}</div>}<small>Maximum file size: 15 MB · Files stored locally in this demo.</small></div>
 <div className="chat"><div className="chathead"><div className="boticon"><Bot/></div><div><b>Chat with DIV'S AI</b><small>Answers grounded in retrieved document context</small></div><em>RAG ENABLED</em></div>
 <div className="messages">{messages.map((m,i)=><div className={`row ${m.role}`} key={i}><div className={`avatar ${m.role}`}>{m.role==="assistant"?<Bot/>:<User/>}</div><div className="msg"><small>{m.role==="assistant"?"DIV'S AI":"You"}</small><article>{m.content}</article>{m.sources?.length>0&&<div className="sources"><b>Sources</b>{m.sources.map((s,j)=><span key={j}><FileText size={12}/>{s.filename}{s.page?` · Page ${s.page}`:""}</span>)}</div>}</div></div>)}{asking&&<div className="row assistant"><div className="avatar assistant"><Bot/></div><div className="msg"><small>DIV'S AI</small><article>Searching documents and generating an answer...</article></div></div>}</div>
 <form className="composer" onSubmit={send}><input value={question} onChange={e=>setQuestion(e.target.value)} placeholder="Ask a question about your uploaded documents..."/><button disabled={!question.trim()||asking}><Send/></button></form><div className="disclaimer">DIV'S AI can make mistakes. Verify important information against your original documents.</div></div>
 </section></main></div>}
