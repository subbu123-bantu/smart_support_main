import { useState } from "react";
import { createTicket } from "../services/api";
import { useNavigate } from "react-router-dom";
import { toast } from "react-toastify";

function CreateTicket() {

    const [title, setTitle] = useState("");
    const [description, setDescription] = useState("");

    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();

        try {

            await createTicket({
                title,
                description
            });

            toast.success("Ticket Created Successfully!");

            setTimeout(() => {
                navigate("/dashboard/");
            }, 1200);

        } catch (error) {

            console.log(error);

            toast.error("Failed to create ticket");

        }
    };

    return (
        <div>
            <h2>Create Ticket</h2>

            <input
                placeholder="title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
            />

            <br/><br/>

            <textarea
                placeholder="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
            />

            <br/><br/>

            <button onClick={handleSubmit}>
                Create Ticket
            </button>

        </div>
    );
}

export default CreateTicket;