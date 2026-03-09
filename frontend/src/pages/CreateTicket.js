import { useState } from "react";

function CreateTicket(){

const [title,setTitle]=useState("")
const [description,setDescription]=useState("")

const handleSubmit = async (e)=>{
 e.preventDefault()

 const token = localStorage.getItem("token");

 const res =await fetch("http://127.0.0.1:8000/api/tickets/",{
  method:"POST",
  headers:{
   "Content-Type":"application/json",
   "Authorization":`Bearer ${token}`
  },
  body:JSON.stringify({
   title,
   description
  })
 })
 if(res.ok){
   alert("Ticket Created Successfully")
   
   // reset form
   setTitle("")
   setDescription("")
 }
}
return(
<div>
<h2>Create Ticket</h2>
<form onSubmit={handleSubmit}>
<input
placeholder="title"
value={title}
onChange={(e)=>setTitle(e.target.value)}
/>
<textarea
placeholder="description"
value={description}
onChange={(e)=>setDescription(e.target.value)}
/>
<button>Create Ticket</button>
</form>
</div>
)
}
export default CreateTicket