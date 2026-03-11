import { useParams } from "react-router-dom"
import { useEffect,useState } from "react"
import { getTicketById } from "../services/api"

function TicketDetails(){

    const {id} = useParams()

    const [ticket,setTicket] = useState(null)

    useEffect(()=>{

    getTicketById(id)
    .then(res=>{
    setTicket(res.data)
    })

    },[])

    if(!ticket) return <p>Loading...</p>

    return(

        <div>

            <h2>{ticket.title}</h2>

            <p>{ticket.description}</p>

            <p>Status: {ticket.status}</p>

            <p>Priority: {ticket.priority}</p>

        </div>

    )

}

export default TicketDetails