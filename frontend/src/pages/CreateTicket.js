import { useState } from "react";
import { createTicket } from "../services/api";
import { useNavigate } from "react-router-dom";

function CreateTicket(){
    const [title,setTitle]=useState("")
    const [description,setDescription]=useState("")

    const navigate=useNavigate()

    const handleSubmit = async (e) =>{
        e.preventDefault();

        await createTicket({
            title,
            description
        })
        alert("Ticket Created");
        navigate("/dashboard/");
    }

    return (
        <div>
            <h2>Create Ticket</h2>

            <input 
                placeholder="title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
            />

            <textarea
                placeholder="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)} 
            />

            <button onClick={handleSubmit}>Create Ticket
            </button>
        </div>
    )
}
export default CreateTicket;